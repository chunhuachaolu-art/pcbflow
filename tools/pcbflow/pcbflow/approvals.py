"""APPROVALS-1 人工批准登记（disposition 域；SPEC-v3.0-PROPOSAL §1.2/§1.4）。

2026-09-03 用户（human authority）对 v3.0 轨道五个挂起点 + 一项 TL-5 授权
下达「全部允许」。本模块把该人工决定按既有 ledger/disposition 机制登记：

- 每项批准 = 一条 disposition_record（kind=accept）+ 一条 ledger entry
  （entry_kind=disposition、authority=human、trust_level=untrusted——
  处置是决定不是事实，恒不可升级为 observed/verified）；
- 批准只落在 disposition 域，不改变任何机器门裁决语义：
  TL-3 physics_gate 仍 fail、TL-4-G 仍 blocked、TL-2 Critic 上岗仍
  not reached——validate_no_gate_write 对全部记录强制（无门写键）；
- 语义限定（人工处置与机器门的合取关系、不得自动 apply、旧 config
  immutable、批准 scope 绝不把门翻成 pass）逐条写入 rationale_text；
- evidence 指针=被批准冻结产物 sha256（collect_evidence_hashes 生成时
  从磁盘实读对账；缺文件 fail-closed 拒绝构造）。

生成器模式：纯函数、stdout canonical JSON、零子进程、零自身落盘、零网络；
无 wall-clock（APPROVAL_DATE 为人工声明常量，非机器时间）、无主机路径
（evidence 一律仓库相对 POSIX 路径）。批准只能被后续 supersedes 追加式
取代，不可回写。
"""

from __future__ import annotations

import json

from . import config, disposition, hashing, ledger, schemas

SCHEMA_VERSION = schemas.SCHEMA_V3

#: 人工批准日期（用户下达指示的声明日期；非机器 wall-clock）
APPROVAL_DATE = "2026-09-03"

#: 批准人（§1.2 权限矩阵：human 只写处置，无事实/门写权）
APPROVER = "user"
APPROVER_ROLE = "human_authority"

#: 批准账本快照标识（disposition 域独立账本，不与各链账本混写）
APPROVALS_REVISION = "v3-approvals-r1"

#: 批准账本 checkpoint 标识
CHECKPOINT_ID = "CKPT-V3-APPROVALS-R1"

#: evidence 逻辑名 → 仓库相对 POSIX 路径（磁盘实读；输出无主机路径）
EVIDENCE_FILES = (
    ("tl0_gate_record_smoke_2l", "out/v3-tl0/gate-record-smoke-2l.json"),
    ("tl0_gate_record_smoke_4l", "out/v3-tl0/gate-record-smoke-4l.json"),
    ("tl1_gate_record", "out/v3-tl1/gate-record.json"),
    ("tl1_decision_ledger", "out/v3-tl1/decision-ledger.jsonl"),
    ("tl3_gate_record", "out/v3-tl3/gate-record.json"),
    ("tl3_physics_report", "out/v3-tl3/physics-report.json"),
    ("smoke_4l_profile", "profiles/smoke-4l/profile.json"),
    ("tl4_proposal_patch_smoke_2l", "out/v3-tl4/proposal-patch-smoke-2l.json"),
    ("tl4_proposal_patch_smoke_4l", "out/v3-tl4/proposal-patch-smoke-4l.json"),
    ("tl4_gate_record_smoke_2l", "out/v3-tl4/gate-record-smoke-2l.json"),
    ("tl4_gate_record_smoke_4l", "out/v3-tl4/gate-record-smoke-4l.json"),
    ("tl4_baseline_config_smoke_2l",
     "profiles/smoke-2l/inputs/baseline-config.json"),
    ("tl4_baseline_config_smoke_4l",
     "profiles/smoke-4l/inputs/baseline-config.json"),
    ("critic_module", "pcbflow/critic.py"),
    ("spec_v3_proposal", "SPEC-v3.0-PROPOSAL.md"),
)

#: TL-1 批准对象附加绑定的 schema 基线（生成时从注册表实算 schema_hash；
#: 即「现行 schema v3.0 合同=被批准基线」的机器可复核表达）
SCHEMA_BASELINE = ("decision_ledger_entry", "disposition_record",
                   "gate_record")

