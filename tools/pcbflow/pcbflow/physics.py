"""TD6 物理证据与 bring-up 层合同（SPEC-v3.0-PROPOSAL §TD6）。

物理轨道三分类 physics_screening / external_required / bring_up，不与
kicad-cli 几何 authority 合并；本模块只做证据分级与 fail-closed 门评估：

  - required 项须同过 scope/coverage/输入完整/执行/有效性收敛/limits/
    uncertainty/批准/freshness 门（freshness 由 status=stale 承载）；
  - coverage=100% 是必要条件而非充分条件：coverage 完整但任一门 fail →
    physics_gate=fail，绝不是 pass；
  - 资料级证据（authority=datasheet_derived 或 fidelity=screening，如
    revc-tbd1 的 102.7Ω 资料/推导值）只能归 physics_screening 轨，不能
    satisfy external_required/bring_up；
  - openems 与 scikit_rf 非等价后端（profile 指定适用者，逐字匹配）：
    仿真结果可入 external_required、不可入 bring_up；bring_up 只认
    lab_measurement 实测；
  - 无真实回板 witness 时 bring-up 状态只能 not_available，永不能凭
    资料推导 pass（fail-closed）。

生成器模式：纯函数、零子进程、零写盘、无 wall-clock、标准库 only。
"""

from __future__ import annotations

import copy

from . import schemas

# ---------------------------------------------------------------------------
# 常量（内聚本模块）
# ---------------------------------------------------------------------------

#: 物理证据三轨（与 schemas["physics_report"] 项级 track enum 逐字一致）
TRACKS = ("physics_screening", "external_required", "bring_up")

#: 项状态全集（与 schemas._PHYSICS_STATUS 同步；仅用于 status_invalid 判别）
STATUSES = ("pass", "fail", "unknown", "not_available", "not_executed", "stale")

#: 证据 authority 分级（TD6：资料级 < 仿真级 < 实测级）
_SCREENING_AUTHORITIES = frozenset({"datasheet_derived"})
_SIMULATION_AUTHORITIES = frozenset({"openems", "scikit_rf", "vendor_tool"})
_MEASUREMENT_AUTHORITIES = frozenset({"lab_measurement"})

#: fidelity 显式降级标记：一旦为 screening，证据只归 physics_screening 轨
_SCREENING_FIDELITY = "screening"

#: 项级 schema（physics_report.properties.items.items；构造/评估走 validate_spec）
_ITEM_SPEC = schemas.SCHEMAS["physics_report"]["properties"]["items"]["items"]

#: required 十门中八个布尔门 → 机器失败码（status/freshness 门在
#: evaluate_gate；bring_up 处置门按轨在 check_item 追加）
_CHECK_GATES = (
    ("required_scope_defined", "not_required_scope_defined"),
    ("coverage_complete", "coverage_incomplete"),
    ("input_model_complete", "input_model_incomplete"),
    ("executed", "not_executed"),
    ("convergence_or_validity_pass", "validity_fail"),
    ("limit_pass", "limit_fail"),
    ("uncertainty_acceptable", "uncertainty_fail"),
    ("external_approval_present", "no_approval"),
)

#: fail 类失败码（证据在但违例 → physics_gate=fail）；未列出者一律按
#: blocked 类（证据缺失/无法评判 → physics_gate=blocked）。fail-closed：
#: 未知码不在 fail 集内时保守归 blocked（缺证据优于误判通过）。
FAIL_CLASS_CODES = frozenset({
    "status_fail", "validity_fail", "limit_fail", "uncertainty_fail",
    "no_approval", "authority_mismatch", "bring_up_disposition_fail",
    "duplicate_item", "item_schema_invalid", "invalid_item",
})

#: bring_up witness 必需字段（与 schemas["bring_up_report"].required 对齐；
#: 缺失/None/空串/空对象均视同缺失——fail-closed）
_WITNESS_FIELDS = ("board_serial", "board_revision", "fixture",
                   "firmware_version", "test_software_version", "environment",
                   "operator", "input_hash", "output_hash")


# ---------------------------------------------------------------------------
# 1. 项构造
# ---------------------------------------------------------------------------

