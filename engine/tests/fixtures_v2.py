# -*- coding: utf-8 -*-
"""V2 场景黄金夹具（D 层：V2 场景衍生自造板）。

来源：partition-judge-v2/prompt-v2-template.md（冻结件，sha256 见 SOURCE_SHA256）。
黄金四值 = V2 判分键 J2+J3 联合解四组合成本（先于被试会话预冻结，判分键权威）：
  A  P3→B.Cu  + P5留F.Cu = 34.85
  B  P3留F.Cu + P5→B.Cu  = 37.25
  C  P3留F.Cu + P5→In1   = 38.05
  D  P3→In1   + P5留F.Cu = 42.40
  双留F.Cu = 容量不可行（4.7 > 4.3）

走廊槽位口径（重要，判分键转录）：四组合的 C1 槽位中心线
（P3_F=34.85 / P3_B=34.70 / P3_I=34.75 / P5_F=34.85 / P5_BI=35.00）
为 V2 判分键原手算值，按判分键权威原样转录进夹具；它们是黄金测试的固定输入，
不是引擎推断值。引擎的通用度量函数（绕行 0.5、逆向 0.2、过孔 4+回流 1、
容量占用=铜宽+0.5×相邻对）对其算术必须逐值复现判分键。
"""
import hashlib

from v5.board import compute_board_sha256

SOURCE_PATH = "E:/ZCodeData/ZCodeProject/partition-judge-v2/prompt-v2-template.md"
SOURCE_SHA256 = "ca70b863816c1b5ef3fa9047828860185577b30765966702d06b2cbd647e8900"

# V2 场景常量（prompt 模板逐条转录）
C1_BAND = (30.85, 35.15)        # 每信号层可用布线带（4.3mm，已含对禁布区间距扣减）
C1_CAPACITY = 4.3
P4_OCCUPANCY = 3.3              # 8 位 ribbon 声明占用
P4_BAND = (30.95, 34.25)        # P4 铜带
ANA_RECT = {"x_min": 20.0, "y_min": 8.0, "x_max": 28.0, "y_max": 15.0}
K1_RECT = {"x_min": 0.0, "y_min": 16.0, "x_max": 30.0, "y_max": 24.0}
K2_RECT = {"x_min": 36.0, "y_min": 16.0, "x_max": 50.0, "y_max": 24.0}
PAD_RADIUS = 0.15

GOLDEN = {
    "A_P3B_P5F": 34.85,
    "B_P3F_P5B": 37.25,
    "C_P3F_P5I": 38.05,
    "D_P3I_P5F": 42.40,
}

LAYER_DIRECTIONS = {"F.Cu": "h", "In1.Cu": "v", "In2.Cu": "any", "B.Cu": "any"}


