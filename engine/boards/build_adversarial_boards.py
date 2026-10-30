# -*- coding: utf-8 -*-
"""7 类理念冲突对抗板构造器（V5.0-DEV-TASKBOOK §5.1 冲突电池 / §6 D 层，P1）。

七块板（board_id 固定，均为 D 层对抗板，禁入任何验收门）：
  adv-01-pwr-vs-bus            电源 vs 普通总线
  adv-02-clk-vs-short          时钟 vs 短线偏好
  adv-03-diff-vs-capacity      差分对 vs 走廊容量
  adv-04-xtalk-vs-vias         串扰预算 vs 过孔数量
  adv-05-eqlen-vs-layerpref    等长组 vs 层优选
  adv-06-copper-vs-completion  既有铜保护 vs 新网完成性
  adv-07-objection-vs-floor    软先验 objection vs 不变式地板

契约（冻结任务书 + P0 件）：
  - 每板 6–12 网；1 条分区粒度先验 + 1 对冲突原则（conflicts_with 相互对称声明、
    loser 一方 yields_to winner、priority 分出高低）；hard_rules=V2 默认。
  - board["principle_registry"]=裸条目数组；条目 15 字段（fail-closed schema）；
    条目 source_hash = sha256(canonical(剔除 source_hash 后条目字节))。
  - 文件字节 = v5.canonical.canonical_json；board_sha256 先算好填；
    provenance：source_type=synthetic / adapter=hand /
    source_uri=boards/build_adversarial_boards.py#<board_id> /
    source_sha256=该板构造函数源码文本的 sha256（确定性披露）。
  - 确定性：无 wall-clock、无随机、无主机路径；同输入双跑字节相等（tests 覆盖）。

用法：
  python boards/build_adversarial_boards.py             # 写入 boards/d/
  python boards/build_adversarial_boards.py <out_dir>   # 写入指定目录（测试用 tmp_path）
"""
import hashlib
import inspect
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from v5 import canonical                    # noqa: E402
from v5.board import compute_board_sha256   # noqa: E402

# V2 默认硬规则（取值照 tests/fixtures_v2.py 转录；按纪律不 import 之）
HARD_RULES = {
    "R1": {"k_a": 0.4, "floor_mm": 0.3},
    "R2": {"min_distance_mm": 3.0, "max_parallel_mm": 5.0},
    "R3": {"unsplittable": True},
    "R4": {"return_via_required": True, "max_distance_mm": 2.0},
    "R5": {"min_clearance_mm": 0.5},
    "R6": {"plane_forbidden": True, "keepout_zones_forbidden": True},
}

_GRAN_EVIDENCE = "V5.0-DEV-TASKBOOK §5.1/§6 D 层"

# scope 语法合同（L0.5 编译器 v5/compiler.py，五形态，逗号可多值，语法非法 fail-closed）：
#   partitioning / partition:<id> / zone:<id> / ptype:<P> / net_class:<x>
#
# 初版自由标签 → 合法选择器映射表（2026-09-13 交叉冒烟修正；priority/yields_to/几何/note
# 算式一律不动，仅 scope 换锚，冲突语义不变）：
#   power_corridor       → ptype:PWR     （scope 只锚对象类型；走廊维度属几何解析，
#                                          由 P2/P3 生成器挂钩处理——派发方给定映射）
#   bus_routing          → ptype:BUS     （ribbon 组分区 BUS-RIB 即 ptype BUS，类型锚定）
#   clock_routing        → ptype:CLK     （CLK 分区类型锚定）
#   length_cost          → partitioning  （短线偏好=全板政策类，无特定对象——派发方给定）
#   diff_pair            → ptype:DIFF    （差分对组分区 DP1 即 ptype DIFF）
#   corridor_capacity    → zone:COR-D    （容量预算精确锚定声明容量的那条走廊几何）
#   crosstalk_mitigation → partition:VI  （串扰预算的动作对象=victim 分区，精确锚定）
#   via_budget           → partitioning  （过孔节俭=全板层计划政策类）
#   length_matching      → partition:EQA,partition:EQB,partition:EQC
#                                          （等长组=固定三分区，逗号多值精确锚定组几何）
#   layer_strategy       → partitioning  （层优选=全板层政策类）
#   net_completion       → partitioning  （完成性=全板排序政策类）
#   existing_copper      → partition:RT1 （既布铜保护精确锚定 RT1 既布分区）
#   width_invariant      → ptype:PWR     （R1 载流地板作用于电源分区类型）
#   width_prior          → partition:PW2 （细线先验精确锚定其作用分区 PW2）
# 另：粒度先验 scope 本即合法裸 token "partitioning"，不在映射之列。


# --------------------------------------------------------------- 公共构造件

def _sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _principle_hash(entry):
    """条目 source_hash = sha256(canonical(剔除 source_hash 后条目字节))。统一入口。"""
    view = dict(entry)
    view.pop("source_hash", None)
    return canonical.canonical_sha256(view)


def _layer(lid, kind, direction, available):
    return {"id": lid, "kind": kind, "preferred_direction": direction,
            "available": available}


def _stackup(b_cu=True, in1_signal=False):
    """四层叠层模板。b_cu=False 用于 adv-01（仅 F.Cu 可用，制造单层容量挤兑）。"""
    layers = [_layer("F.Cu", "signal", "h", True)]
    if in1_signal:
        layers.append(_layer("In1.Cu", "signal", "v", True))
    layers.append(_layer("In2.Cu", "plane", "any", False))
    layers.append(_layer("B.Cu", "signal", "any", b_cu))
    return layers


