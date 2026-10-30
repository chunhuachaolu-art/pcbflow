"""三类设计对象角色声明契约（纠偏词 P2；2026-09-06 起采纳/权威）。

status: adopted（2026-09-06 用户五点批准采纳，APR-0012..0016，登记于
out/v3-approvals/ r5 批次；此前为 proposal_not_authorized 提案，提案文档
V3-DESIGN-ARTIFACT-ROLES.md 已同步转权威）。本契约已追加式注册进
pcbflow/schemas.py registry（条目 artifact-role-declaration-v1；
REGISTRY_VERSION 保持 3.0 不动，既有 schema 条目与逐条哈希零改动——
APR-0012 语义限定）；后续 schema 演进只能走追加式（新版本+supersedes），
不得回写本批准或既有冻结产物。采纳定稿明细见下方 docstring 采纳段与
「2026-09-06 采纳定稿标记」常量块。
纯函数、零 IO、零子进程、零网络、无 wall-clock、无主机路径。

三角色语义（纠正「规范化输出带 .kicad_pcb 后缀 ⇒ 可执行板」的混称；
规范化输出是 pcbflow 分析方言，会丢失部分 setup/zones/图形/布线信息，
新版 k9 解析支持不自动使它成为完整可加载执行板）：
  - source_design_package（ROLE_SOURCE）：只读源设计及适用的规则/项目
    文件、来源与许可绑定；无 transform（identity 或 None）。
  - normalized_analysis_model（ROLE_ANALYSIS）：结构统计/拓扑/特征分析
    对象；显式声明能力与信息损失（loss_notes 必填非空）。结构上不可能
    携带执行类能力（构造器强制）。
  - staging_execution_package（ROLE_STAGING）：真实工具可加载、可执行、
    可检查的设计包；来源转换及工具保存版本明确（transform 必填）；
    check_scope 必填显式。

能力枚举 rationale（六项已定稿冻结，APR-0013）：
  - 分析类：analysis_stats（计数/统计账本）、analysis_topology（网/封装/
    焊盘多重集与连通结构）、analysis_features（约定表/关键网等特征）；
  - 执行类：tool_loadable（真实工具可加载）、tool_checkable（真实工具可
    对其执行检查/DRC）、tool_transform_target（真实工具可保存/转换出该
    格式为其目标）。分析模型不可能携带执行类能力（它是分析方言，不是
    工具域板文件）；执行包可声明分析能力子集——仅当未声明信息损失
    （loss_notes 为空）时才允许（构造器强制；该「loss_notes 为空」判据
    经 APR-0013 批准成立，为唯一判据）。

2026-09-06 采纳定稿（用户五点批准，批准号 APR-0012..0016）：
①schema 注册——本契约以纯追加方式注册进 schemas.py registry
（APR-0012；REGISTRY_VERSION 保持 3.0，冻结基线可复现性不破坏）；
②能力枚举六项定稿冻结——不增补 tool_export_target，staging 声明分析
能力子集以「loss_notes 为空」为唯一判据，后续增补/修订走 supersedes
（APR-0013）；③staging 绑定——未来 staging 产物强制携带声明+通过
validate_executor_consumption 消费合同才可进 executor；S21 历史 staging
按盘上实测 hash+DRC 证据追溯补构造声明（用户明确选择补声明而非只读
历史登记；原 S21 记录零改动，声明=新增只读引用层；APR-0014，见
scripts/s27_s21_historical_declarations.py 与
out/v3-tl5/s21-historical-staging-declarations-r1.json）；
④三角色名按现值冻结为模块常量（APR-0015）；⑤source 包 check_scope
允许显式声明口径、缺省（None）=未声明，analysis 侧恒 None 边界不变
（APR-0016）。PROPOSAL_STATUS 常量值保持不变（构造器输出形状的一部分，
既有声明对象字段值不回写）；采纳状态以本段、采纳常量块与 APR 处置
记录为准。

为何 path 不能替代类型检查：执行器消费判定只看声明字段（role/
capabilities/format/check_scope）。artifact_id/文件名后缀（.kicad_pcb
等）是命名惯例，可被任意角色冠用——S18 规范化板就落盘为
profiles/<pid>/inputs/board.kicad_pcb（板扩展名承载分析方言）；若按
后缀判型，分析方言会静默冒充可执行板。负向语义被测试固定：analysis
角色即使 artifact_id 以 .kicad_pcb 结尾仍被 validate_executor_consumption
拒绝（错误码 analysis_model_not_executable）。

检查口径（check_scope）：staging 必填显式；source 允许可空声明、缺省
（None）=未声明（APR-0016）。历史 S8/S21 staging 为裸板默认规则口径
（kicad-cli pcb drc，staging 隔离、无项目规则文件）——如实沿用
CHECK_SCOPE_BARE，不改历史语义；新链不得混称（项目自定义规则必须显式
CHECK_SCOPE_PROJECT 并声明 rule_dependencies）。
"""

