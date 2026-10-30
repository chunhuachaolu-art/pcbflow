# -*- coding: utf-8 -*-
"""D 层 demo 板构造验收测试（V5.0 P1 D 层；只测本任务产物，stdlib+pytest）。

覆盖：三板 fail-closed 载入、board_sha256 链复算、granularity 先验形状、
principle 条目逐条过 principle schema、demo-01 V2 几何与播种缺陷、
demo-02 DIFF/BUS 组引用、demo-03 层栈与网构成、builder 双跑字节等、
committed 文件 canonical 稳定性与 builder 同步。
"""
import hashlib
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from boards import build_demo_boards  # noqa: E402
from v5 import canonical, schema_loader  # noqa: E402
from v5.board import compute_board_sha256, load_board_file  # noqa: E402

BOARD_IDS = ["demo-01-v2-corridor", "demo-02-mixed-types", "demo-03-small-mixed"]
BOARDS_DIR = build_demo_boards.OUT_DIR
ALL_PTYPES = {"PWR", "CLK", "HS", "BUS", "DIFF", "MISC", "ANA", "ROUTED"}
# 每板 granularity 先验的 min_gap_mm（任务书指定：demo-01/02/03 = 2.0/1.5/3.0）
MIN_GAP_BY_BOARD = {"demo-01-v2-corridor": 2.0,
                    "demo-02-mixed-types": 1.5,
                    "demo-03-small-mixed": 3.0}

_PRINCIPLE_SCHEMA = schema_loader.load_schema(
    "principle_registry.v1.schema.json")["definitions"]["principle"]


def _board_path(bid):
    return os.path.join(BOARDS_DIR, "%s.board.v1.json" % bid)


def _load(bid):
    return load_board_file(_board_path(bid))


def _part(board, pid):
    return next(p for p in board["partitions"] if p["partition_id"] == pid)


def _ptypes(board):
    return [p["ptype"] for p in board["partitions"]]


@pytest.fixture(params=BOARD_IDS)
def board(request):
    """逐板参数化夹具（已过 fail-closed 载入）。"""
    return _load(request.param)


# ------------------------------------------------ 1. 载入与 provenance 链

def test_demo_board_loads(board):
    """三板 load_board_file 全过（schema+跨字段+哈希链 fail-closed）。"""
    assert board["schema_version"] == "v5.board.v1"
    assert board["board_id"] in BOARD_IDS


def test_board_sha256_recomputes(board):
    """board_sha256 重算一致（canonical 剔除本字段后 sha256）。"""
    assert board["provenance"]["board_sha256"] == compute_board_sha256(board)


def test_provenance_shapes(board):
    """source_type/adapter/哈希形态齐全。"""
    prov = board["provenance"]
    assert prov["source_type"] in ("v2_derived", "synthetic")
    assert len(prov["source_sha256"]) == 64 and len(prov["board_sha256"]) == 64
    assert prov["adapter"]


# ------------------------------------------------ 2. principle_registry

def test_principle_entries_pass_principle_schema(board):
    """principle 条目逐条过 principle schema 校验（v5.schema_loader）。"""
    for i, entry in enumerate(board["principle_registry"]):
        schema_loader.validate(entry, _PRINCIPLE_SCHEMA,
                               schema_loader.default_registry(),
                               "%s.principle_registry[%d]" % (board["board_id"], i))


def test_principle_entries_have_15_fields(board):
    """全部条目 15 字段齐（缺一不可），intent 双侧非空。"""
    required = set(_PRINCIPLE_SCHEMA["required"])
    for entry in board["principle_registry"]:
        assert required <= set(entry) and len(entry) == 15
        assert entry["intent"]["protects"] and entry["intent"]["sacrifices"]


def test_principle_source_hash_recomputes(board):
    """source_hash = sha256(canonical(剔除 source_hash 后的条目))。"""
    for entry in board["principle_registry"]:
        view = dict(entry)
        view.pop("source_hash")
        assert canonical.canonical_sha256(view) == entry["source_hash"]


def test_hard_principles_not_overridable(board):
    """hard 条目（如有）必须 overridable=false。"""
    for entry in board["principle_registry"]:
        if entry["hard_or_soft"] == "hard":
            assert entry["overridable"] is False