def _principle(pid, name, protects, sacrifices, scope, resources, freedom,
               priority, compiled_rule, enforcement, conflicts_with, yields_to,
               evidence_refs, hard_or_soft="soft", overridable=True):
    """15 字段理念条目（字段清单=schemas/principle_registry.v1.schema.json）。"""
    entry = {
        "principle_id": pid,
        "name": name,
        "intent": {"protects": protects, "sacrifices": sacrifices},
        "scope": scope,
        "protected_resources": list(resources),
        "target_freedom": freedom,
        "priority": priority,
        "hard_or_soft": hard_or_soft,
        "overridable": overridable,
        "compiled_rule": compiled_rule,
        "enforcement": enforcement,
        "conflict_policy": {"conflicts_with": list(conflicts_with),
                            "yields_to": list(yields_to)},
        "evidence_refs": list(evidence_refs),
        "version": "1.0.0",
    }
    entry["source_hash"] = _principle_hash(entry)
    return entry


def _granularity(suffix, min_gap_mm):
    """分区聚类粒度先验（任务书逐字模板；仅板短名与 min_gap_mm 逐板不同）。"""
    entry = {
        "principle_id": "P-PART-GRAN-" + suffix,
        "name": "分区聚类粒度先验",
        "intent": {"protects": "走廊通行容量", "sacrifices": "细粒度分配自由"},
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
        "evidence_refs": [_GRAN_EVIDENCE],
        "version": "1.0.0",
    }
    entry["source_hash"] = _principle_hash(entry)
    return entry


def _misc(pid, x0, y0, x1, y1, note="无关网（不涉本板冲突几何）"):
    """无关填充网分区（MISC 短线，远离冲突几何；用于把每板网数补到 6）。"""
    return {"partition_id": pid, "ptype": "MISC",
            "geometry": {"endpoints": [[x0, y0], [x1, y1]]},
            "layer_policy": "any",
            "width_prior": {"w_min": 0.2, "w_max": 0.2},
            "current_a": 0.0, "speed_class": "low_speed", "note": note}


def _net(nid, ncls, pids):
    return {"net_id": nid, "net_class": ncls, "partitions": list(pids)}


def _finalize(builder_fn):
    """落链：source_sha256=构造函数源码文本 sha256；board_sha256=现算填入。"""
    board = builder_fn()
    prov = board["provenance"]
    prov["source_sha256"] = _sha256_text(inspect.getsource(builder_fn))
    prov["board_sha256"] = compute_board_sha256(board)
    return board


# --------------------------------------------------------------- 七块对抗板

