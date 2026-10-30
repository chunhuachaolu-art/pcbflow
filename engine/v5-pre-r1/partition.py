# -*- coding: utf-8 -*-
"""L1 分区器（任务书 §4 L1 行）：类型×几何邻接的确定性聚类，产出分区表工件。

硬要求（任务书）：聚类粒度须可溯源到注册表具体先验，不许无出处的魔法数。
本模块从 principle_registry 中**恰好一条** compiled_rule.kind == "partition_granularity"
的条目读取 min_gap_mm / group_types；0 条或 ≥2 条一律 PartitionError（fail-closed）。
每个参与聚类的数值参数记入工件 granularity_provenance 块
（[{"param","value","principle_id"}...]，按参数名字典序）；非数值参数（group_types，
类型分组声明而非魔法数）按任务书模板口径不进数值溯源块。

聚类规则（确定性，文档化）：
- 类型相容：两分区 ptype 相同，或两者 ptype 都 ∈ group_types（组内可跨类型合并）；
- 几何相邻：endpoints 点对最小距离 ≤ min_gap_mm（含 1e-9 浮点容差），
  或两者都带 copper_band 且区间（闭区间）重叠；
- 两条同时满足即合并，合并可传递（并查集，根=成员字典序最小 id）。
- 粗分区编号：簇按「成员最小 partition_id 字典序」排序后依次编 PG-1..PG-n；
  未合并分区保留原 partition_id 原样透传（source_partitions=[自身]）。
- 归属字段（layer_policy/width_prior/current_a/speed_class）取 current_a 最大的成员；
  平局取 partition_id 字典序最小者。
- ptype：成员 ptype 唯一则取之；跨类型合并取排序去重后用 "+" 连接（如 "BUS+DIFF"）。
  文档化决定：board schema 的 ptype 枚举不约束本工件（工件非 board 实例）。
- 透传条目归一为与合并条目相同的字段形状（不携带 planned_width/bottleneck 等扩展
  字段；容量核算在 L2 直接读板分区，无信息损失）。文档化决定。

输出 = v5.partition.v1 工件纯 dict（不写文件，落盘由主审集成时做）；
canonical 字节函数 artifact_bytes / artifact_sha256 作工件指纹（双跑字节等）。
"""
from . import canonical
from .board import BoardLoadError, load_board
from .metrics import clearance
from .schema_loader import SchemaViolation

ARTIFACT_VERSION = "v5.partition.v1"
GRANULARITY_KIND = "partition_granularity"
_EPS = 1e-9


class PartitionError(ValueError):
    """L1 分区器 fail-closed 错误；path=键路径，message=原因。"""

    def __init__(self, path, message):
        self.path = path
        self.message = message
        super().__init__("[%s] %s" % (path or "<root>", message))


def net_index(board):
    """反查表：partition_id → 引用它的 net_id 排序列表（由 board["nets"] 反查）。"""
    idx = {}
    for net in board.get("nets", []):
        nid = net.get("net_id", "")
        for ref in net.get("partitions", []):
            bucket = idx.setdefault(ref, [])
            if nid not in bucket:
                bucket.append(nid)
    return {k: sorted(v) for k, v in idx.items()}


def _find_granularity_entry(board):
    """恰好一条 partition_granularity 粒度先验；0 条或 ≥2 条 fail-closed。"""
    hits = []
    for i, entry in enumerate(board.get("principle_registry", [])):
        rule = entry.get("compiled_rule") if isinstance(entry, dict) else None
        if isinstance(rule, dict) and rule.get("kind") == GRANULARITY_KIND:
            hits.append((i, entry))
    if not hits:
        raise PartitionError(
            "principle_registry",
            "缺少 kind=%r 的分区聚类粒度先验（得到 0 条）；"
            "L1 聚类粒度必须溯源到注册表具体先验，禁止无出处魔法数" % GRANULARITY_KIND)
    if len(hits) > 1:
        ids = sorted(str(e.get("principle_id", "<principle_registry[%d]>" % i))
                     for i, e in hits)
        raise PartitionError(
            "principle_registry",
            "分区聚类粒度先验恰须 1 条，得到 %d 条: %s" % (len(hits), ", ".join(ids)))
    return hits[0][1]


