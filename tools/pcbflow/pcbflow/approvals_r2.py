"""APPROVALS-R2 人工批准登记第二批（S17；disposition 域；与 approvals.py
同构模式）。

2026-09-05 用户（human authority）三项人工决策登记：

- APR-0007：ITEM-run-r1 处置——7 条 flag 全部作为 advisory 登记入处置
  台账并关闭队列项；语料板只读，处置≠改板；
- APR-0008：Critic 校准域建设方案批准——用 Rev-C 判例做种子（ASM 链
  已确证的缺陷与处置做人工标注 ground truth，先建小而可信的标注集）；
- APR-0009：VERIFICATION-ROADMAP Tier 1+2 全部批准立项（硬前置不豁免、
  Tier 2 不提前开跑）。

同构不变量（与 approvals.py 逐字同模式）：
- 每项批准 = 一条 disposition_record（kind=accept）+ 一条 ledger entry
  （entry_kind=disposition、authority=human、trust_level=untrusted——
  处置是决定不是事实，恒不可升级为 observed/verified）；
- 批准只落在 disposition 域，不改变任何机器门裁决语义：
  validate_no_gate_write 对全部记录强制（无门写键）；批准≠校准达标、
  批准≠门翻转、处置≠改板，逐条写入 rationale_text；
- evidence 指针=被批准/被登记事实的冻结产物 sha256
  （collect_evidence_hashes 生成时从磁盘实读对账；缺文件 fail-closed
  拒绝构造）；queue-event-ledger 绑定的是**追加后**账本字节（含
  QE-000001/QE-000002 关闭事件）；
- 批准日期=人工声明常量 APPROVAL_DATE_R2="2026-09-05"（非机器
  wall-clock）；evidence 一律仓库相对 POSIX 路径（无主机路径）；
  批准只能被后续 supersedes 追加式取代，不可回写；r1 登记文件字节不动
  （本批全部为新文件）。

生成器模式：纯函数（collect_evidence_hashes 只读磁盘）、stdout canonical
JSON、零子进程、零自身落盘、零网络。
"""

from __future__ import annotations

import json

from . import config, disposition, hashing, ledger, schemas

SCHEMA_VERSION = schemas.SCHEMA_V3

#: 人工批准日期（用户下达指示的声明日期；非机器 wall-clock）
APPROVAL_DATE_R2 = "2026-09-05"

#: 批准人（§1.2 权限矩阵：human 只写处置，无事实/门写权）
APPROVER = "user"
APPROVER_ROLE = "human_authority"

#: 批准账本快照标识（disposition 域独立账本第二批，不与 r1 混写）
APPROVALS_REVISION_R2 = "v3-approvals-r2"

#: 批准账本 checkpoint 标识
CHECKPOINT_ID_R2 = "CKPT-V3-APPROVALS-R2"

#: evidence 逻辑名 → 仓库相对 POSIX 路径（磁盘实读；输出无主机路径）
EVIDENCE_FILES_R2 = (
    ("run_r1_raw_flags",
     "out/v3-tl2/critic-runs/run-r1/raw-flags.json"),
    ("run_r1_record",
     "out/v3-tl2/critic-runs/run-r1/critic-run-record-CR-run-r1.json"),
    ("run_r1_queue_ledger",
     "out/v3-tl2/critic-runs/run-r1/queue-event-ledger.jsonl"),
    ("calibration_domain_manifest",
     "out/v3-tl2/calibration/calibration-domain-v1.json"),
    ("calibration_ground_truth",
     "out/v3-tl2/calibration/ground-truth-v1.json"),
    ("critic_run_module", "pcbflow/critic_run.py"),
    ("verification_roadmap", "VERIFICATION-ROADMAP.md"),
)

