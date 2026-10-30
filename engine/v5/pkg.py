# -*- coding: utf-8 -*-
"""盲包组装器 v5.pkg.v1（任务书 §3.2；P2-J 合同）。

盲包 = V2 提示词（partition-judge-v2/prompt-v2-template.md，冻结件）的数据化：
板参数（workspace 四边界必须披露，f8-01 教训）、叠层、成本模型（序数化注记）、
区域、分区表（v5.partition.v1 工件 partitions 原样透传——主粒度=分区，含
width_prior/电流/速度等级；数据矛盾留给模型在 defect_scan 通道自己发现）、
J 项（v5.jitems）、路由阶梯常量（V2 逐字数据化）、输出合同（A3 五通道，
形状+枚举值逐字内嵌——P0-c 教训：服务端不强制 json_schema）。

文档化最小决定：
1. 分区 geometry 透传压缩为端点/中心线/占用带三种可读形态（照板数据原值，
   不造新值）：endpoints=端点（单例=板原值；合并簇=各源分区端点按
   source_partitions 序拼接）；centerline=中心线（板有则透传，仅单例）；
   occupancy_band=占用带 {occupancy_mm, copper_band}（板有则透传，仅单例；
   合并簇不造聚合值）。
2. output_contract.channels 为 V2 走廊场景锚定的逐字常量（A3 逐字内嵌；
   P2 唯一实战场景即 V2 衍生 demo）；泛化为任意板的通道枚举属后续决策件，
   本版不发明。
3. 成本权重为引擎冻结常量（V2 成本模型；board schema 不携带成本模型）；
   宽度区间内调整零罚以 width_adjust_in_interval_penalty=0.0 + 注记显式声明
   （V2 成本模型逐字语义「宽度在允许区间内调整 0 罚」）。
4. 分区表行扩展字段按 source_partitions 回查原始 board["partitions"]：单例并
   planned_width/bottleneck/板注（板注非空时覆盖 L1 的「未合并，原样透传」占位
   注，无信息损失——该占位注不含任何板信息）；合并簇经 sources_detail 列表
   [{partition_id, planned_width?, bottleneck?, note?}] 逐源承载。目的：P8 播种
   缺陷（planned 0.5 < w_min 0.8）与 P1 瓶颈行注必须对盲包读者可见（V2 分区表
   逐行带计划宽/注口径；数据矛盾仍留给模型 defect_scan 自己发现，包内零预判）。
5. board_brief.scan_disclosure / endpoint_disclosure 为披露注记常量：前者数据化
   V2【冲突扫描说明】（保守包络口径 + 包络重叠≠实际冲突须按 R5 实际几何复核 +
   V2/v5 包络基差披露——V2=实际铜几何外扩 0.6mm，v5=分区直线段几何 ±0.6mm，
   铜宽大时结论可不同，J6 型场景）；后者披露 v5.board.v1 不携带焊盘半径/焊盘
   几何、端点按点处理、焊盘级间距复核须回源板。

确定性：纯函数、无时间戳无随机；build_pkg 双跑 canonical 字节相等（硬测试）。
落盘经 v5.sidecar.write_sidecar（generator="v5.pkg"）；provenance 头由 sidecar
注入，注入后的落盘形态仍过 schemas/pkg.v1.schema.json（顶层可选 provenance 三键，
§3.1 provenance 契约：下游产物引用板必须携带 board_sha256，按 hash 对账）。
"""
import copy

from . import canonical, jitems
from . import partition as partition_mod
from . import schema_loader, sidecar
from .board import BoardLoadError, compute_board_sha256, load_board

SCHEMA_VERSION = "v5.pkg.v1"
GENERATOR = "v5.pkg"
GENERATOR_VERSION = "0.1.0"
SCHEMA_FILENAME = "pkg.v1.schema.json"

# 成本模型（V2 冻结值；序数化注记逐字——只用于排序，不要求模型输出数值）
COST_WEIGHTS = {"detour_rate": 0.5, "direction_rate": 0.2,
                "via_cost": 4.0, "return_cost": 1.0}
ORDINAL_NOTE = "仅用于排序，不要求输出数值"
# V2 成本模型末条逐字语义：区间内调整不计罚（数值与注记显式成对披露）
WIDTH_ADJUST_PENALTY = 0.0
WIDTH_ADJUST_NOTE = "宽度在允许区间内调整 0 罚"

# 披露注记（数据化 V2【冲突扫描说明】+ 端点/焊盘口径，主审裁决 fix_candidates）
SCAN_DISCLOSURE = (
    "冲突扫描基于保守包络：保守包络口径=v5 分区包络（端点几何 ±0.6mm）；"
    "包络重叠不代表实际冲突，是否真冲突须按 R5 用实际几何自行复核。"
    "口径差异披露：V2 文本包络=实际铜几何向外扩 0.6mm，v5=分区中心线几何 ±0.6mm，"
    "两者在铜宽大时结论可不同（J6 型场景）。")
