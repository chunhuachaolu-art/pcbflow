"""TD10/v2.1 §4.4-§4.5 Artifact Graph：节点/边、stale 传播、环与拓扑序。

节点：{artifact_id, kind, path, sha256|null, schema_version, producer,
producer_version, inputs[artifact_id], consumers[], status, revision,
stage_label}。图校验输出六件套（SPEC-v3.0 §3.1）：
topological_order / cycle_nodes / stale_nodes / unresolved_inputs /
cross_revision_edges / future_label_violations——任一非空（拓扑序除外）即
gate fail/blocked。

stale 语义：任一输入节点 sha 与本节点声明的 expected_input_hashes 不符、
或输入节点自身 stale/missing ⇒ 本节点 stale（v2.1 §7.3 stale_plan 不静默）。

生成器模式：compare_with_disk 只读重哈希；零写盘、零子进程、无 wall-clock。
Generic Core 纪律：本模块不出现任何项目专名。
"""

from __future__ import annotations

from . import hashing, schemas

SCHEMA_VERSION = schemas.SCHEMA_V3

# 阶段全序（future-label 泄漏审计用；只收通用阶段名）
STAGE_ORDER = [
    "manifest", "compile", "enum", "audit", "coplace", "feedforward",
    "route", "residual", "check", "signoff",
    "physics", "external", "ledger", "critic", "gate", "readiness",
]
_STAGE_RANK = {name: i for i, name in enumerate(STAGE_ORDER)}

_NODE_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["artifact_id", "kind", "sha256", "inputs", "status"],
    "properties": {
        "artifact_id": {"type": "string", "minLength": 1, "maxLength": 128},
        "kind": {"type": "string", "minLength": 1, "maxLength": 64},
        "path": {"type": ["string", "null"]},
        "sha256": {"type": ["string", "null"]},
        "schema_version": {"type": ["string", "null"]},
        "producer": {"type": ["string", "null"]},
        "producer_version": {"type": ["string", "null"]},
        "inputs": {"type": "array",
                   "items": {"type": "string", "minLength": 1}},
        "consumers": {"type": "array",
                      "items": {"type": "string", "minLength": 1}},
        "status": {"enum": ["present", "stale", "missing"]},
        "revision": {"type": ["string", "null"]},
        "stage_label": {"type": ["string", "null"]},
        "expected_input_hashes": {"type": "object", "additionalProperties":
                                  {"type": "string"}},
    },
}


def make_node(artifact_id: str, kind: str, *, sha256=None, path=None,
              inputs=(), status="present", revision=None, stage_label=None,
              producer=None, producer_version=None, schema_version=None,
              expected_input_hashes=None) -> dict:
    node = {
        "artifact_id": artifact_id, "kind": kind, "path": path,
        "sha256": sha256, "schema_version": schema_version,
        "producer": producer, "producer_version": producer_version,
        "inputs": list(inputs), "consumers": [],
        "status": status, "revision": revision, "stage_label": stage_label,
        "expected_input_hashes": dict(expected_input_hashes or {}),
    }
    errs = schemas.validate_spec(_NODE_SCHEMA, node)
    if errs:
        raise ValueError(f"node 非法 {artifact_id}: {errs}")
    return node


def build_graph(nodes: list) -> dict:
    """装配图：校验节点 schema、id 唯一、边引用存在；接线 consumers。"""
    by_id: dict = {}
    for n in nodes:
        if n["artifact_id"] in by_id:
            raise ValueError(f"artifact_id 重复: {n['artifact_id']}")
        by_id[n["artifact_id"]] = dict(n)
    for n in by_id.values():
        n["consumers"] = []
    edges = []
    for n in by_id.values():
        for inp in n["inputs"]:
            if inp not in by_id:
                raise ValueError(
                    f"unresolved input {inp!r} (node {n['artifact_id']})")
            by_id[inp]["consumers"].append(n["artifact_id"])
            edges.append({"from": inp, "to": n["artifact_id"]})
    return {"schema_version": SCHEMA_VERSION, "nodes": list(by_id.values()),
            "edges": edges}