def _parse_granularity(entry):
    """解析粒度先验参数并产出 granularity_provenance（全部数值参数，按名排序）。"""
    pid = entry.get("principle_id", "<unknown>")
    base = "principle_registry[%s].compiled_rule.params" % pid
    rule = entry.get("compiled_rule")
    params = rule.get("params") if isinstance(rule, dict) else None
    if not isinstance(params, dict):
        raise PartitionError(base, "compiled_rule.params 缺失或不是对象")
    if "min_gap_mm" not in params:
        raise PartitionError(base + ".min_gap_mm", "缺少数值参数 min_gap_mm（聚类几何粒度）")
    min_gap = params["min_gap_mm"]
    if isinstance(min_gap, bool) or not isinstance(min_gap, (int, float)):
        raise PartitionError(base + ".min_gap_mm", "min_gap_mm 须为数字，得到 %r" % (min_gap,))
    if min_gap < 0:
        raise PartitionError(base + ".min_gap_mm", "min_gap_mm 须非负，得到 %r" % (min_gap,))
    # 文档化决定：group_types 键缺省视作空组（仅同 ptype 聚类）；存在时强类型校验。
    group_types = params.get("group_types", [])
    if not isinstance(group_types, list) or any(not isinstance(t, str) for t in group_types):
        raise PartitionError(base + ".group_types", "group_types 须为字符串列表")
    provenance = []
    for name in sorted(params):
        value = params[name]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            continue  # 非数值参数不进数值溯源块（本版本聚类数值输入=min_gap_mm）
        provenance.append({"param": name, "value": value, "principle_id": pid})
    if not provenance:
        raise PartitionError(base, "无数值粒度参数可溯源（granularity_provenance 不可为空）")
    return min_gap, group_types, provenance


def _adjacency_evidence(geom_a, geom_b, min_gap):
    """相邻判定；相邻则返回证据串（进 note 留痕），否则 None。"""
    gap = min(clearance.point_point(p, q)
              for p in geom_a["endpoints"] for q in geom_b["endpoints"])
    if gap <= min_gap + _EPS:
        return "端点距 %.4f <= min_gap_mm %.4g" % (gap, min_gap)
    band_a = geom_a.get("copper_band")
    band_b = geom_b.get("copper_band")
    if band_a is not None and band_b is not None and \
            max(band_a[0], band_b[0]) <= min(band_a[1], band_b[1]) + _EPS:
        return "copper_band 区间重叠 [%s,%s]∩[%s,%s]" % (
            band_a[0], band_a[1], band_b[0], band_b[1])
    return None


def _cluster_entry(rank, members, by_id, nets, min_gap, rule_id, reasons):
    """构造一个粗分区条目（合并簇编 PG-n；单例原 id 透传；字段形状统一）。"""
    srcs = [by_id[m] for m in members]
    member_set = set(members)
    if len(members) == 1:
        out_id = members[0]
        ptype = srcs[0]["ptype"]
        note = "未合并，原样透传"
    else:
        out_id = "PG-%d" % rank
        ptypes = sorted({s["ptype"] for s in srcs})
        ptype = ptypes[0] if len(ptypes) == 1 else "+".join(ptypes)
        evidence = "; ".join(
            "%s~%s(%s)" % (a, b, reasons[(a, b)])
            for a, b in sorted(reasons) if a in member_set and b in member_set)
        note = ("聚类合并 %d 个分区（先验 %s: min_gap_mm=%.4g）: %s"
                % (len(members), rule_id, min_gap, evidence))
    # 归属成员：current_a 最大者；平局取 partition_id 字典序最小。
    dom = min(srcs, key=lambda s: (-s["current_a"], s["partition_id"]))
    xs, ys = [], []
    for s in srcs:
        for pt in s["geometry"]["endpoints"]:
            xs.append(pt[0])
            ys.append(pt[1])
    return {
        "partition_id": out_id,
        "ptype": ptype,
        "net_ids": sorted({n for m in members for n in nets.get(m, [])}),
        "geometry": {"endpoints": [[min(xs), min(ys)], [max(xs), max(ys)]]},
        "layer_policy": dom["layer_policy"],
        "width_prior": {"w_min": dom["width_prior"]["w_min"],
                        "w_max": dom["width_prior"]["w_max"]},
        "current_a": dom["current_a"],
        "speed_class": dom["speed_class"],
        "source_partitions": list(members),
        "note": note,
    }