from __future__ import annotations

import json
import re

CONTRACT_ID = "pcbflow.artifact_roles#artifact-role-declaration-v1"
# 值保持不变的构造器注记常量（历史声明对象字段值不回写；采纳状态见
# docstring 采纳段与下方采纳常量块）
PROPOSAL_STATUS = "proposal_not_authorized"

# 角色枚举（三名称 2026-09-06 按现值定稿冻结，APR-0015）
ROLE_SOURCE = "source_design_package"
ROLE_ANALYSIS = "normalized_analysis_model"
ROLE_STAGING = "staging_execution_package"
ROLES = (ROLE_SOURCE, ROLE_ANALYSIS, ROLE_STAGING)

# 能力枚举（六项 2026-09-06 定稿冻结，APR-0013；不增补 tool_export_target）
CAP_ANALYSIS_STATS = "analysis_stats"
CAP_ANALYSIS_TOPOLOGY = "analysis_topology"
CAP_ANALYSIS_FEATURES = "analysis_features"
CAP_TOOL_LOADABLE = "tool_loadable"
CAP_TOOL_CHECKABLE = "tool_checkable"
CAP_TOOL_TRANSFORM_TARGET = "tool_transform_target"
ANALYSIS_CAPABILITIES = (CAP_ANALYSIS_STATS, CAP_ANALYSIS_TOPOLOGY,
                         CAP_ANALYSIS_FEATURES)
EXECUTION_CAPABILITIES = (CAP_TOOL_LOADABLE, CAP_TOOL_CHECKABLE,
                          CAP_TOOL_TRANSFORM_TARGET)
ALL_CAPABILITIES = ANALYSIS_CAPABILITIES + EXECUTION_CAPABILITIES

# 检查口径枚举（staging 必填显式；source 可空声明、缺省=未声明（APR-0016）；
# 历史裸板口径语义不变）
CHECK_SCOPE_BARE = "bare_board_default_rules"
CHECK_SCOPE_PROJECT = "project_custom_rules"
CHECK_SCOPES = (CHECK_SCOPE_BARE, CHECK_SCOPE_PROJECT)

# ---------------------------------------------------------------------------
# 2026-09-06 用户批准采纳定稿标记（P2 五点采纳，APR-0012..0016；本块仅
# 新增常量与注记，不改任何既有函数行为。登记见 out/v3-approvals/ r5 批次
# approvals-bundle-r5.json / decision-ledger-r5.jsonl / disposition-APR-00*）
# ---------------------------------------------------------------------------

#: ② 能力枚举六项定稿冻结（APR-0013）：ALL_CAPABILITIES 六项即终集，
#: 不增补 tool_export_target；后续任何增补/修订走追加式 supersedes
#: （新契约版本），不回写本枚举与既有冻结产物。
CAPABILITY_ENUM_FROZEN = True
CAPABILITY_ENUM_FROZEN_APPROVAL = "APR-0013"
CAPABILITY_ENUM_FROZEN_DATE = "2026-09-06"