def validate_graph(graph: dict) -> dict:
    """六件套校验报告（§3.1）。只判结构，不触盘。"""
    nodes = {n["artifact_id"]: n for n in graph["nodes"]}
    report = {
        "schema_version": SCHEMA_VERSION,
        "acyclic": True,
        "topological_order": [],
        "cycle_nodes": [],
        "stale_nodes": [],
        "unresolved_inputs": [],
        "cross_revision_edges": [],
        "future_label_violations": [],
        "unlabeled_nodes": [],
    }
    for n in graph["nodes"]:
        errs = schemas.validate_spec(_NODE_SCHEMA, n)
        if errs:
            report["unresolved_inputs"].append(
                f"{n['artifact_id']}:node_schema:{errs[0]}")
        for inp in n["inputs"]:
            if inp not in nodes:
                report["unresolved_inputs"].append(
                    f"{n['artifact_id']}→{inp}")

    # Kahn 拓扑排序（入度削平；同级按 id 字典序保证确定性）
    indeg = {nid: 0 for nid in nodes}
    for n in nodes.values():
        for _inp in n["inputs"]:
            indeg[n["artifact_id"]] += 1
    ready = sorted(nid for nid, d in indeg.items() if d == 0)
    order = []
    while ready:
        nid = ready.pop(0)
        order.append(nid)
        for c in sorted(nodes[nid]["consumers"]):
            indeg[c] -= 1
            if indeg[c] == 0:
                ready.append(c)
        ready.sort()
    if len(order) != len(nodes):
        report["acyclic"] = False
        report["cycle_nodes"] = sorted(set(nodes) - set(order))
        report["topological_order"] = order  # 削平部分（前缀有效）
        return report
    report["topological_order"] = order

    # stale：输入 status 异常或 expected hash 不符 ⇒ 下游 stale（闭包传播）
    status = {nid: n["status"] for nid, n in nodes.items()}
    for nid in order:  # 拓扑序保证输入先判
        n = nodes[nid]
        bad = status[nid] != "present"
        for inp in n["inputs"]:
            if status.get(inp) != "present":
                bad = True
            exp = n.get("expected_input_hashes") or {}
            if inp in exp and nodes[inp]["sha256"] != exp[inp]:
                bad = True
        if bad:
            status[nid] = "stale"
    report["stale_nodes"] = sorted(nid for nid, s in status.items()
                                   if s != "present")

    for e in graph["edges"]:
        src, dst = nodes.get(e["from"]), nodes.get(e["to"])
        if src and dst and src["revision"] and dst["revision"] \
                and src["revision"] != dst["revision"]:
            report["cross_revision_edges"].append(
                f"{e['from']}@{src['revision']}→{e['to']}@{dst['revision']}")
        if src and dst and src["stage_label"] and dst["stage_label"]:
            rs, rd = _STAGE_RANK.get(src["stage_label"]), \
                _STAGE_RANK.get(dst["stage_label"])
            if rs is not None and rd is not None and rs > rd:
                report["future_label_violations"].append(
                    f"{dst['stage_label']}({e['to']}) 消费未来阶段 "
                    f"{src['stage_label']}({e['from']})")
    report["unlabeled_nodes"] = sorted(
        nid for nid, n in nodes.items()
        if n["stage_label"] and n["stage_label"] not in _STAGE_RANK)
    return report


def graph_sha256(graph: dict) -> str:
    """图 canonical hash（nodes 按 id 稳定排序后整体哈希）。"""
    stable = {
        "schema_version": graph["schema_version"],
        "nodes": sorted(graph["nodes"], key=lambda n: n["artifact_id"]),
    }
    return hashing.sha256_bytes(hashing.canonical_json_bytes(stable))


def invalidate(graph: dict, changed_ids) -> set:
    """§4.5 增量重建：changed 集合的传递下游受影响节点集（含自身）。"""
    nodes = {n["artifact_id"]: n for n in graph["nodes"]}
    affected = set()
    frontier = [i for i in changed_ids if i in nodes]
    while frontier:
        nid = frontier.pop()
        if nid in affected:
            continue
        affected.add(nid)
        frontier.extend(nodes[nid]["consumers"])
    return affected


def compare_with_disk(graph: dict, root_dir: str, *,
                      _hash_file=None) -> dict:
    """只读重哈希对账：path 存在且 sha 一致=present；不一致=stale；
    文件缺失=missing。不入图（报告用途；落盘由编排侧决定）。"""
    import os
    hash_file = _hash_file or hashing.sha256_file
    out = {}
    for n in graph["nodes"]:
        if not n.get("path"):
            continue  # 纯声明节点（派生产物未落盘）不参与盘上对账
        p = os.path.join(root_dir, *n["path"].split("/"))
        if not os.path.isfile(p):
            out[n["artifact_id"]] = "missing"
            continue
        actual = hash_file(p)
        out[n["artifact_id"]] = ("present" if actual == n["sha256"]
                                 else "stale")
    return out