def build_adv01():
    """adv-01-pwr-vs-bus——电源 vs 普通总线（冲突电池第 1 对）。

    几何事实：本板仅 F.Cu 可用（B.Cu/In1/In2 均 unavailable），唯一近道走廊
    COR-C 声明容量 3.7；capacity 账本口径（铜宽+0.5×相邻对）：
    ribbon 声明 2.4 + PWR 铜宽 0.8 + 相邻对 0.5×1 = 3.7 = 容量（零余量临界）。
    PWR 抢走廊则限宽 0.8 且零余量；PWR 取 1.0 则 3.9>3.7，
    ribbon（R3 整体不可拆）让位须整体绕行东缘 +53.3mm——两个方向都真实可算。
    """
    board = {
        "schema_version": "v5.board.v1",
        "board_id": "adv-01-pwr-vs-bus",
        "stackup": _stackup(b_cu=False),
        "workspace": {"x_min": 0.0, "y_min": 0.0, "x_max": 60.0, "y_max": 40.0},
        "zones": [
            {"zone_id": "K-WEST", "kind": "keepout", "layers": "all",
             "rect": {"x_min": 0.0, "y_min": 12.0, "x_max": 26.0, "y_max": 28.0},
             "note": "西墙禁布"},
            {"zone_id": "K-EAST", "kind": "keepout", "layers": "all",
             "rect": {"x_min": 34.0, "y_min": 12.0, "x_max": 52.0, "y_max": 28.0},
             "note": "东墙禁布（其右侧 x∈(52,60) 为整体绕行道）"},
            {"zone_id": "COR-C", "kind": "corridor", "layers": "signal",
             "rect": {"x_min": 26.0, "y_min": 12.0, "x_max": 34.0, "y_max": 28.0},
             "capacity": 3.7,
             "note": "唯一近道（本板仅 F.Cu 可用，容量即总量）；capacity 账本口径"
                     "（铜宽+0.5×相邻对）：ribbon 声明 2.4+PWR 铜宽 0.8+相邻对 "
                     "0.5×1=3.7=容量 3.7，零余量临界；可用布线带 x∈[28.15,31.85]"
                     "（ribbon 铜带 [28.15,30.55]，PWR 槽 [31.05,31.85]）；"
                     "PWR 若取 1.0 则 2.4+0.5+1.0=3.9>3.7，ribbon 让位须整体绕行"
                     "东缘 [29.35,2]→[56,2]→[56,38]→[29.35,38]="
                     "26.65+36.0+26.65=89.3（较直通 36.0 多 53.3）"},
        ],
        "partitions": [
            {"partition_id": "PW1", "ptype": "PWR",
             "geometry": {"endpoints": [[8.0, 4.0], [50.0, 36.0]]},
             "layer_policy": "F.Cu",
             "width_prior": {"w_min": 0.8, "w_max": 1.2},
             "current_a": 2.0, "speed_class": "power", "planned_width": 0.8,
             "note": "PWR 2.0A：R1 下限=max(0.4×2.0,0.3)=0.8；抢走廊则限宽 0.8 且零余量"},
            {"partition_id": "BUS-RIB", "ptype": "BUS",
             "geometry": {"endpoints": [[29.35, 2.0], [29.35, 38.0]],
                          "centerline": [[29.35, 2.0], [29.35, 38.0]],
                          "occupancy_mm": 2.4,
                          "copper_band": [28.15, 30.55]},
             "layer_policy": "F.Cu",
             "width_prior": {"w_min": 0.3, "w_max": 0.3},
             "current_a": 0.0, "speed_class": "bus_4bit",
             "note": "4 位 ribbon（BUS-B0..B3 共用本组分区），R3 整体不可拆；"
                     "声明占用 2.4=4×0.3 铜宽+3×0.4 对内距；让位结果："
                     "P-BUS-INTEGRITY(40) yields_to P-PWR-PRIORITY(80)，"
                     "让位范围=放弃直通、整体绕行东缘 +53.3"},
            _misc("MS1", 4.0, 4.0, 4.0, 10.0, "无关网（西区内短线，不涉走廊）"),
        ],
        "nets": [
            _net("PWR-MAIN", "PWR", ["PW1"]),
            _net("BUS-B0", "BUS", ["BUS-RIB"]),
            _net("BUS-B1", "BUS", ["BUS-RIB"]),
            _net("BUS-B2", "BUS", ["BUS-RIB"]),
            _net("BUS-B3", "BUS", ["BUS-RIB"]),
            _net("MISC-A", "MISC", ["MS1"]),
        ],
        "hard_rules": HARD_RULES,
        "principle_registry": [
            _granularity("PWR-BUS", 2.0),
            _principle("P-PWR-PRIORITY", "电源网走廊优先权",
                       "大电流电源网的低阻通路（R1 宽度自由）", "普通总线的直通路径",
                       "ptype:PWR", ["corridor_capacity", "power_ir_drop"],
                       "allocation", 80,
                       {"kind": "power_corridor_priority",
                        "params": {"min_width_mm": 0.8}},
                       "generation", ["P-BUS-INTEGRITY"], [],
                       ["V5.0-DEV-TASKBOOK §5.1 冲突电池第1对（电源 vs 普通总线）/§6 D 层"]),
            _principle("P-BUS-INTEGRITY", "总线 ribbon 完整性",
                       "ribbon 整体不可拆与对内间距（R3）", "电源网在走廊内的宽度裕量",
                       "ptype:BUS", ["ribbon_unity", "bus_skew"],
                       "allocation", 40,
                       {"kind": "ribbon_whole_route", "params": {"member_count": 4}},
                       "generation", ["P-PWR-PRIORITY"], ["P-PWR-PRIORITY"],
                       ["V5.0-DEV-TASKBOOK §5.1 冲突电池第1对（电源 vs 普通总线）/§6 D 层"]),
        ],
        "provenance": {
            "source_type": "synthetic",
            "source_uri": "boards/build_adversarial_boards.py#adv-01-pwr-vs-bus",
            "adapter": "hand",
        },
    }
    return board


def build_adv02():
    """adv-02-clk-vs-short——时钟 vs 短线偏好（冲突电池第 2 对）。

    几何事实：CLK 200MHz 直线 y=8.8（36.0mm 最短）距敏感区下缘 y=12.0 仅
    3.2mm>3.0（R2 合规：check_ana_proximity 要求距离<3.0 且平行>5.0 才违例），
    但原则 P-CLK-ISOLATE 要求 5.0；绕行至 y=7.0（距 5.0）后 36.0→39.6（+3.6），
    绕行使 CLK 变长的事实写进 zone note。
    """
    board = {
        "schema_version": "v5.board.v1",
        "board_id": "adv-02-clk-vs-short",
        "stackup": _stackup(),
        "workspace": {"x_min": 0.0, "y_min": 0.0, "x_max": 60.0, "y_max": 40.0},
        "zones": [
            {"zone_id": "SENS", "kind": "sensitive", "layers": "signal",
             "rect": {"x_min": 20.0, "y_min": 12.0, "x_max": 26.0, "y_max": 18.0},
             "note": "敏感区（R2 口径）：CLK 直线 y=8.8 距下缘 12.0-8.8=3.2>3.0 "
                     "R2 合规；P-CLK-ISOLATE 要求 5.0，绕行至 y=7.0（距 5.0）后 "
                     "36.0→39.6（+3.6），绕行使 CLK 变长的事实在此立据"},
        ],
        "partitions": [
            {"partition_id": "CK1", "ptype": "CLK",
             "geometry": {"endpoints": [[4.0, 8.8], [40.0, 8.8]]},
             "layer_policy": "F.Cu",
             "width_prior": {"w_min": 0.15, "w_max": 0.15},
             "current_a": 0.0, "speed_class": "clk_200M", "planned_width": 0.15,
             "note": "CLK 200MHz；直线 36.0mm 最短但距敏感区仅 3.2mm；让位结果："
                     "P-SHORT-RUN(30) yields_to P-CLK-ISOLATE(60)，"
                     "让位范围=接受 +3.6mm 绕行"},
            _misc("MS1", 50.0, 4.0, 56.0, 4.0),
            _misc("MS2", 50.0, 8.0, 56.0, 8.0),
            _misc("MS3", 50.0, 12.0, 56.0, 12.0),
            _misc("MS4", 4.0, 36.0, 10.0, 36.0),
            _misc("MS5", 50.0, 36.0, 56.0, 36.0),
        ],
        "nets": [
            _net("CLK-200M", "CLK", ["CK1"]),
            _net("MISC-A", "MISC", ["MS1"]),
            _net("MISC-B", "MISC", ["MS2"]),
            _net("MISC-C", "MISC", ["MS3"]),
            _net("MISC-D", "MISC", ["MS4"]),
            _net("MISC-E", "MISC", ["MS5"]),
        ],
        "hard_rules": HARD_RULES,
        "principle_registry": [
            _granularity("CLK-SHORT", 2.5),
            _principle("P-CLK-ISOLATE", "时钟远离敏感区",
                       "时钟信号对敏感区的隔离距离", "时钟网的走线长度（绕行变长）",
                       "ptype:CLK", ["sensitive_zone_isolation",
                                         "clk_signal_integrity"],
                       "corridor", 60,
                       {"kind": "sensitive_clearance",
                        "params": {"min_distance_mm": 5.0}},
                       "generation", ["P-SHORT-RUN"], [],
                       ["V5.0-DEV-TASKBOOK §5.1 冲突电池第2对（时钟 vs 短线偏好）/§6 D 层"]),
            _principle("P-SHORT-RUN", "短线偏好",
                       "走线长度与铜成本最小化", "对敏感区的额外隔离距离",
                       "partitioning", ["route_length", "copper_cost"],
                       "ordering", 30,
                       {"kind": "short_run", "params": {"prefer": "min_length"}},
                       "generation", ["P-CLK-ISOLATE"], ["P-CLK-ISOLATE"],
                       ["V5.0-DEV-TASKBOOK §5.1 冲突电池第2对（时钟 vs 短线偏好）/§6 D 层"]),
        ],
        "provenance": {
            "source_type": "synthetic",
            "source_uri": "boards/build_adversarial_boards.py#adv-02-clk-vs-short",
            "adapter": "hand",
        },
    }
    return board