#: ② staging 声明分析能力子集的唯一判据=loss_notes 为空（APR-0013 批准
#: 判据成立；构造器既有强制不变：staging+分析能力+非空 loss → ValueError）。
STAGING_ANALYSIS_CAP_CRITERION = "loss_notes_empty"
STAGING_ANALYSIS_CAP_CRITERION_APPROVAL = "APR-0013"

#: ④ 三角色名按现值定稿冻结（APR-0015）：ROLE_SOURCE/ROLE_ANALYSIS/
#: ROLE_STAGING 三常量值即终名（source_design_package /
#: normalized_analysis_model / staging_execution_package）。
ROLE_NAMING_FROZEN = True
ROLE_NAMING_FROZEN_APPROVAL = "APR-0015"

#: ⑤ source 包 check_scope 允许显式声明口径；缺省（None）=未声明
#: （APR-0016）。analysis 侧 check_scope 恒 None 边界不变（构造器既有
#: 强制不变）。
SOURCE_CHECK_SCOPE_NULLABLE = True
SOURCE_CHECK_SCOPE_APPROVAL = "APR-0016"

#: ③ staging 绑定政策（APR-0014）：未来 staging 产物必须携带声明+通过
#: validate_executor_consumption 消费合同才可进 executor。本批准包不接
#: 线生产链（TL-5 staging 生产当前未运行），接线时点见 enforcement；
#: S21 历史 staging 追溯补声明见 scripts/s27_s21_historical_declarations.py
#: 与 out/v3-tl5/s21-historical-staging-declarations-r1.json（原 S21 记录
#: 零改动，声明=新增只读引用层）。
STAGING_BINDING_POLICY = {
    "status": "adopted",
    "adopted_date": "2026-09-06",
    "approval_ref": "APR-0014",
    "rule": ("未来 staging 产物必须携带 artifact-role-declaration-v1 声明"
             "并通过 validate_executor_consumption 消费合同，才可进入 "
             "executor 消费"),
    "enforcement": ("下一轮 TL-5 staging 生产恢复时接线（本批准包未接线"
                    "生产链）"),
}

# source_binding：kind 必须是 manifest 绑定（防静默绕过 manifest 直读
# datasets raw 板；其他 kind 值显式枚举白名单，本版仅 manifest 一种）
SBK_DATASET_MANIFEST_ENTRY = "dataset_manifest_entry"
SOURCE_BINDING_KINDS = (SBK_DATASET_MANIFEST_ENTRY,)
SOURCE_BINDING_KEYS = ("kind", "manifest_ref", "entry_key", "source_sha256")
TRANSFORM_KEYS = ("description", "tool", "tool_version", "saved_by")

_HEX64_RE = re.compile(r"^[0-9a-f]{64}$")


def _check_hex64(value, field: str, errors: list) -> None:
    if not isinstance(value, str) or not _HEX64_RE.match(value):
        errors.append(f"{field}: must be 64-char lowercase hex sha256, "
                      f"got {value!r}")


def _check_nonempty_str(value, field: str, errors: list) -> None:
    if not isinstance(value, str) or not value:
        errors.append(f"{field}: must be non-empty string, got {value!r}")


def _loss_declared(loss_notes) -> bool:
    """loss_notes 是否为「非空声明」（dict/非空 或 list/非空）。"""
    if isinstance(loss_notes, dict):
        return len(loss_notes) > 0
    if isinstance(loss_notes, list):
        return len(loss_notes) > 0
    return False


