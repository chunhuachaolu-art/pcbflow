# -*- coding: utf-8 -*-
"""L3 J 项生成（任务书 §4 L3 行；P2-J 合同）。

v5.conflicts.v1 冲突工件 → 裁决问句（J 项）列表。纯映射、确定性：无时间戳、
无随机、无 set 迭代序依赖；同输入双跑 canonical 字节相等（硬测试）。

映射合同（盲包 = V2 提示词的数据化，语句型态对齐 prompt-v2-template.md）：
- kind="straight_zone_cross"（blocking/advisory 均可）→ disposition 项
  （V2 J1 型「<basis>。给出处置。」）；
- kind="bottleneck" → disposition 项（V2 J4 型「<basis>。给出处置。」）；
- kind="capacity_infeasible" → joint 项：按 zone 分组，同 zone 的多条冲突合并为
  一个 joint 项（V2 J2/J3 型「…共享 <zone>，必须联合求解，给出…联合最优方案
  排序」），subjects 取并集，source_conflicts 收全组（按 conflict_id 排序）；
- seeded_width_defect / seeded_clearance_defect / envelope_overlap_diagnostic
  **一律不产 J 项**。数据缺陷必须留给模型 defect_scan 通道自己发现——盲包绝不
  能预先披露缺陷位置/类型，否则缺陷扫描通道失效（A6 席位 A 的 V2 证据：
  零误报、能抓出题者未播种缺陷，其前提正是包内零暗示）。本条由负向测试锁定
  （tests/test_jitems.py::test_seeded_and_diagnostic_produce_no_j_items）。
- 其余未知 kind 一律 fail-closed（新 kind 必须显式扩本合同，禁止静默丢弃）。

statement 合同：裁决问句只由 basis 事实描述生成；arithmetic（可复算算术串）
绝不拼入 statement（不向模型泄漏数值答案，A1 权责分置）；statement 以固定问句
结尾，不含任何处置结论（处置权归模型）。

jid 编号合同：全部 J 项按 (subjects_partitions, kind) 排序后连续编号 J-1..J-n；
平手依次以 (joint_group, source_conflicts) 兜底，保证全序确定（无输入序依赖）。
"""
from . import canonical

ARTIFACT_VERSION = "v5.conflicts.v1"

KIND_DISPOSITION = "disposition"
KIND_JOINT = "joint"

# 源冲突 kind 分类：disposition 两类 / joint 一类 / 不产 J 项三类
DISPOSITION_SOURCE_KINDS = ("straight_zone_cross", "bottleneck")
JOINT_SOURCE_KIND = "capacity_infeasible"
NON_J_SOURCE_KINDS = ("seeded_width_defect", "seeded_clearance_defect",
                      "envelope_overlap_diagnostic")
KNOWN_SOURCE_KINDS = DISPOSITION_SOURCE_KINDS + (JOINT_SOURCE_KIND,) \
    + NON_J_SOURCE_KINDS

SEVERITIES = ("blocking", "advisory")

_SUFFIX_DISPOSITION = "。给出处置。"
_SUFFIX_JOINT = "，必须联合求解，给出联合最优方案排序。"


class JItemError(ValueError):
    """J 项生成 fail-closed 错误；path=键路径，message=原因。"""

    def __init__(self, path, message):
        self.path = path
        self.message = message
        super().__init__("[%s] %s" % (path or "<root>", message))


def _require(cond, path, msg):
    if not cond:
        raise JItemError(path, msg)


def _rstrip_sentence(text):
    """去尾部句读（basis 可能自带句号），统一由模板补齐，语句形态确定。"""
    text = text.strip()
    while text and text[-1] in "。．.；;，,":
        text = text[:-1].rstrip()
    return text


def _join_and(parts):
    """中文并列：1 个原样；2 个「A 与 B」；n 个「A、B 与 C」。"""
    if len(parts) == 1:
        return parts[0]
    return "、".join(parts[:-1]) + " 与 " + parts[-1]


