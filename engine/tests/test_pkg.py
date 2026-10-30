# -*- coding: utf-8 -*-
"""v5.pkg 单测：盲包组装（f8-01 工作区披露、board_sha256 对账、序数注记、
路由阶梯常量、A3 五通道）、schema 合法/非法（键路径）、write_pkg 落盘
provenance 注入兼容、双跑字节等、V2 锚点 demo-01 只读冒烟。
"""
import json
import os

import pytest

from fixtures_v2 import build_v2_board
from v5 import canonical, sidecar
from v5.board import compute_board_sha256
from v5.jitems import build_j_items
from v5.partition import build_partition_artifact
from v5.pkg import (PkgError, ROUTING_LADDER, CHANNELS, ORDINAL_NOTE,
                    COST_WEIGHTS, OUTPUT_NOTE, build_pkg, validate_pkg,
                    write_pkg)
from v5.schema_loader import SchemaViolation, validate_file


# --------------------------------------------------------------- 夹具（内联板+分区+冲突）

def gran_entry(min_gap_mm=2.0, principle_id="P-PART-GRAN-PKGTEST"):
    """分区聚类粒度先验条目（tests/test_partition.py 同模板；L1 必需）。"""
    from v5 import canonical as _canon
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
                                     "group_types": ["BUS", "DIFF"]}},
        "enforcement": "generation",
        "conflict_policy": {"conflicts_with": [], "yields_to": []},
        "evidence_refs": ["V5.0-DEV-TASKBOOK §4 L1"],
        "version": "1.0.0",
    }
    entry["source_hash"] = _canon.canonical_sha256(entry)
    return entry


def v2_board_with_gran():
    """V2 板 + 粒度先验（L1 可跑；板内容变更后链式重算 board_sha256）。"""
    board = build_v2_board()
    board["principle_registry"] = [gran_entry()]
    board["provenance"]["board_sha256"] = compute_board_sha256(board)
    return board


def make_conflicts(board, extra=()):
    """V2 场景冲突清单（内联 fixture；L3 overlay.py 未到货前的手写形状）。"""
    conflicts = [
        {"conflict_id": "CF-001", "kind": "straight_zone_cross",
         "subjects": ["P2"], "zone": "ANA", "layer": None,
         "basis": "P2 直线路径穿过 ANA", "arithmetic": None,
         "severity": "blocking"},
        {"conflict_id": "CF-002", "kind": "capacity_infeasible",
         "subjects": ["P3"], "zone": "C1", "layer": None,
         "basis": "P3 若留 F.Cu 过 C1，占用合计将超单层剩余容量",
         "arithmetic": "3.3+0.5+0.2=4.0 > 4.3", "severity": "blocking"},
        {"conflict_id": "CF-003", "kind": "capacity_infeasible",
         "subjects": ["P5"], "zone": "C1", "layer": None,
         "basis": "P5 若留 F.Cu 过 C1，占用合计将超单层剩余容量",
         "arithmetic": "3.3+0.5+0.2+0.2+0.5=4.7 > 4.3", "severity": "blocking"},
        {"conflict_id": "CF-004", "kind": "straight_zone_cross",
         "subjects": ["P5"], "zone": "K2", "layer": None,
         "basis": "P5 直线路径穿过 K2", "arithmetic": None,
         "severity": "advisory"},
        {"conflict_id": "CF-005", "kind": "bottleneck",
         "subjects": ["P1"], "zone": None, "layer": None,
         "basis": "P1 在 x∈[8,10] 瓶颈段可用宽度低于计划宽度",
         "arithmetic": None, "severity": "blocking"},
    ]
    conflicts.extend(extra)
    return {"artifact": "v5.conflicts.v1",
            "board_id": board["board_id"],
            "board_sha256": board["provenance"]["board_sha256"],
            "conflicts": conflicts}


def built(board=None):
    """（板, L1 工件, 冲突工件, 盲包）四件套。"""
    board = board or v2_board_with_gran()
    part = build_partition_artifact(board)
    conf = make_conflicts(board)
    return board, part, conf, build_pkg(board, part, conf)


# --------------------------------------------------------------- 组装：board_brief

def test_workspace_four_bounds_disclosed():
    """f8-01：布线工作区四边界必须在包内披露。"""
    board, _part, _conf, pkg = built()
    ws = pkg["board_brief"]["workspace"]
    assert ws == board["workspace"]
    for key in ("x_min", "y_min", "x_max", "y_max"):
        assert key in ws


