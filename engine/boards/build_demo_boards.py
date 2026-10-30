# -*- coding: utf-8 -*-
"""D 层 demo 板构造器（V5.0 P1；任务书 §3.1 板契约 / §6 D 层定义）。

产出三块 v5.board.v1 板文件到 boards/d/（文件字节 = v5.canonical.canonical_json(board)）：
  demo-01-v2-corridor   source_type=v2_derived，adapter=v2derive v1.0.0，
                        复刻 V2 场景几何（源模板 sha256 运行时读文件字节计算，provenance 落链）
  demo-02-mixed-types   synthetic 两层板，15 网覆盖全部 8 种 ptype
  demo-03-small-mixed   synthetic 四层板（含 available=false 的 plane 层）

铁律：
  - stdlib only；不 import tests/ 下任何模块（构造代码独立重写，不以夹具为 import 源）；
  - builder 可重复运行：同输入产出同字节，覆盖写零 diff（无 wall-clock、无随机）；
  - 写盘前逐板过 v5.board.load_board fail-closed 自检（schema + provenance 链 + 跨字段合同）。

provenance 约定（本构造器的最小文档化决定）：
  - demo-01：source_sha256 = V2 源模板文件字节哈希（运行时读取计算）；source_uri = 该模板 E 盘路径。
  - demo-02/03（synthetic，hand 构造，无外部源文件）：source_sha256 = 本构造器脚本字节哈希
    （authoring provenance：脚本即源，脚本变更即换源，符合 source+adapter⇒board 链式规则）；
    source_uri 用仓库相对键，避免主机路径进入 canonical 内容。
"""
import hashlib
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from v5 import canonical  # noqa: E402
from v5.board import compute_board_sha256, load_board  # noqa: E402

# 输出目录：<repo>/boards/d（E 盘真实路径）
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "d")

# demo-01 的源模板（V2 场景冻结件；哈希运行时读取计算，不硬编码）
V2_SOURCE_PATH = "E:/ZCodeData/ZCodeProject/partition-judge-v2/prompt-v2-template.md"

# 本构造器脚本自身（synthetic 板的 authoring 源）
_SCRIPT_PATH = os.path.abspath(__file__)

# V2 场景硬规则（R1–R6，照 V2 分区表口径；三块板共用同一组，保持 R1 手算口径一致）
_HARD_RULES_V2 = {
    "R1": {"k_a": 0.4, "floor_mm": 0.3},
    "R2": {"min_distance_mm": 3.0, "max_parallel_mm": 5.0},
    "R3": {"unsplittable": True},
    "R4": {"return_via_required": True, "max_distance_mm": 2.0},
    "R5": {"min_clearance_mm": 0.5},
    "R6": {"plane_forbidden": True, "keepout_zones_forbidden": True},
}

# 四层 stackup：F.Cu 横 / In1.Cu 纵 / In2.Cu 平面层不可用 / B.Cu 任意（V2 口径）
_STACKUP_4L = [
    {"id": "F.Cu", "kind": "signal", "preferred_direction": "h", "available": True},
    {"id": "In1.Cu", "kind": "signal", "preferred_direction": "v", "available": True},
    {"id": "In2.Cu", "kind": "plane", "preferred_direction": "any", "available": False},
    {"id": "B.Cu", "kind": "signal", "preferred_direction": "any", "available": True},
]


def _sha256_file(path):
    """文件字节 sha256（provenance 落链用）。"""
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


# ---------------------------------------------------------------- 理念条目构造

def _principle(principle_id, name, protects, sacrifices, scope, protected_resources,
               target_freedom, priority, hard_or_soft, overridable, compiled_rule,
               enforcement, evidence_refs, conflicts_with=(), yields_to=(),
               version="1.0.0"):
    """构造一条理念条目（15 字段齐）；source_hash = sha256(canonical(剔除 source_hash 后的条目))。"""
    entry = {
        "principle_id": principle_id,
        "name": name,
        "intent": {"protects": protects, "sacrifices": sacrifices},
        "scope": scope,
        "protected_resources": list(protected_resources),
        "target_freedom": target_freedom,
        "priority": priority,
        "hard_or_soft": hard_or_soft,
        "overridable": overridable,
        "compiled_rule": compiled_rule,
        "enforcement": enforcement,
        "conflict_policy": {"conflicts_with": list(conflicts_with),
                            "yields_to": list(yields_to)},
        "evidence_refs": list(evidence_refs),
        "version": version,
        "source_hash": "",
    }
    view = dict(entry)
    view.pop("source_hash")
    entry["source_hash"] = canonical.canonical_sha256(view)
    return entry