#: 六项批准定义（数据即账：语义限定逐条对应人工指示原文）
APPROVAL_SPECS = (
    {
        "approval_id": "APR-0001",
        "entry_id": "APR-E-0001",
        "slug": "tl0-gate-scope",
        "subject": "TL-0 基座范围确认：tl0 gate 范围=两个非 Rev-C smoke "
                   "profile 可替换 manifest + 负向四类（stale/path/lease/"
                   "transaction），维持现有门定义不变",
        "kind": "accept",
        "scope": "checker",
        "rationale_code": "tl0_gate_scope_confirmed",
        "rationale_text": "用户人工批准 @2026-09-03：TL-0 基座范围确认——"
            "tl0 gate 范围=两个 smoke profile（smoke-2l/smoke-4l）可替换 "
            "manifest 运行 + 负向四类（stale/path/lease/transaction），"
            "维持现有门定义不变。语义限定：本批准仅确认门范围定义"
            "（disposition 域），不构成新增机器门裁决、不构成产品化声明；"
            "TL-0-G1 机器 pass 裁决独立于本处置，重跑门以机器谓词为准。",
        "fact_refs": ["TL-0-G1", "negative_tests_covered",
                      "second_profile_distinct"],
        "evidence": ("tl0_gate_record_smoke_2l", "tl0_gate_record_smoke_4l"),
    },
    {
        "approval_id": "APR-0002",
        "entry_id": "APR-E-0002",
        "slug": "tl1-schema-baseline",
        "subject": "TL-1 ledger/gate schema 批准：现行 schema v3.0 合同"
                   "（decision_ledger_entry/disposition_record/gate_record"
                   " 注册表）即被批准基线",
        "kind": "accept",
        "scope": "checker",
        "rationale_code": "tl1_schema_v3_baseline_approved",
        "rationale_text": "用户人工批准 @2026-09-03：TL-1 ledger/gate "
            "schema 批准——现行 schema v3.0 合同即被批准基线（本条 "
            "artifact_hashes 绑定生成时注册表 schema_hash，机器可复核）。"
            "语义限定：批准的是 schema 合同基线；后续 schema 演进只能走"
            "追加式（新版本+supersedes），不得回写本批准或既有冻结产物；"
            "TL-1-G1 机器 pass 裁决独立于本处置。",
        "fact_refs": ["TL-1-G1", "ledger_chain_valid",
                      "trust_policy_enforced"],
        "evidence": ("tl1_gate_record", "tl1_decision_ledger",
                     "schema_decision_ledger_entry",
                     "schema_disposition_record", "schema_gate_record"),
    },
    {
        "approval_id": "APR-0003",
        "entry_id": "APR-E-0003",
        "slug": "tl3-required-scope",
        "subject": "TL-3 required scope 批准：smoke-4l 的 "
                   "physics_required=[\"PHY-IMP-1\"] 范围声明",
        "kind": "accept",
        "scope": "physics",
        "rationale_code": "tl3_required_scope_approved",
        "rationale_text": "用户人工批准 @2026-09-03：TL-3 required scope——"
            "smoke-4l 的 physics_required=[\"PHY-IMP-1\"] 范围声明获批准。"
            "语义限定：本批准只解除 required_scope_approved 谓词的人工"
            "挂起；physics_gate 仍因 uncertainty_fail/no_approval/"
            "authority 级差而 fail——这是真实缺口（需 TD7 外部执行链"
            "产出更高 authority 证据），批准 scope 绝不能把门翻成 pass；"
            "out/v3-tl3/ 冻结产物不回写，重跑门裁决以机器谓词为准。",
        "fact_refs": ["PHY-IMP-1", "TL-3-G1", "required_scope_approved"],
        "evidence": ("tl3_gate_record", "tl3_physics_report",
                     "smoke_4l_profile"),
    },
    {
        "approval_id": "APR-0004",
        "entry_id": "APR-E-0004",
        "slug": "tl4-adoption-disposition",
        "subject": "TL-4 patch/config adoption 人工处置：两个 profile 的 "
                   "proposal-patch 记 human disposition=approved",
        "kind": "accept",
        "scope": "adoption",
        "rationale_code": "tl4_adoption_human_disposition_approved",
        "rationale_text": "用户人工批准 @2026-09-03：TL-4 patch/config "
            "adoption 人工处置——两个 profile 的 proposal-patch"
            "（PP-SS-SMOKE2L-R1-CAND-0001、PP-SS-SMOKE4L-R1-CAND-0008）"
            "记 human disposition=approved（human 意愿在案）。语义限定："
            "adoption 整体仍被机器谓词挡住（holdout_non_regression_"
            "evidenced 缺 TL-5、judge_post_ok=false）——人工处置与机器门"
            "是合取关系，本批准后状态=human_approved_machine_blocked；"
            "不得自动 apply、不得改 baseline config、旧 config 保持 "
            "immutable；TL-4-G 机器 blocked 裁决不变。",
        "fact_refs": ["PP-SS-SMOKE2L-R1-CAND-0001",
                      "PP-SS-SMOKE4L-R1-CAND-0008", "TL-4-G"],
        "evidence": ("tl4_proposal_patch_smoke_2l",
                     "tl4_proposal_patch_smoke_4l",
                     "tl4_gate_record_smoke_2l", "tl4_gate_record_smoke_4l",
                     "tl4_baseline_config_smoke_2l",
                     "tl4_baseline_config_smoke_4l"),
    },
    {
        "approval_id": "APR-0005",
        "entry_id": "APR-E-0005",
        "slug": "critic-duty-level",
        "subject": "Critic 上岗等级裁决：批准以最小等级上岗（advisory_only、"
                   "fail-closed 分诊、不得形成任何 authority 结论）",
        "kind": "accept",
        "scope": "checker",
        "rationale_code": "critic_duty_level_minimal_advisory",
        "rationale_text": "用户人工批准 @2026-09-03：Critic 上岗等级裁决——"
            "批准以最小等级上岗：advisory_only、fail-closed 分诊、不得"
            "形成任何 authority 结论。语义限定：当前无模型接入，本批准"
            "生效但「上岗」仍 not reached（如实记录）；critic 任何输出"
            "恒 untrusted，不得进入 gate 谓词或板写路径。",
        "fact_refs": ["TL-2", "critic_duty_level"],
        "evidence": ("critic_module",),
    },
    {
        "approval_id": "APR-0006",
        "entry_id": "APR-E-0006",
        "slug": "tl5-corpus-authorization",
        "subject": "TL-5 语料获取授权：外部语料源研究、许可审查与获取"
                   "（读网络/下载允许，仅限语料获取用途）",
        "kind": "accept",
        "scope": "corpus",
        "rationale_code": "tl5_corpus_acquisition_authorized",
        "rationale_text": "用户人工授权 @2026-09-03：TL-5 语料获取授权——"
            "授权开展外部语料源研究、许可审查与获取（读网络/下载允许，"
            "仅限语料获取用途）。语义限定：仅处置域授权，不改变 TL-5 门"
            "未启动状态；获取的语料入账须走 license/provenance/split/"
            "leakage 审计（TL-5 门），授权本身不预支任何门结论。",
        "fact_refs": ["TL-5", "corpus_acquisition"],
        "evidence": ("spec_v3_proposal",),
    },
)

