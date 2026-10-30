"""§1.4 Human 处置记录与 waiver policy 检查（SPEC-v3.0-PROPOSAL §1.2/§1.4）。

红线（本模块机器侧落地）：
- Human 只写处置事件：build_disposition 构造 disposition_record；
  不得改写 raw DRC/solver proof/measurement/residual——修正只能追加
  （apply_supersedes 追加式索引，原记录内容不变）；
- waiver fail-closed：kind=waive 时必须绑定 policy——无 policy（空 dict）
  一切 waive 无效；waiver_policy_ref/expiry 缺失、rationale_code 越出
  allowed_reason_codes、approver_role 越出 allowed_approver_roles、
  fact_refs 含不可豁免项（不在 waivable_check_ids）任一命中即无效；
  policy 缺键按空集处理（默认全拒）；
- 处置无门写权：validate_no_gate_write 扫描处置对象（含嵌套 dict），
  键命中 gate/gate_result/gate_pass/production_signoff_ready/signoff_pass
  即报错——gate 由机器谓词计算，人工不可直写。

生成器模式：纯函数、零子进程、零写盘、零网络、无 wall-clock、标准库 only。
"""

from __future__ import annotations

from . import schemas

SCHEMA_VERSION = schemas.SCHEMA_V3

#: waiver 专用 kind（唯一受 waiver policy 约束的处置类）
WAIVE_KIND = "waive"

#: 处置对象禁区键（§1.2 权限矩阵：人工不能写 gate result / 生产准入）
GATE_WRITE_FORBIDDEN_KEYS = frozenset({
    "gate", "gate_result", "gate_pass",
    "production_signoff_ready", "signoff_pass",
})

#: waiver policy 的三个必需清单键（缺键按空集 = 全拒，fail-closed）
_POLICY_LIST_KEYS = ("waivable_check_ids", "allowed_reason_codes",
                     "allowed_approver_roles")


def build_disposition(*, disposition_id, fact_refs, kind, scope,
                      rationale_code, approver, approver_role, **opt) -> dict:
    """按 disposition_record schema 构造处置记录（违例即 ValueError）。

    opt 透传可选字段（rationale_text/waiver_policy_ref/expiry/supersedes）；
    未知键由 schema additionalProperties=false fail-closed 拒绝。
    """
    record = {
        "schema_version": SCHEMA_VERSION,
        "disposition_id": disposition_id,
        "fact_refs": list(fact_refs),
        "kind": kind,
        "scope": scope,
        "rationale_code": rationale_code,
        "approver": approver,
        "approver_role": approver_role,
    }
    record.update(opt)
    errs = schemas.validate("disposition_record", record)
    if errs:
        raise ValueError(f"disposition 非法（fail-closed）: {errs}")
    return record


def check_waiver_policy(disposition: dict, policy: dict) -> list:
    """waiver policy 检查，返回错误列表（[] = 该 waive 在 policy 内有效）。

    policy={waivable_check_ids:[...], allowed_reason_codes:[...],
    allowed_approver_roles:[...]}；policy 为空 dict ⇒ 一切 waive 无效
    （fail-closed 默认：无 policy 即无豁免权）；缺键按空集处理（该维度
    全拒）。kind 非 waive 的处置不受 waiver policy 约束，直接通过。
    """
    if not isinstance(disposition, dict):
        return ["disposition 必须为 dict"]
    if disposition.get("kind") != WAIVE_KIND:
        return []
    if not policy:
        return ["waive 无 policy（空 policy ⇒ 一切 waive 无效；"
                "豁免权必须显式授予）"]
    errors: list = []
    waivable = set(policy.get("waivable_check_ids") or [])
    reason_codes = set(policy.get("allowed_reason_codes") or [])
    roles = set(policy.get("allowed_approver_roles") or [])
    if not disposition.get("waiver_policy_ref"):
        errors.append("waive 缺 waiver_policy_ref（必须绑定豁免 policy）")
    if not disposition.get("expiry"):
        errors.append("waive 缺 expiry（豁免必须带失效条件/复审点）")
    if disposition.get("rationale_code") not in reason_codes:
        errors.append(f"rationale_code {disposition.get('rationale_code')!r}"
                      f" 不在 allowed_reason_codes 内")
    if disposition.get("approver_role") not in roles:
        errors.append(f"approver_role {disposition.get('approver_role')!r}"
                      f" 不在 allowed_approver_roles 内（越权豁免）")
    for fact_ref in disposition.get("fact_refs") or []:
        if fact_ref not in waivable:
            errors.append(f"fact_ref {fact_ref!r} 不在 waivable_check_ids "
                          f"内（不可豁免项）")
    return errors


def validate_no_gate_write(obj, path: str = "$") -> list:
    """递归扫描处置对象：键命中 GATE_WRITE_FORBIDDEN_KEYS 即报错。

    处置不得携带 gate/result/pass 类字段——人工只能写处置事件，
    不能写 gate result 或 production_signoff_ready（§1.2 权限矩阵）。
    """
    errors: list = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key in GATE_WRITE_FORBIDDEN_KEYS:
                errors.append(f"{path}.{key}: 处置对象含门写禁区键 "
                              f"{key!r}（gate 由机器谓词计算，人工不可直写）")
            errors.extend(validate_no_gate_write(value, f"{path}.{key}"))
    elif isinstance(obj, list):
        for i, value in enumerate(obj):
            errors.extend(validate_no_gate_write(value, f"{path}[{i}]"))
    return errors


def apply_supersedes(index: dict, old_id, new_disposition: dict) -> dict:
    """追加式处置索引：old 标 superseded_by，new 标 supersedes。

    返回新索引（浅拷贝重建），不修改调用方的原记录 dict 与原索引；
    old 已被 supersede 或 new_id 已存在 ⇒ ValueError（一次失效、不可改写）。
    注意：superseded_by 是索引层标注（不属于 disposition_record schema），
    存档正本保持干净——追溯关系由 new.supersedes 承载（schema 内字段）。
    """
    if not isinstance(index, dict):
        raise ValueError("index 必须为 dict（disposition_id → 记录）")
    if old_id not in index:
        raise ValueError(f"被取代的处置 {old_id!r} 不在索引内")
    old = index[old_id]
    if old.get("superseded_by"):
        raise ValueError(f"处置 {old_id!r} 已被 {old['superseded_by']!r} "
                         f"取代——追加式账本不允许二次 supersede/改写")
    new_id = (new_disposition.get("disposition_id")
              if isinstance(new_disposition, dict) else None)
    if not isinstance(new_id, str) or not new_id:
        raise ValueError("new_disposition 缺非空 disposition_id")
    if new_id == old_id:
        raise ValueError("new_disposition 不得取代自身")
    if new_id in index:
        raise ValueError(f"disposition_id {new_id!r} 已在索引内（不可改写）")
    supersedes = list(new_disposition.get("supersedes") or [])
    if old_id not in supersedes:
        supersedes = supersedes + [old_id]
    marked_new = dict(new_disposition)
    marked_new["supersedes"] = supersedes
    errs = schemas.validate("disposition_record", marked_new)
    if errs:
        raise ValueError(f"new_disposition 非法: {errs}")
    new_index = {k: dict(v) for k, v in index.items()}
    new_index[old_id] = dict(old)
    new_index[old_id]["superseded_by"] = new_id
    new_index[new_id] = marked_new
    return new_index
