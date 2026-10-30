# -*- coding: utf-8 -*-
"""v5.overlay —— L3 叠加与冲突检测（任务书 §4 L3 行）→ 冲突清单工件 v5.conflicts.v1。

入口 build_conflicts(board)：board 须能过 v5.board.load_board（入口内先 fail-closed
复检 schema+provenance 哈希链，同 v5.partition 模式）。产出纯 dict 工件，不写文件。

六类检测器规则（全部确定性、无时间戳无随机无 dict 序依赖；文档化如下）：

1. straight_zone_cross 直线穿区
   - 对每分区 endpoints 直线段 × 每个 kind ∈ {keepout, sensitive} 的 zone 求交；
     corridor 不算冲突（穿越走廊是正常布线意图，容量问题由检测器 2 承接）。
   - zone.layers ∈ {"all","signal"} 均检（层分配前的几何预检，不按 layer_policy 过滤；
     文档化决定：v1 直线叠加不建模层分配）。
   - 相交判定 = v5.metrics.clearance.segment_rect_distance ≤ 1e-9（接触即相交，
     与 v5.drc.check_keepout 的 rect_rect_gap≤0 接触口径一致）。
   - 穿 keepout → blocking（R6 直线预检）；穿 sensitive → advisory（V2 J1 型待裁决）。
   - arithmetic=null（纯几何事实，无可复算数值式）。

2. capacity_infeasible 容量不可行
   - 对每个带 capacity 声明的 corridor zone，收集直线段与其矩形相交的分区。
   - 占用口径与 v5.metrics.capacity 一致：单分区占用 = geometry.occupancy_mm
     （ribbon/差分对声明优先）> planned_width > width_prior.w_max；
     走廊占用 = Σ单分区占用 + 0.5×(n−1)（网间间距，相邻对计一次）。
   - 占用 > capacity（1e-9 容差外）→ blocking；arithmetic 必填，多分区形如
     "1.2+0.15+3.3+0.2+0.2+0.5*4=7.05>4.3"（分区按 id 字典序排列），单分区形如 "1.1>1.0"。

3. bottleneck 瓶颈
   - 分区声明 bottleneck 且 usable_width < planned_width（有 planned_width 时）
     或 usable_width < width_prior.w_min → blocking（V2 J4 型）。
   - 两约束均违时取缺口（约束值 − usable_width）更大者为绑定约束写入 arithmetic
     （缺口相同取计划宽，平局规则确定）；basis 注明"取更严者"。
   - 擦边合规（usable ≥ 约束值 − 1e-9 不报）。

4. seeded_width_defect 播种宽度缺陷
   - 分区声明 planned_width 且落在 [w_min, w_max] 区间外（v5.metrics.width_prior
     .in_interval，1e-9 容差）→ advisory（V2 P8 型数据缺陷素材，不阻塞）。
   - arithmetic："0.5<0.8"（低于下限）或 "1.8>1.6"（超出上限）。

5. seeded_clearance_defect 播种净距缺陷
   - 全部分区对（几何=endpoints 直线段）：实际净距 = 线段距 − (w1+w2)/2
     （有效铜宽 = planned_width 或 width_prior.w_max），round(·,10) 后
     < R5.min_clearance − 1e-9 → advisory（V2 P7/P9 型，arithmetic 必填，如 "0.6-0.2=0.4<0.5"）。
   - 豁免：共享端点的分区对（任一端点距 ≤ 1e-9 视为共享，即相连链）。
   - 文档化决定：按任务书字面口径仅豁免共享端点，不套用 v5.drc 的同网豁免——
     本检测器是数据缺陷扫描（席位 A 素材），advisory 不阻塞，同网净距矛盾仍是缺陷素材。

6. envelope_overlap_diagnostic 包络伪影披露
   - 分区对直线段包络 = 包围盒 ±0.6mm（v5.metrics.envelope.segment_envelope，
     half_width=0、margin=DEFAULT_MARGIN=0.6），按 v5.drc.check_envelope_overlap 口径：
     同网分区对跳过（net_id 集合相交视为同网）。
   - 包络重叠 且 实际净距（同检测器 5 口径）≥ R5 → advisory
     （§3.4 保守包络伪影披露；净距 < R5 的真缺陷对由检测器 5 承接，不重复报）。
   - arithmetic："0.55>=0.5"（实际净距 ≥ R5）。

排序与编号：conflicts 按 (kind, subjects, zone) 升序排序（subjects 按元组字典序，
zone=null 视作 ""；排序键全相等在构造上不可能：同 kind 同 subjects 的冲突至多一条），
排序后连续编号 CF-001..。换分区/zone 构造顺序输出不变（全部按 id 字典序遍历）。

pairs_checked（审计披露）= n_parts×n_keepout_sensitive_zones（检测器 1）
 + n_parts×n_capacity_corridors（检测器 2）+ 2×C(n_parts,2)（检测器 5+6 各一遍分区对）。
检测器 3/4 为单分区检查，不计入"对"数。

layer 恒为 null（v1：直线叠加是层分配前的几何预检；validate 强制）。
"""
from . import canonical
from .board import BoardLoadError, load_board
from .metrics import clearance, envelope as envelope_metric
from .metrics import width_prior as width_prior_metric
from .schema_loader import SchemaViolation