def test_granularity_principle_exactly_one(board):
    """granularity 条目恰 1 条/板，params 键齐且 min_gap_mm 按板取值。"""
    bid = board["board_id"]
    gran = [e for e in board["principle_registry"]
            if isinstance(e["compiled_rule"], dict)
            and e["compiled_rule"].get("kind") == "partition_granularity"]
    assert len(gran) == 1
    entry = gran[0]
    params = entry["compiled_rule"]["params"]
    assert set(params) == {"min_gap_mm", "group_types"}
    assert params["min_gap_mm"] == MIN_GAP_BY_BOARD[bid]
    assert params["group_types"] == ["BUS", "DIFF"]
    assert entry["principle_id"] == "P-PART-GRAN-DEMO" + bid.split("-")[1]
    assert entry["evidence_refs"] == ["V5.0-DEV-TASKBOOK §4 L1"]


def test_demo01_extra_principles_present():
    """demo-01 专属：走廊容量、check_only 复查、既有铜保护三原则在场。"""
    reg = _load("demo-01-v2-corridor")["principle_registry"]
    by_kind = {}
    for e in reg:
        rule = e["compiled_rule"]
        by_kind[rule.get("kind") if isinstance(rule, dict) else rule] = e
    cap = by_kind["corridor_capacity"]
    assert cap["compiled_rule"]["params"] == {"zone_id": "C1", "capacity_mm": 4.3}
    assert cap["target_freedom"] == "corridor"
    check = by_kind["check_only"]
    assert check["enforcement"] == "check" and check["compiled_rule"] == "check_only"
    guard = by_kind["existing_copper_guard"]
    assert guard["scope"] == "ptype:ROUTED"
    assert guard["compiled_rule"]["params"] == {"min_gap_mm": 1.0}


def test_demo02_demo03_zone_ptype_principles():
    """demo-02/03 各配 ≥2 条与板内 zone/ptype 对应的原则（granularity 之外）。"""
    for bid, kinds in [("demo-02-mixed-types", 2), ("demo-03-small-mixed", 2)]:
        reg = _load(bid)["principle_registry"]
        extra = [e for e in reg
                 if not (isinstance(e["compiled_rule"], dict)
                         and e["compiled_rule"].get("kind") == "partition_granularity")]
        assert len(extra) >= kinds
        scopes = " ".join(e["scope"] for e in extra)
        rules = [e["compiled_rule"].get("kind") for e in extra
                 if isinstance(e["compiled_rule"], dict)]
        assert "layer_preference" in rules and "equal_length_group" in rules
        # scope 与板内真实 zone/partition 对应
        board = _load(bid)
        zone_ids = {z["zone_id"] for z in board["zones"]}
        part_ids = {p["partition_id"] for p in board["partitions"]}
        for e in extra:
            scope = e["scope"]
            if scope.startswith("zone:"):
                assert scope.split(":", 1)[1] in zone_ids
            elif scope.startswith("partition:"):
                assert scope.split(":", 1)[1] in part_ids


# ------------------------------------------------ 3. demo-01 V2 几何与播种缺陷

def test_demo01_zones_exact():
    """四个 zone 矩形与 C1 capacity 精确断言。"""
    board = _load("demo-01-v2-corridor")
    zones = {z["zone_id"]: z for z in board["zones"]}
    assert zones["K1"]["rect"] == {"x_min": 0.0, "y_min": 16.0, "x_max": 30.0, "y_max": 24.0}
    assert zones["K1"]["kind"] == "keepout" and zones["K1"]["layers"] == "all"
    assert zones["K2"]["rect"] == {"x_min": 36.0, "y_min": 16.0, "x_max": 50.0, "y_max": 24.0}
    assert zones["K2"]["kind"] == "keepout" and zones["K2"]["layers"] == "all"
    assert zones["C1"]["rect"] == {"x_min": 30.0, "y_min": 0.0, "x_max": 36.0, "y_max": 40.0}
    assert zones["C1"]["kind"] == "corridor" and zones["C1"]["layers"] == "signal"
    assert zones["C1"]["capacity"] == 4.3
    assert "[30.85,35.15]" in zones["C1"]["note"]
    assert zones["ANA"]["rect"] == {"x_min": 20.0, "y_min": 8.0, "x_max": 28.0, "y_max": 15.0}
    assert zones["ANA"]["kind"] == "sensitive"


