# -*- coding: utf-8 -*-
"""L2 宽度先验与单分区最优包络 + 容量账本（任务书 §4 L2 行）。

输入 = 已载入板 + L1 分区表工件（v5.partition.v1）；输出 = v5.envelope.v1 工件
纯 dict（纯函数不写文件，落盘由主审集成时做）。

- width_prior（文档化映射，零魔法数）：
  * current_a > 0：以分区既有区间的 w_min 为厂商工艺最小线宽、w_max 为参考宽度，
    调 metrics.width_prior.conservative_min_width / significant_max_width
    （关键字参数）；载流下限参数取板 hard_rules.R1 的 k_a / floor_mm；
    显著提升阈值用缺省 5%。
  * current_a == 0：分区既有 width_prior 原值透传（无载流诉求不重算）。
  * optimal_width = w_min（保守最优：先验区间内调整 0 罚，取最保守值，文档化）。
- envelope：L1 分区几何（包围盒对角）± metrics.envelope.DEFAULT_MARGIN（0.6）。
- 容量账本（V2 口径，占用 = Σ条目占用 + 0.5×相邻对，metrics.capacity 实现）：
  * 核算对象 = 每个 kind=="corridor" 且带 capacity 的 zone（无 capacity 声明的
    走廊跳过，文档化决定：无容量即无账可核）；
  * 命中规则（文档化）：分区几何包围盒命中走廊矩形（含擦边，gap≤1e-9），
    或其 copper_band 区间命中走廊 x 跨且端点 y 跨与走廊 y 跨有交（V2 转录口径：
    copper_band 记 x 向铜带）；
  * 条目占用：occupancy_mm 声明占用优先（ribbon 整体），否则铜宽 planned_width；
    CapacityEntry.span 携带 copper_band；
  * 条目顺序 = 板注册序（capacity 模块调用方约定）；net_id = 分区主网
    （net_index 反查表排序首位），无网引用时用 partition_id。
"""
from . import canonical
from .board import BoardLoadError, load_board
from .metrics import capacity as cap_mod
from .metrics import clearance
from .metrics import envelope as env_mod
from .metrics import width_prior as wp_mod
from .partition import (PartitionError, net_index, validate_partition_artifact)

ARTIFACT_VERSION = "v5.envelope.v1"
_EPS = 1e-9


class EnvelopePlanError(ValueError):
    """L2 包络规划 fail-closed 错误；path=键路径，message=原因。"""

    def __init__(self, path, message):
        self.path = path
        self.message = message
        super().__init__("[%s] %s" % (path or "<root>", message))


def _bbox(endpoints):
    """端点集包围盒 (x0, y0, x1, y1)（升序）。"""
    xs = sorted(pt[0] for pt in endpoints)
    ys = sorted(pt[1] for pt in endpoints)
    return (xs[0], ys[0], xs[-1], ys[-1])


def _hits_corridor(partition, zrect):
    """分区是否在走廊 Z 声明占用（命中规则见模块 docstring）。"""
    bbox = _bbox(partition["geometry"]["endpoints"])
    if clearance.rect_rect_gap(bbox, zrect) <= _EPS:
        return True
    band = partition["geometry"].get("copper_band")
    if band is None:
        return False
    band_overlap = max(band[0], zrect[0]) <= min(band[1], zrect[2]) + _EPS
    ys_overlap = max(bbox[1], zrect[1]) <= min(bbox[3], zrect[3]) + _EPS
    return band_overlap and ys_overlap


def _primary_net(partition_id, nets):
    refs = nets.get(partition_id, [])
    return refs[0] if refs else partition_id


def _corridor_ledger_inputs(board):
    """逐走廊收集占用条目（板注册序）→ (entries_by_corridor, caps, occ_by_partition)。"""
    corridors = [z for z in board.get("zones", [])
                 if z.get("kind") == "corridor" and z.get("capacity") is not None]
    nets = net_index(board)
    entries_by, caps, occ_by = {}, {}, {}
    for zone in sorted(corridors, key=lambda z: z["zone_id"]):
        zid = zone["zone_id"]
        rect = zone["rect"]
        zrect = (rect["x_min"], rect["y_min"], rect["x_max"], rect["y_max"])
        entries = []
        for p in board.get("partitions", []):  # 板注册序（capacity 模块约定）
            if not _hits_corridor(p, zrect):
                continue
            geom = p["geometry"]
            entry = cap_mod.CapacityEntry(
                _primary_net(p["partition_id"], nets),
                p.get("planned_width", 0.0),
                declared_occupancy=geom.get("occupancy_mm"),
                span=list(geom["copper_band"]) if geom.get("copper_band") is not None else None,
            )
            entries.append(entry)
            occ_by.setdefault(p["partition_id"], []).append((zid, entry.occupancy))
        entries_by[zid] = entries
        caps[zid] = zone["capacity"]
    return entries_by, caps, occ_by


