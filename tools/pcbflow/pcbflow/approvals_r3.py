"""APPROVALS-R3 人工批准/处置登记第三批（S20；disposition 域；与
approvals_r2.py 同构模式）。

2026-09-05 用户（human authority）人工决策登记：

- APR-0010：ITEM-run-r2 处置——12 条旗标（天线出界/端子贴边/JLC 占位
  丝印/拼板缝等观察，其中 5 条 abstain）全量作为 advisory 登记入处置
  台账并关闭队列项；语料板只读，处置≠改板。

同构不变量（与 approvals.py/approvals_r2.py 逐字同模式）：
- 每项批准 = 一条 disposition_record（kind=accept）+ 一条 ledger entry
  （entry_kind=disposition、authority=human、trust_level=untrusted——
  处置是决定不是事实，恒不可升级为 observed/verified）；
- 批准只落在 disposition 域，不改变任何机器门裁决语义：
  validate_no_gate_write 对全部记录强制（无门写键）；处置≠改板、
  登记≠校准达标、critic 输出恒 untrusted，逐条写入 rationale_text；
- evidence 指针=被登记事实的冻结产物 sha256（collect_evidence_hashes
  生成时从磁盘实读对账；缺文件 fail-closed 拒绝构造）；
  queue-event-ledger 绑定的是**追加后**账本字节（含 QE-000001/QE-000002
  关闭事件）；
- 批准日期=人工声明常量 APPROVAL_DATE_R3="2026-09-05"（非机器
  wall-clock）；evidence 一律仓库相对 POSIX 路径（无主机路径）；
  批准只能被后续 supersedes 追加式取代，不可回写；r1/r2 批次登记文件
  字节不动（本批全部为新文件）。

生成器模式：纯函数（collect_evidence_hashes 只读磁盘）、stdout canonical
JSON、零子进程、零自身落盘、零网络。
"""

from __future__ import annotations

import json

from . import config, disposition, hashing, ledger, schemas

SCHEMA_VERSION = schemas.SCHEMA_V3

#: 人工批准日期（用户下达指示的声明日期；非机器 wall-clock）
APPROVAL_DATE_R3 = "2026-09-05"

#: 批准人（§1.2 权限矩阵：human 只写处置，无事实/门写权）
APPROVER = "user"
APPROVER_ROLE = "human_authority"

#: 批准账本快照标识（disposition 域独立账本第三批，不与 r1/r2 混写）
APPROVALS_REVISION_R3 = "v3-approvals-r3"

#: 批准账本 checkpoint 标识
CHECKPOINT_ID_R3 = "CKPT-V3-APPROVALS-R3"

#: evidence 逻辑名 → 仓库相对 POSIX 路径（磁盘实读；输出无主机路径）
EVIDENCE_FILES_R3 = (
    ("run_r2_raw_flags",
     "out/v3-tl2/critic-runs/run-r2/raw-flags.json"),
    ("run_r2_record",
     "out/v3-tl2/critic-runs/run-r2/critic-run-record-CR-run-r2.json"),
    ("run_r2_queue_ledger",
     "out/v3-tl2/critic-runs/run-r2/queue-event-ledger.jsonl"),
)

#: 一项处置定义（数据即账：语义限定逐条对应 2026-09-05 人工指示原文）
APPROVAL_SPECS_R3 = (
    {
        "approval_id": "APR-0010",
        "entry_id": "APR-E-0010",
        "slug": "item-run-r2-disposition",
        "subject": "ITEM-run-r2 处置：12 条 flag 全量作为 advisory 登记"
                   "入处置台账并关闭队列项（其中 5 条 abstain；语料板"
                   "只读，处置≠改板）",
        "kind": "accept",
        "scope": "checker",
        "rationale_code": "item_run_r2_flags_advisory_dispositioned",
        "rationale_text": "用户人工处置 @2026-09-05：ITEM-run-r2 的 "
            "12 条旗标（data-manager：丝印密集/贴靠 1 条+U1 天线出界 "
            "1 条+J2/J4/J5 端子贴边 1 条+suspicious_reroute 已 abstain "
            "1 条；flatpack2：JA1/JB1 存疑已 abstain 1 条+器件贴边 "
            "1 条+JLC 占位丝印 1 条；karabas-nano-reva：拼板缝存疑已 "
            "abstain 1 条+3D 模型缺失存疑已 abstain 1 条+键盘第四行"
            "字符缺失存疑已 abstain 1 条；karabas-nano-wifi：U1 天线"
            "出界 1 条+logo 丝印压特征 1 条）全量作为 advisory 登记"
            "入处置台账并关闭队列项（其中 5 条 abstain 如实单列；"
            "QE-000001 assign / QE-000002 "
            "approve，approve 以人工裁决角色 human_final 入账、"
            "reason_code=item_dispositioned_apr_0010 引用本条）。"
            "语义限定：语料板只读，处置≠改板——本批准不构成任何改板"
            "指令或板写授权；critic 输出恒 untrusted，不进 gate 谓词"
            "或板写路径；「无旗」语义与自动分流仍由管线把守（校准"
            "未正式建立，critic_calibration_in_range 谓词语义不变）；"
            "本处置只落 disposition 域，不改变任何机器门裁决语义。",
        "fact_refs": ["ITEM-run-r2", "CR-run-r2", "critic_flags_advisory"],
        "evidence": ("run_r2_raw_flags", "run_r2_record",
                     "run_r2_queue_ledger"),
    },
)