def _granularity_principle(board_tag, min_gap_mm):
    """分区聚类粒度先验（任务书给定形状逐字；仅板短名与 min_gap_mm 随板变化）。

    L1 分区器的聚类粒度必须可溯源到本条先验（任务书 §4 L1：不许无出处的魔法数）。
    """
    return _principle(
        principle_id="P-PART-GRAN-%s" % board_tag,
        name="分区聚类粒度先验",
        protects="走廊通行容量不被过度细分侵占",
        sacrifices="细粒度局部分配自由",
        scope="partitioning",
        protected_resources=["corridor_capacity"],
        target_freedom="corridor",
        priority=50,
        hard_or_soft="soft",
        overridable=True,
        compiled_rule={"kind": "partition_granularity",
                       "params": {"min_gap_mm": min_gap_mm,
                                  "group_types": ["BUS", "DIFF"]}},
        enforcement="generation",
        evidence_refs=["V5.0-DEV-TASKBOOK §4 L1"],
    )


# ---------------------------------------------------------------- demo-01

def build_demo_01():
    """demo-01-v2-corridor：V2 场景几何复刻（v2_derived / v2derive v1.0.0）。

    与夹具蓝本的差异（任务书明确规定）：C1 走廊矩形为全高 x∈[30,36]、y∈[0,40]
    （K1/K2 之间的完整自由竖条），容量与可用带口径不变（4.3 / [30.85,35.15]）。
    """
    board = {
        "schema_version": "v5.board.v1",
        "board_id": "demo-01-v2-corridor",
        "stackup": _STACKUP_4L,
        "workspace": {"x_min": 0.0, "y_min": 0.0, "x_max": 50.0, "y_max": 40.0},
        "zones": [
            {"zone_id": "K1", "kind": "keepout",
             "rect": {"x_min": 0.0, "y_min": 16.0, "x_max": 30.0, "y_max": 24.0},
             "layers": "all", "note": "全层禁布区（V2 K1）"},
            {"zone_id": "K2", "kind": "keepout",
             "rect": {"x_min": 36.0, "y_min": 16.0, "x_max": 50.0, "y_max": 24.0},
             "layers": "all", "note": "全层禁布区（V2 K2）"},
            {"zone_id": "C1", "kind": "corridor",
             "rect": {"x_min": 30.0, "y_min": 0.0, "x_max": 36.0, "y_max": 40.0},
             "layers": "signal", "capacity": 4.3,
             "note": "唯一通道；每信号层可用布线带 x∈[30.85,35.15]（4.3mm，已含对禁布区间距扣减）"},
            {"zone_id": "ANA", "kind": "sensitive",
             "rect": {"x_min": 20.0, "y_min": 8.0, "x_max": 28.0, "y_max": 15.0},
             "layers": "signal", "note": "模拟敏感区（R2）"},
        ],
        "partitions": [
            {"partition_id": "P1", "ptype": "PWR",
             "geometry": {"endpoints": [[2.0, 38.0], [44.0, 38.0]]},
             "layer_policy": "F.Cu", "width_prior": {"w_min": 0.6, "w_max": 1.4},
             "current_a": 1.5, "speed_class": "power", "planned_width": 1.2,
             "bottleneck": {"span": [8.0, 10.0], "usable_width": 1.0},
             "note": "PWR-5V；x∈[8,10] 段因两侧焊盘可用宽度仅 1.0"},
            {"partition_id": "P2", "ptype": "CLK",
             "geometry": {"endpoints": [[5.0, 10.0], [45.0, 10.0]]},
             "layer_policy": "F.Cu", "width_prior": {"w_min": 0.15, "w_max": 0.15},
             "current_a": 0.0, "speed_class": "clk_200M", "planned_width": 0.15},
            {"partition_id": "P3", "ptype": "HS",
             "geometry": {"endpoints": [[16.0, 4.0], [16.0, 36.0]]},
             "layer_policy": "F.Cu", "width_prior": {"w_min": 0.2, "w_max": 0.2},
             "current_a": 0.0, "speed_class": "hs_125M", "planned_width": 0.2,
             "note": "ETH-MAC 纵贯；直线穿 K1，唯一通路 C1"},
            {"partition_id": "P4", "ptype": "BUS",
             "geometry": {"endpoints": [[32.6, 4.0], [32.6, 36.0]],
                          "centerline": [[32.6, 4.0], [32.6, 36.0]],
                          "occupancy_mm": 3.3, "copper_band": [30.95, 34.25]},
             "layer_policy": "F.Cu", "width_prior": {"w_min": 0.15, "w_max": 0.15},
             "current_a": 0.0, "speed_class": "bus_8bit",
             "note": "BUS-FMC 8 位 ribbon 整体不可拆分（R3）"},
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
             "note": "既布低速，路径固定"},
            {"partition_id": "P8", "ptype": "PWR",
             "geometry": {"endpoints": [[44.0, 4.0], [48.0, 4.0]]},
             "layer_policy": "F.Cu", "width_prior": {"w_min": 0.8, "w_max": 1.6},
             "current_a": 2.0, "speed_class": "power", "planned_width": 0.5,
             "note": "PWR-3V3-BR；播种缺陷 D1：计划宽 0.5 < R1 下限 0.8"},
            {"partition_id": "P9", "ptype": "ROUTED",
             "geometry": {"endpoints": [[2.0, 36.1], [44.0, 36.1]]},
             "layer_policy": "F.Cu", "width_prior": {"w_min": 0.2, "w_max": 0.2},
             "current_a": 0.0, "speed_class": "low_speed", "planned_width": 0.2,
             "note": "既布低速；播种缺陷 D2：与 P7 净距 0.4 < R5 0.5"},
        ],
        # nets 按 V2 分区表命名，与 P1–P9 一一引用
        "nets": [
            {"net_id": "PWR-5V", "net_class": "PWR", "partitions": ["P1"]},
            {"net_id": "CLK-200M", "net_class": "CLK", "partitions": ["P2"]},
            {"net_id": "ETH-MAC", "net_class": "HS", "partitions": ["P3"]},
            {"net_id": "BUS-FMC", "net_class": "BUS", "partitions": ["P4"]},
            {"net_id": "MISC1", "net_class": "MISC", "partitions": ["P5"]},
            {"net_id": "MISC2", "net_class": "MISC", "partitions": ["P6"]},
            {"net_id": "ROUTED-P7", "net_class": "MISC", "partitions": ["P7"]},
            {"net_id": "PWR-3V3-BR", "net_class": "PWR", "partitions": ["P8"]},
            {"net_id": "ROUTED-P9", "net_class": "MISC", "partitions": ["P9"]},
        ],
        "hard_rules": _HARD_RULES_V2,
        "principle_registry": [
            _granularity_principle("DEMO01", 2.0),
            _principle(
                principle_id="P-COR-CAP-C1-DEMO01",
                name="走廊 C1 容量守护",
                protects="C1 唯一通道 4.3mm 通行容量不被过载占用",
                sacrifices="穿越走廊网络的路径直线性与最短性",
                scope="zone:C1",
                protected_resources=["corridor_capacity"],
                target_freedom="corridor",
                priority=60,
                hard_or_soft="soft",
                overridable=True,
                compiled_rule={"kind": "corridor_capacity",
                               "params": {"zone_id": "C1", "capacity_mm": 4.3}},
                enforcement="generation",
                evidence_refs=["V5.0-DEV-TASKBOOK §3.1 zones.capacity",
                               "V2 判分键 J2/J3 联合解"],
            ),
            _principle(
                principle_id="P-CHECK-WIDTHPRIOR-DEMO01",
                name="计划宽与宽度先验下限一致性复查（R1 载流下限复查）",
                protects="电源分区计划宽不被声明低于 R1 下限（播种缺陷 D1 类数据矛盾）",
                sacrifices="无（纯复查，不参与生成，不改任何候选）",
                scope="ptype:PWR",
                protected_resources=["width_prior_floor"],
                target_freedom="allocation",
                priority=10,
                hard_or_soft="soft",
                overridable=True,
                compiled_rule="check_only",
                enforcement="check",
                evidence_refs=["V5.0-DEV-TASKBOOK §3.3 宽度先验",
                               "V2 播种缺陷 D1"],
            ),
            _principle(
                principle_id="P-XCOPPER-GUARD-DEMO01",
                name="既有铜保护（P7/P9 既布走线净距守护）",
                protects="既布铜几何不被重规划侵蚀（邻域净距 ≥1.0）",
                sacrifices="新网络在既布铜邻域内的路径自由",
                scope="ptype:ROUTED",
                protected_resources=["existing_copper_clearance"],
                target_freedom="ordering",
                priority=40,
                hard_or_soft="soft",
                overridable=True,
                compiled_rule={"kind": "existing_copper_guard",
                               "params": {"min_gap_mm": 1.0}},
                enforcement="generation",
                evidence_refs=["V5.0-DEV-TASKBOOK §5.1 冲突电池：既有铜保护 vs 新网络完成性"],
            ),
        ],
        "provenance": {
            "source_type": "v2_derived",
            "source_uri": V2_SOURCE_PATH,
            "source_sha256": _sha256_file(V2_SOURCE_PATH),
            "adapter": "v2derive v1.0.0",
        },
    }
    return _finish(board)