ARTIFACT_VERSION = "v5.conflicts.v1"
DETECTOR_VERSION = "v5.overlay/0.1.0"

# 包络半宽外扩（任务书 §3.4 / V2 场景口径 0.6mm，与 metrics.envelope.DEFAULT_MARGIN 一致）
ENVELOPE_MARGIN = 0.6

KIND_STRAIGHT_ZONE_CROSS = "straight_zone_cross"
KIND_CAPACITY_INFEASIBLE = "capacity_infeasible"
KIND_BOTTLENECK = "bottleneck"
KIND_SEEDED_WIDTH_DEFECT = "seeded_width_defect"
KIND_SEEDED_CLEARANCE_DEFECT = "seeded_clearance_defect"
KIND_ENVELOPE_OVERLAP_DIAGNOSTIC = "envelope_overlap_diagnostic"

KINDS = (
    KIND_STRAIGHT_ZONE_CROSS,
    KIND_CAPACITY_INFEASIBLE,
    KIND_BOTTLENECK,
    KIND_SEEDED_WIDTH_DEFECT,
    KIND_SEEDED_CLEARANCE_DEFECT,
    KIND_ENVELOPE_OVERLAP_DIAGNOSTIC,
)
SEVERITIES = ("blocking", "advisory")

_ZONE_KIND_LABEL = {"keepout": "禁布区", "sensitive": "敏感区"}
_HEX = "0123456789abcdef"


class OverlayError(ValueError):
    """L3 叠加层 fail-closed 错误；path=键路径，message=原因。"""

    def __init__(self, path, message):
        self.path = path
        self.message = message
        super().__init__("[%s] %s" % (path or "<root>", message))


# ---------------------------------------------------------------- 基础原语

def _fmt(x):
    """数值紧凑确定格式：round(·,10) 后 repr（如 7.05 / 0.4 / -0.1），供 arithmetic 复算。"""
    return repr(round(float(x), 10))


def segment_intersects_rect(a, b, rect):
    """线段与轴对齐矩形相交判定（接触即相交）。

    基于 v5.metrics.clearance.segment_rect_distance 的现成段-矩形几何
    （矩形内/边上/穿过后距离为 0），≤1e-9 视为相交；不另写平行几何实现
    （与 v5.drc.check_keepout 的"接触即命中"口径一致）。
    """
    return clearance.segment_rect_distance(a, b, rect) <= clearance.EPS


def _require(cond, path, msg):
    if not cond:
        raise OverlayError(path, msg)


def _check_hex64(path, value):
    _require(isinstance(value, str) and len(value) == 64
             and all(c in _HEX for c in value),
             path, "须为 64 位小写 hex sha256，得到 %r" % (value,))


def _net_ids_by_partition(board):
    """反查表：partition_id → 引用它的 net_id 排序列表（检测器 6 同网跳过用）。"""
    idx = {}
    for net in board.get("nets", []):
        nid = net.get("net_id", "")
        for ref in net.get("partitions", []):
            bucket = idx.setdefault(ref, [])
            if nid not in bucket:
                bucket.append(nid)
    return idx