def build_item(item_id, track, **fields) -> dict:
    """按 physics_report 项级 schema 形状构造证据项并校验（非法即抛 ValueError）。

    默认值 fail-closed：未给证据的布尔门一律 False，status 缺省
    not_executed，bring_up_disposition 缺省 not_available，authority 缺省
    none——调用方必须显式给全证据才能得到可过门的项。可选字段（net_or_relation/
    model_or_tool/limits/...）由 **fields 透传，未给即不写入。
    """
    if track not in TRACKS:
        raise ValueError(f"track {track!r} 不在三轨 {TRACKS} 内")
    item = {
        "item_id": item_id,
        "track": track,
        "status": "not_executed",
        "required_scope_defined": False,
        "coverage_complete": False,
        "input_model_complete": False,
        "executed": False,
        "convergence_or_validity_pass": False,
        "limit_pass": False,
        "uncertainty_acceptable": False,
        "external_approval_present": False,
        "bring_up_disposition": "not_available",
        "authority": "none",
    }
    item.update(fields)
    errors = schemas.validate_spec(_ITEM_SPEC, item)
    if errors:
        raise ValueError("physics item schema 校验失败: " + "; ".join(errors))
    return item


# ---------------------------------------------------------------------------
# 2. required 项逐门检查
# ---------------------------------------------------------------------------

def check_item(item) -> list:
    """对 required 项逐门检查，返回机器失败码列表（空 = 全门通过）。

    八个布尔门（scope/coverage/输入完整/执行/有效性收敛/limits/uncertainty/
    批准）按 _CHECK_GATES 映射；track=bring_up 时额外要求
    bring_up_disposition=="pass"（缺失/not_available → blocked 类，
    fail/deferred → fail 类）。status/freshness 门由 evaluate_gate 承载
    （十门 = 八布尔 + status + bring_up 处置）。
    """
    if not isinstance(item, dict):
        return ["invalid_item"]
    codes = [code for field, code in _CHECK_GATES if not item.get(field)]
    if item.get("track") == "bring_up":
        disposition = item.get("bring_up_disposition")
        if disposition == "pass":
            pass
        elif disposition in ("not_available", None):
            codes.append("bring_up_not_available")
        else:                                   # fail / deferred
            codes.append("bring_up_disposition_fail")
    return codes


# ---------------------------------------------------------------------------
# 3. authority 兼容性（证据分级 vs 轨道要求）
# ---------------------------------------------------------------------------

def authority_compatible(item, required_track) -> bool:
    """证据的 authority/fidelity 分级能否 satisfy 指定轨道。

    - physics_screening：任何证据都可归档（screening 是最低轨）；
    - external_required：datasheet_derived 或 fidelity=screening 的资料级
      证据不可（只归 physics_screening）；openems/scikit_rf/vendor_tool
      仿真与 lab_measurement 实测可入；
    - bring_up：只认 lab_measurement 实测——仿真（openems/scikit_rf/
      vendor_tool）不可入 bring_up；资料级更不可。
    未知轨道 fail-closed 返回 False。
    """
    if not isinstance(item, dict):
        return False
    if required_track == "physics_screening":
        return True
    if required_track not in TRACKS:
        return False
    authority = item.get("authority")
    # 资料级证据（含显式 fidelity 降级）只归 physics_screening 轨
    if authority in _SCREENING_AUTHORITIES or item.get("fidelity") == _SCREENING_FIDELITY:
        return False
    if required_track == "external_required":
        return authority in _SIMULATION_AUTHORITIES | _MEASUREMENT_AUTHORITIES
    if required_track == "bring_up":
        return authority in _MEASUREMENT_AUTHORITIES
    return False


# ---------------------------------------------------------------------------
# 4. required physics gate（fail-closed 合取门）
# ---------------------------------------------------------------------------