#: 登记不变量说明（随 bundle 归档；字符串仅描述冻结状态，非门写）
FROZEN_MACHINE_GATE_STATUS = (
    "本登记不重算、不改写任何机器门：TL-3-G1 physics_gate=fail（保持）、"
    "TL-4-G=blocked（保持）、TL-2 Critic 上岗=not reached（保持）。"
    "批准只落在 disposition 域（L6 事实/处置/门分离）；人工处置与机器"
    "谓词是合取关系，不构成 waiver（kind=accept 非 waive，机器门缺口"
    "不得由豁免绕过）。"
)


def collect_evidence_hashes(root=".") -> tuple:
    """从磁盘实读 evidence 文件 sha256（只读、零落盘）。

    返回 (hashes, errors)：逻辑名 → sha256；任一文件缺失即记入 errors
    （fail-closed：调用方见错即拒绝构造批准）。root 仅用于拼出磁盘路径，
    不进入任何产物。
    """
    import os

    hashes: dict = {}
    errors: list = []
    for name, relpath in EVIDENCE_FILES:
        path = os.path.join(root, *relpath.split("/"))
        if not os.path.isfile(path):
            errors.append(f"evidence {name!r} 文件缺失: {relpath}")
        else:
            hashes[name] = hashing.sha256_file(path)
    return hashes, errors


