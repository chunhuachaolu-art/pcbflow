"""APPROVALS-R4 人工批准/处置登记第四批（R1 包；disposition 域；与
approvals_r3.py 同构模式）。

2026-09-06 用户（human authority）人工决策登记：

- APR-0011：校准达标线提案**暂时采纳**（provisional）——recall≥0.75 /
  precision（=度量 v3 的 seed_match_rate，口径同 process-v1 §5 的
  precision_vs_seed_gt）≥0.5 / abstain≤0.5 / 连续 2 轮 / GT≥12，作为
  critic_calibration_in_range 的评估基准。指示原文（2026-09-06）：
  「校准达标线提案暂时就按这个来，先继续做吧」。

语义红线（rationale_text 与 frozen_machine_gate_status 逐条强制）：
- 「暂时」=provisional：后续可被追加式 supersedes 取代，不构成永久承诺；
- 达标线=评估基准/开发检查点，**不是自动分流资格**：自动分流仍受
  BL-4（Critic 校准域+正式模型）与 TD5 分诊合取约束，恒 blocked；
- 当前两轮实测均未达标 → critic_calibration_in_range 实测评估仍
  False，本批准**不翻转**任何机器门与谓词；
- precision 项命名对账：process-v1 §5 提案的 precision_vs_seed_gt 在
  度量 v3（P3-A）下更名 seed_match_rate（同测量），批准值口径同一，
  seed 相对诊断值 caveat 保留；
- 本批准只落 disposition 域，不写任何机器门、不改任何冻结产物，
  度量阈值常量 CONTAINMENT_MIN=0.5 / AREA_RATIO_MAX=10.0 零变化。

同构不变量（与 approvals.py/approvals_r2.py/approvals_r3.py 逐字同
模式）：每项批准 = 一条 disposition_record（kind=accept）+ 一条 ledger
entry（entry_kind=disposition、authority=human、trust_level=untrusted
——处置是决定不是事实，恒不可升级）；validate_no_gate_write 对全部
记录强制；evidence 指针=被登记事实的冻结产物 sha256（磁盘实读对账，
缺文件 fail-closed）；批准日期=人工声明常量 APPROVAL_DATE_R4=
"2026-09-06"（非机器 wall-clock）；evidence 一律仓库相对 POSIX 路径；
批准只能被后续 supersedes 追加式取代，不可回写；r1/r2/r3 批次登记
文件字节不动（本批全部为新文件）。

scope 取值说明：disposition_record schema 的 scope 枚举（candidate/
constraint/checker/physics/external/waiver_policy/adoption/profile/
corpus）无 calibration 项；本批准按最近先例（APR-0008 校准域种子
登记）取 scope="checker"（校准对象=TL-2 critic 检查器），如实映射。

本模块另提供域状态 v3 纯函数构造 build_calibration_domain_v3（基于
盘上实读 domain-v2 深拷贝定向更新；输入 dict 零变异；v1/v2 文件
字节不动）与评估协议冻结声明常量。

生成器模式：纯函数（collect_evidence_hashes 只读磁盘）、canonical
JSON、零子进程、零自身落盘、零网络、无 wall-clock。
"""

from __future__ import annotations

import copy
import json

from . import config, disposition, hashing, ledger, schemas

SCHEMA_VERSION = schemas.SCHEMA_V3

#: 人工批准日期（用户下达指示的声明日期；非机器 wall-clock）
APPROVAL_DATE_R4 = "2026-09-06"

#: 批准人（§1.2 权限矩阵：human 只写处置，无事实/门写权）
APPROVER = "user"
APPROVER_ROLE = "human_authority"

#: 批准账本快照标识（disposition 域独立账本第四批，不与 r1/r2/r3 混写）
APPROVALS_REVISION_R4 = "v3-approvals-r4"

#: 批准账本 checkpoint 标识
CHECKPOINT_ID_R4 = "CKPT-V3-APPROVALS-R4"

#: 人工指示原文（2026-09-06；逐字引用入 rationale_text）
INSTRUCTION_QUOTE_R4 = "校准达标线提案暂时就按这个来，先继续做吧"

#: evidence 逻辑名 → 仓库相对 POSIX 路径（磁盘实读；输出无主机路径）
EVIDENCE_FILES_R4 = (
    ("process_v1",
     "out/v3-tl2/calibration/calibration-process-v1.md"),
    ("domain_v2",
     "out/v3-tl2/calibration/calibration-domain-v2.json"),
    ("run_v2",
     "out/v3-tl2/calibration/calibration-run-v2.json"),
    ("run_v3_on_r2",
     "out/v3-tl2/calibration/calibration-run-v3-on-r2-inputs.json"),
    ("process_v2",
     "out/v3-tl2/calibration/calibration-process-v2.md"),
)