def build_envelope_artifact(board, partition_artifact):
    """L2 入口：(板, L1 工件) → v5.envelope.v1 工件（纯 dict，不写文件）。"""
    # 入口校验：板必须先过 load_board；L1 工件过形状自检并与本板证据链对账。
    try:
        load_board(board)
    except (BoardLoadError, SchemaViolation) as exc:
        raise EnvelopePlanError("board", "板未过 load_board 校验: %s" % exc) from exc
    try:
        validate_partition_artifact(partition_artifact)
    except PartitionError as exc:
        raise EnvelopePlanError(exc.path, "L1 工件形状自检失败: %s" % exc) from exc
    if partition_artifact.get("board_id") != board["board_id"]:
        raise EnvelopePlanError(
            "board_id", "L1 工件 board_id %r 与板 %r 不一致"
            % (partition_artifact.get("board_id"), board["board_id"]))
    if partition_artifact.get("board_sha256") != board["provenance"]["board_sha256"]:
        raise EnvelopePlanError(
            "board_sha256", "L1 工件 board_sha256 与板不复算一致（证据链断裂）")

    entries_by, caps, occ_by = _corridor_ledger_inputs(board)
    ledger = cap_mod.ledger_for_layer(entries_by, caps)

    per_partition = []
    for entry in partition_artifact["partitions"]:
        x0, y0, x1, y1 = _bbox(entry["geometry"]["endpoints"])
        env = env_mod.expand_rect((x0, y0, x1, y1), env_mod.DEFAULT_MARGIN)
        base = entry["width_prior"]
        current = entry["current_a"]
        if current > 0:
            r1 = board["hard_rules"]["R1"]
            w_min = wp_mod.conservative_min_width(
                current_a=current, fab_min_mm=base["w_min"],
                k_per_amp=r1["k_a"], floor_mm=r1["floor_mm"])
            w_max = wp_mod.significant_max_width(w_ref=base["w_max"], r_ref=1.0)
            prior = {"w_min": w_min, "w_max": w_max}
        else:
            prior = {"w_min": base["w_min"], "w_max": base["w_max"]}
        notes = []
        for src in entry["source_partitions"]:
            for zid, occupancy in occ_by.get(src, []):
                notes.append({"zone_id": zid, "partition_ref": src,
                              "kind": "corridor_occupancy", "occupancy_mm": occupancy})
        notes.sort(key=lambda n: (n["zone_id"], n["partition_ref"]))
        per_partition.append({
            "partition_ref": entry["partition_id"],
            "width_prior": prior,
            "optimal_width": prior["w_min"],
            "envelope_mm": [env[0], env[1], env[2], env[3]],
            "margin_mm": env_mod.DEFAULT_MARGIN,
            "capacity_notes": notes,
        })

    return {
        "artifact": ARTIFACT_VERSION,
        "board_id": board["board_id"],
        "board_sha256": board["provenance"]["board_sha256"],
        "per_partition": per_partition,
        "corridor_ledger": ledger,
    }


def envelope_artifact_bytes(artifact):
    """工件 payload 的 canonical 字节（§3.4；双跑字节等）。"""
    return canonical.canonical_json(artifact)


def envelope_artifact_sha256(artifact):
    """工件指纹 = canonical 字节的 sha256。"""
    return canonical.canonical_sha256(artifact)


def _require(cond, path, msg):
    if not cond:
        raise EnvelopePlanError(path, msg)


def _check_number(path, value, minimum=None):
    _require(not isinstance(value, bool) and isinstance(value, (int, float)),
             path, "须为数字，得到 %r" % (value,))
    if minimum is not None:
        _require(value >= minimum, path, "须 ≥ %r，得到 %r" % (minimum, value))