def build_v2_board():
    """构造 v5.board.v1 实例（V2 场景转录）。board_sha256 由链式规则现算。"""
    board = {
        "schema_version": "v5.board.v1",
        "board_id": "v2-scenario-golden",
        "stackup": [
            {"id": "F.Cu", "kind": "signal", "preferred_direction": "h", "available": True},
            {"id": "In1.Cu", "kind": "signal", "preferred_direction": "v", "available": True},
            {"id": "In2.Cu", "kind": "plane", "preferred_direction": "any", "available": False},
            {"id": "B.Cu", "kind": "signal", "preferred_direction": "any", "available": True},
        ],
        "workspace": {"x_min": 0.0, "y_min": 0.0, "x_max": 50.0, "y_max": 40.0},
        "zones": [
            {"zone_id": "K1", "kind": "keepout",
             "rect": K1_RECT, "layers": "all", "note": "全层禁布区"},
            {"zone_id": "K2", "kind": "keepout",
             "rect": K2_RECT, "layers": "all", "note": "全层禁布区"},
            {"zone_id": "C1", "kind": "corridor",
             "rect": {"x_min": 30.0, "y_min": 16.0, "x_max": 36.0, "y_max": 24.0},
             "layers": "signal", "capacity": C1_CAPACITY,
             "note": "唯一通道；每信号层可用布线带 x∈[30.85,35.15]"},
            {"zone_id": "ANA", "kind": "sensitive",
             "rect": ANA_RECT, "layers": "signal", "note": "模拟敏感区（R2）"},
        ],
        "partitions": [
            {"partition_id": "P1", "ptype": "PWR",
             "geometry": {"endpoints": [[2.0, 38.0], [44.0, 38.0]]},
             "layer_policy": "F.Cu", "width_prior": {"w_min": 0.6, "w_max": 1.4},
             "current_a": 1.5, "speed_class": "power", "planned_width": 1.2,
             "bottleneck": {"span": [8.0, 10.0], "usable_width": 1.0},
             "note": "x∈[8,10] 段因两侧焊盘可用宽度仅 1.0"},
            {"partition_id": "P2", "ptype": "CLK",
             "geometry": {"endpoints": [[5.0, 10.0], [45.0, 10.0]]},
             "layer_policy": "F.Cu", "width_prior": {"w_min": 0.15, "w_max": 0.15},
             "current_a": 0.0, "speed_class": "clk_200M", "planned_width": 0.15},
            {"partition_id": "P3", "ptype": "HS",
             "geometry": {"endpoints": [[16.0, 4.0], [16.0, 36.0]]},
             "layer_policy": "F.Cu", "width_prior": {"w_min": 0.2, "w_max": 0.2},
             "current_a": 0.0, "speed_class": "hs_125M", "planned_width": 0.2},
            {"partition_id": "P4", "ptype": "BUS",
             "geometry": {"endpoints": [[32.6, 4.0], [32.6, 36.0]],
                          "centerline": [[32.6, 4.0], [32.6, 36.0]],
                          "occupancy_mm": P4_OCCUPANCY, "copper_band": [30.95, 34.25]},
             "layer_policy": "F.Cu", "width_prior": {"w_min": 0.15, "w_max": 0.15},
             "current_a": 0.0, "speed_class": "bus_8bit",
             "note": "ribbon 整体不可拆分（R3）"},
            {"partition_id": "P5", "ptype": "MISC",
             "geometry": {"endpoints": [[37.0, 10.0], [37.0, 30.0]]},
             "layer_policy": "F.Cu", "width_prior": {"w_min": 0.2, "w_max": 0.2},
             "current_a": 0.0, "speed_class": "low_speed", "planned_width": 0.2},
            {"partition_id": "P6", "ptype": "MISC",
             "geometry": {"endpoints": [[46.0, 32.0], [46.0, 38.0]]},
             "layer_policy": "F.Cu", "width_prior": {"w_min": 0.2, "w_max": 0.2},
             "current_a": 0.0, "speed_class": "low_speed", "planned_width": 0.2},
            {"partition_id": "P7", "ptype": "ROUTED",
             "geometry": {"endpoints": [[2.0, 36.7], [44.0, 36.7]]},
             "layer_policy": "F.Cu", "width_prior": {"w_min": 0.2, "w_max": 0.2},
             "current_a": 0.0, "speed_class": "low_speed", "planned_width": 0.2,
             "note": "既布，路径固定"},
            {"partition_id": "P8", "ptype": "PWR",
             "geometry": {"endpoints": [[44.0, 4.0], [48.0, 4.0]]},
             "layer_policy": "F.Cu", "width_prior": {"w_min": 0.8, "w_max": 1.6},
             "current_a": 2.0, "speed_class": "power", "planned_width": 0.5,
             "note": "播种缺陷 D1：计划宽 0.5 < R1 下限 0.8"},
            {"partition_id": "P9", "ptype": "ROUTED",
             "geometry": {"endpoints": [[2.0, 36.1], [44.0, 36.1]]},
             "layer_policy": "F.Cu", "width_prior": {"w_min": 0.2, "w_max": 0.2},
             "current_a": 0.0, "speed_class": "low_speed", "planned_width": 0.2,
             "note": "既布；播种缺陷 D2：与 P7 净距 0.4 < 0.5"},
        ],
        "nets": [
            {"net_id": "P%d" % i, "net_class": cls, "partitions": ["P%d" % i]}
            for i, cls in [(1, "PWR"), (2, "CLK"), (3, "HS"), (4, "BUS"), (5, "MISC"),
                           (6, "MISC"), (7, "MISC"), (8, "PWR"), (9, "MISC")]
        ],
        "hard_rules": {
            "R1": {"k_a": 0.4, "floor_mm": 0.3},
            "R2": {"min_distance_mm": 3.0, "max_parallel_mm": 5.0},
            "R3": {"unsplittable": True},
            "R4": {"return_via_required": True, "max_distance_mm": 2.0},
            "R5": {"min_clearance_mm": 0.5},
            "R6": {"plane_forbidden": True, "keepout_zones_forbidden": True},
        },
        "principle_registry": [],
        "provenance": {
            "source_type": "v2_derived",
            "source_uri": SOURCE_PATH,
            "source_sha256": SOURCE_SHA256,
            "adapter": "hand",
        },
    }
    board["provenance"]["board_sha256"] = compute_board_sha256(board)
    return board


