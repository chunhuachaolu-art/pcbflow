# -*- coding: utf-8 -*-
"""7 类理念冲突对抗板验收测试（V5.0-DEV-TASKBOOK §5.1 冲突电池 / §6 D 层，P1）。

被测对象（只针对 adv-01..adv-07 七块板；boards/d 下的 demo 板归并行工作，不碰）：
  - load_board_file 全过 + provenance 哈希链重算一致；
  - 文件字节 = v5.canonical.canonical_json；builder 双跑同字节；
  - 每条 principle 过 principle_registry.v1 schema + 15 字段完整性 + source_hash 重算；
  - 每板 granularity 恰 1 条（逐字模板）；conflicts_with 对称；loser yields_to winner；
  - adv-07 hard 条目 overridable=false；adv-03/adv-06 note 算式数值在场；
  - 板几何关键断言（capacity/sensitive/平行 6mm/等长组成员）。
"""
import hashlib
import inspect
import json
import os

import pytest

from boards.build_adversarial_boards import BOARDS, BOARDS_DIR, write_all
from v5 import canonical
from v5.board import compute_board_sha256, load_board_file
from v5 import schema_loader

BOARD_IDS = sorted(BOARDS)

PRINCIPLE_FIELDS = [
    "principle_id", "name", "intent", "scope", "protected_resources",
    "target_freedom", "priority", "hard_or_soft", "overridable",
    "compiled_rule", "enforcement", "conflict_policy", "evidence_refs",
    "version", "source_hash",
]

# V2 默认硬规则（照 fixtures_v2.py 取值转录；按纪律不 import 之）
EXPECTED_HARD_RULES = {
    "R1": {"k_a": 0.4, "floor_mm": 0.3},
    "R2": {"min_distance_mm": 3.0, "max_parallel_mm": 5.0},
    "R3": {"unsplittable": True},
    "R4": {"return_via_required": True, "max_distance_mm": 2.0},
    "R5": {"min_clearance_mm": 0.5},
    "R6": {"plane_forbidden": True, "keepout_zones_forbidden": True},
}

# 每板冲突对的 winner/loser 预案（winner=高优先级、loser yields_to winner）
EXPECTED_PAIRS = {
    "adv-01-pwr-vs-bus": ("P-PWR-PRIORITY", "P-BUS-INTEGRITY"),
    "adv-02-clk-vs-short": ("P-CLK-ISOLATE", "P-SHORT-RUN"),
    "adv-03-diff-vs-capacity": ("P-DIFF-PAIRING", "P-CORRIDOR-BUDGET"),
    "adv-04-xtalk-vs-vias": ("P-XTALK-BUDGET", "P-VIA-FRUGAL"),
    "adv-05-eqlen-vs-layerpref": ("P-EQLEN-GROUP", "P-LAYER-PREF"),
    "adv-06-copper-vs-completion": ("P-COMPLETION", "P-COPPER-GUARD"),
    "adv-07-objection-vs-floor": ("P-R1-FLOOR", "P-WIDTH-SLIM"),
}

# 每板 granularity 的 min_gap_mm（各板不同，1.5–3.0）
EXPECTED_GRAN_GAP = {
    "adv-01-pwr-vs-bus": 2.0,
    "adv-02-clk-vs-short": 2.5,
    "adv-03-diff-vs-capacity": 1.5,
    "adv-04-xtalk-vs-vias": 2.25,
    "adv-05-eqlen-vs-layerpref": 3.0,
    "adv-06-copper-vs-completion": 1.75,
    "adv-07-objection-vs-floor": 2.75,
}


def _board_path(board_id):
    return os.path.join(BOARDS_DIR, board_id + ".board.v1.json")


def _load(board_id):
    return load_board_file(_board_path(board_id))


def _by_id(entries, key="principle_id"):
    return {e[key]: e for e in entries}


def _zone(board, zone_id):
    return _by_id(board["zones"], "zone_id")[zone_id]


def _part(board, partition_id):
    return _by_id(board["partitions"], "partition_id")[partition_id]


def _len_mm(partition):
    """分区 endpoints 两点欧氏距离（等长组直线长度断言用）。"""
    (x0, y0), (x1, y1) = partition["geometry"]["endpoints"]
    return ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5


# ------------------------------------------------------------- 全板通用

