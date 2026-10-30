"""S13-ARCHIVE TD7 线收档治理登记（disposition 域；approvals 机制复用）。

2026-09-04 用户（human authority）裁决「TD7 线收档并总结经验」。本模块把
该人工决定按 APPROVALS-1 同一 ledger/disposition 机制登记（独立账本
v3-archive-r1，落 out/v3-archive/ 新命名空间）：

- 四项收档处置 = 四条 disposition_record（kind=reject——schema enum 内唯一
  的关线语义；archived/not_adopted/closed_by_archive 决策词由
  decision_summary 与 rationale_code/text 承载）+ 四条 ledger entry
  （entry_kind=disposition、authority=human、trust_level=untrusted——
  处置是决定不是事实，恒不可升级为 observed/verified）；
- 收档只落在 disposition 域：不重算、不改写任何机器门与冻结产物
  （out/v3-td7/ 与 out/v3-td7/s12/ 全部只读保留）——TD7-QUAL-G 的 S11
  机器 pass 记录与 S12 judge 复评记录（judge_pre ok/judge_post fail）
  冻结不动；TL-4-G fail 维持、TL-3-G1 fail 维持、TL-2 not reached 维持
  （validate_no_gate_write 对全部记录强制）；
- 语义限定（收档不撤销既有资格证据、TD7-QUAL-G pass 自收档起仅为历史
  资格证据不得引用为现行能力、重开条件=新引擎版本/换 backend 须重走
  qualification、toolchain_lock.json 零改动、批门语义与 v2.4.1 调研
  随线关闭且不预支任何结论）逐条写入 rationale_text；
- evidence 指针=被引用产物磁盘实测 sha256（collect_evidence_hashes
  实读对账；缺文件 fail-closed 拒绝构造）。

生成器模式：纯函数、stdout canonical JSON、零子进程、零自身落盘、零网络；
无 wall-clock（ARCHIVE_DATE 为人工声明常量，非机器时间）、无主机路径
（evidence 一律仓库相对 POSIX 路径）。收档处置只能被后续 supersedes
追加式取代，不可回写。
"""

from __future__ import annotations

import json

from . import config, disposition, hashing, ledger, schemas

SCHEMA_VERSION = schemas.SCHEMA_V3

#: 收档裁决日期（用户下达指示的声明日期；非机器 wall-clock）
ARCHIVE_DATE = "2026-09-04"

#: 裁决人（§1.2 权限矩阵：human 只写处置，无事实/门写权）
ACTOR = "user"
ACTOR_ROLE = "human_authority"

#: 收档账本快照标识（disposition 域独立账本，不与各链账本混写）
ARCHIVE_REVISION = "v3-archive-r1"

#: 收档账本 checkpoint 标识
CHECKPOINT_ID = "CKPT-V3-ARCHIVE-R1"

#: 被引用资格结论的机器可核对常量（S11 定格、S12 未重开；编排侧与
#: out/v3-td7/gate-record-td7.json 实测 gate_core_hash 对账后才入账）
TD7_QUAL_GATE_CORE_HASH = (
    "40dccac4179e4bfdf352afcb19a913ddf4a74a71b31a23fff8d1740894ed591c")
TD7_QUAL_GATE_CORE_HASH16 = TD7_QUAL_GATE_CORE_HASH[:16]

#: toolchain_lock.json 收档时点零改动见证（受保护文件既有 hash 前缀；
#: 编排侧对实测 sha256 复核此前缀后才入账）
TOOLCHAIN_LOCK_SHA256_16 = "d43dad89c1559ff0"

#: evidence 逻辑名 → 仓库相对 POSIX 路径（磁盘实读；输出无主机路径）
EVIDENCE_FILES = (
    ("td7_gate_record", "out/v3-td7/gate-record-td7.json"),
    ("td7_qualification_report", "out/v3-td7/qualification-report.json"),
    ("td7_toolchain_registry", "out/v3-td7/toolchain-registry.json"),
    ("td7_toolchain_lock_proposal",
     "out/v3-td7/toolchain-lock-proposal.json"),
    ("td7_decision_ledger", "out/v3-td7/decision-ledger.json"),
    ("s12_quality_matrix", "out/v3-td7/s12/quality-matrix.json"),
    ("s12_ab_report", "out/v3-td7/s12/ab-report.json"),
    ("s12_dsn_rule_triangulation",
     "out/v3-td7/s12/dsn-rule-triangulation.json"),
    ("s12_decision_ledger", "out/v3-td7/s12/decision-ledger-s12.json"),
    ("s12_judge_records", "out/v3-td7/s12/judge-records-s12.json"),
    ("toolchain_lock", "toolchain_lock.json"),
)