#: 三项批准定义（数据即账：语义限定逐条对应 2026-09-05 人工指示原文）
APPROVAL_SPECS_R2 = (
    {
        "approval_id": "APR-0007",
        "entry_id": "APR-E-0007",
        "slug": "item-run-r1-disposition",
        "subject": "ITEM-run-r1 处置：7 条 flag 全部作为 advisory 登记"
                   "入处置台账并关闭队列项（语料板只读，处置≠改板）",
        "kind": "accept",
        "scope": "checker",
        "rationale_code": "item_run_r1_flags_advisory_dispositioned",
        "rationale_text": "用户人工处置 @2026-09-05：ITEM-run-r1 的 "
            "7 条 flag（launchxl 3 条丝印可读性叠字+1 条底铜覆盖 "
            "other_advisory；bm11 2 条丝印可读性叠字+1 条排针跨度异常"
            "已 abstain）全部作为 advisory 登记入处置台账并关闭队列项"
            "（QE-000001 assign / QE-000002 approve，approve 以人工"
            "裁决角色 human_final 入账）。语义限定：语料板只读，处置"
            "≠改板——本批准不构成任何改板指令或板写授权；critic 输出"
            "恒 untrusted，不进 gate 谓词或板写路径；「无旗」语义仍由"
            "管线把守（校准域未建立，自动分流仍恒 blocked）；本处置只"
            "落 disposition 域，不改变任何机器门裁决语义。",
        "fact_refs": ["ITEM-run-r1", "CR-run-r1", "critic_flags_advisory"],
        "evidence": ("run_r1_raw_flags", "run_r1_record",
                     "run_r1_queue_ledger"),
    },
    {
        "approval_id": "APR-0008",
        "entry_id": "APR-E-0008",
        "slug": "calibration-domain-seed",
        "subject": "Critic 校准域建设方案批准：用 Rev-C 判例做种子"
                   "（calibration-domain-v1 人工标注 ground truth）",
        "kind": "accept",
        "scope": "checker",
        "rationale_code": "calibration_domain_seed_rev_c_approved",
        "rationale_text": "用户人工批准 @2026-09-05：Critic 校准域建设"
            "方案——用 Rev-C 判例做种子，用 ASM 链已确证的缺陷与处置做"
            "人工标注 ground truth（calibration-domain-v1：4 判例簇，"
            "从 pose-revision-proof 等冻结证据确定性提取，R4/F1 簇映射"
            "放置类、L1 簇按缺陷性质诚实映射），先建小而可信的标注集。"
            "语义限定：方案批准≠校准达标——critic_calibration_in_range"
            " 谓词语义不变，校准域未正式建立前 bundle 声明 "
            "domain_established 仍为 False、in_calibrated_range 恒 "
            "False、flags=[] 一律 blocked（fail-closed）；比较器是 "
            "advisory 侧分析不是门；GT 标注属 pipeline 侧不混入 reader "
            "视野；critic 输出恒 untrusted。本批准的证据之一 "
            "critic-run-record-CR-run-r1.json 即 critic_calibration_"
            "in_range 现状 fail（failed_conditions 在案）的实况记录。",
        "fact_refs": ["calibration-domain-v1",
                      "critic_calibration_in_range", "CR-run-r1"],
        "evidence": ("calibration_domain_manifest",
                     "calibration_ground_truth", "critic_run_module",
                     "run_r1_record"),
    },
    {
        "approval_id": "APR-0009",
        "entry_id": "APR-E-0009",
        "slug": "verification-roadmap-tiers",
        "subject": "VERIFICATION-ROADMAP Tier 1+2 全部批准立项"
                   "（硬前置不豁免、Tier 2 不提前开跑）",
        "kind": "accept",
        "scope": "constraint",
        "rationale_code": "verification_roadmap_tier1_tier2_approved",
        "rationale_text": "用户人工批准 @2026-09-05：VERIFICATION-ROADMAP"
            ".md 两层次工程验证路线图 Tier 1（V1-a/V1-b/V1-c）与 "
            "Tier 2（V2-a…V2-d）全部批准立项（两级都立项；V1-c 维持"
            "「可选、低优先级」定位）。语义限定：硬前置（物理实证）"
            "不受批准影响——布线引擎决策或等效外部后端（BL-1）与 TL-3 "
            "真实物理证据链（BL-2）未齐备前，层次二不启动、Tier 2 不"
            "提前开跑，V2-c 试产仍须届时用户对预算/数量的显式投产裁决；"
            "批准不构成任何机器门翻转——不改写任何门谓词与既有门记录，"
            "「生产正文工具生成资格」仍以 Tier 2 出口门为准（L7 缺证据"
            "闭门律，不预支 signoff）。",
        "fact_refs": ["VERIFICATION-ROADMAP", "tier1", "tier2"],
        "evidence": ("verification_roadmap",),
    },
)