@pytest.mark.parametrize("board_id", BOARD_IDS)
def test_load_and_hash_chain(board_id):
    """七板 load_board_file 全过 + board_sha256 重算一致。"""
    board = _load(board_id)
    assert board["board_id"] == board_id
    assert board["provenance"]["board_sha256"] == compute_board_sha256(board)


@pytest.mark.parametrize("board_id", BOARD_IDS)
def test_file_bytes_are_canonical(board_id):
    """落盘字节 = canonical json（重序列化字节等）。"""
    raw = open(_board_path(board_id), "rb").read()
    parsed = json.loads(raw.decode("utf-8"))
    assert canonical.canonical_json(parsed) == raw


def test_builder_double_run_identical_bytes_and_match_repo(tmp_path):
    """builder 双跑字节相等，且与仓库内正式落盘文件字节相等。"""
    dir_a, dir_b = str(tmp_path / "a"), str(tmp_path / "b")
    paths_a = write_all(dir_a)
    paths_b = write_all(dir_b)
    assert set(paths_a) == set(BOARD_IDS)
    for bid in BOARD_IDS:
        bytes_a = open(paths_a[bid], "rb").read()
        bytes_b = open(paths_b[bid], "rb").read()
        bytes_repo = open(_board_path(bid), "rb").read()
        assert bytes_a == bytes_b == bytes_repo


@pytest.mark.parametrize("board_id", BOARD_IDS)
def test_principles_pass_schema(board_id):
    """每板 principle_registry 逐条过 principle_registry.v1 schema 的 principle 定义。"""
    board = _load(board_id)
    principle_def = schema_loader.load_schema(
        "principle_registry.v1.schema.json")["definitions"]["principle"]
    for i, entry in enumerate(board["principle_registry"]):
        schema_loader.validate(entry, principle_def,
                               schema_loader.default_registry(),
                               "principle_registry[%d]" % i)


@pytest.mark.parametrize("board_id", BOARD_IDS)
def test_fifteen_fields_complete(board_id):
    """对全部条目跑 15 字段清单比对（一项不可缺、无多余）。"""
    for entry in _load(board_id)["principle_registry"]:
        assert sorted(entry.keys()) == sorted(PRINCIPLE_FIELDS), entry["principle_id"]


@pytest.mark.parametrize("board_id", BOARD_IDS)
def test_principle_source_hash_recomputes(board_id):
    """条目 source_hash = sha256(canonical(剔除 source_hash 后条目字节))。"""
    for entry in _load(board_id)["principle_registry"]:
        view = dict(entry)
        view.pop("source_hash", None)
        assert entry["source_hash"] == canonical.canonical_sha256(view)


@pytest.mark.parametrize("board_id", BOARD_IDS)
def test_granularity_exactly_one(board_id):
    """每板分区粒度先验恰 1 条。"""
    grans = [e for e in _load(board_id)["principle_registry"]
             if e["principle_id"].startswith("P-PART-GRAN-")]
    assert len(grans) == 1


def test_granularity_template_verbatim():
    """粒度先验逐字模板：除 principle_id 后缀与 min_gap_mm 外全部字段与模板一致。"""
    for bid in BOARD_IDS:
        gran = [e for e in _load(bid)["principle_registry"]
                if e["principle_id"].startswith("P-PART-GRAN-")][0]
        assert gran["name"] == "分区聚类粒度先验"
        assert gran["intent"] == {"protects": "走廊通行容量",
                                  "sacrifices": "细粒度分配自由"}
        assert gran["scope"] == "partitioning"
        assert gran["protected_resources"] == ["corridor_capacity"]
        assert gran["target_freedom"] == "corridor"
        assert gran["priority"] == 50
        assert gran["hard_or_soft"] == "soft"
        assert gran["overridable"] is True
        assert gran["compiled_rule"]["kind"] == "partition_granularity"
        assert gran["compiled_rule"]["params"]["group_types"] == ["BUS", "DIFF"]
        assert gran["enforcement"] == "generation"
        assert gran["conflict_policy"] == {"conflicts_with": [], "yields_to": []}
        assert gran["evidence_refs"] == ["V5.0-DEV-TASKBOOK §5.1/§6 D 层"]
        assert gran["version"] == "1.0.0"