def validate_envelope_artifact(artifact):
    """v5.envelope.v1 工件形状自检：fail-closed 报键路径；通过则原样返回。"""
    _require(isinstance(artifact, dict), "",
             "工件须为 dict，得到 %s" % type(artifact).__name__)
    _require(artifact.get("artifact") == ARTIFACT_VERSION, "artifact",
             "artifact 标识须为 %r，得到 %r" % (ARTIFACT_VERSION, artifact.get("artifact")))
    _require(isinstance(artifact.get("board_id"), str) and artifact["board_id"],
             "board_id", "须为非空字符串")
    _require(isinstance(artifact.get("board_sha256"), str)
             and len(artifact["board_sha256"]) == 64,
             "board_sha256", "须为 64 位 hex sha256")

    per = artifact.get("per_partition")
    _require(isinstance(per, list), "per_partition", "须为列表")
    for i, e in enumerate(per):
        base = "per_partition[%d]" % i
        _require(isinstance(e, dict), base, "须为对象")
        for key in ("partition_ref", "width_prior", "optimal_width",
                    "envelope_mm", "margin_mm", "capacity_notes"):
            _require(key in e, base + "." + key, "必填字段缺失")
        _require(isinstance(e["partition_ref"], str) and e["partition_ref"],
                 base + ".partition_ref", "须为非空字符串")
        wpv = e["width_prior"]
        _require(isinstance(wpv, dict), base + ".width_prior", "须为对象")
        _check_number(base + ".width_prior.w_min", wpv.get("w_min"), minimum=0)
        _check_number(base + ".width_prior.w_max", wpv.get("w_max"), minimum=0)
        _require(wpv["w_min"] <= wpv["w_max"], base + ".width_prior", "w_min > w_max")
        _check_number(base + ".optimal_width", e["optimal_width"])
        _require(abs(e["optimal_width"] - wpv["w_min"]) <= _EPS,
                 base + ".optimal_width", "须等于 w_min（保守最优合同）")
        env = e["envelope_mm"]
        _require(isinstance(env, list) and len(env) == 4
                 and all(not isinstance(c, bool) and isinstance(c, (int, float)) for c in env),
                 base + ".envelope_mm", "须为 4 数值阵列 [x0,y0,x1,y1]")
        _require(env[0] <= env[2] and env[1] <= env[3],
                 base + ".envelope_mm", "包络坐标须升序")
        _check_number(base + ".margin_mm", e["margin_mm"], minimum=0)
        notes = e["capacity_notes"]
        _require(isinstance(notes, list), base + ".capacity_notes", "须为列表")
        for j, note in enumerate(notes):
            npath = "%s.capacity_notes[%d]" % (base, j)
            _require(isinstance(note, dict), npath, "须为对象")
            for key in ("zone_id", "partition_ref", "kind", "occupancy_mm"):
                _require(key in note, npath + "." + key, "必填字段缺失")
            _require(isinstance(note["zone_id"], str), npath + ".zone_id", "须为字符串")
            _require(isinstance(note["partition_ref"], str), npath + ".partition_ref", "须为字符串")
            _require(isinstance(note["kind"], str), npath + ".kind", "须为字符串")
            _check_number(npath + ".occupancy_mm", note["occupancy_mm"], minimum=0)

    ledger = artifact.get("corridor_ledger")
    _require(isinstance(ledger, dict), "corridor_ledger", "须为对象")
    for zid, row in ledger.items():
        path = "corridor_ledger.%s" % zid
        _require(isinstance(row, dict), path, "须为对象")
        for key in ("capacity_mm", "occupancy_mm", "slack_mm", "fits", "entries"):
            _require(key in row, path + "." + key, "必填字段缺失")
        _check_number(path + ".capacity_mm", row["capacity_mm"])
        _check_number(path + ".occupancy_mm", row["occupancy_mm"])
        _check_number(path + ".slack_mm", row["slack_mm"])
        _require(isinstance(row["fits"], bool), path + ".fits", "须为布尔")
        _require(isinstance(row["entries"], list), path + ".entries", "须为列表")
        for k, item in enumerate(row["entries"]):
            _require(isinstance(item, dict) and isinstance(item.get("net_id"), str),
                     "%s.entries[%d]" % (path, k), "须为带 net_id 的对象")
    return artifact