def test_demo01_p8_seeded_defect_in_data():
    """P8 播种缺陷在场：planned_width 0.5 < w_min 0.8（缺陷写在数据里）。"""
    p8 = _part(_load("demo-01-v2-corridor"), "P8")
    assert p8["planned_width"] == 0.5
    assert p8["width_prior"]["w_min"] == 0.8
    assert p8["planned_width"] < p8["width_prior"]["w_min"]
    assert p8["current_a"] == 2.0


def test_demo01_v2_provenance_chain():
    """demo-01 source_sha256 = V2 源模板文件字节哈希；adapter=v2derive v1.0.0。"""
    prov = _load("demo-01-v2-corridor")["provenance"]
    assert prov["source_type"] == "v2_derived"
    assert prov["adapter"] == "v2derive v1.0.0"
    assert prov["source_uri"] == build_demo_boards.V2_SOURCE_PATH
    actual = hashlib.sha256(open(build_demo_boards.V2_SOURCE_PATH, "rb").read()).hexdigest()
    assert prov["source_sha256"] == actual


def test_demo01_partitions_match_v2_table():
    """P1–P9 照 V2 分区表：几何/宽度/瓶颈/既布逐项断言。"""
    board = _load("demo-01-v2-corridor")
    assert [p["partition_id"] for p in board["partitions"]] == ["P%d" % i for i in range(1, 10)]
    p1 = _part(board, "P1")
    assert p1["geometry"]["endpoints"] == [[2.0, 38.0], [44.0, 38.0]]
    assert p1["planned_width"] == 1.2 and p1["width_prior"] == {"w_min": 0.6, "w_max": 1.4}
    assert p1["bottleneck"] == {"span": [8.0, 10.0], "usable_width": 1.0}
    p3 = _part(board, "P3")
    assert p3["geometry"]["endpoints"] == [[16.0, 4.0], [16.0, 36.0]]
    assert p3["width_prior"]["w_min"] == 0.2 and p3["ptype"] == "HS"
    p4 = _part(board, "P4")
    assert p4["geometry"]["centerline"] == [[32.6, 4.0], [32.6, 36.0]]
    assert p4["geometry"]["occupancy_mm"] == 3.3
    assert p4["geometry"]["copper_band"] == [30.95, 34.25]
    assert _part(board, "P7")["geometry"]["endpoints"] == [[2.0, 36.7], [44.0, 36.7]]
    assert _part(board, "P9")["geometry"]["endpoints"] == [[2.0, 36.1], [44.0, 36.1]]
    assert _part(board, "P7")["ptype"] == "ROUTED" and _part(board, "P9")["ptype"] == "ROUTED"
    assert _part(board, "P1")["speed_class"] and _part(board, "P8")["speed_class"]


def test_demo01_nets_one_to_one():
    """nets 按 V2 分区表命名，与 P1–P9 一一引用。"""
    board = _load("demo-01-v2-corridor")
    pairs = [(n["net_id"], n["partitions"]) for n in board["nets"]]
    assert dict(pairs) == {"PWR-5V": ["P1"], "CLK-200M": ["P2"], "ETH-MAC": ["P3"],
                           "BUS-FMC": ["P4"], "MISC1": ["P5"], "MISC2": ["P6"],
                           "ROUTED-P7": ["P7"], "PWR-3V3-BR": ["P8"], "ROUTED-P9": ["P9"]}


# ------------------------------------------------ 4. demo-02 / demo-03 构成

def test_demo02_diff_pair_shares_partition():
    """demo-02 DIFF 两网指向同一分区。"""
    board = _load("demo-02-mixed-types")
    diff_parts = [p["partition_id"] for p in board["partitions"] if p["ptype"] == "DIFF"]
    assert len(diff_parts) == 1
    refs = [n["net_id"] for n in board["nets"] if n["partitions"] == diff_parts]
    assert len(refs) == 2 and sorted(refs) == ["DIFF-N", "DIFF-P"]