def test_cost_model_weights_and_ordinal_note():
    board, _part, _conf, pkg = built()
    cm = pkg["board_brief"]["cost_model"]
    assert cm["weights"] == COST_WEIGHTS == {
        "detour_rate": 0.5, "direction_rate": 0.2, "via_cost": 4.0, "return_cost": 1.0}
    assert cm["ordinal_note"] == ORDINAL_NOTE == "仅用于排序，不要求输出数值"
    # V2 成本模型末条逐字语义（审计必修 2）：区间内调整零罚显式成对披露
    assert cm["width_adjust_in_interval_penalty"] == 0.0
    assert cm["width_adjust_note"] == "宽度在允许区间内调整 0 罚"


def test_hard_rules_and_stackup_passthrough():
    """R1..R6 原值透传 + 叠层透传。"""
    board, _part, _conf, pkg = built()
    assert pkg["board_brief"]["hard_rules"] == board["hard_rules"]
    assert pkg["board_brief"]["stackup"] == board["stackup"]
    assert set(pkg["board_brief"]["hard_rules"]) == {"R1", "R2", "R3", "R4", "R5", "R6"}


def test_zones_passthrough():
    board, _part, _conf, pkg = built()
    assert pkg["zones"] == board["zones"]
    assert [z["zone_id"] for z in pkg["zones"]] == ["K1", "K2", "C1", "ANA"]


# --------------------------------------------------------------- 对账与常量

def test_board_sha256_reconciliation():
    """证据链按 hash 对账（§3.1）：工件头与板复算不符即 fail-closed 报键路径。"""
    board, part, conf, pkg = built()
    assert pkg["board_sha256"] == board["provenance"]["board_sha256"]
    bad_conf = dict(conf, board_sha256="0" * 64)
    with pytest.raises(PkgError) as ei:
        build_pkg(board, part, bad_conf)
    assert ei.value.path == "conflicts_artifact.board_sha256"
    bad_part = dict(part, board_id="other-board")
    with pytest.raises(PkgError) as ei:
        build_pkg(board, bad_part, conf)
    assert ei.value.path == "partition_artifact.board_id"


def test_routing_ladder_constant():
    board, _part, _conf, pkg = built()
    assert pkg["routing_ladder"] == ROUTING_LADDER
    assert pkg["routing_ladder"] == ("时钟 > 高速串行 > 并行总线 > 电源 > 低速杂项；"
                                     "同档位先占用稀缺资源（走廊）者在前；"
                                     "仍平手按分区编号字典序")


def test_output_contract_five_channels():
    board, _part, _conf, pkg = built()
    oc = pkg["output_contract"]
    assert oc["note"] == OUTPUT_NOTE
    channels = oc["channels"]
    assert set(channels) == {"ranked_options", "ranked_combos", "routing_order",
                             "defect_scan", "principle_objection"}
    assert channels == CHANNELS  # A3：形状+枚举值逐字内嵌的常量
    assert channels["ranked_combos"][0]["P3"] == "留F.Cu过C1|换层B.Cu|换层In1"


# --------------------------------------------------------------- schema 合法/非法

def test_pkg_passes_schema():
    _board, _part, _conf, pkg = built()
    assert validate_pkg(pkg) is pkg
    assert validate_file(pkg, "pkg.v1.schema.json") is pkg


def test_broken_field_reports_key_path():
    """拆坏字段必须报具体键路径（fail-closed，P0 门口径）。"""
    _board, _part, _conf, pkg = built()

    bad = json.loads(json.dumps(pkg))
    bad["j_items"][0]["kind"] = "bogus"
    with pytest.raises(SchemaViolation) as ei:
        validate_pkg(bad)
    assert ei.value.path == "j_items[0].kind"

    bad2 = json.loads(json.dumps(pkg))
    del bad2["board_brief"]["workspace"]["x_min"]
    with pytest.raises(SchemaViolation) as ei:
        validate_pkg(bad2)
    assert ei.value.path == "board_brief.workspace.x_min"

    bad3 = json.loads(json.dumps(pkg))
    bad3["j_items"][0]["extra"] = 1
    with pytest.raises(SchemaViolation) as ei:
        validate_pkg(bad3)
    assert ei.value.path == "j_items[0].extra"


# --------------------------------------------------------------- 落盘（sidecar）