def test_granularity_min_gap_distinct_and_in_range():
    """各板 min_gap_mm 互不相同且落在 1.5–3.0。"""
    gaps = [EXPECTED_GRAN_GAP[bid] for bid in BOARD_IDS]
    assert len(set(gaps)) == len(gaps)
    for bid in BOARD_IDS:
        gran = [e for e in _load(bid)["principle_registry"]
                if e["principle_id"].startswith("P-PART-GRAN-")][0]
        gap = gran["compiled_rule"]["params"]["min_gap_mm"]
        assert gap == EXPECTED_GRAN_GAP[bid]
        assert 1.5 <= gap <= 3.0


def test_conflicts_with_symmetry():
    """conflicts_with 对称性：A 声明 B 则 B 声明 A（逐板全条目）。"""
    for bid in BOARD_IDS:
        reg = _by_id(_load(bid)["principle_registry"])
        for pid, entry in reg.items():
            for other_id in entry["conflict_policy"]["conflicts_with"]:
                assert other_id in reg, "%s: %s 引用注册表外条目" % (bid, pid)
                back = reg[other_id]["conflict_policy"]["conflicts_with"]
                assert pid in back, "%s: %s→%s 不对称" % (bid, pid, other_id)


def test_loser_yields_to_winner():
    """每板恰一对冲突：winner/loser 与预案一致；loser yields_to 非空且指向 winner；
    winner 的 yields_to 为空；priority winner > loser。"""
    for bid in BOARD_IDS:
        winner_id, loser_id = EXPECTED_PAIRS[bid]
        reg = _by_id(_load(bid)["principle_registry"])
        assert winner_id in reg and loser_id in reg
        winner, loser = reg[winner_id], reg[loser_id]
        assert loser_id in winner["conflict_policy"]["conflicts_with"]
        assert winner_id in loser["conflict_policy"]["conflicts_with"]
        assert loser["conflict_policy"]["yields_to"] == [winner_id]
        assert winner["conflict_policy"]["yields_to"] == []
        assert winner["priority"] > loser["priority"]


@pytest.mark.parametrize("board_id", BOARD_IDS)
def test_provenance_contract(board_id):
    """provenance：synthetic/hand/固定 source_uri/source_sha256=构造函数源码 sha256。"""
    board = _load(board_id)
    prov = board["provenance"]
    assert prov["source_type"] == "synthetic"
    assert prov["adapter"] == "hand"
    assert prov["source_uri"] == "boards/build_adversarial_boards.py#" + board_id
    expected = hashlib.sha256(
        inspect.getsource(BOARDS[board_id]).encode("utf-8")).hexdigest()
    assert prov["source_sha256"] == expected


@pytest.mark.parametrize("board_id", BOARD_IDS)
def test_hard_rules_v2_defaults(board_id):
    assert _load(board_id)["hard_rules"] == EXPECTED_HARD_RULES


@pytest.mark.parametrize("board_id", BOARD_IDS)
def test_nets_count_and_partition_refs(board_id):
    """每板 6–12 网；nets[].partitions 指向真实分区。"""
    board = _load(board_id)
    assert 6 <= len(board["nets"]) <= 12
    part_ids = {p["partition_id"] for p in board["partitions"]}
    for net in board["nets"]:
        assert net["partitions"]
        for pid in net["partitions"]:
            assert pid in part_ids


@pytest.mark.parametrize("board_id", BOARD_IDS)
def test_zones_present(board_id):
    """每板 zones ≥1（走廊/禁布/敏感配合冲突几何）。"""
    assert len(_load(board_id)["zones"]) >= 1


# ------------------------------------------------------------- 板几何断言

def test_adv01_corridor_capacity_critical():
    """adv-01：走廊容量与双方占用同场且恰好临界（账本口径 铜宽+0.5×相邻对）。"""
    board = _load("adv-01-pwr-vs-bus")
    corridor = _zone(board, "COR-C")
    assert corridor["capacity"] == 3.7
    ribbon = _part(board, "BUS-RIB")
    assert ribbon["geometry"]["occupancy_mm"] == 2.4      # 4×0.3 铜宽+3×0.4 对内距
    pwr = _part(board, "PW1")
    assert pwr["width_prior"]["w_min"] == 0.8             # R1: max(0.4×2.0, 0.3)
    # 账本口径手算：2.4 + 0.8 + 0.5×1 = 3.7 = capacity（零余量临界）
    assert abs(ribbon["geometry"]["occupancy_mm"] + 0.8 + 0.5 * 1 - corridor["capacity"]) < 1e-9
    # PWR 取 w_max 1.0 则溢出（3.9 > 3.7），ribbon 让位整体绕行
    assert ribbon["geometry"]["occupancy_mm"] + 0.5 + pwr["width_prior"]["w_max"] > corridor["capacity"]
    # 单信号层可用（B.Cu 不可用），容量即总量
    available = [l["id"] for l in board["stackup"] if l["available"] and l["kind"] == "signal"]
    assert available == ["F.Cu"]
    # 4 网 BUS ribbon 共用组分区（R3 整体不可拆）
    bus_nets = [n for n in board["nets"] if n["net_class"] == "BUS"]
    assert len(bus_nets) == 4 and all(n["partitions"] == ["BUS-RIB"] for n in bus_nets)
    assert "53.3" in corridor["note"] and "3.9>3.7" in corridor["note"]