def _collect_field_errors(*, role, artifact_id, format_id, format_version,
                          capabilities, source_binding, transform,
                          output_sha256, rule_dependencies, check_scope,
                          loss_notes) -> list:
    """单一事实源的字段校验（builder 抛 ValueError；validate_declaration
    收集为错误列表——同一规则两用，防分叉）。"""
    errors: list = []
    if role not in ROLES:
        errors.append(f"role: must be one of {ROLES}, got {role!r}")
    _check_nonempty_str(artifact_id, "artifact_id", errors)
    _check_nonempty_str(format_id, "format_id", errors)
    _check_nonempty_str(format_version, "format_version", errors)
    _check_hex64(output_sha256, "output_sha256", errors)

    # capabilities：非空、已知枚举、无重复；角色结构约束
    caps = capabilities
    if not isinstance(caps, (list, tuple)) or \
            not all(isinstance(c, str) for c in caps):
        errors.append(f"capabilities: must be list of strings, "
                      f"got {caps!r}")
        caps = ()
    else:
        if len(set(caps)) != len(caps):
            errors.append(f"capabilities: duplicates in {caps!r}")
        unknown = [c for c in caps if c not in ALL_CAPABILITIES]
        if unknown:
            errors.append(f"capabilities: unknown values {unknown} "
                          f"(known: {list(ALL_CAPABILITIES)})")
        if not caps:
            errors.append("capabilities: must be non-empty")
        exec_declared = [c for c in caps if c in EXECUTION_CAPABILITIES]
        ana_declared = [c for c in caps if c in ANALYSIS_CAPABILITIES]
        if role == ROLE_ANALYSIS and exec_declared:
            errors.append(
                f"capabilities: {ROLE_ANALYSIS} structurally cannot carry "
                f"execution capabilities {exec_declared}（分析方言不是可"
                f"加载执行板；执行类能力只属于工具域板文件）")
        if role == ROLE_STAGING and not exec_declared:
            errors.append(f"capabilities: {ROLE_STAGING} must declare "
                          f"at least one execution capability "
                          f"{list(EXECUTION_CAPABILITIES)}")
        if role == ROLE_STAGING and ana_declared and _loss_declared(loss_notes):
            errors.append(
                f"capabilities/loss_notes: {ROLE_STAGING} declaring "
                f"analysis capabilities {ana_declared} contradicts "
                f"non-empty loss_notes（信息不丢才可声明分析能力子集）")

    # source_binding：kind 白名单=manifest 绑定（防静默绕过 manifest）
    if not isinstance(source_binding, dict):
        errors.append(f"source_binding: must be dict, "
                      f"got {source_binding!r}")
    else:
        if set(source_binding.keys()) != set(SOURCE_BINDING_KEYS):
            errors.append(f"source_binding: keys must be exactly "
                          f"{sorted(SOURCE_BINDING_KEYS)}, "
                          f"got {sorted(source_binding.keys())}")
        kind = source_binding.get("kind")
        if kind not in SOURCE_BINDING_KINDS:
            errors.append(
                f"source_binding.kind: must be one of "
                f"{SOURCE_BINDING_KINDS}（manifest 绑定强制，防静默绕过 "
                f"manifest 直读 datasets raw 板）, got {kind!r}")
        _check_nonempty_str(source_binding.get("manifest_ref"),
                            "source_binding.manifest_ref", errors)
        _check_nonempty_str(source_binding.get("entry_key"),
                            "source_binding.entry_key", errors)
        _check_hex64(source_binding.get("source_sha256"),
                     "source_binding.source_sha256", errors)

    # transform：source 无 transform（identity 或 None）；analysis/staging
    # 必填四键（工具保存版本/转换器身份显式）
    if transform is None:
        if role in (ROLE_ANALYSIS, ROLE_STAGING):
            errors.append(f"transform: required for {role}（来源转换与工"
                          f"具保存版本必须显式）")
    elif not isinstance(transform, dict):
        errors.append(f"transform: must be dict or None, "
                      f"got {transform!r}")
    else:
        if set(transform.keys()) != set(TRANSFORM_KEYS):
            errors.append(f"transform: keys must be exactly "
                          f"{sorted(TRANSFORM_KEYS)}, "
                          f"got {sorted(transform.keys())}")
        for k in TRANSFORM_KEYS:
            _check_nonempty_str(transform.get(k), f"transform.{k}", errors)
        if role == ROLE_SOURCE and transform.get("description") != "identity":
            errors.append(f"transform.description: {ROLE_SOURCE} has no "
                          f"transform（identity 或 None）, "
                          f"got {transform.get('description')!r}")

    # rule_dependencies：staging 必填非空（适用规则依赖声明）
    if rule_dependencies is None:
        rdeps: list = []
    elif isinstance(rule_dependencies, list) and \
            all(isinstance(r, str) and r for r in rule_dependencies):
        rdeps = rule_dependencies
    else:
        errors.append(f"rule_dependencies: must be list of non-empty "
                      f"strings, got {rule_dependencies!r}")
        rdeps = []
    if role == ROLE_STAGING and not rdeps:
        errors.append(f"rule_dependencies: required non-empty for "
                      f"{ROLE_STAGING}（适用规则依赖必须显式声明）")

    # check_scope：staging 必填显式；analysis 不得声明（非执行对象）
    if check_scope is not None and check_scope not in CHECK_SCOPES:
        errors.append(f"check_scope: must be one of {CHECK_SCOPES} "
                      f"or None, got {check_scope!r}")
    if role == ROLE_STAGING and check_scope is None:
        errors.append(f"check_scope: required explicit for "
                      f"{ROLE_STAGING}（bare_board_default_rules | "
                      f"project_custom_rules；禁混称）")
    if role == ROLE_ANALYSIS and check_scope is not None:
        errors.append(f"check_scope: {ROLE_ANALYSIS} is not an execution "
                      f"object（不得声明检查口径）")

    # loss_notes：analysis 必填非空（信息损失声明）；source 必须为 None
    if loss_notes is not None:
        if not isinstance(loss_notes, (dict, list)):
            errors.append(f"loss_notes: must be non-empty dict "
                          f"{{field: note}} or list of non-empty strings, "
                          f"got {loss_notes!r}")
        elif not _loss_declared(loss_notes):
            errors.append(f"loss_notes: must be non-empty, "
                          f"got {loss_notes!r}")
        elif isinstance(loss_notes, dict):
            items_ok = all(isinstance(k, str) and k and isinstance(v, str)
                           and v for k, v in loss_notes.items())
            if not items_ok:
                errors.append(f"loss_notes: entries must be non-empty "
                              f"strings（dict 键值）, got {loss_notes!r}")
        else:
            items_ok = all(isinstance(x, str) and x for x in loss_notes)
            if not items_ok:
                errors.append(f"loss_notes: entries must be non-empty "
                              f"strings（list 元素）, got {loss_notes!r}")
    if role == ROLE_ANALYSIS and not _loss_declared(loss_notes):
        errors.append(f"loss_notes: required non-empty for "
                      f"{ROLE_ANALYSIS}（信息损失声明必填）")
    if role == ROLE_SOURCE and loss_notes is not None:
        errors.append(f"loss_notes: {ROLE_SOURCE} has no transform, "
                      f"loss_notes must be None, got {loss_notes!r}")
    return errors