def build_adv03():
    """adv-03-diff-vs-capacity——差分对 vs 走廊容量（冲突电池第 3 对）。

    几何事实：DP1 分区（两网 DP-P/DP-N 同分区）几何为 2 条平行 endpoints
    （P 线与 N 线 centerline，对内耦合间距 0.6）；两网必须同层成对过走廊 COR-D，
    而走廊声明容量 1.0 < 对占用（capacity 账本口径：铜宽+0.5×相邻对 =
    0.3+0.3+0.5×1=1.1）——冲突真实成立，P-DIFF-PAIRING(70) 胜。
    """
    board = {
        "schema_version": "v5.board.v1",
        "board_id": "adv-03-diff-vs-capacity",
        "stackup": _stackup(),
        "workspace": {"x_min": 0.0, "y_min": 0.0, "x_max": 60.0, "y_max": 40.0},
        "zones": [
            {"zone_id": "K-WEST", "kind": "keepout", "layers": "all",
             "rect": {"x_min": 0.0, "y_min": 12.0, "x_max": 26.0, "y_max": 28.0},
             "note": "西墙禁布"},
            {"zone_id": "K-EAST", "kind": "keepout", "layers": "all",
             "rect": {"x_min": 34.0, "y_min": 12.0, "x_max": 52.0, "y_max": 28.0},
             "note": "东墙禁布（其右侧 x∈(52,60) 为替代长通道）"},
            {"zone_id": "COR-D", "kind": "corridor", "layers": "signal",
             "rect": {"x_min": 26.0, "y_min": 12.0, "x_max": 34.0, "y_max": 28.0},
             "capacity": 1.0,
             "note": "声明容量 1.0；DIFF 对占用按 capacity 账本口径"
                     "（铜宽+0.5×相邻对）=0.3+0.3+0.5×1=1.1>1.0；"
                     "P-CORRIDOR-BUDGET(45) yields_to P-DIFF-PAIRING(70)，"
                     "让位范围=容忍该走廊超支，或为对改道东缘长通道"},
        ],
        "partitions": [
            {"partition_id": "DP1", "ptype": "DIFF",
             "geometry": {"endpoints": [[10.0, 4.0], [50.0, 36.0]],
                          "centerline": [[10.0, 4.6], [50.0, 36.6]],
                          "occupancy_mm": 1.1},
             "layer_policy": "F.Cu",
             "width_prior": {"w_min": 0.3, "w_max": 0.3},
             "current_a": 0.0, "speed_class": "diff_100M",
             "note": "差分对同分区（DP-P/DP-N 两网共用）；几何=2 条平行 endpoints："
                     "P 线 [10,4]-[50,36]，N 线（centerline）[10,4.6]-[50,36.6]，"
                     "对内耦合间距 0.6；须同层成对过走廊；对占用 "
                     "0.3+0.3+0.5×1=1.1>声明容量 1.0"},
            _misc("MS1", 4.0, 30.0, 4.0, 36.0),
            _misc("MS2", 56.0, 4.0, 56.0, 10.0),
            _misc("MS3", 40.0, 2.0, 46.0, 2.0),
            _misc("MS4", 14.0, 2.0, 20.0, 2.0),
        ],
        "nets": [
            _net("DP-P", "DIFF", ["DP1"]),
            _net("DP-N", "DIFF", ["DP1"]),
            _net("MISC-A", "MISC", ["MS1"]),
            _net("MISC-B", "MISC", ["MS2"]),
            _net("MISC-C", "MISC", ["MS3"]),
            _net("MISC-D", "MISC", ["MS4"]),
        ],
        "hard_rules": HARD_RULES,
        "principle_registry": [
            _granularity("DIFF-CAP", 1.5),
            _principle("P-DIFF-PAIRING", "差分对同层成对",
                       "差分对内耦合（同层成对过走廊）", "走廊声明容量的严格遵守",
                       "ptype:DIFF", ["diff_pair_coupling",
                                     "common_mode_rejection"],
                       "allocation", 70,
                       {"kind": "diff_pair_coupling",
                        "params": {"coupling_gap_mm": 0.6, "same_layer": True}},
                       "generation", ["P-CORRIDOR-BUDGET"], [],
                       ["V5.0-DEV-TASKBOOK §5.1 冲突电池第3对（差分对 vs 走廊容量）/§6 D 层"]),
            _principle("P-CORRIDOR-BUDGET", "走廊容量预算",
                       "走廊声明容量不超支", "差分对的成对直通",
                       "zone:COR-D", ["corridor_capacity"],
                       "corridor", 45,
                       {"kind": "corridor_capacity_budget",
                        "params": {"respect_declared_capacity": True}},
                       "generation", ["P-DIFF-PAIRING"], ["P-DIFF-PAIRING"],
                       ["V5.0-DEV-TASKBOOK §5.1 冲突电池第3对（差分对 vs 走廊容量）/§6 D 层"]),
        ],
        "provenance": {
            "source_type": "synthetic",
            "source_uri": "boards/build_adversarial_boards.py#adv-03-diff-vs-capacity",
            "adapter": "hand",
        },
    }
    return board