#: 四项收档处置定义（数据即账：语义限定逐条对应用户裁决原文）
ARCHIVE_SPECS = (
    {
        "archive_id": "ARC-0001",
        "entry_id": "ARC-E-0001",
        "slug": "td7-line-archive",
        "decision": "archived",
        "subject": "TD7 外部执行线关线：freerouting CLI qualification 线"
                   "收档（archived）",
        "kind": "reject",
        "scope": "external",
        "rationale_code": "td7_line_archived",
        "rationale_text": "用户人工裁决 @2026-09-04：TD7 外部执行线收档"
            "（decision=archived）。入档依据（全部为冻结产物实测事实）："
            "TD7-QUAL-G 资格 pass（合同面四轴；gate core hash "
            "40dccac4179e4bfd…，S11 定格、S12 未重开）+S12 质量结论="
            "不可行（3 板×N=3 同参复评 9/9 次运行全部被验证链拒收："
            "severity-error 新增 launchxl [18,12,18]/emonth [61,61,61]/"
            "bm1 [109,110,113]，unconnected 1/7/46）+引擎能力边界证据"
            "（D20(d) 三角对账证伪——DSN 忠实携带类宽、SES 亚类宽线="
            "类宽×0.75 引擎减宽回退；D20(b') post-optimization 非确定性"
            "死锁；D20(b) nondeterministic）。语义限定：收档不撤销、不改写"
            "任何既有冻结产物与机器门记录（out/v3-td7/ 与 out/v3-td7/s12/ "
            "只读保留，hash 逐件绑定）；TD7-QUAL-G pass 自本处置起仅为"
            "历史资格证据，不得引用为现行外部执行/布线能力；TL-4 executor "
            "接入议题随之关闭。重开条件=新引擎版本（含 v2.4.1+）或更换 "
            "backend——重开须按新包重走 qualification（含减宽行为/死锁/"
            "非确定性复测），不得沿用本资格结论。",
        "fact_refs": ["TD7-QUAL-G", "TD7", "D20", "TL-4-G"],
        "evidence": ("td7_gate_record", "td7_qualification_report",
                     "s12_quality_matrix", "s12_ab_report",
                     "s12_dsn_rule_triangulation"),
    },
    {
        "archive_id": "ARC-0002",
        "entry_id": "ARC-E-0002",
        "slug": "toolchain-lock-proposal",
        "decision": "not_adopted",
        "subject": "TD7 toolchain_lock 锁定提案处置：not_adopted"
                   "（锁保持现状 optional/null，toolchain_lock.json 零改动）",
        "kind": "reject",
        "scope": "constraint",
        "rationale_code": "toolchain_lock_proposal_not_adopted",
        "rationale_text": "用户人工裁决 @2026-09-04：S11 toolchain_lock "
            "锁定提案（out/v3-td7/toolchain-lock-proposal.json，status="
            "proposed_not_executed）处置=not_adopted——TD7 线收档，不执行"
            "锁定。锁保持现状：toolchain_lock.json 零改动（本处置绑定其"
            "入账时点实测 sha256=d43dad89c1559ff0… 以证收档时零改动；"
            "freerouting/jdk 维持 optional/null、locked_when_called 语义"
            "不变）。语义限定：本处置不构成对 toolchain_lock.json 的任何"
            "写入或版本变更；若日后重开外部执行线并重新 qualification，"
            "锁定提案须按新证据重新生成与重新呈批，本提案不因重开而复活。",
        "fact_refs": ["TOOLCHAIN-LOCK", "TD7", "D20"],
        "evidence": ("td7_toolchain_lock_proposal", "toolchain_lock"),
    },
    {
        "archive_id": "ARC-0003",
        "entry_id": "ARC-E-0003",
        "slug": "d20-batch-gate-semantics",
        "decision": "closed_by_archive",
        "subject": "D20③ 批门语义挂账点处置：closed_by_archive（线收档，"
                   "不再议）",
        "kind": "reject",
        "scope": "adoption",
        "rationale_code": "d20_batch_gate_semantics_closed_by_archive",
        "rationale_text": "用户人工裁决 @2026-09-04：D20③ 批门语义挂账点"
            "（是否接受 severity-error 零新增门对 freerouting v2.3.0 输出"
            "恒不过=blocked 常态、或放宽该门——原定须用户另批）处置="
            "closed_by_archive：TD7 线收档，议题随之关闭、不再议。语义"
            "限定：现行机器门语义零改动（severity-error 零新增谓词保持"
            "原样——既未接受 blocked 常态化、也未放宽任何门）；TL-4 出口"
            "门 fail 维持。若日后以其他 backend 或新引擎版本重开外部执行"
            "线，批门语义须按该引擎实测重新呈批，本关闭不预支任何门语义"
            "结论。",
        "fact_refs": ["D20", "TD7", "TL-4-G"],
        "evidence": ("s12_quality_matrix", "s12_ab_report",
                     "td7_gate_record"),
    },
    {
        "archive_id": "ARC-0004",
        "entry_id": "ARC-E-0004",
        "slug": "freerouting-v241-upgrade",
        "decision": "closed_by_archive",
        "subject": "freerouting v2.4.1 升级调研挂账点处置："
                   "closed_by_archive（不追）",
        "kind": "reject",
        "scope": "external",
        "rationale_code": "freerouting_v241_upgrade_closed_by_archive",
        "rationale_text": "用户人工裁决 @2026-09-04：freerouting v2.4.1 "
            "升级调研挂账点处置=closed_by_archive：不追——TD7 线收档后"
            "升级调研不再开展。语义限定：本关闭不构成对 v2.4.1 的任何"
            "评估结论（未实测、无数据）；D20(c) 启动版本探测行为如实登记"
            "不变；已资格定格的引擎版本=v2.3.0（registry 实测 sha256 "
            "绑定）。若日后重开 TD7 线，换版本=新包重走 qualification"
            "+复评（含减宽行为、死锁、非确定性复测），届时调研作为候选"
            "路径重新立项。",
        "fact_refs": ["D20", "TD7"],
        "evidence": ("td7_toolchain_registry", "td7_gate_record"),
    },
)

