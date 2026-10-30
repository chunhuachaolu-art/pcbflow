"""§1.4 gate-record 机器谓词评估与验证（SPEC-v3.0-PROPOSAL §1.4/TL-1）。

红线（本模块机器侧落地）：
- gate 由版本化 evaluator 从 inputs/required_predicates/graph_report 计算，
  人工不可直写 result；evaluate_gate 是唯一构造入口；
- 判定次序（blocked 严格优先于 fail 优先于 pass——缺证据闭门律 L7）：
  * 任一 input status 非 present（stale→stale_input；missing→
    missing_input；present 但 sha256=null 同记 missing_input——无 hash
    即无绑定）⇒ blocked；
  * graph_report 给定且 cycle_nodes/stale_nodes/unresolved_inputs/
    cross_revision_edges/future_label_violations 任一非空或 acyclic=False
    ⇒ blocked（对应码）；product 门必须给出非空可查图，否则
    graph_report_missing blocked；无图且非 product 时 cycle_check 用
    空默认 {acyclic: True, topological_order: []}；
  * 任一 required_predicate value 非 True ⇒ fail（predicate_failed:<id>；
    证据在但不过）；任一 predicate 无 evidence 字符串 ⇒ blocked
    （evidence_missing:<id>——防凭空断言，True/False 断言均需证据）；
  * 全过 ⇒ pass；
- 核心 JSON 无 wall-clock：evaluation_metadata 三字段恒 null，
  gate_core_hash 剔除 evaluation_metadata（时间/主机/耗时不参加核心 hash）；
- verify_gate_record：schema + evaluator.code_sha256 绑定检查 +
  人工注入检查（value=True 无 evidence）+ pass 方向重算核对
  （result=pass 必须与机器重算一致——人工直写 pass 必被查出）。

生成器模式：纯函数、零子进程、零写盘、零网络、无 wall-clock、标准库 only。
"""

from __future__ import annotations

import re

from . import hashing, schemas

SCHEMA_VERSION = schemas.SCHEMA_V3

_HEX64_RE = re.compile(r"^[0-9a-f]{64}$")

RESULT_PASS = "pass"
RESULT_FAIL = "fail"
RESULT_BLOCKED = "blocked"

#: product 门语义：必须有非空可查图（无 graph_report 或拓扑序为空均
#: graph_report_missing——产品门不允许"无图可查"的空默认）
PRODUCT_GATE_KIND = "product"

#: graph_report 六件套中的违例字段 → blocked 失败码（topological_order 除外）
_GRAPH_REPORT_VIOLATIONS = (
    ("cycle_nodes", "cycle_detected"),
    ("stale_nodes", "stale_nodes"),
    ("unresolved_inputs", "unresolved_inputs"),
    ("cross_revision_edges", "cross_revision_edges"),
    ("future_label_violations", "future_label_violations"),
)

#: 无图可查时的 cycle_check 默认（仅 gate_kind != product 可用）
_EMPTY_CYCLE_CHECK = {"acyclic": True, "topological_order": []}


def _dedupe(codes) -> list:
    """按序去重（确定性：保持首次出现顺序）。"""
    seen: set = set()
    out = []
    for c in codes:
        if c not in seen:
            seen.add(c)
            out.append(c)
    return out


def _has_evidence(pred: dict) -> bool:
    ev = pred.get("evidence")
    return isinstance(ev, str) and bool(ev.strip())