def build_adv04():
    """adv-04-xtalk-vs-vias——串扰预算 vs 过孔数量（冲突电池第 4 对）。

    几何事实：aggressor（AG，HS）与 victim（VI）平行走线段恰 6.0mm
    （x∈[15,21]）>5.0 且 centerline 间距 2.4<3.0 → 触发 P-XTALK-BUDGET 预算；
    缓解=VI 换层 B.Cu 须打 2 过孔（下 1 上 1）> P-VIA-FRUGAL 上限 1——
    两原则的让位结果写进 AG/VI 各自 note。本板无敏感区，R2 不触发（硬规则零冲突）。
    """
    board = {
        "schema_version": "v5.board.v1",
        "board_id": "adv-04-xtalk-vs-vias",
        "stackup": _stackup(),
        "workspace": {"x_min": 0.0, "y_min": 0.0, "x_max": 60.0, "y_max": 40.0},
        "zones": [
            {"zone_id": "COR-P", "kind": "corridor", "layers": "signal",
             "rect": {"x_min": 14.0, "y_min": 19.0, "x_max": 22.0, "y_max": 24.0},
             "capacity": 0.9,
             "note": "平行段共用通道（容量擦边）：0.2+0.2+0.5×1=0.9=容量 0.9；"
                     "非本板原则冲突点"},
        ],
        "partitions": [
            {"partition_id": "AG", "ptype": "HS",
             "geometry": {"endpoints": [[15.0, 20.0], [21.0, 20.0]]},
             "layer_policy": "F.Cu",
             "width_prior": {"w_min": 0.2, "w_max": 0.2},
             "current_a": 0.0, "speed_class": "hs_250M", "planned_width": 0.2,
             "note": "aggressor（高速翻转源）；与 victim 平行 6.0mm（x∈[15,21]）、"
                     "centerline 间距 2.4；裁决预告：P-XTALK-BUDGET(65) 胜，"
                     "AG 自身不动"},
            {"partition_id": "VI", "ptype": "MISC",
             "geometry": {"endpoints": [[13.0, 22.4], [23.0, 22.4]]},
             "layer_policy": "F.Cu",
             "width_prior": {"w_min": 0.2, "w_max": 0.2},
             "current_a": 0.0, "speed_class": "low_speed", "planned_width": 0.2,
             "note": "victim；平行 6.0>5.0 且间距 2.4<3.0 触发 P-XTALK-BUDGET；"
                     "缓解=换层 B.Cu 打 2 过孔（下 1 上 1）>P-VIA-FRUGAL 上限 1；"
                     "让位结果：P-VIA-FRUGAL(35) yields_to P-XTALK-BUDGET(65)，"
                     "让位范围=接受 2 过孔以使 6mm 平行归零"},
            _misc("MS1", 30.0, 4.0, 36.0, 4.0),
            _misc("MS2", 44.0, 8.0, 50.0, 8.0),
            _misc("MS3", 4.0, 30.0, 10.0, 30.0),
            _misc("MS4", 50.0, 30.0, 56.0, 30.0),
        ],
        "nets": [
            _net("AGGR-HS", "HS", ["AG"]),
            _net("VICT-SNS", "MISC", ["VI"]),
            _net("MISC-A", "MISC", ["MS1"]),
            _net("MISC-B", "MISC", ["MS2"]),
            _net("MISC-C", "MISC", ["MS3"]),
            _net("MISC-D", "MISC", ["MS4"]),
        ],
        "hard_rules": HARD_RULES,
        "principle_registry": [
            _granularity("XTALK-VIA", 2.25),
            _principle("P-XTALK-BUDGET", "串扰平行长度预算",
                       "victim 信号完整性（平行长度预算）", "过孔数量与层计划简单性",
                       "partition:VI", ["victim_snr",
                                                "parallel_length_budget"],
                       "layer_plan", 65,
                       {"kind": "crosstalk_budget",
                        "params": {"max_parallel_mm": 5.0, "min_gap_mm": 3.0}},
                       "generation", ["P-VIA-FRUGAL"], [],
                       ["V5.0-DEV-TASKBOOK §5.1 冲突电池第4对（串扰预算 vs 过孔数量）/§6 D 层"]),
            _principle("P-VIA-FRUGAL", "过孔节俭",
                       "过孔数量（制造成本与回流质量）", "victim 的换层拉开缓解",
                       "partitioning", ["via_count", "return_path_quality"],
                       "layer_plan", 35,
                       {"kind": "via_frugal", "params": {"max_extra_vias": 1}},
                       "generation", ["P-XTALK-BUDGET"], ["P-XTALK-BUDGET"],
                       ["V5.0-DEV-TASKBOOK §5.1 冲突电池第4对（串扰预算 vs 过孔数量）/§6 D 层"]),
        ],
        "provenance": {
            "source_type": "synthetic",
            "source_uri": "boards/build_adversarial_boards.py#adv-04-xtalk-vs-vias",
            "adapter": "hand",
        },
    }
    return board