def build_partition_artifact(board):
    """L1 入口：board（须过 load_board）→ v5.partition.v1 分区表工件（纯 dict）。"""
    # 入口校验：板必须先过 load_board（schema fail-closed + provenance 哈希链复算）。
    try:
        load_board(board)
    except (BoardLoadError, SchemaViolation) as exc:
        raise PartitionError("board", "板未过 load_board 校验: %s" % exc) from exc

    entry = _find_granularity_entry(board)
    min_gap, group_types, provenance = _parse_granularity(entry)
    rule_id = entry.get("principle_id", "<unknown>")

    by_id = {p["partition_id"]: p for p in board.get("partitions", [])}
    ids = sorted(by_id)
    nets = net_index(board)

    def type_ok(a, b):
        ta, tb = by_id[a]["ptype"], by_id[b]["ptype"]
        return ta == tb or (ta in group_types and tb in group_types)

    parent = {pid: pid for pid in ids}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    reasons = {}
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            if not type_ok(a, b):
                continue
            evidence = _adjacency_evidence(by_id[a]["geometry"], by_id[b]["geometry"], min_gap)
            if evidence is None:
                continue
            reasons[(a, b)] = evidence
            ra, rb = find(a), find(b)
            if ra != rb:
                lo, hi = sorted((ra, rb))
                parent[hi] = lo

    components = {}
    for pid in ids:
        components.setdefault(find(pid), []).append(pid)
    # 簇按成员最小 partition_id 字典序排序 ⇒ PG 编号确定（无随机无 set 迭代序依赖）。
    clusters = sorted((sorted(ms) for ms in components.values()), key=lambda ms: ms[0])

    entries = [_cluster_entry(rank, members, by_id, nets, min_gap, rule_id, reasons)
               for rank, members in enumerate(clusters, start=1)]
    return {
        "artifact": ARTIFACT_VERSION,
        "board_id": board["board_id"],
        "board_sha256": board["provenance"]["board_sha256"],
        "granularity_provenance": provenance,
        "partitions": entries,
    }


def artifact_bytes(artifact):
    """工件 payload 的 canonical 字节（§3.4；双跑字节等）。"""
    return canonical.canonical_json(artifact)


def artifact_sha256(artifact):
    """工件指纹 = canonical 字节的 sha256。"""
    return canonical.canonical_sha256(artifact)


_HEX = "0123456789abcdef"


def _require(cond, path, msg):
    if not cond:
        raise PartitionError(path, msg)


def _check_hex64(path, value):
    _require(isinstance(value, str) and len(value) == 64
             and all(c in _HEX for c in value),
             path, "须为 64 位小写 hex sha256，得到 %r" % (value,))


def _check_number(path, value, minimum=None):
    _require(not isinstance(value, bool) and isinstance(value, (int, float)),
             path, "须为数字，得到 %r" % (value,))
    if minimum is not None:
        _require(value >= minimum, path, "须 ≥ %r，得到 %r" % (minimum, value))