def evaluate_gate(items, required_scope) -> dict:
    """对 profile 声明的必需 item_id 集合做 fail-closed 合取门评估。

    规则：scope 内缺项 → missing_report；项 status != pass → status_<v>
    （stale/unknown/not_available/not_executed 为 freshness/缺证据 blocked 类，
    fail 为 fail 类）；authority_compatible(item, item.track)=False →
    authority_mismatch；check_item 非空 → 逐码。coverage=100% 只是必要条件：
    任一门 fail → physics_gate=fail；证据缺失类 → blocked；scope 为空 →
    not_required。authority 检查按项自身声明的 track（required_scope 只含
    item_id，轨道权威在项上）。
    """
    by_id: dict = {}
    duplicate = False
    invalid = False
    for entry in items:
        if not isinstance(entry, dict):
            invalid = True
            continue
        iid = entry.get("item_id")
        if not isinstance(iid, str) or not iid:
            invalid = True
            continue
        if iid in by_id:
            duplicate = True
        else:
            by_id[iid] = entry
    codes: list = []
    if invalid:
        codes.append("invalid_item")
    if duplicate:
        codes.append("duplicate_item")
    for iid in required_scope:
        if iid not in by_id:
            codes.append("missing_report")
            continue
        item = by_id[iid]
        if schemas.validate_spec(_ITEM_SPEC, item):
            codes.append("item_schema_invalid")
        status = item.get("status")
        if status != "pass":
            codes.append(f"status_{status}" if status in STATUSES
                         else "status_invalid")
        if not authority_compatible(item, item.get("track")):
            codes.append("authority_mismatch")
        codes.extend(check_item(item))
    failure_codes = sorted(set(codes))
    unique_scope = list(dict.fromkeys(required_scope))
    evaluated = [iid for iid in unique_scope if iid in by_id]
    covered = len(evaluated)
    if not required_scope:
        gate = "not_required"
    elif not failure_codes:
        gate = "pass"
    elif any(code in FAIL_CLASS_CODES for code in failure_codes):
        gate = "fail"
    else:
        gate = "blocked"
    return {
        "physics_gate": gate,
        "failure_codes": failure_codes,
        "evaluated_required": evaluated,
        "denominator": len(required_scope),
        "coverage": {"covered": covered, "complete": covered == len(unique_scope)},
    }


# ---------------------------------------------------------------------------
# 5. coverage 产物
# ---------------------------------------------------------------------------

def build_coverage(required_scope, items, *, project_id="unspecified",
                   profile_id="unspecified", snapshot_revision="unspecified",
                   note=None) -> dict:
    """按 schemas["physics_coverage"] 构造覆盖产物（缺报告 id 计入 missing_scope）。

    coverage 只度量「报告在场」，不度量结果通过（coverage=100% != pass）。
    project_id/profile_id/snapshot_revision 缺省 "unspecified" 占位以保持
    双位置参数合同；正式落盘（physics-coverage.json）时调用方应显式传入。
    """
    present = set()
    for entry in items:
        if isinstance(entry, dict) and isinstance(entry.get("item_id"), str):
            present.add(entry["item_id"])
    covered = [iid for iid in required_scope if iid in present]
    missing = [iid for iid in required_scope if iid not in present]
    coverage = {
        "schema_version": schemas.SCHEMA_V3,
        "project_id": project_id,
        "profile_id": profile_id,
        "snapshot_revision": snapshot_revision,
        "required_scope": list(required_scope),
        "covered_scope": covered,
        "coverage_complete": not missing,
        "missing_scope": missing,
    }
    if note is not None:
        coverage["note"] = note
    errors = schemas.validate("physics_coverage", coverage)
    if errors:
        raise ValueError("physics_coverage schema 校验失败: " + "; ".join(errors))
    return coverage


# ---------------------------------------------------------------------------
# 6. physics_report 产物
# ---------------------------------------------------------------------------

def build_report(project_id, profile_id, snapshot_revision, items,
                 required_scope) -> dict:
    """组合 physics_report：内嵌 evaluate_gate 结果（schema 允许的承载方式）。

    schema additionalProperties=false，故 evaluate_gate 的完整结果经
    physics_gate + gate_failure_codes 两个白名单字段落入报告；
    evaluated_required/denominator/coverage 由 build_coverage 单独成档
    （physics-coverage.json）。构造后按 schemas["physics_report"] 严格校验，
    非法即抛 ValueError。items 深拷贝嵌入，保持纯函数。
    """
    gate = evaluate_gate(items, required_scope)
    report = {
        "schema_version": schemas.SCHEMA_V3,
        "project_id": project_id,
        "profile_id": profile_id,
        "snapshot_revision": snapshot_revision,
        "items": copy.deepcopy(items),
        "physics_gate": gate["physics_gate"],
        "gate_failure_codes": gate["failure_codes"],
    }
    errors = schemas.validate("physics_report", report)
    if errors:
        raise ValueError("physics_report schema 校验失败: " + "; ".join(errors))
    return report


# ---------------------------------------------------------------------------
# 7. bring-up 实测 witness（fail-closed：无实测只能 not_available）
# ---------------------------------------------------------------------------