#: 达标线基线（APR-0011 暂时采纳；数值=process-v1 §5 提案逐项同一）
THRESHOLD_BASELINE_R4 = {
    "gt_recall_min": 0.75,
    "seed_match_rate_min": 0.5,
    "abstain_rate_max": 0.5,
    "consecutive_rounds_required": 2,
    "gt_count_min": 12,
    "approved_by": "APR-0011",
    "approval_date": APPROVAL_DATE_R4,
    "adoption": "provisional_supersedable",
    "precision_metric_mapping": (
        "提案「precision≥0.5」出处=calibration-process-v1.md §5 的 "
        "reader_precision_vs_seed_gt；度量 v3（calibration-metric-v3，"
        "P3-A）已将其更名 seed_match_rate（同测量、更名+语义约束）。"
        "本批准的 precision≥0.5 在度量 v3 下对应 seed_match_rate≥0.5"
        "（口径同一）；caveat 保留：seed 匹配率=相对种子 GT 的诊断值，"
        "禁称完整 precision/FPR（种子为部分覆盖判例，框命中不证明"
        "电气事实）。"),
    "source": ("calibration-process-v1.md §5（proposal_only 条款；"
               "人工 2026-09-06 指示暂时采纳）"),
    "evaluation_note": (
        "联合评价（任一不满足即未达标；弃权率不单独优化）；"
        "达标≠自动分流（BL-4+TD5 合取仍在，恒 blocked）；"
        "评估协议冻结件=out/v3-tl2/calibration/evaluation-protocol-v1.md。"),
}

#: 域 v3 状态常量（构造校验用）
DOMAIN_V3_ID = "calibration-domain-v3"
DOMAIN_V3_VERSION = "3.0"
DOMAIN_V3_STATUS = "threshold_provisionally_adopted"
GT_COUNT_CURRENT_EXPECTED = 4
GT_EXPANSION_REQUIRED = 12

#: 一项批准定义（数据即账：语义限定逐条对应 2026-09-06 人工指示原文）
APPROVAL_SPECS_R4 = (
    {
        "approval_id": "APR-0011",
        "entry_id": "APR-E-0011",
        "slug": "calibration-threshold-provisional-adoption",
        "subject": "校准达标线提案暂时采纳：recall≥0.75 / "
                   "precision(=度量 v3 的 seed_match_rate，口径同 "
                   "process-v1 §5 的 precision_vs_seed_gt)≥0.5 / "
                   "abstain≤0.5 / 连续 2 轮 / GT≥12，作为 "
                   "critic_calibration_in_range 的评估基准"
                   "（provisional，可被 supersedes 取代；不是自动分流"
                   "资格）",
        "kind": "accept",
        "scope": "checker",
        "rationale_code": "calibration_threshold_provisionally_adopted",
        "rationale_text": "用户人工批准 @2026-09-06（human authority，"
            "指示原文引用：「" + INSTRUCTION_QUOTE_R4 + "」）：校准"
            "达标线提案（calibration-process-v1.md §5 proposal_only "
            "条款）暂时采纳为 critic_calibration_in_range 的评估基准"
            "——recall≥0.75 / precision≥0.5 / abstain≤0.5 / 连续 2 轮"
            " / GT≥12。语义限定：①人工指示=2026-09-06 原文（见上，"
            "暂时采纳）；②「暂时」=provisional：仅暂时采纳，后续可被"
            "追加式 supersedes 取代，不构成永久承诺；③达标线=评估基准"
            "/开发检查点，不是自动分流资格——达标线组合≠自动分流资格"
            "（还需独立评测与有效分母），自动分流仍受 BL-4（Critic "
            "校准域+正式模型）与 TD5 分诊合取约束，恒 blocked 直至其"
            "条件实际满足；④当前两轮实测均未达标（GT=4<12 分母不足"
            "不判定；v2 轮 recall 0.25 / precision_vs_seed_gt "
            "0.142857；v3 复算 recall 0.25 / seed_match_rate "
            "0.142857 / abstain 0.533333），critic_calibration_in_range"
            " 实测评估仍 False，本批准不翻转任何机器门与谓词；"
            "⑤precision 项命名对账：提案 precision≥0.5 出处=process-v1"
            " §5 的 precision_vs_seed_gt，度量 v3 已更名 seed_match_rate"
            "（同测量），本批准的 precision≥0.5 在度量 v3 下对应 "
            "seed_match_rate≥0.5（口径同一），seed 相对诊断值 caveat "
            "保留（禁称完整 precision/FPR，框命中不构成电气事实）；"
            "⑥本批准只落 disposition 域，不写任何机器门、不改任何"
            "冻结产物，度量阈值常量 CONTAINMENT_MIN=0.5 / "
            "AREA_RATIO_MAX=10.0 不因本批准变化；正式翻转谓词须由"
            "独立流程（连续 2 轮实测达标+有效分母 GT≥12+人工裁决）"
            "执行，非本登记。",
        "fact_refs": ["TL-2", "critic_calibration_in_range",
                      "calibration_threshold_baseline"],
        "evidence": ("process_v1", "domain_v2", "run_v2", "run_v3_on_r2",
                     "process_v2"),
    },
)