#: 登记不变量说明（随 bundle 归档；字符串仅描述冻结状态，非门写）
FROZEN_MACHINE_GATE_STATUS_R3 = (
    "本登记不重算、不改写任何机器门：TL-2 critic 分诊谓词（含 "
    "critic_calibration_in_range）语义不变、fail-closed 路由不变；"
    "TL-3-G1/TL-4-G 既有裁决不变；TL-6 readiness 投影不回写。本项处置"
    "只落 disposition 域（L6 事实/处置/门分离）：处置≠改板、12 旗 "
    "advisory 登记不构成任何质量结论或门输入。queue-event-ledger 追加"
    "为 append-only（既有行字节不动），approve 事件以人工裁决角色 "
    "human_final 入账。"
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
    for name, relpath in EVIDENCE_FILES_R3:
        path = os.path.join(root, *relpath.split("/"))
        if not os.path.isfile(path):
            errors.append(f"evidence {name!r} 文件缺失: {relpath}")
        else:
            hashes[name] = hashing.sha256_file(path)
    return hashes, errors


def disposition_filename(spec: dict) -> str:
    """批准处置记录落盘文件名（out/v3-approvals/ 编排口径）。"""
    return f"disposition-{spec['approval_id']}-{spec['slug']}.json"


def build_approvals_bundle_r3(evidence_hashes: dict) -> dict:
    """构造人工处置的完整登记 bundle（纯函数；同输入 byte-exact）。

    evidence_hashes 必须覆盖 EVIDENCE_FILES_R3 全部逻辑名（缺一
    fail-closed ValueError）。每条 ledger entry：entry_kind=disposition、
    authority=human、trust_level=untrusted（verify_chain 白名单强制）、
    payload_ref=处置记录 canonical 落盘字节的 sha256、
    artifact_hashes=被登记事实的冻结产物（queue-event-ledger=追加后
    字节实测）。
    """
    missing = [name for name, _ in EVIDENCE_FILES_R3
               if not evidence_hashes.get(name)]
    if missing:
        raise ValueError(
            f"evidence 缺失（fail-closed 拒绝构造批准）: {missing}")
    hashes = dict(evidence_hashes)

    dispositions: list = []
    entries: list = []
    gate_write_scan: dict = {}
    for spec in APPROVAL_SPECS_R3:
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
            snapshot_revision=APPROVALS_REVISION_R3))

    bundle = {
        "schema_version": SCHEMA_VERSION,
        "approval_date": APPROVAL_DATE_R3,
        "approver": {"actor": APPROVER, "actor_role": APPROVER_ROLE},
        "revision": APPROVALS_REVISION_R3,
        "approval_count": len(APPROVAL_SPECS_R3),
        "supersedes_note": (
            "r3 为追加批次：不取代、不改写 r1（APR-0001–0006）与 "
            "r2（APR-0007–0009）；out/v3-approvals/ 既有 r1/r2 文件"
            "字节不动。"),
        "dispositions": dispositions,
        "ledger_entries": entries,
        "ledger_file_sha256": _ledger_bytes_sha256(entries),
        "ledger_verify": {
            "chain_errors": ledger.verify_chain(entries),
            "supersedes_errors": ledger.verify_supersedes(entries),
        },
        "ledger_checkpoint": ledger.make_checkpoint(entries,
                                                   CHECKPOINT_ID_R3),
        "gate_write_scan": gate_write_scan,
        "evidence_registry": [
            {"name": name, "path": path, "sha256": hashes[name]}
            for name, path in EVIDENCE_FILES_R3
        ],
        "disposition_files": {spec["approval_id"]:
                              disposition_filename(spec)
                              for spec in APPROVAL_SPECS_R3},
        "frozen_machine_gate_status": FROZEN_MACHINE_GATE_STATUS_R3,
        "notes": [
            "一项人工处置（2026-09-05）：ITEM-run-r2 十二旗全 advisory "
            "登记并关闭队列项（APR-0010，其中 5 条 abstain 如实单列）。",
            "处置不改机器门裁决语义（见 rationale_text 语义限定与 "
            "frozen_machine_gate_status）；本账本为 disposition 域独立"
            "账本 r3 批次，不改写既有 out/v3-approvals/ r1/r2 文件与"
            "任何 out/ 冻结产物；queue-event-ledger 证据为追加后字节"
            "实测（含关闭事件）。",
            "批准日期为人工声明常量（非机器 wall-clock）；evidence hash "
            "为生成时磁盘实读值，可用 sha256sum 对 out/ 内文件复核。",
        ],
    }
    return bundle


def _ledger_bytes_sha256(entries) -> str:
    """账本文件字节 hash（与 out/v3-tl1|tl3|tl4 既有口径一致）。"""
    return hashing.sha256_bytes(ledger_file_bytes(entries))


def ledger_file_bytes(entries) -> bytes:
    """账本落盘字节（编排侧写 decision-ledger-r3.jsonl 的唯一口径）。"""
    return hashing.jsonl_bytes(entries)  # REPAIR-P3 W-4 正身收编（等价验证在案）