def test_write_pkg_roundtrip_provenance_compatible(tmp_path, monkeypatch):
    """落盘→重读仍过 schema：write_sidecar 注入的 provenance 头被顶层可选
    provenance 三键收纳（§3.1/§3.5）。"""
    monkeypatch.setattr(sidecar, "ALLOWED_ROOTS", (str(tmp_path),))
    _board, _part, _conf, pkg = built()
    path = os.path.join(str(tmp_path), "v2-scenario-golden.pkg.json")
    assert write_pkg(pkg, path) == path
    doc = json.load(open(path, encoding="utf-8"))
    assert doc["provenance"] == {"generator": "v5.pkg", "generator_version": "0.1.0",
                                 "board_sha256": pkg["board_sha256"]}
    assert doc["schema_version"] == "v5.pkg.v1"
    assert validate_file(doc, "pkg.v1.schema.json") == doc  # 注入后仍过 schema


def test_write_outside_allowed_root_rejected(tmp_path):
    """越界路径（out/ 之外）拒绝落盘（§3.5 sidecar 卫生）。"""
    _board, _part, _conf, pkg = built()
    with pytest.raises(sidecar.SidecarViolation):
        write_pkg(pkg, str(tmp_path / "evil.pkg.json"))


def test_double_run_bytes_equal(tmp_path, monkeypatch):
    """双跑字节等（§3.4 硬性测试）：内存 canonical 字节 + 落盘文件字节。"""
    monkeypatch.setattr(sidecar, "ALLOWED_ROOTS", (str(tmp_path),))
    p1 = built()
    p2 = built()
    assert canonical.canonical_json(p1[3]) == canonical.canonical_json(p2[3])
    f1 = os.path.join(str(tmp_path), "a.pkg.json")
    f2 = os.path.join(str(tmp_path), "b.pkg.json")
    write_pkg(p1[3], f1)
    write_pkg(p2[3], f2)
    assert open(f1, "rb").read() == open(f2, "rb").read()


# --------------------------------------------------------------- 分区表透传

def test_partition_table_matches_l1_artifact():
    """partition_table = L1 工件 partitions 透传：行数与 partition_id 一致。"""
    board, part, _conf, pkg = built()
    ids = [e["partition_id"] for e in part["partitions"]]
    got = [e["partition_id"] for e in pkg["partition_table"]]
    assert got == ids
    assert len(board["partitions"]) == 9
    assert len(got) == 8          # P7/P9 聚类合并 → 9 板分区 → 8 表行
    assert "PG-7" in got
    row = next(e for e in pkg["partition_table"] if e["partition_id"] == "PG-7")
    assert row["source_partitions"] == ["P7", "P9"]
    assert row["width_prior"] == {"w_min": 0.2, "w_max": 0.2}
    assert row["current_a"] == 0.0
    # 合并簇扩展字段走 sources_detail（板原值逐源承载，键缺省不造）
    assert row["sources_detail"] == [
        {"partition_id": "P7", "planned_width": 0.2, "note": "既布，路径固定"},
        {"partition_id": "P9", "planned_width": 0.2,
         "note": "既布；播种缺陷 D2：与 P7 净距 0.4 < 0.5"},
    ]
    assert "planned_width" not in row and "bottleneck" not in row


def test_partition_row_extensions_disclosed():
    """审计必修 1：单例行并 planned_width/bottleneck/板注——P8 播种缺陷与
    P1 瓶颈行注对盲包读者可见（V2 分区表逐行带计划宽/注口径）。"""
    board, _part, _conf, pkg = built()
    by_id = {e["partition_id"]: e for e in pkg["partition_table"]}
    p1 = by_id["P1"]
    assert p1["planned_width"] == 1.2
    assert p1["bottleneck"] == {"span": [8.0, 10.0], "usable_width": 1.0}
    assert p1["note"] == board["partitions"][0]["note"]  # 板注覆盖 L1 占位注
    p8 = by_id["P8"]
    assert p8["planned_width"] == 0.5                    # 播种缺陷 D1 素材在包内
    assert "播种缺陷 D1" in p8["note"]
    assert p8["width_prior"] == {"w_min": 0.8, "w_max": 1.6}
    assert by_id["P2"]["planned_width"] == 0.15
    # 板没有的键不造：P4 无 planned_width/bottleneck（fixtures 口径）
    assert "planned_width" not in by_id["P4"]
    assert "bottleneck" not in by_id["P4"]