def bring_up_witness(report) -> dict:
    """验证真实回板记录是否构成有效 bring-up witness。

    按 schemas["bring_up_report"] 验证 + raw_measurements 非空 + 板/序列号/
    Rev/治具/固件/测试软件/环境/operator/输入输出 hash/逐项结果字段非空。
    齐全 → {has_witness: True, status: report["bring_up_status"]}；缺任一 →
    {has_witness: False, status: "not_available", missing: [...]}——无实测
    记录只能 not_available，永不能凭资料/推导给 pass。
    """
    if not isinstance(report, dict):
        return {"has_witness": False, "status": "not_available",
                "missing": ["report_invalid"]}
    missing: list = []
    for field in _WITNESS_FIELDS:
        value = report.get(field)
        if value is None or (isinstance(value, (str, dict)) and not value):
            missing.append(field)
    raw = report.get("raw_measurements")
    if not isinstance(raw, list) or not raw:
        missing.append("raw_measurements")
    per_item = report.get("items")
    if not isinstance(per_item, list) or not per_item:
        missing.append("items")
    if schemas.validate("bring_up_report", report):
        missing.append("schema_invalid")
    if missing:
        return {"has_witness": False, "status": "not_available",
                "missing": sorted(set(missing))}
    return {"has_witness": True, "status": report["bring_up_status"]}


# ---------------------------------------------------------------------------
# 8. 指定后端逐字匹配（openEMS 与 scikit-rf 非等价）
# ---------------------------------------------------------------------------

def designated_backend_ok(item, designated) -> bool:
    """项的 model_or_tool 必须逐字等于 profile 指定后端（非等价后端不可互换）。

    openems 与 scikit_rf 是不同后端：model_or_tool=openems 的项在
    designated=scikit_rf 下为 False（反之亦然）。designated 非非空字符串
    或项无 model_or_tool → False（fail-closed）。
    """
    if not isinstance(designated, str) or not designated:
        return False
    if not isinstance(item, dict):
        return False
    return item.get("model_or_tool") == designated


# ---------------------------------------------------------------------------
# 9. IPC-2141 一阶差分阻抗筛查计算器（screening 级闭式；非仿真/实测）
# ---------------------------------------------------------------------------

#: IPC-2221/2141 一阶微带公式的公开引用适用域（w/h 超界 → validity 不过）
IPC2141_VALIDITY_W_OVER_H = (0.1, 2.0)


def ipc2141_first_order_diff_ohm(*, trace_width_mm, trace_gap_mm,
                                 dielectric_thickness_mm,
                                 copper_thickness_mm, epsilon_r) -> float:
    """边缘耦合微带差分阻抗的 IPC-2141/IPC-2221 一阶闭式估计（单位 Ω）。

    单端：Z0 = 87/sqrt(er+1.41) * ln(5.98*h/(0.8*w+t))
    差分：Zdiff = 2*Z0*(1 - 0.48*exp(-0.96*s/h))

    纯确定性闭式（math.log/exp），非 openEMS/scikit-rf 仿真、非
    lab_measurement 实测；产出只能归 physics_screening 轨（TD6：
    资料级/推导级证据不可 satisfy external_required/bring_up）。
    输入非法（w/s/h/t ≤ 0 或 er ≤ 0）抛 ValueError（fail-closed）。
    """
    import math

    if min(trace_width_mm, trace_gap_mm, dielectric_thickness_mm,
           copper_thickness_mm, epsilon_r) <= 0:
        raise ValueError("IPC-2141 一阶计算器输入必须全为正数"
                         "（w/s/h/t/er）")
    z0 = (87.0 / math.sqrt(epsilon_r + 1.41)) * math.log(
        5.98 * dielectric_thickness_mm /
        (0.8 * trace_width_mm + copper_thickness_mm))
    coupling = 1.0 - 0.48 * math.exp(
        -0.96 * trace_gap_mm / dielectric_thickness_mm)
    return 2.0 * z0 * coupling


def ipc2141_first_order_validity(*, trace_width_mm, trace_gap_mm,
                                 dielectric_thickness_mm,
                                 copper_thickness_mm, epsilon_r) -> bool:
    """一阶公式适用域检查（convergence_or_validity 门在闭式下的承载）。

    w/h 落在 IPC2141_VALIDITY_W_OVER_H（0.1–2.0）且全部输入为正即视为
    公式适用；任何超界/非数 → False（fail-closed，闭式筛查不冒充域外有效）。
    """
    import math

    values = (trace_width_mm, trace_gap_mm, dielectric_thickness_mm,
              copper_thickness_mm, epsilon_r)
    if any(not isinstance(v, (int, float)) or not math.isfinite(v)
           or v <= 0 for v in values):
        return False
    w_over_h = trace_width_mm / dielectric_thickness_mm
    lo, hi = IPC2141_VALIDITY_W_OVER_H
    return lo <= w_over_h <= hi