def _effective_width(part):
    """净距口径的有效铜宽：planned_width 优先，否则 width_prior.w_max（检测器 5/6）。"""
    planned = part.get("planned_width")
    if planned is not None:
        return planned
    return part["width_prior"]["w_max"]


def _corridor_entry_occupancy(part):
    """容量口径的单分区占用：geometry.occupancy_mm 声明优先（ribbon/差分对），
    否则铜宽 = planned_width 或 width_prior.w_max（与 v5.metrics.capacity 一致）。"""
    declared = part["geometry"].get("occupancy_mm")
    if declared is not None:
        return declared
    return _effective_width(part)


def _shares_endpoint(seg_a, seg_b):
    """两线段是否共享端点（任一端点对距 ≤ 1e-9；相连链豁免，检测器 5 口径）。"""
    return any(clearance.point_point(p, q) <= clearance.EPS
               for p in seg_a for q in seg_b)


# ---------------------------------------------------------------- 检测器

def _detect_zone_cross(parts_by_id, ids, zones):
    """检测器 1：直线穿 keepout→blocking；穿 sensitive→advisory；corridor 不算。"""
    out = []
    cand = [z for z in zones
            if z["kind"] in ("keepout", "sensitive")
            and z.get("layers") in ("all", "signal")]
    for pid in ids:
        seg = parts_by_id[pid]["geometry"]["endpoints"]
        a, b = seg[0], seg[1]
        for zone in sorted(cand, key=lambda z: z["zone_id"]):
            if not segment_intersects_rect(a, b, zone["rect"]):
                continue
            label = _ZONE_KIND_LABEL[zone["kind"]]
            rect = zone["rect"]
            if zone["kind"] == "keepout":
                severity = "blocking"
                basis = ("分区 %s 直线段 (%s,%s)-(%s,%s) 穿禁布区 %s "
                         "rect(x %s..%s, y %s..%s)（R6 直线预检）"
                         % (pid, _fmt(a[0]), _fmt(a[1]), _fmt(b[0]), _fmt(b[1]),
                            zone["zone_id"], _fmt(rect["x_min"]), _fmt(rect["x_max"]),
                            _fmt(rect["y_min"]), _fmt(rect["y_max"])))
            else:
                severity = "advisory"
                basis = ("分区 %s 直线段 (%s,%s)-(%s,%s) 穿敏感区 %s "
                         "rect(x %s..%s, y %s..%s)（V2 J1 型，待裁决）"
                         % (pid, _fmt(a[0]), _fmt(a[1]), _fmt(b[0]), _fmt(b[1]),
                            zone["zone_id"], _fmt(rect["x_min"]), _fmt(rect["x_max"]),
                            _fmt(rect["y_min"]), _fmt(rect["y_max"])))
            out.append({"kind": KIND_STRAIGHT_ZONE_CROSS, "subjects": [pid],
                        "zone": zone["zone_id"], "basis": basis,
                        "arithmetic": None, "severity": severity})
    return out


def _detect_capacity(parts_by_id, ids, zones):
    """检测器 2：走廊容量不可行（占用口径与 metrics.capacity 一致）。"""
    out = []
    corridors = sorted((z for z in zones
                        if z["kind"] == "corridor" and z.get("capacity") is not None),
                       key=lambda z: z["zone_id"])
    for zone in corridors:
        cap = zone["capacity"]
        occupying = []
        for pid in ids:
            seg = parts_by_id[pid]["geometry"]["endpoints"]
            if segment_intersects_rect(seg[0], seg[1], zone["rect"]):
                occupying.append((pid, _corridor_entry_occupancy(parts_by_id[pid])))
        if not occupying:
            continue
        n = len(occupying)
        total = round(sum(w for _, w in occupying) + 0.5 * (n - 1), 10)
        if not total > cap + clearance.EPS:
            continue
        if n > 1:
            expr = "%s+0.5*%d=%s" % ("+".join(_fmt(w) for _, w in occupying),
                                     n - 1, _fmt(total))
        else:
            expr = _fmt(total)
        out.append({
            "kind": KIND_CAPACITY_INFEASIBLE,
            "subjects": sorted(pid for pid, _ in occupying),
            "zone": zone["zone_id"],
            "basis": ("直线段与走廊 %s 相交的 %d 个分区按 capacity 口径"
                      "（occupancy_mm 声明优先，否则铜宽=planned_width 或 width_prior.w_max；"
                      "占用=Σ+0.5×(n−1)）合计 %s 超声明容量 %s"
                      % (zone["zone_id"], n, _fmt(total), _fmt(cap))),
            "arithmetic": "%s>%s" % (expr, _fmt(cap)),
            "severity": "blocking",
        })
    return out