def validate_partition_artifact(artifact):
    """工件形状自检：fail-closed 报键路径；通过则原样返回（便于链式调用）。"""
    _require(isinstance(artifact, dict), "",
             "工件须为 dict，得到 %s" % type(artifact).__name__)
    _require(artifact.get("artifact") == ARTIFACT_VERSION, "artifact",
             "artifact 标识须为 %r，得到 %r" % (ARTIFACT_VERSION, artifact.get("artifact")))
    _require(isinstance(artifact.get("board_id"), str) and artifact["board_id"],
             "board_id", "须为非空字符串")
    _check_hex64("board_sha256", artifact.get("board_sha256"))

    prov = artifact.get("granularity_provenance")
    _require(isinstance(prov, list) and prov, "granularity_provenance",
             "须为非空列表（粒度溯源不许为空）")
    for i, item in enumerate(prov):
        path = "granularity_provenance[%d]" % i
        _require(isinstance(item, dict), path, "须为对象")
        _require(isinstance(item.get("param"), str) and item["param"],
                 path + ".param", "须为非空字符串")
        _check_number(path + ".value", item.get("value"))
        _require(isinstance(item.get("principle_id"), str) and item["principle_id"],
                 path + ".principle_id", "须为非空字符串")

    parts = artifact.get("partitions")
    _require(isinstance(parts, list), "partitions", "须为列表")
    seen = set()
    for i, e in enumerate(parts):
        base = "partitions[%d]" % i
        _require(isinstance(e, dict), base, "须为对象")
        for key in ("partition_id", "ptype", "net_ids", "geometry", "layer_policy",
                    "width_prior", "current_a", "speed_class", "source_partitions", "note"):
            _require(key in e, base + "." + key, "必填字段缺失")
        pid = e["partition_id"]
        _require(isinstance(pid, str) and pid, base + ".partition_id", "须为非空字符串")
        _require(pid not in seen, base + ".partition_id", "partition_id 重复: %r" % pid)
        seen.add(pid)
        _require(isinstance(e["ptype"], str) and e["ptype"], base + ".ptype", "须为非空字符串")
        nets = e["net_ids"]
        _require(isinstance(nets, list) and all(isinstance(n, str) for n in nets),
                 base + ".net_ids", "须为字符串列表")
        _require(nets == sorted(set(nets)), base + ".net_ids", "须排序去重（确定性合同）")
        geom = e["geometry"]
        _require(isinstance(geom, dict), base + ".geometry", "须为对象")
        eps = geom.get("endpoints")
        _require(isinstance(eps, list) and len(eps) == 2
                 and all(isinstance(pt, list) and len(pt) == 2
                         and all(not isinstance(c, bool) and isinstance(c, (int, float))
                                 for c in pt) for pt in eps),
                 base + ".geometry.endpoints", "须为 2×2 数值阵列")
        _require(eps[0][0] <= eps[1][0] and eps[0][1] <= eps[1][1],
                 base + ".geometry.endpoints", "须为包围盒对角（x/y 升序）")
        _require(isinstance(e["layer_policy"], str) and e["layer_policy"],
                 base + ".layer_policy", "须为非空字符串")
        wpv = e["width_prior"]
        _require(isinstance(wpv, dict), base + ".width_prior", "须为对象")
        _check_number(base + ".width_prior.w_min", wpv.get("w_min"), minimum=0)
        _check_number(base + ".width_prior.w_max", wpv.get("w_max"), minimum=0)
        _require(wpv["w_min"] <= wpv["w_max"], base + ".width_prior", "w_min > w_max")
        _check_number(base + ".current_a", e["current_a"], minimum=0)
        _require(isinstance(e["speed_class"], str) and e["speed_class"],
                 base + ".speed_class", "须为非空字符串")
        srcs = e["source_partitions"]
        _require(isinstance(srcs, list) and srcs
                 and all(isinstance(s, str) for s in srcs),
                 base + ".source_partitions", "须为非空字符串列表")
        _require(srcs == sorted(set(srcs)), base + ".source_partitions",
                 "须排序去重（确定性合同）")
        _require(isinstance(e["note"], str), base + ".note", "须为字符串")
    return artifact