def build_artifact_role_declaration(*, role, artifact_id, format_id,
                                    format_version, capabilities,
                                    source_binding, transform,
                                    output_sha256, rule_dependencies,
                                    check_scope=None, loss_notes=None):
    """构造角色声明 dict；非法输入 ValueError（错误消息明确到字段）。"""
    errors = _collect_field_errors(
        role=role, artifact_id=artifact_id, format_id=format_id,
        format_version=format_version, capabilities=capabilities,
        source_binding=source_binding, transform=transform,
        output_sha256=output_sha256, rule_dependencies=rule_dependencies,
        check_scope=check_scope, loss_notes=loss_notes)
    if errors:
        raise ValueError(errors[0])
    rdeps = list(rule_dependencies or [])
    return {
        "contract": CONTRACT_ID,
        "proposal_status": PROPOSAL_STATUS,
        "role": role,
        "artifact_id": artifact_id,
        "format_id": format_id,
        "format_version": format_version,
        "capabilities": sorted(capabilities),
        "source_binding": {k: source_binding[k] for k in SOURCE_BINDING_KEYS},
        "transform": ({k: transform[k] for k in TRANSFORM_KEYS}
                      if transform is not None else None),
        "output_sha256": output_sha256,
        "rule_dependencies": sorted(rdeps),
        "check_scope": check_scope,
        "loss_notes": loss_notes,
    }