# ---------------------------------------------------------------- demo-02

def build_demo_02():
    """demo-02-mixed-types：两层板，15 网覆盖全部 8 种 ptype（synthetic / hand）。"""
    board = {
        "schema_version": "v5.board.v1",
        "board_id": "demo-02-mixed-types",
        "stackup": [
            {"id": "F.Cu", "kind": "signal", "preferred_direction": "h", "available": True},
            {"id": "B.Cu", "kind": "signal", "preferred_direction": "any", "available": True},
        ],
        "workspace": {"x_min": 0.0, "y_min": 0.0, "x_max": 60.0, "y_max": 40.0},
        "zones": [
            {"zone_id": "K1", "kind": "keepout",
             "rect": {"x_min": 20.0, "y_min": 16.0, "x_max": 32.0, "y_max": 24.0},
             "layers": "all", "note": "全层禁布区（板中央障碍）"},
            {"zone_id": "C1", "kind": "corridor",
             "rect": {"x_min": 40.0, "y_min": 0.0, "x_max": 44.0, "y_max": 40.0},
             "layers": "signal", "capacity": 2.6,
             "note": "中央走廊；BUS 铜带占用 2.1 过后单层余量仅 0.5"},
            {"zone_id": "S1", "kind": "sensitive",
             "rect": {"x_min": 0.0, "y_min": 26.0, "x_max": 12.0, "y_max": 36.0},
             "layers": "signal", "note": "模拟敏感区（R2）"},
        ],
        "partitions": [
            {"partition_id": "PW1", "ptype": "PWR",
             "geometry": {"endpoints": [[2.0, 38.0], [58.0, 38.0]]},
             "layer_policy": "F.Cu", "width_prior": {"w_min": 0.4, "w_max": 0.8},
             "current_a": 1.0, "speed_class": "power", "planned_width": 0.6,
             "note": "w_min 手算可核：max(R1 0.4×1.0A, 地板 0.3)=0.4"},
            {"partition_id": "PW2", "ptype": "PWR",
             "geometry": {"endpoints": [[58.0, 36.0], [58.0, 22.0]]},
             "layer_policy": "F.Cu", "width_prior": {"w_min": 0.3, "w_max": 0.6},
             "current_a": 0.5, "speed_class": "power", "planned_width": 0.4,
             "note": "w_min=max(0.4×0.5, 0.3)=0.3"},
            {"partition_id": "CK1", "ptype": "CLK",
             "geometry": {"endpoints": [[4.0, 4.0], [56.0, 4.0]]},
             "layer_policy": "F.Cu", "width_prior": {"w_min": 0.15, "w_max": 0.15},
             "current_a": 0.0, "speed_class": "clk_100M", "planned_width": 0.15},
            {"partition_id": "HS1", "ptype": "HS",
             "geometry": {"endpoints": [[4.0, 12.0], [56.0, 12.0]]},
             "layer_policy": "F.Cu", "width_prior": {"w_min": 0.2, "w_max": 0.2},
             "current_a": 0.0, "speed_class": "hs_125M", "planned_width": 0.2},
            {"partition_id": "DF1", "ptype": "DIFF",
             "geometry": {"endpoints": [[50.0, 34.0], [50.0, 10.0]]},
             "layer_policy": "F.Cu", "width_prior": {"w_min": 0.2, "w_max": 0.3},
             "current_a": 0.0, "speed_class": "diff_100ohm", "planned_width": 0.2,
             "note": "差分对两网（DIFF-P/DIFF-N）同指本分区"},
            {"partition_id": "BS1", "ptype": "BUS",
             "geometry": {"endpoints": [[35.0, 8.0], [52.0, 8.0]],
                          "centerline": [[35.0, 8.0], [52.0, 8.0]],
                          "occupancy_mm": 2.1, "copper_band": [6.95, 9.05]},
             "layer_policy": "F.Cu", "width_prior": {"w_min": 0.15, "w_max": 0.15},
             "current_a": 0.0, "speed_class": "bus_4bit",
             "note": "4 位 ribbon 整体不可拆分（R3）；铜带 y∈[6.95,9.05]"},
            {"partition_id": "MS1", "ptype": "MISC",
             "geometry": {"endpoints": [[6.0, 6.0], [6.0, 20.0]]},
             "layer_policy": "F.Cu", "width_prior": {"w_min": 0.2, "w_max": 0.2},
             "current_a": 0.0, "speed_class": "low_speed", "planned_width": 0.2},
            {"partition_id": "MS2", "ptype": "MISC",
             "geometry": {"endpoints": [[54.0, 24.0], [54.0, 34.0]]},
             "layer_policy": "F.Cu", "width_prior": {"w_min": 0.2, "w_max": 0.2},
             "current_a": 0.0, "speed_class": "low_speed", "planned_width": 0.2},
            {"partition_id": "MS3", "ptype": "MISC",
             "geometry": {"endpoints": [[14.0, 14.0], [14.0, 30.0]]},
             "layer_policy": "F.Cu", "width_prior": {"w_min": 0.2, "w_max": 0.2},
             "current_a": 0.0, "speed_class": "low_speed", "planned_width": 0.2},
            {"partition_id": "RT1", "ptype": "ROUTED",
             "geometry": {"endpoints": [[16.0, 30.0], [34.0, 30.0]]},
             "layer_policy": "F.Cu", "width_prior": {"w_min": 0.2, "w_max": 0.2},
             "current_a": 0.0, "speed_class": "low_speed", "planned_width": 0.2,
             "note": "既布，路径固定（既有铜保护对象）"},
            {"partition_id": "AN1", "ptype": "ANA",
             "geometry": {"endpoints": [[3.0, 28.0], [9.0, 34.0]]},
             "layer_policy": "F.Cu", "width_prior": {"w_min": 0.2, "w_max": 0.2},
             "current_a": 0.0, "speed_class": "analog", "planned_width": 0.2,
             "note": "敏感区内的模拟采样线"},
        ],
        # 每网或每组一分区（authored）；DIFF 两网同指 DF1，BUS 四网同指 BS1
        "nets": [
            {"net_id": "PWR-MAIN", "net_class": "PWR", "partitions": ["PW1"]},
            {"net_id": "PWR-AUX", "net_class": "PWR", "partitions": ["PW2"]},
            {"net_id": "CLK-SYS", "net_class": "CLK", "partitions": ["CK1"]},
            {"net_id": "HS-LINK", "net_class": "HS", "partitions": ["HS1"]},
            {"net_id": "DIFF-P", "net_class": "DIFF", "partitions": ["DF1"]},
            {"net_id": "DIFF-N", "net_class": "DIFF", "partitions": ["DF1"]},
            {"net_id": "BUS-D0", "net_class": "BUS", "partitions": ["BS1"]},
            {"net_id": "BUS-D1", "net_class": "BUS", "partitions": ["BS1"]},
            {"net_id": "BUS-D2", "net_class": "BUS", "partitions": ["BS1"]},
            {"net_id": "BUS-D3", "net_class": "BUS", "partitions": ["BS1"]},
            {"net_id": "MISC-A", "net_class": "MISC", "partitions": ["MS1"]},
            {"net_id": "MISC-B", "net_class": "MISC", "partitions": ["MS2"]},
            {"net_id": "MISC-C", "net_class": "MISC", "partitions": ["MS3"]},
            {"net_id": "ROUTED-LEGACY", "net_class": "MISC", "partitions": ["RT1"]},
            {"net_id": "ANA-SENSE", "net_class": "ANA", "partitions": ["AN1"]},
        ],
        "hard_rules": _HARD_RULES_V2,
        "principle_registry": [
            _granularity_principle("DEMO02", 1.5),
            _principle(
                principle_id="P-LAYER-PREF-HIGHF-DEMO02",
                name="高频层偏好（CLK/HS 优先 F.Cu 短回流）",
                protects="时钟与高速分区的回流连续性与串扰预算",
                sacrifices="B.Cu 的通用布线自由度",
                scope="ptype:CLK",
                protected_resources=["return_path_quality", "crosstalk_budget"],
                target_freedom="layer_plan",
                priority=30,
                hard_or_soft="soft",
                overridable=True,
                compiled_rule={"kind": "layer_preference",
                               "params": {"ptypes": ["CLK", "HS"], "layer": "F.Cu"}},
                enforcement="generation",
                evidence_refs=["V5.0-DEV-TASKBOOK §5.1 冲突电池：时钟 vs 短线偏好"],
            ),
            _principle(
                principle_id="P-EQLEN-DIFF-DEMO02",
                name="差分对等长组（DF1 两网相位匹配）",
                protects="DF1 差分对两网长度差不超过 0.5（相位匹配）",
                sacrifices="两网各自的独立路径自由",
                scope="partition:DF1",
                protected_resources=["diff_pair_skew"],
                target_freedom="ordering",
                priority=35,
                hard_or_soft="soft",
                overridable=True,
                compiled_rule={"kind": "equal_length_group",
                               "params": {"partition_id": "DF1", "tolerance_mm": 0.5}},
                enforcement="generation",
                evidence_refs=["V5.0-DEV-TASKBOOK §5.1 冲突电池：差分对 vs 走廊容量"],
            ),
            _principle(
                principle_id="P-SENS-GUARD-S1-DEMO02",
                name="敏感区 S1 邻域守护（ANA 采样线静音）",
                protects="S1 内 ANA 分区不受邻网开关噪声侵扰（邻域净距 ≥3.0）",
                sacrifices="敏感区邻域内普通网络的布线通道",
                scope="zone:S1",
                protected_resources=["analog_quiet_zone"],
                target_freedom="allocation",
                priority=45,
                hard_or_soft="soft",
                overridable=True,
                compiled_rule={"kind": "sensitive_zone_guard",
                               "params": {"zone_id": "S1", "min_distance_mm": 3.0}},
                enforcement="generation",
                evidence_refs=["V5.0-DEV-TASKBOOK §3.1 zones(R2 敏感区)"],
            ),
        ],
        "provenance": {
            "source_type": "synthetic",
            "source_uri": "hand-authored:boards/build_demo_boards.py#demo-02",
            "source_sha256": _sha256_file(_SCRIPT_PATH),
            "adapter": "hand",
        },
    }
    return _finish(board)