#: 登记不变量说明（随 bundle 归档；字符串仅描述冻结状态，非门写）
FROZEN_MACHINE_GATE_STATUS_R4 = (
    "本登记不重算、不改写任何机器门：TL-2 critic 分诊谓词（含 "
    "critic_calibration_in_range）语义不变、fail-closed 路由不变，当前"
    "实测未达标→仍 False；TD5 分诊合取约束不变、自动分流仍 blocked；"
    "TL-3-G1/TL-4-G 既有裁决不变；TL-6 readiness 投影不回写；度量阈值"
    "常量 CONTAINMENT_MIN=0.5 / AREA_RATIO_MAX=10.0 数值零变化。本项"
    "批准只落 disposition 域（L6 事实/处置/门分离）：达标线采纳=评估"
    "基准登记，不构成任何质量结论、门输入或自动分流资格。"
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
    for name, relpath in EVIDENCE_FILES_R4:
        path = os.path.join(root, *relpath.split("/"))
        if not os.path.isfile(path):
            errors.append(f"evidence {name!r} 文件缺失: {relpath}")
        else:
            hashes[name] = hashing.sha256_file(path)
    return hashes, errors


def disposition_filename(spec: dict) -> str:
    """批准处置记录落盘文件名（out/v3-approvals/ 编排口径）。"""
    return f"disposition-{spec['approval_id']}-{spec['slug']}.json"


def build_approvals_bundle_r4(evidence_hashes: dict) -> dict:
    """构造人工批准的完整登记 bundle（纯函数；同输入 byte-exact）。

    evidence_hashes 必须覆盖 EVIDENCE_FILES_R4 全部逻辑名（缺一
    fail-closed ValueError）。每条 ledger entry：entry_kind=disposition、
    authority=human、trust_level=untrusted（verify_chain 白名单强制）、
    payload_ref=处置记录 canonical 落盘字节的 sha256、
    artifact_hashes=被登记事实的冻结产物（磁盘实读实测）。
    """
    missing = [name for name, _ in EVIDENCE_FILES_R4
               if not evidence_hashes.get(name)]
    if missing:
        raise ValueError(
            f"evidence 缺失（fail-closed 拒绝构造批准）: {missing}")
    hashes = dict(evidence_hashes)

    dispositions: list = []
    entries: list = []
    gate_write_scan: dict = {}
    for spec in APPROVAL_SPECS_R4:
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
            snapshot_revision=APPROVALS_REVISION_R4))

    bundle = {
        "schema_version": SCHEMA_VERSION,
        "approval_date": APPROVAL_DATE_R4,
        "approver": {"actor": APPROVER, "actor_role": APPROVER_ROLE},
        "revision": APPROVALS_REVISION_R4,
        "approval_count": len(APPROVAL_SPECS_R4),
        "supersedes_note": (
            "r4 为追加批次：不取代、不改写 r1（APR-0001–0006）、"
            "r2（APR-0007–0009）、r3（APR-0010）；out/v3-approvals/ "
            "既有文件字节不动。APR-0011 自身=provisional（暂时采纳），"
            "可被后续 supersedes 追加式取代。"),
        "threshold_baseline": copy.deepcopy(THRESHOLD_BASELINE_R4),
        "dispositions": dispositions,
        "ledger_entries": entries,
        "ledger_file_sha256": _ledger_bytes_sha256(entries),
        "ledger_verify": {
            "chain_errors": ledger.verify_chain(entries),
            "supersedes_errors": ledger.verify_supersedes(entries),
        },
        "ledger_checkpoint": ledger.make_checkpoint(entries,
                                                   CHECKPOINT_ID_R4),
        "gate_write_scan": gate_write_scan,
        "evidence_registry": [
            {"name": name, "path": path, "sha256": hashes[name]}
            for name, path in EVIDENCE_FILES_R4
        ],
        "disposition_files": {spec["approval_id"]:
                              disposition_filename(spec)
                              for spec in APPROVAL_SPECS_R4},
        "frozen_machine_gate_status": FROZEN_MACHINE_GATE_STATUS_R4,
        "notes": [
            "一项人工批准（2026-09-06）：校准达标线提案暂时采纳"
            "（APR-0011；recall≥0.75 / precision=seed_match_rate≥0.5 / "
            "abstain≤0.5 / 连续 2 轮 / GT≥12）为 critic_calibration_"
            "in_range 评估基准。",
            "「暂时」=provisional：后续可被追加式 supersedes 取代；"
            "达标线=评估基准/开发检查点，不是自动分流资格（自动分流仍"
            "受 BL-4+TD5 合取约束，恒 blocked）；当前实测未达标→"
            "critic_calibration_in_range 仍 False，本批准不翻转任何"
            "机器门。",
            "本账本为 disposition 域独立账本 r4 批次，不改写既有 "
            "out/v3-approvals/ r1/r2/r3 文件与任何 out/ 冻结产物；"
            "域状态 v3（calibration-domain-v3.json）与评估协议 v1"
            "（evaluation-protocol-v1.md）为本包声明的两件新产物，"
            "均不回写既有文件。",
            "scope 取值说明：disposition_record schema 的 scope 枚举无"
            " calibration 项，本批准按最近先例（APR-0008 校准域种子"
            "登记）取 scope=checker（校准对象=TL-2 critic 检查器），"
            "如实映射不冒名。",
            "批准日期为人工声明常量（非机器 wall-clock）；evidence "
            "hash 为生成时磁盘实读值，可用 sha256sum 对 out/ 内文件"
            "复核。",
        ],
    }
    return bundle