def schema_baseline_hashes() -> dict:
    """从注册表实算 schema 基线 hash（逻辑名 schema_<name>）。"""
    return {"schema_" + name: schemas.schema_hash(name)
            for name in SCHEMA_BASELINE}


def disposition_filename(spec: dict) -> str:
    """批准处置记录落盘文件名（out/v3-approvals/ 编排口径）。"""
    return f"disposition-{spec['approval_id']}-{spec['slug']}.json"


def build_approvals_bundle(evidence_hashes: dict) -> dict:
    """构造六项人工批准的完整登记 bundle（纯函数；同输入 byte-exact）。

    evidence_hashes 必须覆盖 EVIDENCE_FILES 全部逻辑名（缺一 fail-closed
    ValueError）；schema 基线 hash 由注册表实算（不取自入参，防伪造）。
    每条 ledger entry：entry_kind=disposition、authority=human、
    trust_level=untrusted（verify_chain 白名单强制）、payload_ref=处置
    记录 canonical 落盘字节的 sha256、artifact_hashes=被批准冻结产物。
    """
    missing = [name for name, _ in EVIDENCE_FILES
               if not evidence_hashes.get(name)]
    if missing:
        raise ValueError(
            f"evidence 缺失（fail-closed 拒绝构造批准）: {missing}")
    hashes = dict(evidence_hashes)
    hashes.update(schema_baseline_hashes())

    dispositions: list = []
    entries: list = []
    gate_write_scan: dict = {}
    for spec in APPROVAL_SPECS:
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
            snapshot_revision=APPROVALS_REVISION))

    bundle = {
        "schema_version": SCHEMA_VERSION,
        "approval_date": APPROVAL_DATE,
        "approver": {"actor": APPROVER, "actor_role": APPROVER_ROLE},
        "revision": APPROVALS_REVISION,
        "approval_count": len(APPROVAL_SPECS),
        "dispositions": dispositions,
        "ledger_entries": entries,
        "ledger_file_sha256": _ledger_bytes_sha256(entries),
        "ledger_verify": {
            "chain_errors": ledger.verify_chain(entries),
            "supersedes_errors": ledger.verify_supersedes(entries),
        },
        "ledger_checkpoint": ledger.make_checkpoint(entries, CHECKPOINT_ID),
        "gate_write_scan": gate_write_scan,
        "evidence_registry": [
            {"name": name, "path": path, "sha256": hashes[name]}
            for name, path in EVIDENCE_FILES
        ] + [
            {"name": "schema_" + name,
             "path": f"schemas.py:registry:{name}",
             "sha256": hashes["schema_" + name]}
            for name in SCHEMA_BASELINE
        ],
        "disposition_files": {spec["approval_id"]:
                              disposition_filename(spec)
                              for spec in APPROVAL_SPECS},
        "frozen_machine_gate_status": FROZEN_MACHINE_GATE_STATUS,
        "notes": [
            "六项人工批准（2026-09-03「全部允许」）：TL-0 范围确认、TL-1 "
            "schema 基线、TL-3 required scope、TL-4 adoption 人工处置、"
            "Critic 最小上岗等级、TL-5 语料获取授权。",
            "批准不改机器门裁决语义；与机器谓词合取（见各 rationale_text "
            "语义限定）；本账本为 disposition 域独立账本，不改写既有 "
            "out/v3-tl0|tl1|tl3|tl4 冻结产物。",
            "批准日期为人工声明常量（非机器 wall-clock）；evidence hash "
            "为生成时磁盘实读值，可用 sha256sum 对 out/ 内文件复核。",
        ],
    }
    return bundle


def _ledger_bytes_sha256(entries) -> str:
    """账本文件字节 hash（与 out/v3-tl1|tl3|tl4 既有口径一致）。"""
    return hashing.sha256_bytes(ledger_file_bytes(entries))


def ledger_file_bytes(entries) -> bytes:
    """账本落盘字节（编排侧写 decision-ledger.jsonl 的唯一口径）。"""
    return hashing.jsonl_bytes(entries)  # REPAIR-P3 W-4 正身收编（等价验证在案）