def test_scan_and_endpoint_disclosure():
    """审计必修 3/4：扫描口径披露（保守包络 + 重叠≠冲突按 R5 复核 + V2/v5 基差）
    与端点/焊盘口径披露在场。"""
    _board, _part, _conf, pkg = built()
    scan = pkg["board_brief"]["scan_disclosure"]
    for needle in ("保守包络", "包络重叠不代表实际冲突", "R5", "实际几何", "0.6",
                   "±0.6", "铜宽大时结论可不同", "J6"):
        assert needle in scan, needle
    endp = pkg["board_brief"]["endpoint_disclosure"]
    for needle in ("焊盘半径", "端点按点处理", "回源板"):
        assert needle in endp, needle


def test_partition_geometry_three_readable_forms():
    """geometry 压缩为端点/中心线/占用带三种可读形态（照板数据原值）。"""
    board, _part, _conf, pkg = built()
    by_id = {e["partition_id"]: e for e in pkg["partition_table"]}
    p4 = by_id["P4"]["geometry"]
    assert p4["endpoints"] == [[32.6, 4.0], [32.6, 36.0]]
    assert p4["centerline"] == [[32.6, 4.0], [32.6, 36.0]]
    assert p4["occupancy_band"] == {"occupancy_mm": 3.3, "copper_band": [30.95, 34.25]}
    # 合并簇：各源分区端点按 source_partitions 序拼接（板原值），不造 centerline/占用带
    pg = by_id["PG-7"]["geometry"]
    assert pg["endpoints"] == [[2.0, 36.7], [44.0, 36.7], [2.0, 36.1], [44.0, 36.1]]
    assert "centerline" not in pg
    assert "occupancy_band" not in pg


# --------------------------------------------------------------- J 项接线

def test_j_items_wired_and_seeded_not_disclosed():
    """pkg.j_items = jitems 输出；混入的 seeded 缺陷冲突不出现在任何 J 项。"""
    board, part, _conf, pkg = built()
    board2 = v2_board_with_gran()
    conf2 = make_conflicts(board2, extra=[
        {"conflict_id": "CF-006", "kind": "seeded_width_defect",
         "subjects": ["P8"], "zone": None, "layer": None,
         "basis": "P8 计划宽 0.5 低于 R1 下限 0.8", "arithmetic": None,
         "severity": "advisory"}])
    pkg2 = build_pkg(board2, part, conf2)
    assert pkg2["j_items"] == build_j_items(conf2)
    subjects = {s for it in pkg2["j_items"] for s in it["subjects_partitions"]}
    assert "P8" not in subjects                      # 播种缺陷零披露
    joint = [it for it in pkg2["j_items"] if it["kind"] == "joint"]
    assert len(joint) == 1 and joint[0]["joint_group"] == "C1"


# --------------------------------------------------------------- V2 锚点：demo-01 只读冒烟

def test_demo01_smoke_joint_and_disposition():
    """boards/d/demo-01-v2-corridor.board.v1.json 只读冒烟：≥1 个 C1 joint 项
    且 ≥1 个 disposition 项；partition_table 9→8 与 L1 工件一致。"""
    path = os.path.join(os.path.dirname(sidecar.__file__), "..", "boards", "d",
                        "demo-01-v2-corridor.board.v1.json")
    with open(path, encoding="utf-8") as f:
        board = json.load(f)
    # 板哈希链自洽（只读复算，不写盘）
    assert compute_board_sha256(board) == board["provenance"]["board_sha256"]
    part = build_partition_artifact(board)
    conf = make_conflicts(board)
    pkg = build_pkg(board, part, conf)
    assert pkg["board_id"] == "demo-01-v2-corridor"
    assert pkg["board_sha256"] == board["provenance"]["board_sha256"]
    kinds = [it["kind"] for it in pkg["j_items"]]
    assert "joint" in kinds
    assert "disposition" in kinds
    joint = [it for it in pkg["j_items"] if it["kind"] == "joint"]
    assert any(it["joint_group"] == "C1" and
               it["subjects_partitions"] == ["P3", "P5"] for it in joint)
    assert len(pkg["partition_table"]) == 8
    assert ([e["partition_id"] for e in pkg["partition_table"]]
            == [e["partition_id"] for e in part["partitions"]])
    # 审计必修 1 冒烟：P8 播种缺陷计划宽 0.5 与 P1 瓶颈行注在表内可见
    by_id = {e["partition_id"]: e for e in pkg["partition_table"]}
    assert by_id["P8"]["planned_width"] == 0.5
    assert "播种缺陷 D1" in by_id["P8"]["note"]
    assert by_id["P1"]["bottleneck"] == {"span": [8.0, 10.0], "usable_width": 1.0}
    assert by_id["P1"]["planned_width"] == 1.2
    assert validate_pkg(pkg) is pkg
