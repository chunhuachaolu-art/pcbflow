#!/usr/bin/env python
"""S28-R1：P2 五项批准点采纳登记（r5 bundle；disposition 域；与
approvals_r4/s26 同构模式）。

2026-09-06 用户（human authority）人工决策登记（逐字引用见
USER_DECISIONS_R5 与各 disposition rationale_text）：

- APR-0012「批准注册」：artifact-role-declaration-v1 追加式注册进
  schemas.py registry（REGISTRY_VERSION 保持 3.0，既有条目零改动）；
- APR-0013「六项定稿」：六能力冻结，不增补 tool_export_target；staging
  声明分析能力子集以「loss_notes 为空」为唯一判据；增补走 supersedes；
- APR-0014「强制+S21补声明」：未来 staging 产物强制携带声明+通过
  consumption 合同才可进 executor；S21 历史 staging 按盘上实测 hash+DRC
  证据追溯补构造声明（原 S21 记录零改动，声明=新增只读引用层）；
- APR-0015「按现值定稿」：三角色名冻结为模块常量；
- APR-0016「允许source可空声明」：source check_scope 可空声明、缺省=
  未声明；analysis 侧恒 None 边界不变。

同构不变量（与 approvals/approvals_r2/r3/r4 逐字同模式）：每项批准=
一条 disposition_record（kind=accept、scope=adoption）+ 一条 ledger
entry（entry_kind=disposition、authority=human、trust_level=untrusted
——处置是决定不是事实，恒不可升级）；validate_no_gate_write 对全部
记录强制（零门/零谓词翻动）；evidence=被登记事实的冻结产物 sha256
（磁盘实读对账，缺文件 fail-closed）；批准日期=人工声明常量
APPROVAL_DATE_R5="2026-09-06"（非机器 wall-clock）；evidence 一律仓库
相对 POSIX 路径；批准只能被后续 supersedes 追加式取代，不可回写；
r1–r4 批次登记文件字节不动（本批全部为新文件）。

账本续链（对下发口径「首条 prev 锚 r4 head 330d6392」的机器可验实现）：
decision-ledger-r5.jsonl 首行=r4 末条 entry 原样续入（只读复制，r4 文件
字节不动），其后 5 条新 entry 的 prev_entry_sha256 锚定 r4 末条
entry_sha256（81ace4a7…），首条新 entry 的 ledger_head_sha256=
sha256_text("330d6392…" + ":" + entry_sha256)——即 head 链以 r4 head
330d6392 为 prev_head 跨文件续链；ledger.verify_chain 全链（6 条）可验
（该模块对文件内首条强制 Genesis prev=null，故「prev 锚 r4 head」以
head 续链+prev 锚定 r4 末条 entry 的双锚实现，语义限定入 bundle
prev_batch_anchor 块）。

落盘（byte-exact 可重跑；已存在则重建比对一致后退出不覆写，不一致=
fail；全部为 out/v3-approvals/ r5 新文件）：
- approvals-bundle-r5.json
- decision-ledger-r5.jsonl（6 行：r4 末条续入 + APR-0012..0016）
- disposition-APR-0012-schema-registration.json
- disposition-APR-0013-capability-enum-finalization.json
- disposition-APR-0014-staging-binding-and-s21-retroactive-declaration.json
- disposition-APR-0015-role-naming-finalization.json
- disposition-APR-0016-source-check-scope-nullable.json

机制：canonical JSON；零子进程；零网络；无 wall-clock；datasets/ 只读；
零门/零谓词翻动（gate_write_scan 全空 + frozen_machine_gate_status
显式声明）。收尾打印新件 sha256 前 8。

用法：python scripts/s28_p2_adoption_approvals.py   （仓库根执行）
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from pcbflow import disposition, hashing, ledger, schemas  # noqa: E402

OUT_APR = REPO / "out" / "v3-approvals"

S28_DATE = "2026-09-06"  # 人工会话声明日期（非 wall-clock；=APPROVAL_DATE_R5）
APPROVER = "user"
APPROVER_ROLE = "human_authority"
APPROVALS_REVISION_R5 = "v3-approvals-r5"
CHECKPOINT_ID_R5 = "CKPT-V3-APPROVALS-R5"
SCHEMA_VERSION = schemas.SCHEMA_V3

REL_R4_LEDGER = "out/v3-approvals/decision-ledger-r4.jsonl"
REL_R4_BUNDLE = "out/v3-approvals/approvals-bundle-r4.json"

# 先验锚（盘上实测入账；不配即中止——防篡改/防覆写，fail-closed）
FROZEN_SHA256 = {
    REL_R4_LEDGER: "c7420b9e98fcacc31ba93130fe27551cfd5fe1fec61be763a42d2094190b712e",
    REL_R4_BUNDLE: "a9e74e8b1efbd72979e9295ae6971ceed43c39803ed126a5c3d10b25c7ad8bb2",
    "out/v3-approvals/disposition-APR-0002-tl1-schema-baseline.json":
        "4c122e0ee8dad91e05449611cf76b505ea61f30ab8ac938bb21e18a2f536bb96",
    "out/v3-tl5/artifact-roles-validation-r1.json":
        "d88945d2957870fc93f27fa2efdd953fdaa6be31c93ef8ffb92f6ca4b4745ede",
    "out/v3-tl5/k9-route-check-batch-r1/plan.json":
        "2c8aca6a27d7309e36de4354f41b7b2942a9dfed8014d69290b38b73bb84e17e",
    "out/v3-tl5/k9-route-check-batch-r1/batch-summary.json":
        "a683137eb279292e5e1265618993f279e4e5648715f1757f4e551f2c770a1202",
    "out/v3-tl5/s21-historical-staging-declarations-r1.json":
        "5f8fb67ae91ca5bc21c0b19407976db0019098ca19acbf42cceb83adcbe2f40e",
    "out/v3-tl5/s21-historical-declarations-validation-r1.json":
        "ec38ba26c8311006c6fb1fa683d5181c5548e8169b7b0779b30c43a284636190",
}

# r4 head（CKPT-V3-APPROVALS-R4；续链锚，落盘前与 r4 末条 entry 实读复核）
R4_HEAD_SHA256 = "330d6392ea7f6edadd83cbdcc663d7efd2de14585fea46b7da55b46d7b77d4d9"

# evidence 逻辑名 → 仓库相对 POSIX 路径（磁盘实读；输出无主机路径）
EVIDENCE_FILES_R5 = (
    ("apr0002_schema_baseline",
     "out/v3-approvals/disposition-APR-0002-tl1-schema-baseline.json"),
    ("s25_roles_validation",
     "out/v3-tl5/artifact-roles-validation-r1.json"),
    ("s21_plan", "out/v3-tl5/k9-route-check-batch-r1/plan.json"),
    ("s21_batch_summary",
     "out/v3-tl5/k9-route-check-batch-r1/batch-summary.json"),
    ("s21_declarations",
     "out/v3-tl5/s21-historical-staging-declarations-r1.json"),
    ("s21_declarations_validation",
     "out/v3-tl5/s21-historical-declarations-validation-r1.json"),
)

# 用户决定原文（2026-09-06 会话逐字记录；选择标签+描述要点）
USER_DECISIONS_R5 = {
    "APR-0012": {
        "decision_label": "批准注册",
        "decision_quote": ("「批准注册」——将 artifact-role-declaration-v1 "
                           "注册进 schemas.py registry，追加式、不改既有 "
                           "schema 语义。"),
        "decided_date": S28_DATE,
    },
    "APR-0013": {
        "decision_label": "六项定稿",
        "decision_quote": ("「六项定稿」——六能力冻结，不增补 "
                           "tool_export_target；staging 声明分析能力子集"
                           "以「loss_notes 为空」为唯一判据，判据成立；"
                           "后续新增走 supersedes。"),
        "decided_date": S28_DATE,
    },
    "APR-0014": {
        "decision_label": "强制+S21补声明",
        "decision_quote": ("「强制+S21补声明」——未来 staging 产物强制携带"
                           "声明+通过 consumption 合同才可进 executor；"
                           "S21 历史 staging 按盘上实测 hash+DRC 证据追溯"
                           "补构造声明（用户明确选择了补声明，而非只读历史"
                           "登记），需重跑一致性验证。"),
        "decided_date": S28_DATE,
    },
    "APR-0015": {
        "decision_label": "按现值定稿",
        "decision_quote": "「按现值定稿」——三名称冻结为模块常量。",
        "decided_date": S28_DATE,
    },
    "APR-0016": {
        "decision_label": "允许source可空声明",
        "decision_quote": ("「允许source可空声明」——source 包可显式声明"
                           "口径，缺省=未声明；analysis 侧恒 None 边界不变"
                           "（即维持 §2 表格现设计，无需改构造器）。"),
        "decided_date": S28_DATE,
    },
}

# 一项批准定义（数据即账：语义限定逐条对应 2026-09-06 人工决定原文）
APPROVAL_SPECS_R5 = (
    {
        "approval_id": "APR-0012",
        "entry_id": "APR-E-0012",
        "slug": "schema-registration",
        "subject": ("artifact-role-declaration-v1 追加式注册进 "
                    "pcbflow/schemas.py registry（REGISTRY_VERSION 保持 "
                    "3.0，既有 15 条 schema 语义与逐条哈希零改动）"),
        "kind": "accept",
        "scope": "adoption",
        "rationale_code": "schema_registration_additive_approved",
        "rationale_text": (
            "用户人工批准 @2026-09-06（human authority，决定原文：「批准"
            "注册」——将 artifact-role-declaration-v1 注册进 schemas.py "
            "registry，追加式、不改既有 schema 语义）。语义限定：①纯追"
            "加式注册：registry 仅新增条目 artifact-role-declaration-v1，"
            "既有 15 条 schema 定义零改动；②REGISTRY_VERSION 保持 \"3.0\""
            " 不动——schema_hash 逐条独立（输入={name, schema_version, "
            "schema}），升版会改写全部既有 schema_hash、破坏 "
            "disposition-APR-0002 冻结基线（现行 schema v3.0 合同=被批准"
            "基线）的可复现性，追加不改既有条目哈希（该决定已定，不重新"
            "权衡）；③spec 从 pcbflow/artifact_roles.py 构造器实际输出形"
            "状+tests/test_p2_artifact_roles.py 夹具忠实推导，角色条件结"
            "构经 anyOf 表达（analysis check_scope 恒 None / staging 必"
            "填 transform+check_scope+rule_dependencies 非空 / source "
            "loss_notes 恒 None、transform 恒无或 identity）；④「staging "
            "≥1 执行类能力」「staging 声明分析能力须 loss_notes 为空」"
            "「loss_notes 非空 dict」为语义约束，超出验证器子集表达力"
            "（无 contains/minProperties），由 pcbflow.artifact_roles 单"
            "一事实源强制——schema=形状合同，模块=语义 authority；⑤后续 "
            "schema 演进只能走追加式（新版本+supersedes），不得回写本批"
            "准或既有冻结产物；⑥本批准只落 disposition 域，零门/零谓词"
            "翻动，不改任何冻结产物。"),
        "fact_refs": ["artifact-role-declaration-v1",
                      "V3-DESIGN-ARTIFACT-ROLES", "APR-0002"],
        "evidence": ("apr0002_schema_baseline", "s25_roles_validation"),
    },
    {
        "approval_id": "APR-0013",
        "entry_id": "APR-E-0013",
        "slug": "capability-enum-finalization",
        "subject": ("能力枚举六项定稿冻结：analysis_stats/"
                    "analysis_topology/analysis_features/tool_loadable/"
                    "tool_checkable/tool_transform_target；不增补 "
                    "tool_export_target"),
        "kind": "accept",
        "scope": "adoption",
        "rationale_code": "capability_enum_finalized_six",
        "rationale_text": (
            "用户人工批准 @2026-09-06（human authority，决定原文：「六项"
            "定稿」——六能力冻结，不增补 tool_export_target；staging 声明"
            "分析能力子集以「loss_notes 为空」为唯一判据，判据成立；后续"
            "新增走 supersedes）。语义限定：①六项能力即终集（模块常量 "
            "CAPABILITY_ENUM_FROZEN=True，CAPABILITY_ENUM_FROZEN_APPROVAL"
            "=APR-0013）；②明确不增补 tool_export_target；③staging 声明"
            "分析能力子集的唯一判据=loss_notes 为空（STAGING_ANALYSIS_CAP"
            "_CRITERION=loss_notes_empty；构造器既有强制不变：staging+分"
            "析能力+非空 loss_notes → ValueError），本批准为该判据的成立"
            "登记，不改动构造器行为；④后续任何能力增补/修订走追加式 "
            "supersedes（新契约版本），不回写本枚举、本批准或既有冻结产"
            "物；⑤本批准只落 disposition 域，零门/零谓词翻动。"),
        "fact_refs": ["artifact-role-declaration-v1",
                      "V3-DESIGN-ARTIFACT-ROLES", "S25"],
        "evidence": ("s25_roles_validation",),
    },
    {
        "approval_id": "APR-0014",
        "entry_id": "APR-E-0014",
        "slug": "staging-binding-and-s21-retroactive-declaration",
        "subject": ("staging 绑定政策采纳：未来 staging 产物强制携带声明+"
                    "通过 consumption 合同才可进 executor；S21 历史 "
                    "staging 按盘上实测 hash+DRC 证据追溯补构造声明"
                    "（17 板）并重跑一致性验证"),
        "kind": "accept",
        "scope": "adoption",
        "rationale_code": "staging_binding_adopted_s21_retroactive_declared",
        "rationale_text": (
            "用户人工批准 @2026-09-06（human authority，决定原文：「强制"
            "+S21补声明」——未来 staging 产物强制携带声明+通过 consumption"
            " 合同才可进 executor；S21 历史 staging 按盘上实测 hash+DRC "
            "证据追溯补构造声明（用户明确选择了补声明，而非只读历史登"
            "记），需重跑一致性验证）。语义限定：①政策常量 "
            "STAGING_BINDING_POLICY（status=adopted，adopted_date="
            "2026-09-06，approval_ref=APR-0014）：未来 staging 产物必须携"
            "带 artifact-role-declaration-v1 声明并通过 "
            "validate_executor_consumption 消费合同才可进 executor；②生"
            "产链接线时点=下一轮 TL-5 staging 生产恢复时（enforcement），"
            "本批准包不接线生产链——TL-5 staging 生产当前未运行，本包零"
            "生产行为；③S21 追溯补声明=按盘上实测 hash+DRC 证据构造（17/"
            "17 板 staging 与源逐字节一致实测，loss_notes=None 如实），"
            "原 S21 批次文件（out/v3-tl5/k9-route-check-batch-r1/ 下全"
            "部）零改动，声明为引用只读历史件的新增只读引用层"
            "（s21-historical-staging-declarations-r1.json，5f8fb67a），"
            "不回填不回写；④重跑一致性验证结果：validate_role_consistency"
            " + validate_executor_consumption 17/17 板零错误（executor="
            "kicad-cli/10.0.5/kicad_pcb/[tool_loadable,tool_checkable]）；"
            "⑤DRC 证据分态如实入件：11 板 integrity=pass、5 板仅双运行"
            "error 计数不稳（kicad-cli 跨运行不稳定=D19(b) 类工具实况如"
            "实登记，非判罚）、1 板 constraints（格式 20260624）kicad-cli "
            "10.0.5 拒绝加载（exit 3，无 DRC JSON）——该板 transform 如实"
            "写明拒绝加载、evidence_caveat 明示证据缺席，不冒称可加载/可"
            "检查；⑥本批准可被后续 supersedes 追加式取代，不可回写；"
            "⑦本批准只落 disposition 域，零门/零谓词翻动。"),
        "fact_refs": ["artifact-role-declaration-v1", "S21",
                      "V3-DESIGN-ARTIFACT-ROLES", "STAGING_BINDING_POLICY"],
        "evidence": ("s21_batch_summary", "s21_plan", "s21_declarations",
                     "s21_declarations_validation"),
    },
    {
        "approval_id": "APR-0015",
        "entry_id": "APR-E-0015",
        "slug": "role-naming-finalization",
        "subject": ("三角色名按现值定稿冻结：source_design_package / "
                    "normalized_analysis_model / staging_execution_package"),
        "kind": "accept",
        "scope": "adoption",
        "rationale_code": "role_naming_frozen_asis",
        "rationale_text": (
            "用户人工批准 @2026-09-06（human authority，决定原文：「按现"
            "值定稿」——三名称冻结为模块常量）。语义限定：①三名称按现值"
            "冻结（模块常量 ROLE_NAMING_FROZEN=True，ROLE_NAMING_FROZEN_"
            "APPROVAL=APR-0015）：ROLE_SOURCE=source_design_package、"
            "ROLE_ANALYSIS=normalized_analysis_model、ROLE_STAGING="
            "staging_execution_package；②冻结对象=常量值本身，模块单点"
            "定义不变；③改名/别名须走新契约版本+追加式 supersedes，不得"
            "回写本批准、既有声明对象字段值或任何冻结产物；④本批准只落 "
            "disposition 域，零门/零谓词翻动。"),
        "fact_refs": ["artifact-role-declaration-v1",
                      "V3-DESIGN-ARTIFACT-ROLES", "S25"],
        "evidence": ("s25_roles_validation",),
    },
    {
        "approval_id": "APR-0016",
        "entry_id": "APR-E-0016",
        "slug": "source-check-scope-nullable",
        "subject": ("source 包 check_scope 允许显式声明口径、缺省（None）"
                    "=未声明；analysis 侧恒 None 边界不变（维持 §2 表格"
                    "现设计，无需改构造器）"),
        "kind": "accept",
        "scope": "adoption",
        "rationale_code": "source_check_scope_nullable_approved",
        "rationale_text": (
            "用户人工批准 @2026-09-06（human authority，决定原文：「允许"
            "source可空声明」——source 包可显式声明口径，缺省=未声明；"
            "analysis 侧恒 None 边界不变（即维持 §2 表格现设计，无需改构"
            "造器））。语义限定：①source 角色 check_scope 允许可空声明："
            "可显式声明 bare_board_default_rules | project_custom_rules，"
            "缺省 None=未声明（模块常量 SOURCE_CHECK_SCOPE_NULLABLE=True，"
            "SOURCE_CHECK_SCOPE_APPROVAL=APR-0016）；②analysis 侧 "
            "check_scope 恒 None 边界不变（构造器既有强制：analysis+非空"
            "check_scope → ValueError）；③staging 侧仍必填显式（构造器既"
            "有强制不变）；④检查口径禁混称规则不变（项目自定义规则必须显"
            "式 project_custom_rules 并声明 rule_dependencies）；⑤本批准"
            "不改构造器行为，可被后续 supersedes 追加式取代，不可回写；"
            "⑥只落 disposition 域，零门/零谓词翻动。"),
        "fact_refs": ["artifact-role-declaration-v1",
                      "V3-DESIGN-ARTIFACT-ROLES", "S25"],
        "evidence": ("s25_roles_validation",),
    },
)

FROZEN_MACHINE_GATE_STATUS_R5 = (
    "本登记不重算、不改写任何机器门与谓词：TL-2 critic 分诊谓词语义不"
    "变、fail-closed 路由不变；TD5 分诊合取约束不变、自动分流仍 blocked；"
    "TL-3-G1/TL-4-G/TL-5-G 既有裁决与分母不变（TL-5-G 37 profile 分母不"
    "变）；TL-6 readiness 投影不回写；STAGING_BINDING_POLICY 的接线时点="
    "下一轮 TL-5 staging 生产恢复时，本批准包不触发生产链。本批五项批准"
    "只落 disposition 域（L6 事实/处置/门分离）：P2 契约采纳=接口合同登"
    "记与历史层登记，不构成任何质量结论、门输入或自动分流资格。"
)


def _fail(msg: str) -> None:
    print(f"[s28-apr5] FAIL: {msg}")
    sys.exit(1)


def _sha(rel: str) -> str:
    path = REPO.joinpath(*rel.split("/"))
    if not path.is_file():
        _fail(f"输入缺失（fail-closed）: {rel}")
    return hashing.sha256_file(str(path))


def disposition_filename(spec: dict) -> str:
    """批准处置记录落盘文件名（out/v3-approvals/ 编排口径）。"""
    return f"disposition-{spec['approval_id']}-{spec['slug']}.json"


def _ledger_bytes(entries) -> bytes:
    """账本落盘字节（编排侧写 decision-ledger-r5.jsonl 的唯一口径）。"""
    from pcbflow import config

    return "".join(
        json.dumps(e, ensure_ascii=config.JSON_ENSURE_ASCII,
                   sort_keys=config.JSON_SORT_KEYS) + "\n"
        for e in entries).encode(config.ENCODING)


def build_approvals_bundle_r5(evidence_hashes: dict) -> dict:
    """构造 r5 完整登记 bundle（纯函数；同输入 byte-exact）。

    evidence_hashes 必须覆盖 EVIDENCE_FILES_R5 全部逻辑名（缺一
    fail-closed ValueError）。
    """
    missing = [name for name, _ in EVIDENCE_FILES_R5
               if not evidence_hashes.get(name)]
    if missing:
        raise ValueError(
            f"evidence 缺失（fail-closed 拒绝构造批准）: {missing}")
    hashes = dict(evidence_hashes)

    # r4 末条 entry 实读复核（续链基座；r4 文件字节不动）
    r4_lines = (OUT_APR / "decision-ledger-r4.jsonl") \
        .read_text(encoding="utf-8").splitlines()
    if len(r4_lines) != 1:
        _fail(f"r4 ledger 行数非 1: {len(r4_lines)}")
    r4_entry = json.loads(r4_lines[0])
    if r4_entry.get("ledger_head_sha256") != R4_HEAD_SHA256:
        _fail("r4 head 与先验锚 330d6392 不符")
    if ledger.verify_chain([r4_entry]) != []:
        _fail("r4 末条 entry 链校验失败（续链基座不可信）")

    dispositions: list = []
    entries: list = [r4_entry]
    gate_write_scan: dict = {}
    for spec in APPROVAL_SPECS_R5:
        record = disposition.build_disposition(
            disposition_id=spec["approval_id"],
            fact_refs=spec["fact_refs"],
            kind=spec["kind"],
            scope=spec["scope"],
            rationale_code=spec["rationale_code"],
            rationale_text=spec["rationale_text"],
            approver=APPROVER,
            approver_role=APPROVER_ROLE)
        scan = disposition.validate_no_gate_write(record)
        if scan:
            raise ValueError(f"{spec['approval_id']} 触发门写禁区: {scan}")
        gate_write_scan[spec["approval_id"]] = scan
        dispositions.append(record)
        entries, _ = ledger.append(entries, dict(
            entry_kind="disposition",
            schema_validation=ledger.make_schema_validation(
                "disposition_record"),
            authority="human",
            trust_level="untrusted",
            entry_id=spec["entry_id"],
            actor=APPROVER,
            actor_role=APPROVER_ROLE,
            disposition_refs=[spec["approval_id"]],
            payload_ref=hashing.sha256_bytes(
                hashing.canonical_json_bytes(record)),
            artifact_hashes={name: hashes[name]
                             for name in spec["evidence"]},
            snapshot_revision=APPROVALS_REVISION_R5))

    # 续链语义自证：首条新 entry 的 head 以 r4 head 330d6392 为 prev_head
    first_new = entries[1]
    expected_head = hashing.sha256_text(
        R4_HEAD_SHA256 + ":" + first_new["entry_sha256"])
    if first_new["ledger_head_sha256"] != expected_head or \
            first_new["prev_entry_sha256"] != r4_entry["entry_sha256"]:
        _fail("续链锚定失败（head 未以 330d6392 续链）")
    if ledger.verify_chain(entries) != [] or len(entries) != 6:
        _fail("r5 全链校验失败")

    bundle = {
        "schema_version": SCHEMA_VERSION,
        "approval_date": S28_DATE,
        "approver": {"actor": APPROVER, "actor_role": APPROVER_ROLE},
        "revision": APPROVALS_REVISION_R5,
        "approval_count": len(APPROVAL_SPECS_R5),
        "supersedes_note": (
            "r5 为追加批次：不取代、不改写 r1（APR-0001–0006）、"
            "r2（APR-0007–0009）、r3（APR-0010）、r4（APR-0011）；"
            "out/v3-approvals/ 既有文件字节不动。本批五项批准均可被后续 "
            "supersedes 追加式取代，不可回写。"),
        "prev_batch_anchor": {
            "revision": "v3-approvals-r4",
            "ledger_file_rel": REL_R4_LEDGER,
            "ledger_file_sha256": hashes["_r4_ledger_file"],
            "checkpoint_id": "CKPT-V3-APPROVALS-R4",
            "ledger_head_sha256": R4_HEAD_SHA256,
            "last_entry_sha256": r4_entry["entry_sha256"],
            "anchor_semantics": (
                "r5 账本为跨文件续链：decision-ledger-r5.jsonl 首行=r4 末"
                "条 entry 原样续入（只读复制，r4 文件字节不动），其后 5 条"
                "新 entry 的 prev_entry_sha256 锚定 r4 末条 entry_sha256；"
                "首条新 entry 的 ledger_head_sha256=sha256_text(\""
                "330d6392…\" + \":\" + entry_sha256)——head 链以 r4 head "
                "330d6392 为 prev_head 跨文件续链（「首条 prev 锚 r4 head "
                "330d6392」的机器可验实现；ledger.verify_chain 对文件内首"
                "条强制 Genesis prev=null，故以 head 续链+prev 锚定 r4 末"
                "条 entry 双锚实现），全链 6 条 verify_chain 可验。"),
        },
        "user_decisions": USER_DECISIONS_R5,
        "dispositions": dispositions,
        "ledger_entries": entries,
        "ledger_file_sha256": hashing.sha256_bytes(_ledger_bytes(entries)),
        "ledger_verify": {
            "chain_errors": ledger.verify_chain(entries),
            "supersedes_errors": ledger.verify_supersedes(entries),
        },
        "ledger_checkpoint": ledger.make_checkpoint(entries,
                                                   CHECKPOINT_ID_R5),
        "gate_write_scan": gate_write_scan,
        "evidence_registry": [
            {"name": name, "path": path, "sha256": hashes[name]}
            for name, path in EVIDENCE_FILES_R5],
        "disposition_files": {spec["approval_id"]:
                              disposition_filename(spec)
                              for spec in APPROVAL_SPECS_R5},
        "frozen_machine_gate_status": FROZEN_MACHINE_GATE_STATUS_R5,
        "notes": [
            "五项人工批准（2026-09-06，P2 五点采纳）：APR-0012 schema 追加"
            "式注册（REGISTRY_VERSION 保持 3.0——schema_hash 逐条独立，升"
            "版会改写全部既有哈希、破坏 APR-0002 冻结基线可复现性）；"
            "APR-0013 六能力定稿（不增补 tool_export_target，loss_notes "
            "为空=唯一判据，增补走 supersedes）；APR-0014 staging 绑定强"
            "制+S21 追溯补声明（原 S21 记录零改动，声明=新增只读引用层；"
            "生产链接线时点=下一轮 TL-5 staging 生产恢复时，本包不接线）；"
            "APR-0015 三角色名按现值冻结；APR-0016 source check_scope 可"
            "空声明（analysis 恒 None 边界不变）。",
            "本账本为 disposition 域续链账本 r5 批次（r4 末条原样续入+5 条"
            "新 entry），不改写既有 out/v3-approvals/ r1–r4 文件与任何 "
            "out/ 冻结产物。",
            "scope 取值：disposition_record schema 的 scope 枚举含 "
            "adoption 项，本批五项均取 scope=adoption（契约/枚举/政策/"
            "命名/口径采纳登记），如实映射。",
            "批准日期为人工声明常量（非机器 wall-clock）；evidence hash "
            "为生成时磁盘实读值，可用 sha256sum 对 out/ 内文件复核。",
        ],
    }
    return bundle


def main() -> None:
    # 0) 先验锚：全部输入文件磁盘实读对账（fail-closed）
    hashes = {}
    for name, rel in EVIDENCE_FILES_R5:
        hashes[name] = _sha(rel)
    for rel, want in FROZEN_SHA256.items():
        actual = _sha(rel)
        if actual != want:
            _fail(f"输入 hash 与先验锚不符: {rel} {actual[:8]}…"
                  f"≠{want[:8]}…")
        if rel == REL_R4_LEDGER:
            hashes["_r4_ledger_file"] = actual

    # 1) bundle（纯函数构造 + 门写扫描/链校验/checkpoint 复核）
    bundle = build_approvals_bundle_r5(hashes)
    if bundle["ledger_verify"]["chain_errors"] \
            or bundle["ledger_verify"]["supersedes_errors"]:
        _fail(f"r5 账本校验失败：{bundle['ledger_verify']}")
    for apr, scan in bundle["gate_write_scan"].items():
        if scan:
            _fail(f"{apr} 门写扫描非空（不可落盘）")
    ckpt_errors = ledger.verify_against_checkpoint(
        bundle["ledger_entries"], bundle["ledger_checkpoint"])
    if ckpt_errors:
        _fail(f"checkpoint 复核失败：{ckpt_errors}")

    # 2) 目标七件（byte-exact 可重跑；已存在则校验一致，不覆写）
    ledger_bytes = _ledger_bytes(bundle["ledger_entries"])
    if hashing.sha256_bytes(ledger_bytes) != bundle["ledger_file_sha256"]:
        _fail("decision-ledger-r5.jsonl 字节与 bundle 声明不符")
    targets = [
        (OUT_APR / "approvals-bundle-r5.json",
         hashing.canonical_json_bytes(bundle)),
        (OUT_APR / "decision-ledger-r5.jsonl", ledger_bytes),
    ]
    for spec in APPROVAL_SPECS_R5:
        rec = next(d for d in bundle["dispositions"]
                   if d["disposition_id"] == spec["approval_id"])
        targets.append(
            (OUT_APR / disposition_filename(spec),
             hashing.canonical_json_bytes(rec)))

    written: dict = {}
    for path, expected in targets:
        if path.exists():
            actual = path.read_bytes()
            if actual != expected:
                _fail(f"{path.name} 已存在且字节与本次构造不一致"
                      f"（byte-exact 校验失败；不覆写）")
            print(f"[s28-apr5] 已存在且一致（不覆写）：{path.name}")
        else:
            path.write_bytes(expected)
            print(f"[s28-apr5] 新增落盘：{path.name}")
        written[path] = hashing.sha256_bytes(expected)

    # 3) 落盘复读校验（账本链 + r1–r4 台账字节未动）
    disk_entries = [json.loads(line) for line in
                    (OUT_APR / "decision-ledger-r5.jsonl")
                    .read_text(encoding="utf-8").splitlines()]
    if ledger.verify_chain(disk_entries) != [] or len(disk_entries) != 6:
        _fail("账本落盘复读校验失败")
    for rel, want in FROZEN_SHA256.items():
        if _sha(rel) != want:
            _fail(f"既有文件字节被改（禁止）: {rel}")

    # 4) 收尾：打印新件 sha256 前 8 + 门状态
    print("[s28-apr5] --- 新件 sha256（前 8）---")
    for path in sorted(written):
        print(f"[s28-apr5]   {path.relative_to(REPO).as_posix()}: "
              f"{written[path][:8]}")
    print(f"[s28-apr5] ledger: {len(disk_entries)} entries（r4 末条续入+"
          f"APR-0012..0016）| checkpoint={bundle['ledger_checkpoint']['checkpoint_id']}"
          f" | head={bundle['ledger_checkpoint']['ledger_head_sha256'][:8]}…")
    print("[s28-apr5] APR-0012..0016 登记完成（r5 批次；r1–r4 字节不动）| "
          "零门/零谓词翻动")


if __name__ == "__main__":
    main()