def build_adv05():
    """adv-05-eqlen-vs-layerpref——等长组 vs 层优选（冲突电池第 5 对）。

    几何事实：3 网（EQ-A/EQ-B/EQ-C）等长组，tolerance 0.5mm；最长者 EQ-A
    直线 40.0 沿 F.Cu 优选方向（h）；EQ-B 直线 38.0、EQ-C 直线 37.0 须蛇形
    补偿至 ≥39.5（组内差 <0.5），蛇形竖直 jog 段违背 P-LAYER-PREF 的
    F.Cu/h 优选——冲突真实成立，P-EQLEN-GROUP(60) 胜。
    """
    board = {
        "schema_version": "v5.board.v1",
        "board_id": "adv-05-eqlen-vs-layerpref",
        "stackup": _stackup(in1_signal=True),
        "workspace": {"x_min": 0.0, "y_min": 0.0, "x_max": 60.0, "y_max": 40.0},
        "zones": [
            {"zone_id": "K-EAST", "kind": "keepout", "layers": "all",
             "rect": {"x_min": 50.0, "y_min": 0.0, "x_max": 60.0, "y_max": 40.0},
             "note": "东缘禁布（界定蛇形活动区东界）"},
        ],
        "partitions": [
            {"partition_id": "EQA", "ptype": "CLK",
             "geometry": {"endpoints": [[5.0, 10.0], [45.0, 10.0]]},
             "layer_policy": "F.Cu",
             "width_prior": {"w_min": 0.2, "w_max": 0.2},
             "current_a": 0.0, "speed_class": "clk_150M", "planned_width": 0.2,
             "note": "等长组基准（最长）：直线 40.0 沿 F.Cu h 优选方向"},
            {"partition_id": "EQB", "ptype": "CLK",
             "geometry": {"endpoints": [[5.0, 14.0], [43.0, 14.0]]},
             "layer_policy": "F.Cu",
             "width_prior": {"w_min": 0.2, "w_max": 0.2},
             "current_a": 0.0, "speed_class": "clk_150M", "planned_width": 0.2,
             "note": "直线 38.0（短 2.0）：蛇形补至 ≥39.5（组内差 <0.5）；"
                     "竖直 jog 段违背 P-LAYER-PREF 的 h 优选；让位结果："
                     "P-LAYER-PREF(40) yields_to P-EQLEN-GROUP(60)，"
                     "让位范围=F.Cu 上的蛇形 jog 段豁免"},
            {"partition_id": "EQC", "ptype": "CLK",
             "geometry": {"endpoints": [[5.0, 18.0], [42.0, 18.0]]},
             "layer_policy": "F.Cu",
             "width_prior": {"w_min": 0.2, "w_max": 0.2},
             "current_a": 0.0, "speed_class": "clk_150M", "planned_width": 0.2,
             "note": "直线 37.0（短 3.0）：蛇形补至 ≥39.5（组内差 <0.5）；"
                     "同 EQB，jog 段违背 h 优选"},
            _misc("MS1", 20.0, 30.0, 30.0, 30.0),
            _misc("MS2", 34.0, 30.0, 44.0, 30.0),
            _misc("MS3", 20.0, 34.0, 30.0, 34.0),
        ],
        "nets": [
            _net("EQ-A", "CLK", ["EQA"]),
            _net("EQ-B", "CLK", ["EQB"]),
            _net("EQ-C", "CLK", ["EQC"]),
            _net("MISC-A", "MISC", ["MS1"]),
            _net("MISC-B", "MISC", ["MS2"]),
            _net("MISC-C", "MISC", ["MS3"]),
        ],
        "hard_rules": HARD_RULES,
        "principle_registry": [
            _granularity("EQLEN-LAYER", 3.0),
            _principle("P-EQLEN-GROUP", "等长组补偿",
                       "组内等长（长度差 <0.5mm）",
                       "F.Cu 优选方向的全程遵守（蛇形 jog）",
                       "partition:EQA,partition:EQB,partition:EQC",
                       ["group_skew_budget"],
                       "allocation", 60,
                       {"kind": "equal_length_group",
                        "params": {"tolerance_mm": 0.5,
                                   "members": ["EQ-A", "EQ-B", "EQ-C"]}},
                       "generation", ["P-LAYER-PREF"], [],
                       ["V5.0-DEV-TASKBOOK §5.1 冲突电池第5对（等长组 vs 层优选）/§6 D 层"]),
            _principle("P-LAYER-PREF", "层优选方向",
                       "F.Cu 水平优选方向的通流与制造质量", "等长补偿的蛇形走线",
                       "partitioning", ["preferred_direction_quality",
                                          "fabrication_yield"],
                       "layer_plan", 40,
                       {"kind": "layer_preference",
                        "params": {"layer": "F.Cu", "direction": "h"}},
                       "generation", ["P-EQLEN-GROUP"], ["P-EQLEN-GROUP"],
                       ["V5.0-DEV-TASKBOOK §5.1 冲突电池第5对（等长组 vs 层优选）/§6 D 层"]),
        ],
        "provenance": {
            "source_type": "synthetic",
            "source_uri": "boards/build_adversarial_boards.py#adv-05-eqlen-vs-layerpref",
            "adapter": "hand",
        },
    }
    return board