#: 登记不变量说明（随 bundle 归档；字符串仅描述冻结状态，非门写）
FROZEN_MACHINE_GATE_STATUS = (
    "本登记不重算、不改写任何机器门或冻结产物：TD7-QUAL-G 的 S11 机器 "
    "pass 记录（judge_pre ok/judge_post fail 如实）与 S12 judge 复评记录"
    "冻结只读；TL-4-G fail（S9 v2 复评）维持、TL-3-G1 fail 维持、"
    "TL-2 Critic 上岗 not reached 维持。收档只落在 disposition 域"
    "（L6 事实/处置/门分离）；kind=reject 非 waive（无豁免语义，不解除"
    "任何机器谓词；人工处置与机器谓词恒为合取关系）。"
)


def collect_evidence_hashes(root=".") -> tuple:
    """从磁盘实读 evidence 文件 sha256（只读、零落盘）。

    返回 (hashes, errors)：逻辑名 → sha256；任一文件缺失即记入 errors
    （fail-closed：调用方见错即拒绝构造收档处置）。root 仅用于拼出磁盘
    路径，不进入任何产物。
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


def disposition_filename(spec: dict) -> str:
    """收档处置记录落盘文件名（out/v3-archive/ 编排口径）。"""
    return f"disposition-{spec['archive_id']}-{spec['slug']}.json"


def build_archive_bundle(evidence_hashes: dict) -> dict:
    """构造四项收档处置的完整登记 bundle（纯函数；同输入 byte-exact）。

    evidence_hashes 必须覆盖 EVIDENCE_FILES 全部逻辑名（缺一 fail-closed
    ValueError）。每条 ledger entry：entry_kind=disposition、authority=
    human、trust_level=untrusted（verify_chain 白名单强制）、payload_ref=
    处置记录 canonical 落盘字节的 sha256、artifact_hashes=被引用冻结
    产物实测 hash（对账后入账）。
    """
    missing = [name for name, _ in EVIDENCE_FILES
               if not evidence_hashes.get(name)]
    if missing:
        raise ValueError(
            f"evidence 缺失（fail-closed 拒绝构造收档处置）: {missing}")

    dispositions: list = []
    entries: list = []
    gate_write_scan: dict = {}
    for spec in ARCHIVE_SPECS:
        record = disposition.build_disposition(
            disposition_id=spec["archive_id"],
            fact_refs=spec["fact_refs"],
            kind=spec["kind"],
            scope=spec["scope"],
            rationale_code=spec["rationale_code"],
            rationale_text=spec["rationale_text"],
            approver=ACTOR,
            approver_role=ACTOR_ROLE)
        scan = disposition.validate_no_gate_write(record)
        if scan:
            raise ValueError(f"{spec['archive_id']} 触发门写禁区: {scan}")
        gate_write_scan[spec["archive_id"]] = scan
        dispositions.append(record)
        entries, _ = ledger.append(entries, dict(
            entry_kind="disposition",
            schema_validation=ledger.make_schema_validation(
                "disposition_record"),
            authority="human",
            trust_level="untrusted",
            entry_id=spec["entry_id"],
            actor=ACTOR,
            actor_role=ACTOR_ROLE,
            disposition_refs=[spec["archive_id"]],
            payload_ref=hashing.sha256_bytes(
                hashing.canonical_json_bytes(record)),
            artifact_hashes={name: evidence_hashes[name]
                             for name in spec["evidence"]},
            snapshot_revision=ARCHIVE_REVISION))

    bundle = {
        "schema_version": SCHEMA_VERSION,
        "archive_date": ARCHIVE_DATE,
        "actor": {"actor": ACTOR, "actor_role": ACTOR_ROLE},
        "revision": ARCHIVE_REVISION,
        "disposition_count": len(ARCHIVE_SPECS),
        "decision_summary": {spec["archive_id"]: spec["decision"]
                             for spec in ARCHIVE_SPECS},
        "td7_qual_gate_core_hash": TD7_QUAL_GATE_CORE_HASH,
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
            {"name": name, "path": path, "sha256": evidence_hashes[name]}
            for name, path in EVIDENCE_FILES
        ],
        "disposition_files": {spec["archive_id"]:
                              disposition_filename(spec)
                              for spec in ARCHIVE_SPECS},
        "frozen_machine_gate_status": FROZEN_MACHINE_GATE_STATUS,
        "reopen_condition": (
            "新引擎版本（含 freerouting v2.4.1+）或更换 backend ⇒ 按新包"
            "重走 qualification（含减宽行为/死锁/非确定性复测），不得沿用"
            "TD7-QUAL-G 既有资格结论。"),
        "notes": [
            "四项收档处置（2026-09-04 用户裁决「TD7 线收档并总结经验」）："
            "TD7 线关线（archived）/toolchain_lock 提案（not_adopted）/"
            "D20③ 批门语义+freerouting v2.4.1 升级调研（closed_by_archive）。",
            "收档不撤销既有冻结产物：out/v3-td7/ 与 out/v3-td7/s12/ 全部"
            "只读保留；TD7-QUAL-G pass 自 2026-09-04 起仅为历史资格证据，"
            "不得引用为现行外部执行/布线能力（见 V3-MATRIX Evidence "
            "reality 收档边界句）。",
            "toolchain_lock.json 零改动（freerouting/jdk 维持 optional/"
            "null）；本账本为 disposition 域独立账本（v3-archive 命名空间），"
            "不改写 out/v3-td7|s12 与 out/v3-approvals 冻结产物。",
            "收档日期为人工声明常量（非机器 wall-clock）；evidence hash 为"
            "生成时磁盘实读值，可用 sha256sum 对 out/ 内文件复核。",
        ],
    }
    return bundle


def _ledger_bytes_sha256(entries) -> str:
    """账本文件字节 hash（与 out/v3-approvals 既有口径一致）。"""
    return hashing.sha256_bytes(ledger_file_bytes(entries))


def ledger_file_bytes(entries) -> bytes:
    """账本落盘字节（编排侧写 decision-ledger.jsonl 的唯一口径）。"""
    return hashing.jsonl_bytes(entries)  # REPAIR-P3 W-4 正身收编（等价验证在案）