#: 登记不变量说明（随 bundle 归档；字符串仅描述冻结状态，非门写）
FROZEN_MACHINE_GATE_STATUS_R2 = (
    "本登记不重算、不改写任何机器门：TL-2 critic 分诊谓词（含 "
    "critic_calibration_in_range）语义不变、fail-closed 路由不变；"
    "TL-3-G1/TL-4-G 既有裁决不变；TL-6 readiness 投影不回写。三项批准"
    "只落 disposition 域（L6 事实/处置/门分离）：处置≠改板、方案批准"
    "≠校准达标、路线图批准≠门翻转（机器谓词缺口不得由豁免绕过）。"
    "queue-event-ledger 追加为 append-only（既有行字节不动），approve"
    " 事件以人工裁决角色 human_final 入账。"
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
    for name, relpath in EVIDENCE_FILES_R2:
        path = os.path.join(root, *relpath.split("/"))
        if not os.path.isfile(path):
            errors.append(f"evidence {name!r} 文件缺失: {relpath}")
        else:
            hashes[name] = hashing.sha256_file(path)
    return hashes, errors


def disposition_filename(spec: dict) -> str:
    """批准处置记录落盘文件名（out/v3-approvals/ 编排口径）。"""
    return f"disposition-{spec['approval_id']}-{spec['slug']}.json"


def build_approvals_bundle_r2(evidence_hashes: dict) -> dict:
    """构造三项人工批准的完整登记 bundle（纯函数；同输入 byte-exact）。

    evidence_hashes 必须覆盖 EVIDENCE_FILES_R2 全部逻辑名（缺一
    fail-closed ValueError）。每条 ledger entry：entry_kind=disposition、
    authority=human、trust_level=untrusted（verify_chain 白名单强制）、
    payload_ref=处置记录 canonical 落盘字节的 sha256、
    artifact_hashes=被批准/被登记事实的冻结产物。
    """
    missing = [name for name, _ in EVIDENCE_FILES_R2
               if not evidence_hashes.get(name)]
    if missing:
        raise ValueError(
            f"evidence 缺失（fail-closed 拒绝构造批准）: {missing}")
    hashes = dict(evidence_hashes)

    dispositions: list = []
    entries: list = []
    gate_write_scan: dict = {}
    for spec in APPROVAL_SPECS_R2:
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
            snapshot_revision=APPROVALS_REVISION_R2))

    bundle = {
        "schema_version": SCHEMA_VERSION,
        "approval_date": APPROVAL_DATE_R2,
        "approver": {"actor": APPROVER, "actor_role": APPROVER_ROLE},
        "revision": APPROVALS_REVISION_R2,
        "approval_count": len(APPROVAL_SPECS_R2),
        "supersedes_note": (
            "r2 为追加批次：不取代、不改写 r1（APR-0001–0006）；"
            "out/v3-approvals/ 既有 r1 文件字节不动。"),
        "dispositions": dispositions,
        "ledger_entries": entries,
        "ledger_file_sha256": _ledger_bytes_sha256(entries),
        "ledger_verify": {
            "chain_errors": ledger.verify_chain(entries),
            "supersedes_errors": ledger.verify_supersedes(entries),
        },
        "ledger_checkpoint": ledger.make_checkpoint(entries,
                                                   CHECKPOINT_ID_R2),
        "gate_write_scan": gate_write_scan,
        "evidence_registry": [
            {"name": name, "path": path, "sha256": hashes[name]}
            for name, path in EVIDENCE_FILES_R2
        ],
        "disposition_files": {spec["approval_id"]:
                              disposition_filename(spec)
                              for spec in APPROVAL_SPECS_R2},
        "frozen_machine_gate_status": FROZEN_MACHINE_GATE_STATUS_R2,
        "notes": [
            "三项人工批准/处置（2026-09-05）：ITEM-run-r1 七旗全 advisory"
            "登记并关闭队列项（APR-0007）、校准域 Rev-C 判例种子方案"
            "（APR-0008）、VERIFICATION-ROADMAP Tier 1+2 立项（APR-0009）。",
            "批准/处置不改机器门裁决语义（见各 rationale_text 语义限定与"
            " frozen_machine_gate_status）；本账本为 disposition 域独立"
            "账本 r2 批次，不改写既有 out/v3-approvals/ r1 文件与任何 "
            "out/ 冻结产物。",
            "批准日期为人工声明常量（非机器 wall-clock）；evidence hash "
            "为生成时磁盘实读值，可用 sha256sum 对 out/ 内文件复核。",
        ],
    }
    return bundle


def _ledger_bytes_sha256(entries) -> str:
    """账本文件字节 hash（与 out/v3-tl1|tl3|tl4 既有口径一致）。"""
    return hashing.sha256_bytes(ledger_file_bytes(entries))


def ledger_file_bytes(entries) -> bytes:
    """账本落盘字节（编排侧写 decision-ledger-r2.jsonl 的唯一口径）。"""
    return hashing.jsonl_bytes(entries)  # REPAIR-P3 W-4 正身收编（等价验证在案）