def _detect_bottleneck(parts_by_id, ids):
    """检测器 3：瓶颈（planned_width / width_prior.w_min 双约束，取更严者）。"""
    out = []
    for pid in ids:
        part = parts_by_id[pid]
        bn = part.get("bottleneck")
        if not bn:
            continue
        usable = bn["usable_width"]
        w_min = part["width_prior"]["w_min"]
        planned = part.get("planned_width")
        v_planned = planned is not None and usable < planned - clearance.EPS
        v_wmin = usable < w_min - clearance.EPS
        if not (v_planned or v_wmin):
            continue
        deficit_p = round(planned - usable, 10) if v_planned else float("-inf")
        deficit_w = round(w_min - usable, 10) if v_wmin else float("-inf")
        if deficit_w > deficit_p:  # 取缺口更严者；平局（==）取计划宽（确定性）
            bind = "宽度先验下限 %s" % _fmt(w_min)
            arithmetic = "%s<%s" % (_fmt(usable), _fmt(w_min))
        else:
            bind = "计划宽 %s" % _fmt(planned)
            arithmetic = "%s<%s" % (_fmt(usable), _fmt(planned))
        both = "（计划宽与先验下限均违，取缺口更严者）" if (v_planned and v_wmin) else ""
        span = bn["span"]
        out.append({
            "kind": KIND_BOTTLENECK, "subjects": [pid], "zone": None,
            "basis": "瓶颈段 span [%s, %s] usable_width %s 不足 %s%s"
                     % (_fmt(span[0]), _fmt(span[1]), _fmt(usable), bind, both),
            "arithmetic": arithmetic, "severity": "blocking",
        })
    return out


def _detect_width_defect(parts_by_id, ids):
    """检测器 4：planned_width 落在宽度先验区间外 → advisory（数据缺陷素材）。"""
    out = []
    for pid in ids:
        part = parts_by_id[pid]
        planned = part.get("planned_width")
        if planned is None:
            continue
        w_min = part["width_prior"]["w_min"]
        w_max = part["width_prior"]["w_max"]
        if width_prior_metric.in_interval(planned, w_min, w_max):
            continue
        if planned < w_min:
            arithmetic = "%s<%s" % (_fmt(planned), _fmt(w_min))
            detail = "低于宽度先验下限 w_min %s" % _fmt(w_min)
        else:
            arithmetic = "%s>%s" % (_fmt(planned), _fmt(w_max))
            detail = "超出宽度先验上限 w_max %s" % _fmt(w_max)
        out.append({
            "kind": KIND_SEEDED_WIDTH_DEFECT, "subjects": [pid], "zone": None,
            "basis": "分区 %s planned_width %s %s（V2 P8 型数据缺陷素材）"
                     % (pid, _fmt(planned), detail),
            "arithmetic": arithmetic, "severity": "advisory",
        })
    return out