ENDPOINT_DISCLOSURE = ("v5.board.v1 不携带焊盘半径/焊盘几何，端点按点处理；"
                       "焊盘级间距复核须回源板。")

# 路由阶梯（V2 提示词逐字数据化，作为常量；schema 以 const 锁定同串）
ROUTING_LADDER = ("时钟 > 高速串行 > 并行总线 > 电源 > 低速杂项；"
                  "同档位先占用稀缺资源（走廊）者在前；仍平手按分区编号字典序")

# A3 序数合同五通道（形状+枚举值逐字内嵌；V2 走廊场景锚定常量，见 docstring 决定 2）
CHANNELS = {
    "ranked_options": [{"label": "…"}],
    "ranked_combos": [
        {"P3": "留F.Cu过C1|换层B.Cu|换层In1",
         "P5": "留F.Cu过C1|换层B.Cu|换层In1",
         "label": "…"},
    ],
    "routing_order": ["<partition_id>"],
    "defect_scan": [{"subject": "…", "rule": "R1..R6 或 自相矛盾", "note": "…"}],
    "principle_objection": "…",
}
OUTPUT_NOTE = ("最终回复只输出一个 json 代码块；枚举值逐字使用；"
               "不可行方案排最后并标注；principle_objection 只备案不改排序")


class PkgError(ValueError):
    """盲包组装 fail-closed 错误；path=键路径，message=原因。"""

    def __init__(self, path, message):
        self.path = path
        self.message = message
        super().__init__("[%s] %s" % (path or "<root>", message))


def _require(cond, path, msg):
    if not cond:
        raise PkgError(path, msg)


def validate_pkg(pkg):
    """pkg 过 v5.pkg.v1 schema（fail-closed 报键路径）；通过则原样返回。"""
    return schema_loader.validate(pkg, schema_loader.load_schema(SCHEMA_FILENAME),
                                  schema_loader.default_registry(), "")


def _geometry_passthrough(entry, board_by_id):
    """分区 geometry → 端点/中心线/占用带三种可读形态（照板原值；docstring 决定 1）。"""
    srcs = entry["source_partitions"]
    geom = {"endpoints": []}
    for sid in srcs:  # source_partitions 已排序去重（L1 工件合同）
        g = board_by_id[sid]["geometry"]
        geom["endpoints"].extend([list(pt) for pt in g["endpoints"]])
    if len(srcs) == 1:
        g = board_by_id[srcs[0]]["geometry"]
        if "centerline" in g:
            geom["centerline"] = [list(pt) for pt in g["centerline"]]
        band = {}
        if "occupancy_mm" in g:
            band["occupancy_mm"] = g["occupancy_mm"]
        if "copper_band" in g:
            band["copper_band"] = list(g["copper_band"])
        if band:
            geom["occupancy_band"] = band
    return geom


def _partition_table(partition_artifact, board):
    """v5.partition.v1 的 partitions 原样透传（geometry 按决定 1 压缩；行扩展字段
    按决定 4 回查板原始行：planned_width/bottleneck/板注）。

    - 单例（source_partitions 长度 1）：planned_width/bottleneck 板有则并入条目；
      板注非空时覆盖条目 note（L1 单例注恒为「未合并，原样透传」占位，无信息损失）。
    - 合并簇：加 sources_detail=[{partition_id, planned_width?, bottleneck?, note?}]
      逐源承载（按 source_partitions 序，板原值，键缺省不造）。
    """
    by_id = {p["partition_id"]: p for p in board["partitions"]}
    table = []
    for entry in partition_artifact["partitions"]:
        row = {
            "partition_id": entry["partition_id"],
            "ptype": entry["ptype"],
            "net_ids": list(entry["net_ids"]),
            "geometry": _geometry_passthrough(entry, by_id),
            "layer_policy": entry["layer_policy"],
            "width_prior": dict(entry["width_prior"]),
            "current_a": entry["current_a"],
            "speed_class": entry["speed_class"],
            "source_partitions": list(entry["source_partitions"]),
            "note": entry["note"],
        }
        srcs = row["source_partitions"]
        if len(srcs) == 1:
            bp = by_id[srcs[0]]
            if "planned_width" in bp:
                row["planned_width"] = bp["planned_width"]
            if "bottleneck" in bp:
                row["bottleneck"] = copy.deepcopy(bp["bottleneck"])
            if bp.get("note"):
                row["note"] = bp["note"]
        else:
            detail = []
            for sid in srcs:
                bp = by_id[sid]
                d = {"partition_id": sid}
                if "planned_width" in bp:
                    d["planned_width"] = bp["planned_width"]
                if "bottleneck" in bp:
                    d["bottleneck"] = copy.deepcopy(bp["bottleneck"])
                if bp.get("note"):
                    d["note"] = bp["note"]
                detail.append(d)
            row["sources_detail"] = detail
        table.append(row)
    return table