def build_adv06():
    """adv-06-copper-vs-completion——既有铜保护 vs 新网完成性（冲突电池第 6 对）。

    几何事实：既布 ROUTED 铜带（RT1，0.4 宽，y∈[19.8,20.2]）与南墙禁布
    （K-SOUTH，y≤19.1）之间成 0.7mm 缝隙（y∈[19.1,19.8]，唯一南北通道）；
    新网 NET-NEW（线宽 0.1）守 1.0mm 保护距则 1.0+0.1=1.1>0.7 无法穿过；
    按两侧各留 0.5 净距算 0.5+0.1+0.5=1.1>0.7 亦不够；放弃保护距、铜侧仅守
    R5 0.5（对侧为禁布边界）：0.5+0.1=0.6≤0.7 可过——本对让完成性赢
    （P-COPPER-GUARD(55) yields_to P-COMPLETION(75)，与 adv-01 相反方向）。
    """
    board = {
        "schema_version": "v5.board.v1",
        "board_id": "adv-06-copper-vs-completion",
        "stackup": _stackup(),
        "workspace": {"x_min": 0.0, "y_min": 0.0, "x_max": 60.0, "y_max": 40.0},
        "zones": [
            {"zone_id": "K-SOUTH", "kind": "keepout", "layers": "all",
             "rect": {"x_min": 0.0, "y_min": 8.0, "x_max": 60.0, "y_max": 19.1},
             "note": "南墙禁布；上缘 y=19.1 与既布铜带下缘 y=19.8 之间成 0.7mm "
                     "缝隙（y∈[19.1,19.8]，唯一南北通道）"},
        ],
        "partitions": [
            {"partition_id": "RT1", "ptype": "ROUTED",
             "geometry": {"endpoints": [[0.0, 20.0], [60.0, 20.0]]},
             "layer_policy": "F.Cu",
             "width_prior": {"w_min": 0.4, "w_max": 0.4},
             "current_a": 0.0, "speed_class": "existing_routed",
             "planned_width": 0.4,
             "note": "既布铜带 0.4 宽（y∈[19.8,20.2]），路径固定；受 P-COPPER-GUARD 保护"},
            {"partition_id": "NEW1", "ptype": "MISC",
             "geometry": {"endpoints": [[6.0, 4.0], [40.0, 36.0]]},
             "layer_policy": "F.Cu",
             "width_prior": {"w_min": 0.1, "w_max": 0.2},
             "current_a": 0.0, "speed_class": "low_speed", "planned_width": 0.1,
             "note": "新网必须穿 0.7mm 缝隙连通南北：守 1.0mm 保护距则 "
                     "1.0+0.1=1.1>0.7 无法穿过；按两侧各留 0.5 净距算 "
                     "0.5+0.1+0.5=1.1>0.7 亦不够；放弃保护距、铜侧仅守 R5 0.5"
                     "（对侧为禁布边界）：0.5+0.1=0.6≤0.7 可过，仅剩 0.6mm 可过；"
                     "让位结果：P-COPPER-GUARD(55) yields_to P-COMPLETION(75)，"
                     "让位范围=保护距 1.0→R5 0.5"},
            _misc("MS1", 4.0, 2.0, 10.0, 2.0),
            _misc("MS2", 46.0, 2.0, 52.0, 2.0),
            _misc("MS3", 8.0, 24.0, 14.0, 24.0),
            _misc("MS4", 46.0, 30.0, 52.0, 30.0),
        ],
        "nets": [
            _net("NET-NEW", "MISC", ["NEW1"]),
            _net("NET-EXIST", "MISC", ["RT1"]),
            _net("MISC-A", "MISC", ["MS1"]),
            _net("MISC-B", "MISC", ["MS2"]),
            _net("MISC-C", "MISC", ["MS3"]),
            _net("MISC-D", "MISC", ["MS4"]),
        ],
        "hard_rules": HARD_RULES,
        "principle_registry": [
            _granularity("COPPER-COMP", 1.75),
            _principle("P-COMPLETION", "新网完成性优先",
                       "全部新网布通（完成性）", "对既布铜的额外保护距离",
                       "partitioning", ["net_connectivity"],
                       "ordering", 75,
                       {"kind": "completion_first", "params": {}},
                       "generation", ["P-COPPER-GUARD"], [],
                       ["V5.0-DEV-TASKBOOK §5.1 冲突电池第6对（既有铜保护 vs 新网完成性）/§6 D 层"]),
            _principle("P-COPPER-GUARD", "既有铜保护距离",
                       "既布铜的保护距离与回流完整性", "新网的连通完成性",
                       "partition:RT1", ["existing_copper_integrity",
                                           "return_current_path"],
                       "corridor", 55,
                       {"kind": "existing_copper_guard",
                        "params": {"min_gap_mm": 1.0}},
                       "generation", ["P-COMPLETION"], ["P-COMPLETION"],
                       ["V5.0-DEV-TASKBOOK §5.1 冲突电池第6对（既有铜保护 vs 新网完成性）/§6 D 层"]),
        ],
        "provenance": {
            "source_type": "synthetic",
            "source_uri": "boards/build_adversarial_boards.py#adv-06-copper-vs-completion",
            "adapter": "hand",
        },
    }
    return board