def _detect_clearance_and_envelope(parts_by_id, ids, min_clearance, net_map):
    """检测器 5+6：净距缺陷（真冲突 advisory）与包络伪影披露（同遍分区对）。"""
    out = []
    for i, pa in enumerate(ids):
        for pb in ids[i + 1:]:
            part_a, part_b = parts_by_id[pa], parts_by_id[pb]
            seg_a = part_a["geometry"]["endpoints"]
            seg_b = part_b["geometry"]["endpoints"]
            wa, wb = _effective_width(part_a), _effective_width(part_b)
            dist = round(clearance.segment_segment(seg_a[0], seg_a[1],
                                                   seg_b[0], seg_b[1]), 10)
            gap = round(dist - (wa + wb) / 2.0, 10)
            if _shares_endpoint(seg_a, seg_b):
                continue  # 相连链豁免（检测器 5 字面口径；共享点对 gap≤0 也不可能进检测器 6）
            if gap < min_clearance - clearance.EPS:
                out.append({
                    "kind": KIND_SEEDED_CLEARANCE_DEFECT,
                    "subjects": [pa, pb], "zone": None,
                    "basis": "分区 %s 与 %s 直线段距 %s，扣有效铜宽半和 %s 后净距 %s < R5 %s"
                             % (pa, pb, _fmt(dist), _fmt(round((wa + wb) / 2.0, 10)),
                                _fmt(gap), _fmt(min_clearance)),
                    "arithmetic": "%s-%s=%s<%s" % (_fmt(dist),
                                                   _fmt(round((wa + wb) / 2.0, 10)),
                                                   _fmt(gap), _fmt(min_clearance)),
                    "severity": "advisory",
                })
                continue  # 真缺陷对由检测器 5 承接，检测器 6 不重复报
            if set(net_map.get(pa, [])) & set(net_map.get(pb, [])):
                continue  # drc.check_envelope_overlap 口径：同网跳过
            env_a = envelope_metric.segment_envelope(seg_a[0], seg_a[1], 0.0,
                                                     ENVELOPE_MARGIN)
            env_b = envelope_metric.segment_envelope(seg_b[0], seg_b[1], 0.0,
                                                     ENVELOPE_MARGIN)
            if not envelope_metric.envelopes_overlap(env_a, env_b):
                continue
            depth = round(envelope_metric.envelope_overlap_depth(env_a, env_b), 10)
            out.append({
                "kind": KIND_ENVELOPE_OVERLAP_DIAGNOSTIC,
                "subjects": [pa, pb], "zone": None,
                "basis": "分区 %s 与 %s 直线段包络(±%s)重叠（深度 %s）但实际净距 %s ≥ R5 %s"
                         "（保守外扩伪影，§3.4 披露）"
                         % (pa, pb, _fmt(ENVELOPE_MARGIN), _fmt(depth),
                            _fmt(gap), _fmt(min_clearance)),
                "arithmetic": "%s>=%s" % (_fmt(gap), _fmt(min_clearance)),
                "severity": "advisory",
            })
    return out


# ---------------------------------------------------------------- 入口

def _conflict_sort_key(conflict):
    return (conflict["kind"], tuple(conflict["subjects"]), conflict["zone"] or "")