def test_demo02_bus_ribbon_group():
    """demo-02 BUS ribbon 分区：occupancy 2.1，4 网同指。"""
    board = _load("demo-02-mixed-types")
    bus = next(p for p in board["partitions"] if p["ptype"] == "BUS")
    assert bus["geometry"]["occupancy_mm"] == 2.1
    refs = [n["net_id"] for n in board["nets"] if bus["partition_id"] in n["partitions"]]
    assert len(refs) == 4
    assert all(pid in {p["partition_id"] for p in board["partitions"]}
               for n in board["nets"] for pid in n["partitions"])


def test_demo02_covers_all_ptypes():
    """demo-02 ≥12 网且分区 ptype 覆盖全部 8 种。"""
    board = _load("demo-02-mixed-types")
    assert len(board["nets"]) >= 12
    assert set(_ptypes(board)) == ALL_PTYPES


def test_demo02_pwr_width_prior_handcheck():
    """demo-02 PW1（1.0A）宽度先验手算可核：w_min=max(0.4×1.0, 0.3)=0.4。"""
    board = _load("demo-02-mixed-types")
    pw1 = _part(board, "PW1")
    assert pw1["current_a"] == 1.0
    assert pw1["width_prior"]["w_min"] == max(0.4 * 1.0, 0.3) == 0.4


def test_demo03_plane_layer_unavailable():
    """demo-03 四层含 plane 层 available=false。"""
    stack = _load("demo-03-small-mixed")["stackup"]
    assert len(stack) == 4
    planes = [l for l in stack if l["kind"] == "plane"]
    assert planes and all(l["available"] is False for l in planes)
    assert any(l["kind"] == "signal" and l["available"] for l in stack)


def test_demo03_composition():
    """demo-03：ANA 敏感区 + 走廊 capacity 1.8；网构成 PWR1.5A/DIFF 对/MISC2/ROUTED/CLK。"""
    board = _load("demo-03-small-mixed")
    zones = {z["zone_id"]: z for z in board["zones"]}
    sens = [z for z in zones.values() if z["kind"] == "sensitive"]
    corr = [z for z in zones.values() if z["kind"] == "corridor"]
    assert len(sens) == 1 and len(corr) == 1 and corr[0]["capacity"] == 1.8
    assert set(_ptypes(board)) == {"PWR", "DIFF", "MISC", "ROUTED", "CLK"}
    pw1 = _part(board, "PW1")
    assert pw1["current_a"] == 1.5
    assert pw1["width_prior"]["w_min"] == pytest.approx(max(0.4 * 1.5, 0.3))  # 手算 0.6
    diff_refs = [n["net_id"] for n in board["nets"] if n["partitions"] == ["DF1"]]
    assert sorted(diff_refs) == ["DIFF-N", "DIFF-P"]
    assert len(board["nets"]) == 7  # 枚举求和口径（DIFF 1 对=2 网），见 builder 文档化决定


# ------------------------------------------------ 5. builder 可重复性与落盘同步

def test_builder_double_run_byte_equal(tmp_path):
    """builder 双跑字节等：build 到两个临时目录，同名文件逐字节相等。"""
    dir_a, dir_b = tmp_path / "a", tmp_path / "b"
    build_demo_boards.build_all(str(dir_a))
    build_demo_boards.build_all(str(dir_b))
    for bid in BOARD_IDS:
        a = (dir_a / ("%s.board.v1.json" % bid)).read_bytes()
        b = (dir_b / ("%s.board.v1.json" % bid)).read_bytes()
        assert a == b


def test_committed_files_are_canonical_stable():
    """canonical 文件重读 canonical 字节不变，且与 builder 现算输出逐字节一致。"""
    builders = {"demo-01-v2-corridor": build_demo_boards.build_demo_01,
                "demo-02-mixed-types": build_demo_boards.build_demo_02,
                "demo-03-small-mixed": build_demo_boards.build_demo_03}
    for bid in BOARD_IDS:
        raw = open(_board_path(bid), "rb").read()
        reread = canonical.canonical_json(json.loads(raw.decode("utf-8")))
        assert raw == reread  # 重读再 canonical 序列化字节不变
        assert raw == canonical.canonical_json(builders[bid]())  # 与 builder 同步