def build_pkg(board, partition_artifact, conflicts_artifact):
    """板 + L1 分区表工件 + L3 冲突工件 → v5.pkg.v1 盲包（纯 dict，不落盘）。"""
    # 入口 fail-closed：板必须过 load_board（schema + provenance 链复算）。
    try:
        load_board(board)
    except (BoardLoadError, schema_loader.SchemaViolation) as exc:
        raise PkgError("board", "板未过 load_board 校验: %s" % exc) from exc
    sha = compute_board_sha256(board)

    _require(isinstance(partition_artifact, dict)
             and partition_artifact.get("artifact") == partition_mod.ARTIFACT_VERSION,
             "partition_artifact.artifact",
             "工件标识须为 %r（得到 %r）"
             % (partition_mod.ARTIFACT_VERSION,
                partition_artifact.get("artifact")
                if isinstance(partition_artifact, dict) else None))
    _require(isinstance(conflicts_artifact, dict)
             and conflicts_artifact.get("artifact") == jitems.ARTIFACT_VERSION,
             "conflicts_artifact.artifact",
             "工件标识须为 %r（得到 %r）"
             % (jitems.ARTIFACT_VERSION,
                conflicts_artifact.get("artifact")
                if isinstance(conflicts_artifact, dict) else None))

    # 证据链对账（§3.1）：下游产物按 board_sha256 对账，不按文件名。
    for tag, art in (("partition_artifact", partition_artifact),
                     ("conflicts_artifact", conflicts_artifact)):
        _require(art.get("board_id") == board["board_id"], tag + ".board_id",
                 "与板 board_id 不一致: %r != %r"
                 % (art.get("board_id"), board["board_id"]))
        _require(art.get("board_sha256") == sha, tag + ".board_sha256",
                 "board_sha256 对账失败: 工件 %r != 复算 %r"
                 % (art.get("board_sha256"), sha))

    pkg = {
        "schema_version": SCHEMA_VERSION,
        "board_id": board["board_id"],
        "board_sha256": sha,
        "generator": GENERATOR,
        "generator_version": GENERATOR_VERSION,
        "board_brief": {
            # f8-01：布线工作区四边界必须披露
            "workspace": copy.deepcopy(board["workspace"]),
            "stackup": copy.deepcopy(board["stackup"]),
            "cost_model": {"weights": dict(COST_WEIGHTS),
                           "width_adjust_in_interval_penalty": WIDTH_ADJUST_PENALTY,
                           "width_adjust_note": WIDTH_ADJUST_NOTE,
                           "ordinal_note": ORDINAL_NOTE},
            # R1..R6 原值透传（不变式地板，A2①）
            "hard_rules": copy.deepcopy(board["hard_rules"]),
            # 披露注记（决定 5）：扫描口径/包络基差 + 端点/焊盘口径
            "scan_disclosure": SCAN_DISCLOSURE,
            "endpoint_disclosure": ENDPOINT_DISCLOSURE,
        },
        "zones": copy.deepcopy(board["zones"]),
        "partition_table": _partition_table(partition_artifact, board),
        "j_items": jitems.build_j_items(conflicts_artifact),
        "routing_ladder": ROUTING_LADDER,
        "output_contract": {"channels": copy.deepcopy(CHANNELS),
                            "note": OUTPUT_NOTE},
    }
    validate_pkg(pkg)  # 出厂自检：模板漂移/schema 漂移当场爆（fail-closed）
    return pkg


def write_pkg(pkg, path):
    """经 v5.sidecar.write_sidecar 落盘（generator="v5.pkg"）。

    provenance 头由 write_sidecar 注入（generator/generator_version/board_sha256
    三键）；越界路径（out/ 之外）抛 SidecarViolation（§3.5 sidecar 卫生）。
    """
    _require(pkg.get("schema_version") == SCHEMA_VERSION, "schema_version",
             "write_pkg 只收 v5.pkg.v1 盲包，得到 %r" % (pkg.get("schema_version"),))
    _require(isinstance(pkg.get("board_sha256"), str)
             and pkg["board_sha256"], "board_sha256", "落盘前须有 board_sha256")
    return sidecar.write_sidecar(path, pkg, GENERATOR, GENERATOR_VERSION,
                                 pkg["board_sha256"])


def pkg_canonical_bytes(pkg):
    """盲包 canonical 字节（双跑字节等测试用，§3.4）。"""
    return canonical.canonical_json(pkg)