def build_conflicts(board):
    """L3 入口：board（须过 load_board）→ v5.conflicts.v1 冲突清单工件（纯 dict）。"""
    try:
        load_board(board)
    except (BoardLoadError, SchemaViolation) as exc:
        raise OverlayError("board", "板未过 load_board 校验: %s" % exc) from exc

    parts_by_id = {p["partition_id"]: p for p in board["partitions"]}
    ids = sorted(parts_by_id)
    zones = board["zones"]
    min_clearance = board["hard_rules"]["R5"]["min_clearance_mm"]
    net_map = _net_ids_by_partition(board)

    raw = []
    raw.extend(_detect_zone_cross(parts_by_id, ids, zones))
    raw.extend(_detect_capacity(parts_by_id, ids, zones))
    raw.extend(_detect_bottleneck(parts_by_id, ids))
    raw.extend(_detect_width_defect(parts_by_id, ids))
    raw.extend(_detect_clearance_and_envelope(parts_by_id, ids, min_clearance, net_map))
    raw.sort(key=_conflict_sort_key)

    conflicts = []
    for i, c in enumerate(raw, start=1):
        conflicts.append({
            "conflict_id": "CF-%03d" % i,
            "kind": c["kind"],
            "subjects": list(c["subjects"]),
            "zone": c["zone"],
            "layer": None,
            "basis": c["basis"],
            "arithmetic": c["arithmetic"],
            "severity": c["severity"],
        })

    n = len(ids)
    n_zone = sum(1 for z in zones
                 if z["kind"] in ("keepout", "sensitive")
                 and z.get("layers") in ("all", "signal"))
    n_corridor = sum(1 for z in zones
                     if z["kind"] == "corridor" and z.get("capacity") is not None)
    pairs_checked = n * n_zone + n * n_corridor + 2 * (n * (n - 1) // 2)

    return {
        "artifact": ARTIFACT_VERSION,
        "board_id": board["board_id"],
        "board_sha256": board["provenance"]["board_sha256"],
        "conflicts": conflicts,
        "pairs_checked": pairs_checked,
        "detector_version": DETECTOR_VERSION,
    }


# ---------------------------------------------------------------- 形状自检与字节

def validate_conflicts_artifact(artifact):
    """工件形状自检：fail-closed 报键路径；通过则原样返回（便于链式调用）。"""
    _require(isinstance(artifact, dict), "",
             "工件须为 dict，得到 %s" % type(artifact).__name__)
    _require(artifact.get("artifact") == ARTIFACT_VERSION, "artifact",
             "artifact 标识须为 %r，得到 %r" % (ARTIFACT_VERSION, artifact.get("artifact")))
    _require(isinstance(artifact.get("board_id"), str) and artifact["board_id"],
             "board_id", "须为非空字符串")
    _check_hex64("board_sha256", artifact.get("board_sha256"))
    _require(artifact.get("detector_version") == DETECTOR_VERSION, "detector_version",
             "须为 %r，得到 %r" % (DETECTOR_VERSION, artifact.get("detector_version")))
    pc = artifact.get("pairs_checked")
    _require(not isinstance(pc, bool) and isinstance(pc, int) and pc >= 0,
             "pairs_checked", "须为非负整数，得到 %r" % (pc,))

    conflicts = artifact.get("conflicts")
    _require(isinstance(conflicts, list), "conflicts", "须为列表")
    for i, c in enumerate(conflicts):
        base = "conflicts[%d]" % i
        _require(isinstance(c, dict), base, "须为对象")
        for key in ("conflict_id", "kind", "subjects", "zone", "layer", "basis",
                    "arithmetic", "severity"):
            _require(key in c, base + "." + key, "必填字段缺失")
        _require(c["conflict_id"] == "CF-%03d" % (i + 1), base + ".conflict_id",
                 "须按排序后连续编号 CF-001..，得到 %r（第 %d 条）" % (c["conflict_id"], i + 1))
        kind = c["kind"]
        _require(kind in KINDS, base + ".kind",
                 "须为六类检测器之一 %s，得到 %r" % (list(KINDS), kind))
        subs = c["subjects"]
        _require(isinstance(subs, list) and subs
                 and all(isinstance(s, str) and s for s in subs),
                 base + ".subjects", "须为非空字符串列表")
        _require(subs == sorted(set(subs)), base + ".subjects",
                 "须排序去重（确定性合同）")
        if kind in (KIND_STRAIGHT_ZONE_CROSS, KIND_CAPACITY_INFEASIBLE):
            _require(isinstance(c["zone"], str) and c["zone"], base + ".zone",
                     "%s 须带 zone id，得到 %r" % (kind, c["zone"]))
        else:
            _require(c["zone"] is None, base + ".zone",
                     "%s 的 zone 须为 null，得到 %r" % (kind, c["zone"]))
        _require(c["layer"] is None, base + ".layer",
                 "v1 工件 layer 恒为 null（层分配前几何预检），得到 %r" % (c["layer"],))
        _require(isinstance(c["basis"], str) and c["basis"],
                 base + ".basis", "须为非空字符串")
        if kind == KIND_STRAIGHT_ZONE_CROSS:
            _require(c["arithmetic"] is None, base + ".arithmetic",
                     "straight_zone_cross 为纯几何事实，arithmetic 须为 null")
        else:
            _require(isinstance(c["arithmetic"], str) and c["arithmetic"],
                     base + ".arithmetic", "%s 有数值，arithmetic 必填" % kind)
        _require(c["severity"] in SEVERITIES, base + ".severity",
                 "须为 %s，得到 %r" % (list(SEVERITIES), c["severity"]))
    keys = [(c["kind"], tuple(c["subjects"]), c["zone"] or "") for c in conflicts]
    _require(keys == sorted(keys), "conflicts",
             "须按 (kind, subjects, zone) 升序（确定性合同）")
    return artifact


def artifact_bytes(artifact):
    """工件 payload 的 canonical 字节（§3.4；双跑字节等）。"""
    return canonical.canonical_json(artifact)


def artifact_sha256(artifact):
    """工件指纹 = canonical 字节的 sha256。"""
    return canonical.canonical_sha256(artifact)