def test_adv02_sensitive_zone_geometry():
    """adv-02：敏感区坐标在场；CLK 直线距敏感区 3.2mm>3.0（R2 合规）而原则要 5.0。"""
    board = _load("adv-02-clk-vs-short")
    sens = _zone(board, "SENS")
    assert sens["kind"] == "sensitive"
    assert (sens["rect"]["x_min"], sens["rect"]["y_min"],
            sens["rect"]["x_max"], sens["rect"]["y_max"]) == (20.0, 12.0, 26.0, 18.0)
    clk = _part(board, "CK1")
    (x0, y0), (x1, y1) = clk["geometry"]["endpoints"]
    assert y0 == y1 == 8.8                                # 直线水平最短
    assert _len_mm(clk) == pytest.approx(36.0)
    distance = sens["rect"]["y_min"] - y0
    assert distance == pytest.approx(3.2)
    assert distance > board["hard_rules"]["R2"]["min_distance_mm"]   # 3.2 > 3.0 合规
    assert distance < 5.0                                 # 但原则 P-CLK-ISOLATE 要 5.0
    assert "3.2" in sens["note"] and "+3.6" in sens["note"]          # 绕行使 CLK 变长
    isolate = _by_id(board["principle_registry"])["P-CLK-ISOLATE"]
    assert isolate["compiled_rule"]["params"]["min_distance_mm"] == 5.0


def test_adv03_diff_pair_partition_and_arithmetic():
    """adv-03：两网同分区（2 条平行 endpoints）、note 算式在场、容量声明 < 对占用。"""
    board = _load("adv-03-diff-vs-capacity")
    dp_nets = [n for n in board["nets"] if n["net_class"] == "DIFF"]
    assert {n["net_id"] for n in dp_nets} == {"DP-P", "DP-N"}
    assert all(n["partitions"] == ["DP1"] for n in dp_nets)          # 两网同分区
    dp = _part(board, "DP1")
    assert dp["ptype"] == "DIFF"
    (px0, py0), (px1, py1) = dp["geometry"]["endpoints"]             # P 线
    (nx0, ny0), (nx1, ny1) = dp["geometry"]["centerline"]            # N 线
    assert (py1 - py0) == pytest.approx(ny1 - ny0)                   # 两条平行 endpoints
    assert (ny0 - py0) == pytest.approx(0.6)                         # 对内耦合间距 0.6
    assert "0.6" in dp["note"]
    corridor = _zone(board, "COR-D")
    assert corridor["capacity"] == 1.0
    # capacity 账本口径：铜宽 0.3+0.3 + 0.5×相邻对 1 = 1.1 > 声明容量 1.0
    assert "0.3+0.3+0.5" in corridor["note"] and "1.1" in corridor["note"]
    pair_need = 0.3 + 0.3 + 0.5 * 1
    assert pair_need == pytest.approx(1.1)
    assert pair_need > corridor["capacity"]
    assert dp["geometry"]["occupancy_mm"] == pytest.approx(pair_need)