# ---------------------------------------------------------------------------
# 域状态 v3 构造（纯函数；基于盘上实读 domain-v2 定向更新）
# ---------------------------------------------------------------------------

def build_calibration_domain_v3(domain_v2: dict, *, evidence_hashes: dict,
                                protocol_sha256: str) -> dict:
    """由 domain-v2 深拷贝构造域状态 v3（纯函数；输入 dict 零变异）。

    - status: process_formalized_threshold_proposal_pending →
      threshold_provisionally_adopted（APR-0011 暂时采纳）；
    - supersedes 记 v2 的 sha256（evidence_hashes["domain_v2"]，磁盘
      实读；追加式取代声明，v1/v2 文件字节不动）；
    - threshold_baseline=THRESHOLD_BASELINE_R4（五项达标线数值+APR-0011
      +provisional_supersedable+precision_metric_mapping 对账）；
    - gt_count_current=4（与 v2 ground_truth.entry_count 一致，不符
      fail-closed）、gt_expansion_required=12；
    - in_calibrated_range_current=False（实测未达标，本构造无任何置真
      路径）；auto_triage="blocked"（不变）；
    - evaluation_protocol 绑定冻结件 evaluation-protocol-v1.md 的
      sha256（编排侧由协议字节实算，先于落盘）。

    evidence_hashes 必须含 domain_v2/run_v2/run_v3_on_r2（缺一
    fail-closed ValueError）。同输入 byte-exact。
    """
    missing = [name for name in ("domain_v2", "run_v2", "run_v3_on_r2")
               if not evidence_hashes.get(name)]
    if missing:
        raise ValueError(
            f"evidence 缺失（fail-closed 拒绝构造域 v3）: {missing}")
    if not protocol_sha256:
        raise ValueError("protocol_sha256 缺失（fail-closed：评估协议"
                         "冻结件 hash 必须先于域 v3 构造实算绑定）")
    gt_block = domain_v2.get("ground_truth") or {}
    gt_count = gt_block.get("entry_count")
    if gt_count != GT_COUNT_CURRENT_EXPECTED:
        raise ValueError(
            f"GT 计数不符（fail-closed）：期望 "
            f"{GT_COUNT_CURRENT_EXPECTED}，v2 ground_truth.entry_count="
            f"{gt_count!r}——域 v3 的 gt_count_current 必须与被取代域"
            f"实测一致")

    d = copy.deepcopy(domain_v2)
    d["domain_id"] = DOMAIN_V3_ID
    d["domain_version"] = DOMAIN_V3_VERSION
    d["declared_date"] = APPROVAL_DATE_R4
    d["status"] = DOMAIN_V3_STATUS
    d["supersedes"] = {
        "domain": "calibration-domain-v2",
        "path_rel": "out/v3-tl2/calibration/calibration-domain-v2.json",
        "sha256": evidence_hashes["domain_v2"],
        "note": "追加式取代：只取代域状态与达标线采纳状态"
                "（process_formalized_threshold_proposal_pending→"
                "threshold_provisionally_adopted）并追加 "
                "threshold_baseline/evaluation_protocol 块；v1/v2 文件"
                "字节不动，度量产物不回写不重算；APR-0011 本身"
                "=provisional，可被后续 supersedes 取代。",
    }
    d["threshold_baseline"] = copy.deepcopy(THRESHOLD_BASELINE_R4)
    d["gt_count_current"] = gt_count
    d["gt_expansion_required"] = GT_EXPANSION_REQUIRED
    d["in_calibrated_range_current"] = False
    d["in_calibrated_range_basis"] = {
        "status": "not_met_current",
        "rounds_measured": 2,
        "note": "两轮实测均未达标且 GT 分母不足（4<12，按达标线最小"
                "样本前提不判定）；本域构造不翻转任何机器门与谓词，"
                "数值为被取代域归档 run 件如实转录（编排侧对盘实测"
                "复核）。",
        "rounds": [
            {"path_rel": "out/v3-tl2/calibration/calibration-run-v2.json",
             "sha256": evidence_hashes["run_v2"],
             "metric_version": "calibration-metric-v2",
             "gt_recall": 0.25,
             "precision_vs_seed_gt": 0.142857},
            {"path_rel": "out/v3-tl2/calibration/"
                         "calibration-run-v3-on-r2-inputs.json",
             "sha256": evidence_hashes["run_v3_on_r2"],
             "metric_version": "calibration-metric-v3",
             "gt_recall": 0.25,
             "seed_match_rate": 0.142857,
             "abstain_rate": 0.533333},
        ],
    }
    d["auto_triage"] = "blocked"
    d["evaluation_protocol"] = {
        "path_rel": "out/v3-tl2/calibration/evaluation-protocol-v1.md",
        "sha256": protocol_sha256,
        "status": "frozen_from_this_round",
        "metric": "calibration-metric-v3",
        "note": "评估协议 v1 自本轮起冻结（P3-B）；后续修订=新版本"
                "文件，不回写。",
    }
    d["usage_policy"] = (
        "标注 pipeline 侧、不混入 reader 视野；盲读轮按 process 文档 "
        "§2 规程与 evaluation-protocol-v1 派发（r3 轮起按视图分派，"
        "编排侧以 flag_views 注入 compare_v3）；达标线已由 APR-0011 "
        "暂时采纳（provisional）但当前实测未达标"
        "（in_calibrated_range_current=false）→ critic_calibration_"
        "in_range 仍 False、flags=[] 一律 blocked（fail-closed 语义"
        "零改动；自动分流恒 blocked）。")
    d["notes"] = [
        "v3=达标线暂时采纳版本（APR-0011 @2026-09-06）：基于 v2 构造，"
        "v1/v2 文件字节不动；本包只新增本件，不回写不重算任何既有"
        "产物。",
        "metric 块自 v2 原样保留：匹配常量 CONTAINMENT_MIN=0.5 / "
        "AREA_RATIO_MAX=10.0 数值与依据零变化（其 threshold_adoption="
        "proposal_only 标注针对匹配常量与度量 v2 正式化状态，本批准"
        "不扩大到该宣告）；当前评估度量=calibration-metric-v3（见 "
        "evaluation_protocol 块与 calibration-process-v2），达标线采纳"
        "状态见 threshold_baseline 与 status。",
        "命名对账：threshold_baseline.seed_match_rate_min=0.5 对应 "
        "process-v1 §5 提案「precision≥0.5」（同测量更名，口径同一）；"
        "seed 相对诊断值 caveat 保留（禁称完整 precision/FPR）。",
        "达标线=评估基准/开发检查点，不是自动分流资格：auto_triage="
        "blocked 不变（BL-4+TD5 合取约束，恒 blocked）。",
    ]
    return d


def _ledger_bytes_sha256(entries) -> str:
    """账本文件字节 hash（与 out/v3-tl1|tl3|tl4 既有口径一致）。"""
    return hashing.sha256_bytes(ledger_file_bytes(entries))


def ledger_file_bytes(entries) -> bytes:
    """账本落盘字节（编排侧写 decision-ledger-r4.jsonl 的唯一口径）。"""
    return hashing.jsonl_bytes(entries)  # REPAIR-P3 W-4 正身收编（等价验证在案）