def _parse_conflicts(conflicts_artifact):
    """入口校验（fail-closed 报键路径）+ 冲突条目规范化。"""
    _require(isinstance(conflicts_artifact, dict), "",
             "冲突工件须为 dict，得到 %s" % type(conflicts_artifact).__name__)
    _require(conflicts_artifact.get("artifact") == ARTIFACT_VERSION, "artifact",
             "工件标识须为 %r，得到 %r"
             % (ARTIFACT_VERSION, conflicts_artifact.get("artifact")))
    conflicts = conflicts_artifact.get("conflicts")
    _require(isinstance(conflicts, list), "conflicts", "须为列表")
    seen_ids = set()
    parsed = []
    for i, cf in enumerate(conflicts):
        base = "conflicts[%d]" % i
        _require(isinstance(cf, dict), base, "须为对象")
        cid = cf.get("conflict_id")
        _require(isinstance(cid, str) and cid, base + ".conflict_id", "须为非空字符串")
        _require(cid not in seen_ids, base + ".conflict_id",
                 "conflict_id 重复: %r" % cid)
        seen_ids.add(cid)
        kind = cf.get("kind")
        _require(kind in KNOWN_SOURCE_KINDS, base + ".kind",
                 "未知冲突 kind %r（合同外 kind 须显式扩合同，fail-closed）" % (kind,))
        _require(cf.get("severity") in SEVERITIES, base + ".severity",
                 "须为 %r 之一，得到 %r" % (list(SEVERITIES), cf.get("severity")))
        subjects = cf.get("subjects")
        _require(isinstance(subjects, list) and subjects
                 and all(isinstance(s, str) and s for s in subjects),
                 base + ".subjects", "须为非空字符串列表")
        basis = cf.get("basis")
        _require(isinstance(basis, str) and basis.strip(), base + ".basis",
                 "须为非空字符串（裁决问句的唯一事实来源）")
        zone = cf.get("zone")
        _require(zone is None or (isinstance(zone, str) and zone),
                 base + ".zone", "须为字符串或 null")
        if kind == JOINT_SOURCE_KIND:
            _require(isinstance(zone, str) and zone, base + ".zone",
                     "capacity_infeasible 必须带 zone（按走廊分组联合求解）")
        parsed.append({
            "conflict_id": cid,
            "kind": kind,
            "subjects": sorted(set(subjects)),
            "zone": zone,
            "basis": _rstrip_sentence(basis),
            # arithmetic 仅随工件留痕，绝不进 statement（不泄漏数值答案）
            "arithmetic": cf.get("arithmetic"),
        })
    return parsed


def build_j_items(conflicts_artifact):
    """v5.conflicts.v1 → J 项列表（纯映射，确定性；合同见模块 docstring）。

    J 项形状：{"jid", "kind", "subjects_partitions", "zone", "joint_group",
    "statement", "source_conflicts"}。
    """
    parsed = _parse_conflicts(conflicts_artifact)
    items = []

    # 映射一/二：straight_zone_cross、bottleneck → disposition（V2 J1/J4 型）
    for cf in parsed:
        if cf["kind"] in DISPOSITION_SOURCE_KINDS:
            items.append({
                "jid": None,
                "kind": KIND_DISPOSITION,
                "subjects_partitions": list(cf["subjects"]),
                "zone": cf["zone"],
                "joint_group": None,
                "statement": cf["basis"] + _SUFFIX_DISPOSITION,
                "source_conflicts": [cf["conflict_id"]],
            })

    # 映射三：capacity_infeasible 按 zone 分组 → joint（V2 J2/J3 型，subjects 并集）
    groups = {}
    for cf in parsed:
        if cf["kind"] == JOINT_SOURCE_KIND:
            groups.setdefault(cf["zone"], []).append(cf)
    for zone in sorted(groups):
        members = sorted(groups[zone], key=lambda c: c["conflict_id"])
        subjects = sorted({s for c in members for s in c["subjects"]})
        facts = "；".join(c["basis"] for c in members)
        statement = (facts + "。分区 " + _join_and(subjects)
                     + " 共享走廊 " + zone + _SUFFIX_JOINT)
        items.append({
            "jid": None,
            "kind": KIND_JOINT,
            "subjects_partitions": subjects,
            "zone": zone,
            "joint_group": zone,
            "statement": statement,
            "source_conflicts": sorted(c["conflict_id"] for c in members),
        })

    # jid 编号：(subjects, kind) 主序，(joint_group, source_conflicts) 平手兜底。
    items.sort(key=lambda it: (tuple(it["subjects_partitions"]), it["kind"],
                               it["joint_group"] or "",
                               tuple(it["source_conflicts"])))
    for n, it in enumerate(items, start=1):
        it["jid"] = "J-%d" % n
    return items


def jitems_canonical_bytes(j_items):
    """J 项列表 canonical 字节（确定性测试用，§3.4 双跑字节等）。"""
    return canonical.canonical_json(j_items)