def test_adv04_parallel_run_geometry():
    """adv-04：aggressor/victim 平行恰 6.0mm>5.0、间距 2.4<3.0；让位结果在双方 note。"""
    board = _load("adv-04-xtalk-vs-vias")
    aggr = _part(board, "AG")
    vict = _part(board, "VI")
    (ax0, ay0), (ax1, ay1) = aggr["geometry"]["endpoints"]
    (vx0, vy0), (vx1, vy1) = vict["geometry"]["endpoints"]
    assert ay0 == ay1 and vy0 == vy1                      # 两条水平线
    overlap = min(ax1, vx1) - max(ax0, vx0)
    assert overlap == pytest.approx(6.0)                  # 平行走线段恰 6mm
    assert overlap > 5.0                                  # > max_parallel 触发原则预算
    gap = vy0 - ay0
    assert gap == pytest.approx(2.4)
    assert gap < 3.0                                      # < min_gap_mm
    reg = _by_id(board["principle_registry"])
    assert reg["P-XTALK-BUDGET"]["compiled_rule"] == {
        "kind": "crosstalk_budget",
        "params": {"max_parallel_mm": 5.0, "min_gap_mm": 3.0}}
    assert reg["P-VIA-FRUGAL"]["compiled_rule"] == {
        "kind": "via_frugal", "params": {"max_extra_vias": 1}}
    assert "P-XTALK-BUDGET" in aggr["note"]
    assert "P-VIA-FRUGAL" in vict["note"] and "让位" in vict["note"]
    assert "2 过孔" in vict["note"]                       # 缓解=换层 2 过孔 > 上限 1


def test_adv05_equal_length_group():
    """adv-05：等长组三网成员与 tolerance 在场；直线长度 40/38/37 与补偿量可算。"""
    board = _load("adv-05-eqlen-vs-layerpref")
    reg = _by_id(board["principle_registry"])
    group = reg["P-EQLEN-GROUP"]
    assert group["compiled_rule"]["kind"] == "equal_length_group"
    assert group["compiled_rule"]["params"]["tolerance_mm"] == 0.5
    members = group["compiled_rule"]["params"]["members"]
    assert members == ["EQ-A", "EQ-B", "EQ-C"]
    net_ids = {n["net_id"] for n in board["nets"]}
    assert set(members) <= net_ids                        # 成员是真实网
    lens = {mid: _len_mm(_part(board, pid))
            for mid, pid in zip(["EQ-A", "EQ-B", "EQ-C"],
                                ["EQA", "EQB", "EQC"])}
    assert lens["EQ-A"] == pytest.approx(40.0)            # 最长者直线沿优选方向
    assert lens["EQ-B"] == pytest.approx(38.0)            # 短者须蛇形补偿
    assert lens["EQ-C"] == pytest.approx(37.0)
    target = lens["EQ-A"] - group["compiled_rule"]["params"]["tolerance_mm"]
    assert lens["EQ-A"] - lens["EQ-B"] == pytest.approx(2.0)
    assert lens["EQ-A"] - lens["EQ-C"] == pytest.approx(3.0)
    assert "39.5" in _part(board, "EQB")["note"]          # 补偿目标 = 40.0-0.5
    pref = reg["P-LAYER-PREF"]
    assert pref["compiled_rule"] == {"kind": "layer_preference",
                                     "params": {"layer": "F.Cu", "direction": "h"}}


def test_adv06_gap_arithmetic():
    """adv-06：0.7mm 缝隙几何在场；note 算式数值在场；guard yields completion。"""
    board = _load("adv-06-copper-vs-completion")
    routed = _part(board, "RT1")
    assert routed["ptype"] == "ROUTED" and routed["layer_policy"] == "F.Cu"
    keepout = _zone(board, "K-SOUTH")
    copper_edge = routed["geometry"]["endpoints"][0][1] - routed["planned_width"] / 2
    gap = copper_edge - keepout["rect"]["y_max"]
    assert gap == pytest.approx(0.7)                      # 缝隙恰 0.7mm
    new = _part(board, "NEW1")
    note = new["note"]
    assert "0.7" in note
    assert "1.0+0.1=1.1>0.7" in note                      # 守 1.0 保护距则无法穿过
    assert "0.5+0.1+0.5=1.1>0.7" in note                  # 两侧各留 0.5 净距亦不够
    assert "0.5+0.1=0.6" in note                          # 放弃保护距仅剩 0.6mm 可过
    assert new["width_prior"]["w_min"] == 0.1
    assert 0.5 + new["width_prior"]["w_min"] == pytest.approx(0.6)   # ≤ 0.7 可过
    reg = _by_id(board["principle_registry"])
    guard, completion = reg["P-COPPER-GUARD"], reg["P-COMPLETION"]
    assert guard["compiled_rule"] == {"kind": "existing_copper_guard",
                                      "params": {"min_gap_mm": 1.0}}
    assert guard["conflict_policy"]["yields_to"] == ["P-COMPLETION"]  # 本对完成性赢
    assert completion["priority"] == 75 > guard["priority"] == 55
    assert completion["compiled_rule"] == {"kind": "completion_first", "params": {}}