def build_adv07():
    """adv-07-objection-vs-floor——软先验 objection vs 不变式地板（冲突电池第 7 对）。

    几何/数值事实：PWR 0.8A 网 R1 地板=max(0.4×0.8,0.3)=0.32；软先验
    P-WIDTH-SLIM 目标 0.25<0.32，其最优值撞硬地板——此板专测
    「对硬规则的反对即拒」：P-WIDTH-SLIM(45, soft, overridable=true)
    yields_to P-R1-FLOOR(100, hard, overridable=false, enforcement=check)。
    """
    board = {
        "schema_version": "v5.board.v1",
        "board_id": "adv-07-objection-vs-floor",
        "stackup": _stackup(),
        "workspace": {"x_min": 0.0, "y_min": 0.0, "x_max": 60.0, "y_max": 40.0},
        "zones": [
            {"zone_id": "K-MID", "kind": "keepout", "layers": "all",
             "rect": {"x_min": 24.0, "y_min": 24.0, "x_max": 36.0, "y_max": 36.0},
             "note": "中部禁布：PWR 需绕行，几何真实化"},
        ],
        "partitions": [
            {"partition_id": "PW2", "ptype": "PWR",
             "geometry": {"endpoints": [[6.0, 32.0], [54.0, 32.0]]},
             "layer_policy": "F.Cu",
             "width_prior": {"w_min": 0.32, "w_max": 0.6},
             "current_a": 0.8, "speed_class": "power", "planned_width": 0.32,
             "note": "PWR 0.8A：R1 地板=max(0.4×0.8,0.3)=0.32；P-WIDTH-SLIM 目标 "
                     "0.25<0.32 撞硬地板——对硬规则的反对即拒"
                     "（P-WIDTH-SLIM yields_to P-R1-FLOOR）"},
            _misc("MS1", 4.0, 4.0, 12.0, 4.0),
            _misc("MS2", 20.0, 4.0, 28.0, 4.0),
            _misc("MS3", 40.0, 4.0, 48.0, 4.0),
            _misc("MS4", 4.0, 12.0, 12.0, 12.0),
            _misc("MS5", 48.0, 16.0, 56.0, 16.0),
        ],
        "nets": [
            _net("PWR-SLIM", "PWR", ["PW2"]),
            _net("MISC-A", "MISC", ["MS1"]),
            _net("MISC-B", "MISC", ["MS2"]),
            _net("MISC-C", "MISC", ["MS3"]),
            _net("MISC-D", "MISC", ["MS4"]),
            _net("MISC-E", "MISC", ["MS5"]),
        ],
        "hard_rules": HARD_RULES,
        "principle_registry": [
            _granularity("OBJ-FLOOR", 2.75),
            _principle("P-R1-FLOOR", "R1 载流宽度地板",
                       "R1 载流宽度下限不变式", "无——不变式地板不让位",
                       "ptype:PWR", ["current_capacity_floor"],
                       "allocation", 100,
                       {"kind": "r1_width_floor",
                        "params": {"k_a": 0.4, "floor_mm": 0.3}},
                       "check", ["P-WIDTH-SLIM"], [],
                       ["V5.0-DEV-TASKBOOK §5.1 冲突电池第7对（软先验 objection vs 不变式地板）/§6 D 层"],
                       hard_or_soft="hard", overridable=False),
            _principle("P-WIDTH-SLIM", "细线化宽度先验",
                       "细线化的功耗与密度收益", "载流安全裕量（撞 R1 即弃）",
                       "partition:PW2", ["routing_density", "power_loss"],
                       "allocation", 45,
                       {"kind": "width_push", "params": {"target_width_mm": 0.25}},
                       "generation", ["P-R1-FLOOR"], ["P-R1-FLOOR"],
                       ["V5.0-DEV-TASKBOOK §5.1 冲突电池第7对（软先验 objection vs 不变式地板）/§6 D 层"]),
        ],
        "provenance": {
            "source_type": "synthetic",
            "source_uri": "boards/build_adversarial_boards.py#adv-07-objection-vs-floor",
            "adapter": "hand",
        },
    }
    return board


# --------------------------------------------------------------- 落盘入口

BOARDS = {
    "adv-01-pwr-vs-bus": build_adv01,
    "adv-02-clk-vs-short": build_adv02,
    "adv-03-diff-vs-capacity": build_adv03,
    "adv-04-xtalk-vs-vias": build_adv04,
    "adv-05-eqlen-vs-layerpref": build_adv05,
    "adv-06-copper-vs-completion": build_adv06,
    "adv-07-objection-vs-floor": build_adv07,
}

BOARDS_DIR = os.path.join(_ROOT, "boards", "d")


def write_all(out_dir=None):
    """构造七板并以 canonical json 字节落盘；返回 {board_id: 落盘路径}。可重复运行同字节。"""
    out = out_dir or BOARDS_DIR
    os.makedirs(out, exist_ok=True)
    paths = {}
    for bid in sorted(BOARDS):
        board = _finalize(BOARDS[bid])
        data = canonical.canonical_json(board)
        path = os.path.join(out, bid + ".board.v1.json")
        with open(path, "wb") as f:
            f.write(data)
        paths[bid] = path
    return paths


if __name__ == "__main__":
    _out = sys.argv[1] if len(sys.argv) > 1 else None
    for _bid, _path in write_all(_out).items():
        print(_bid, _path)