# ---------------------------------------------------------------- demo-03

def build_demo_03():
    """demo-03-small-mixed：小四层板（plane 层不可用），7 网 6 类（synthetic / hand）。

    网数口径（最小文档化决定）：任务书枚举「PWR 1.5A、DIFF 1 对、MISC 2、
    ROUTED 1、CLK 1」，逐项求和为 7 网（DIFF 1 对=2 网共指 DF1）；
    「6 网」系计法差（把差分对记 1），按枚举为准取 7 网。
    """
    board = {
        "schema_version": "v5.board.v1",
        "board_id": "demo-03-small-mixed",
        "stackup": _STACKUP_4L,
        "workspace": {"x_min": 0.0, "y_min": 0.0, "x_max": 30.0, "y_max": 24.0},
        "zones": [
            {"zone_id": "S1", "kind": "sensitive",
             "rect": {"x_min": 2.0, "y_min": 14.0, "x_max": 10.0, "y_max": 22.0},
             "layers": "signal", "note": "模拟敏感区（R2）"},
            {"zone_id": "C1", "kind": "corridor",
             "rect": {"x_min": 14.0, "y_min": 0.0, "x_max": 17.0, "y_max": 24.0},
             "layers": "signal", "capacity": 1.8,
             "note": "窄走廊：容量 1.8，穿行组合须按容量账本协商"},
        ],
        "partitions": [
            {"partition_id": "PW1", "ptype": "PWR",
             "geometry": {"endpoints": [[2.0, 2.0], [28.0, 2.0]]},
             "layer_policy": "F.Cu", "width_prior": {"w_min": 0.6, "w_max": 1.2},
             "current_a": 1.5, "speed_class": "power", "planned_width": 0.9,
             "note": "w_min 手算可核：max(R1 0.4×1.5A, 地板 0.3)=0.6"},
            {"partition_id": "DF1", "ptype": "DIFF",
             "geometry": {"endpoints": [[26.0, 20.0], [26.0, 4.0]]},
             "layer_policy": "F.Cu", "width_prior": {"w_min": 0.2, "w_max": 0.3},
             "current_a": 0.0, "speed_class": "diff_100ohm", "planned_width": 0.2,
             "note": "差分对两网（DIFF-P/DIFF-N）同指本分区"},
            {"partition_id": "MS1", "ptype": "MISC",
             "geometry": {"endpoints": [[2.0, 8.0], [10.0, 8.0]]},
             "layer_policy": "F.Cu", "width_prior": {"w_min": 0.2, "w_max": 0.2},
             "current_a": 0.0, "speed_class": "low_speed", "planned_width": 0.2},
            {"partition_id": "MS2", "ptype": "MISC",
             "geometry": {"endpoints": [[19.0, 16.0], [19.0, 22.0]]},
             "layer_policy": "F.Cu", "width_prior": {"w_min": 0.2, "w_max": 0.2},
             "current_a": 0.0, "speed_class": "low_speed", "planned_width": 0.2},
            {"partition_id": "RT1", "ptype": "ROUTED",
             "geometry": {"endpoints": [[4.0, 23.0], [24.0, 23.0]]},
             "layer_policy": "F.Cu", "width_prior": {"w_min": 0.2, "w_max": 0.2},
             "current_a": 0.0, "speed_class": "low_speed", "planned_width": 0.2,
             "note": "既布，路径固定（既有铜保护对象）"},
            {"partition_id": "CK1", "ptype": "CLK",
             "geometry": {"endpoints": [[2.0, 5.0], [28.0, 5.0]]},
             "layer_policy": "F.Cu", "width_prior": {"w_min": 0.15, "w_max": 0.15},
             "current_a": 0.0, "speed_class": "clk_50M", "planned_width": 0.15},
        ],
        "nets": [
            {"net_id": "PWR-MAIN", "net_class": "PWR", "partitions": ["PW1"]},
            {"net_id": "DIFF-P", "net_class": "DIFF", "partitions": ["DF1"]},
            {"net_id": "DIFF-N", "net_class": "DIFF", "partitions": ["DF1"]},
            {"net_id": "MISC-A", "net_class": "MISC", "partitions": ["MS1"]},
            {"net_id": "MISC-B", "net_class": "MISC", "partitions": ["MS2"]},
            {"net_id": "ROUTED-LEGACY", "net_class": "MISC", "partitions": ["RT1"]},
            {"net_id": "CLK-SYS", "net_class": "CLK", "partitions": ["CK1"]},
        ],
        "hard_rules": _HARD_RULES_V2,
        "principle_registry": [
            _granularity_principle("DEMO03", 3.0),
            _principle(
                principle_id="P-COR-CAP-C1-DEMO03",
                name="走廊 C1 容量守护",
                protects="窄走廊 C1 的 1.8mm 通行容量不被过载占用",
                sacrifices="穿行走廊网络的路径直线性",
                scope="zone:C1",
                protected_resources=["corridor_capacity"],
                target_freedom="corridor",
                priority=60,
                hard_or_soft="soft",
                overridable=True,
                compiled_rule={"kind": "corridor_capacity",
                               "params": {"zone_id": "C1", "capacity_mm": 1.8}},
                enforcement="generation",
                evidence_refs=["V5.0-DEV-TASKBOOK §3.1 zones.capacity"],
            ),
            _principle(
                principle_id="P-EQLEN-DIFF-DEMO03",
                name="差分对等长组（DF1 两网相位匹配）",
                protects="DF1 差分对两网长度差不超过 0.3（相位匹配）",
                sacrifices="两网各自的独立路径自由",
                scope="partition:DF1",
                protected_resources=["diff_pair_skew"],
                target_freedom="ordering",
                priority=35,
                hard_or_soft="soft",
                overridable=True,
                compiled_rule={"kind": "equal_length_group",
                               "params": {"partition_id": "DF1", "tolerance_mm": 0.3}},
                enforcement="generation",
                evidence_refs=["V5.0-DEV-TASKBOOK §5.1 冲突电池：等长组 vs 层优选"],
            ),
            _principle(
                principle_id="P-LAYER-PREF-CLK-DEMO03",
                name="时钟层偏好（CLK 优先 F.Cu 横向短路径）",
                protects="时钟回路面积最小与回流连续",
                sacrifices="F.Cu 其余网络的横向通道容量",
                scope="ptype:CLK",
                protected_resources=["return_path_quality"],
                target_freedom="layer_plan",
                priority=30,
                hard_or_soft="soft",
                overridable=True,
                compiled_rule={"kind": "layer_preference",
                               "params": {"ptypes": ["CLK"], "layer": "F.Cu",
                                          "direction": "h"}},
                enforcement="generation",
                evidence_refs=["V5.0-DEV-TASKBOOK §5.1 冲突电池：时钟 vs 短线偏好"],
            ),
        ],
        "provenance": {
            "source_type": "synthetic",
            "source_uri": "hand-authored:boards/build_demo_boards.py#demo-03",
            "source_sha256": _sha256_file(_SCRIPT_PATH),
            "adapter": "hand",
        },
    }
    return _finish(board)


# ---------------------------------------------------------------- 落盘

def _finish(board):
    """填 board_sha256 并做 fail-closed 自检（schema + provenance 链 + 跨字段合同）。"""
    board["provenance"]["board_sha256"] = compute_board_sha256(board)
    load_board(board)
    return board


def build_all(out_dir=OUT_DIR):
    """构造三块板并按 canonical 字节覆盖写；返回 [(路径, 文件 sha256, 是否字节有变)]。"""
    os.makedirs(out_dir, exist_ok=True)
    results = []
    for board in (build_demo_01(), build_demo_02(), build_demo_03()):
        data = canonical.canonical_json(board)
        path = os.path.join(out_dir, "%s.board.v1.json" % board["board_id"])
        changed = True
        if os.path.exists(path):
            with open(path, "rb") as f:
                changed = f.read() != data
        with open(path, "wb") as f:
            f.write(data)
        results.append((path, hashlib.sha256(data).hexdigest(), changed))
    return results


def main():
    for path, digest, changed in build_all():
        print("%s  sha256=%s  %s" % (path, digest, "内容有变，已覆写" if changed else "零 diff 覆写"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