def test_adv07_objection_vs_floor():
    """adv-07：hard 条目 overridable=false + compiled r1_width_floor；软目标 0.25<0.32。"""
    board = _load("adv-07-objection-vs-floor")
    reg = _by_id(board["principle_registry"])
    floor, slim = reg["P-R1-FLOOR"], reg["P-WIDTH-SLIM"]
    assert floor["hard_or_soft"] == "hard"
    assert floor["overridable"] is False
    assert floor["enforcement"] == "check"
    assert floor["priority"] == 100
    assert floor["compiled_rule"] == {"kind": "r1_width_floor",
                                      "params": {"k_a": 0.4, "floor_mm": 0.3}}
    assert slim["hard_or_soft"] == "soft"
    assert slim["overridable"] is True
    assert slim["compiled_rule"] == {"kind": "width_push",
                                     "params": {"target_width_mm": 0.25}}
    assert slim["conflict_policy"]["yields_to"] == ["P-R1-FLOOR"]
    pwr = _part(board, "PW2")
    assert pwr["current_a"] == pytest.approx(0.8)
    # R1 地板 = max(0.4×0.8, 0.3) = 0.32；SLIM 最优值 0.25 撞硬地板
    r1_floor = max(EXPECTED_HARD_RULES["R1"]["k_a"] * pwr["current_a"],
                   EXPECTED_HARD_RULES["R1"]["floor_mm"])
    assert r1_floor == pytest.approx(0.32)
    assert slim["compiled_rule"]["params"]["target_width_mm"] < r1_floor
    assert pwr["width_prior"]["w_min"] == pytest.approx(r1_floor)
    assert "0.25<0.32" in pwr["note"]


# ------------------------------------------------------------- scope 语法合同

# L0.5 编译器（v5/compiler.py）scope 五形态，此处内联同款口径（大小写敏感、逗号多值）：
#   partitioning / partition:<id> / zone:<id> / ptype:<P> / net_class:<x>
_SCOPE_KINDS = ("zone", "ptype", "net_class", "partition")


def _scope_legal(scope):
    for token in (t.strip() for t in scope.split(",")):
        if not token:
            continue
        if token == "partitioning":
            continue
        kind, sep, value = token.partition(":")
        if not sep or not value or kind not in _SCOPE_KINDS:
            return False
    return True


# 修正映射后的每条 scope 期望值（builder 映射表的锁定版；语义锚见 builder 注释）
EXPECTED_SCOPES = {
    "adv-01-pwr-vs-bus": {"P-PWR-PRIORITY": "ptype:PWR",
                          "P-BUS-INTEGRITY": "ptype:BUS"},
    "adv-02-clk-vs-short": {"P-CLK-ISOLATE": "ptype:CLK",
                            "P-SHORT-RUN": "partitioning"},
    "adv-03-diff-vs-capacity": {"P-DIFF-PAIRING": "ptype:DIFF",
                                "P-CORRIDOR-BUDGET": "zone:COR-D"},
    "adv-04-xtalk-vs-vias": {"P-XTALK-BUDGET": "partition:VI",
                             "P-VIA-FRUGAL": "partitioning"},
    "adv-05-eqlen-vs-layerpref": {"P-EQLEN-GROUP": "partition:EQA,partition:EQB,"
                                                    "partition:EQC",
                                  "P-LAYER-PREF": "partitioning"},
    "adv-06-copper-vs-completion": {"P-COMPLETION": "partitioning",
                                    "P-COPPER-GUARD": "partition:RT1"},
    "adv-07-objection-vs-floor": {"P-R1-FLOOR": "ptype:PWR",
                                  "P-WIDTH-SLIM": "partition:PW2"},
}


def test_scope_tokens_are_compiler_legal():
    """七板全部 principle 条目的 scope 过编译器五形态合法性断言（内联同款口径），
    且与修正映射表逐条一致；粒度先验恒为裸 token partitioning。"""
    for bid in BOARD_IDS:
        for entry in _load(bid)["principle_registry"]:
            pid, scope = entry["principle_id"], entry["scope"]
            assert _scope_legal(scope), "%s: %s scope %r 非五形态" % (bid, pid, scope)
            if pid.startswith("P-PART-GRAN-"):
                assert scope == "partitioning"
            else:
                assert scope == EXPECTED_SCOPES[bid][pid], (
                    "%s: %s scope %r != 映射表 %r"
                    % (bid, pid, scope, EXPECTED_SCOPES[bid][pid]))