def validate_declaration(declaration) -> list:
    """对（可能由外部构造的）声明 dict 做结构校验，返回错误列表
    （空=结构合法）。不抛异常；消费语义由 validate_executor_consumption
    承担。"""
    if not isinstance(declaration, dict):
        return [{"code": "declaration_invalid",
                 "detail": f"declaration: must be dict, "
                           f"got {declaration!r}"}]
    errs = _collect_field_errors(
        role=declaration.get("role"),
        artifact_id=declaration.get("artifact_id"),
        format_id=declaration.get("format_id"),
        format_version=declaration.get("format_version"),
        capabilities=declaration.get("capabilities"),
        source_binding=declaration.get("source_binding"),
        transform=declaration.get("transform"),
        output_sha256=declaration.get("output_sha256"),
        rule_dependencies=declaration.get("rule_dependencies"),
        check_scope=declaration.get("check_scope"),
        loss_notes=declaration.get("loss_notes"))
    return [{"code": "declaration_invalid", "detail": e} for e in errs]


def validate_executor_consumption(declaration, *, executor_backend,
                                  executor_version, supported_formats,
                                  capabilities) -> list:
    """执行器消费判定：返回错误列表（空=可消费）。

    只看声明字段；路径/文件名（artifact_id 后缀如 .kicad_pcb）不参与
    判定。executor 身份与支持集（能力/format）由调用方显式传入。分析
    角色消费必拒（错误码 analysis_model_not_executable）。
    """
    errors: list = []
    if not isinstance(declaration, dict):
        return [{"code": "declaration_invalid",
                 "detail": "declaration must be a dict"}]
    if not isinstance(executor_backend, str) or not executor_backend:
        errors.append({"code": "executor_identity_missing",
                       "detail": "executor_backend must be non-empty string"})
    if not isinstance(executor_version, str) or not executor_version:
        errors.append({"code": "executor_identity_missing",
                       "detail": "executor_version must be non-empty string"})
    if not isinstance(supported_formats, (list, tuple)) or \
            not supported_formats or \
            not all(isinstance(f, str) and f for f in supported_formats):
        errors.append({"code": "executor_support_missing",
                       "detail": "supported_formats must be non-empty list "
                                 "of strings（执行器支持集须显式传入）"})
    if not isinstance(capabilities, (list, tuple)) or \
            not capabilities or \
            not all(isinstance(c, str) and c for c in capabilities):
        errors.append({"code": "executor_support_missing",
                       "detail": "capabilities must be non-empty list of "
                                 "strings（执行器能力集须显式传入）"})
    if errors:
        return errors

    role = declaration.get("role")
    if role != ROLE_STAGING:
        if role == ROLE_ANALYSIS:
            errors.append({
                "code": "analysis_model_not_executable",
                "detail": f"role={ROLE_ANALYSIS} 不能被执行器消费：规范化"
                          f"分析方言不是完整可加载执行板（信息损失已声明；"
                          f"path/后缀不参与本判定）"})
        elif role == ROLE_SOURCE:
            errors.append({
                "code": "source_package_read_only",
                "detail": f"role={ROLE_SOURCE} 为只读绑定源，不经执行器"
                          f"消费（执行须走 staging 包）"})
        else:
            errors.append({"code": "role_unknown",
                           "detail": f"role unknown: {role!r}"})
        return errors

    decl_caps = declaration.get("capabilities") or []
    extras = sorted(c for c in decl_caps if c not in capabilities)
    if extras:
        errors.append({"code": "capability_not_supported",
                       "detail": f"capabilities beyond executor support: "
                                 f"{extras}"})
    fmt = declaration.get("format_id")
    if fmt not in supported_formats:
        errors.append({"code": "format_not_supported",
                       "detail": f"format_id {fmt!r} not in executor "
                                 f"supported_formats "
                                 f"{sorted(supported_formats)}"})
    if not declaration.get("check_scope"):
        errors.append({"code": "check_scope_missing",
                       "detail": "staging check_scope must be explicit "
                                 "non-empty（bare_board_default_rules | "
                                 "project_custom_rules）"})
    errors.extend(validate_declaration(declaration))
    return errors