def evaluate_gate(*, gate_id, gate_kind, project_id, profile_id,
                  snapshot_revision, predicate_version, inputs,
                  required_predicates, fact_refs=(), disposition_refs=(),
                  graph_report=None, evaluator) -> dict:
    """按 gate_record schema 构造并判定门（构造违例即 ValueError）。

    inputs: [{artifact_id, sha256, status}]；required_predicates:
    [{id, value, evidence?}]（value 非 True → fail；无 evidence 字符串 →
    blocked）。evaluation_metadata 三字段恒 null（无 wall-clock）。
    """
    blocked: list = []
    fail: list = []
    # 1) 输入在场性（stale/missing/无 hash 绑定均 blocked）
    for inp in inputs:
        status = inp.get("status") if isinstance(inp, dict) else None
        if status == "stale":
            blocked.append("stale_input")
        elif status != "present":
            blocked.append("missing_input")
        elif inp.get("sha256") is None:
            blocked.append("missing_input")  # present 但无 hash：不可绑定
    # 2) 图校验（§3.1 六件套）
    if graph_report is None:
        cycle_check = dict(_EMPTY_CYCLE_CHECK)
        cycle_check["topological_order"] = list(
            _EMPTY_CYCLE_CHECK["topological_order"])
        if gate_kind == PRODUCT_GATE_KIND:
            blocked.append("graph_report_missing")
    else:
        acyclic = graph_report.get("acyclic")
        cycle_check = {
            "acyclic": bool(acyclic),
            "topological_order": list(
                graph_report.get("topological_order") or []),
        }
        if graph_report.get("cycle_nodes"):
            cycle_check["cycle_nodes"] = list(graph_report["cycle_nodes"])
        for field, code in _GRAPH_REPORT_VIOLATIONS:
            if field == "cycle_nodes":
                if graph_report.get(field) or acyclic is False:
                    blocked.append(code)
            elif graph_report.get(field):
                blocked.append(code)
        if gate_kind == PRODUCT_GATE_KIND and not cycle_check["topological_order"]:
            blocked.append("graph_report_missing")  # 空图不满足 product 门
    # 3) 谓词（证据在但不过 → fail；无证据 → blocked）
    for pred in required_predicates:
        pid = pred.get("id") if isinstance(pred, dict) else "?"
        if pred.get("value") is not True:
            fail.append(f"predicate_failed:{pid}")
        if not _has_evidence(pred):
            blocked.append(f"evidence_missing:{pid}")
    # 4) 结论（blocked > fail > pass）
    if blocked:
        result = RESULT_BLOCKED
    elif fail:
        result = RESULT_FAIL
    else:
        result = RESULT_PASS
    record = {
        "schema_version": SCHEMA_VERSION,
        "gate_id": gate_id,
        "gate_kind": gate_kind,
        "project_id": project_id,
        "profile_id": profile_id,
        "snapshot_revision": snapshot_revision,
        "predicate_version": predicate_version,
        "inputs": [dict(i) for i in inputs],
        "required_predicates": [dict(p) for p in required_predicates],
        "fact_refs": list(fact_refs),
        "disposition_refs": list(disposition_refs),
        "cycle_check": cycle_check,
        "result": result,
        "failure_codes": _dedupe(blocked + fail),
        "evaluator": {
            "name": evaluator["name"],
            "version": evaluator["version"],
            "code_sha256": evaluator["code_sha256"],
        },
        "evaluation_metadata": {"evaluated_at": None, "host": None,
                                "elapsed_s": None},
    }
    errs = schemas.validate("gate_record", record)
    if errs:
        raise ValueError(f"gate record 非法（fail-closed）: {errs}")
    return record


def gate_core_hash(record: dict) -> str:
    """核心 hash：剔除 evaluation_metadata 后的 canonical hash。

    时间/主机/耗时只在 evaluation_metadata 且不参加核心 hash（§1.4）。
    """
    body = {k: v for k, v in record.items() if k != "evaluation_metadata"}
    return hashing.sha256_bytes(hashing.canonical_json_bytes(body))


def _recompute_result(record: dict) -> str:
    """从记录自身可存字段（inputs/predicates/cycle_check/gate_kind）重算结果。

    仅覆盖可从 gate_record 核心字段重建的判定（graph_report 内部六件套
    细节不落盘，重算以 cycle_check.acyclic 与 product 空图规则为准）。
    """
    blocked = False
    fail = False
    for inp in record.get("inputs") or []:
        if isinstance(inp, dict):
            if inp.get("status") != "present" or inp.get("sha256") is None:
                blocked = True
    cc = record.get("cycle_check") or {}
    if cc.get("acyclic") is False:
        blocked = True
    if record.get("gate_kind") == PRODUCT_GATE_KIND \
            and not (cc.get("topological_order") or []):
        blocked = True
    for pred in record.get("required_predicates") or []:
        if isinstance(pred, dict):
            if pred.get("value") is not True:
                fail = True
            if not _has_evidence(pred):
                blocked = True
    if blocked:
        return RESULT_BLOCKED
    return RESULT_FAIL if fail else RESULT_PASS


def verify_gate_record(record) -> list:
    """验证 gate record，返回错误列表（[] = 合法且与机器重算一致）。

    检查项：schema 严格验证；evaluator.code_sha256 缺失/非 64hex（无法
    绑定判定代码版本——人工不可直写门）；required_predicates 中 value=True
    但 evidence 为空（防人工凭空断言）；result=pass 与机器重算核对
    （pass 方向强制：人工注入 pass 必与重算不一致而报错；fail/blocked 为
    收紧方向，不作重算强一致要求）。
    """
    if not isinstance(record, dict):
        return ["gate record 必须为 dict"]
    errors: list = []
    errors.extend(schemas.validate("gate_record", record))
    evaluator = record.get("evaluator")
    code_sha = evaluator.get("code_sha256") if isinstance(evaluator, dict) \
        else None
    if not isinstance(code_sha, str) or not _HEX64_RE.search(code_sha):
        errors.append("evaluator.code_sha256 缺失或非 64hex"
                      "（无法绑定判定代码版本；gate 由机器谓词计算）")
    for pred in record.get("required_predicates") or []:
        if isinstance(pred, dict) and pred.get("value") is True \
                and not _has_evidence(pred):
            errors.append(f"required_predicate {pred.get('id')!r} value=True "
                          f"但无 evidence（防人工凭空断言）")
    if record.get("result") == RESULT_PASS:
        recomputed = _recompute_result(record)
        if recomputed != RESULT_PASS:
            errors.append(
                f"result=pass 与机器重算不一致（重算={recomputed}；"
                f"gate 由机器谓词计算，人工不可直写 pass）")
    return errors