# ------------------------------------------------------- 黄金组合路由（判分键转录）

def _p3_route(slot_x, layer, vias):
    return {"net_id": "P3", "layer": layer, "transition_vias": vias,
            "polyline": [[16.0, 4.0], [slot_x, 4.0], [slot_x, 36.0], [16.0, 36.0]]}


def _p5_route(slot_x, layer, vias):
    return {"net_id": "P5", "layer": layer, "transition_vias": vias,
            "polyline": [[37.0, 10.0], [slot_x, 10.0], [slot_x, 30.0], [37.0, 30.0]]}


# 判分键原手算槽位（转录，非引擎推断；见文件头说明）
SLOT_P3_F = 34.85
SLOT_P3_B = 34.70
SLOT_P3_I = 34.75
SLOT_P5_F = 34.85
SLOT_P5_BI = 35.00


GOLDEN_COMBOS = {
    "A_P3B_P5F": {
        "routes": [_p3_route(SLOT_P3_B, "B.Cu", 2), _p5_route(SLOT_P5_F, "F.Cu", 0)],
        "layers": {"P3": "B.Cu", "P5": "F.Cu"},
    },
    "B_P3F_P5B": {
        "routes": [_p3_route(SLOT_P3_F, "F.Cu", 0), _p5_route(SLOT_P5_BI, "B.Cu", 2)],
        "layers": {"P3": "F.Cu", "P5": "B.Cu"},
    },
    "C_P3F_P5I": {
        "routes": [_p3_route(SLOT_P3_F, "F.Cu", 0), _p5_route(SLOT_P5_BI, "In1.Cu", 2)],
        "layers": {"P3": "F.Cu", "P5": "In1.Cu"},
    },
    "D_P3I_P5F": {
        "routes": [_p3_route(SLOT_P3_I, "In1.Cu", 2), _p5_route(SLOT_P5_F, "F.Cu", 0)],
        "layers": {"P3": "In1.Cu", "P5": "F.Cu"},
    },
}


def c1_fcu_entries(p3_on_f=False, p5_on_f=False):
    """C1 走廊 F.Cu 占用条目（P4 恒在；P3/P5 视组合）。"""
    from v5.metrics.capacity import CapacityEntry
    entries = [CapacityEntry("P4", 0.0, declared_occupancy=P4_OCCUPANCY, span=P4_BAND)]
    if p3_on_f:
        entries.append(CapacityEntry("P3", 0.2))
    if p5_on_f:
        entries.append(CapacityEntry("P5", 0.2))
    return entries


def verify_source_frozen():
    """源模板仍在且哈希未变（夹具自检；防转录失真）。"""
    actual = hashlib.sha256(open(SOURCE_PATH, "rb").read()).hexdigest()
    return actual == SOURCE_SHA256