def _sb_canonical(decl: dict) -> dict:
    sb = decl.get("source_binding")
    if not isinstance(sb, dict):
        return {}
    return {k: sb.get(k) for k in SOURCE_BINDING_KEYS}


def _sb_canonical_json(decl: dict) -> str:
    return json.dumps(_sb_canonical(decl), sort_keys=True,
                      ensure_ascii=False)


def validate_role_consistency(declarations) -> list:
    """同链一致性：按 artifact_id 分组——组内 source_binding 必须一致；
    staging 的绑定必须可追溯到同组 source 声明（source_sha256 ==
    source 声明的 output_sha256，且组内须存在 source 声明）；analysis
    的 source 与 staging 的 source 不一致 → 错误。返回错误列表
    （空=一致）。"""
    errors: list = []
    if not isinstance(declarations, list) or not declarations:
        return [{"code": "declarations_invalid",
                 "detail": "declarations must be non-empty list"}]
    groups: dict = {}
    for i, d in enumerate(declarations):
        structural = validate_declaration(d)
        for e in structural:
            aid = d.get("artifact_id") if isinstance(d, dict) else None
            errors.append(dict(e, artifact_id=aid, index=i))
        if isinstance(d, dict) and not structural:
            groups.setdefault(d.get("artifact_id"), []).append(d)
    for artifact_id in sorted(groups):
        decls = groups[artifact_id]
        sbs = {_sb_canonical_json(d) for d in decls}
        if len(sbs) > 1:
            errors.append({
                "code": "source_binding_inconsistent",
                "artifact_id": artifact_id,
                "detail": f"source_binding differs within chain "
                          f"（analysis 与 staging 的 source 不一致等）: "
                          f"{sorted(sbs)}"})
            continue
        sources = [d for d in decls if d.get("role") == ROLE_SOURCE]
        stagings = [d for d in decls if d.get("role") == ROLE_STAGING]
        if len(sources) > 1:
            errors.append({"code": "duplicate_source_declaration",
                           "artifact_id": artifact_id,
                           "detail": f"{len(sources)} source declarations "
                                     f"share one artifact_id"})
            continue
        if stagings and not sources:
            errors.append({"code": "source_declaration_missing",
                           "artifact_id": artifact_id,
                           "detail": "staging declaration has no "
                                     "source_design_package declaration "
                                     "in the same chain（不可追溯到源）"})
            continue
        if sources:
            src = sources[0]
            for d in decls:
                if d is src:
                    continue
                if _sb_canonical(d).get("source_sha256") != \
                        src.get("output_sha256"):
                    errors.append({
                        "code": "source_hash_chain_broken",
                        "artifact_id": artifact_id,
                        "role": d.get("role"),
                        "detail": f"{d.get('role')}.source_binding."
                                  f"source_sha256 != source.output_sha256"
                                  f"（hash 链断裂）"})
    return errors
