"""TL-6 环路健康度/readiness 投影（S16；SPEC-v3.0-PROPOSAL §4 可计算定义）。

职责（全部纯函数；盘上实测与落盘由编排侧完成）：

1. 四项指标投影——每条带 SPEC §4 要求的九个描述字段
   （dataset/mode/definition/denominator/baseline/threshold/window/
   profile/revision）：
   - 人工队列长度：从 queue-event-ledger 事件投影 open 项数+reason 分布
     +时间窗（时间窗以事件序号表达——账本无 epoch 字段，禁 wall-clock）；
   - Critic 一致率：分母=已执行+有效+有人工 verdict 的分歧项数；
   - Proposer 接受率：按 patch kind/version 有完整 disposition 的候选中
     adoption 数/有效候选数；
   - 跨板回测不回退率：仅留出板中 required metrics+白名单子项均不回退
     的有效板数/有效板数。

   SPEC §4 语义（fail-closed）：
   - 分母为 0 → ``not_available``（不编数值）；
   - 缺 hash 或 trust invalid（账本链校验失败）→ ``blocked``；
   - not_available/blocked 一律不携带 value/numerator（不冒充数值）。

2. 辅助刻度：DAG blocked 数、physics coverage、required report
   freshness、queue aging（SPEC §4 辅助刻度清单的当前可计算子集；
   ② 预检 recall/误报分布与账本 low_margin 无数据源=不出现，不冒充）。

3. readiness matrix：逐 TL 门+TD7+生产签核的逐格状态，每格带证据指针
   （gate-record 路径+sha256 前 8）；``production_signoff_ready=false``
   恒定（L7 闭门律）。TL-6 出口门=blocked 如实，本包不申请 closure。

4. 健康度 gate-record 机器谓词：投影可计算性/分母诚实性/
   not_available 不冒充数值/证据 hash 对账。

生成器模式：零 IO、零子进程、零网络、无 wall-clock、无主机路径；
仅标准库 + 包内 queue/hashing。证据 hash 全部由编排侧实测后注入，
本模块只做格式校验与对账（sha256_8 前缀一致性）。
"""

from __future__ import annotations

import re

from . import queue

SCHEMA_VERSION = "3.0"
PROJECTION_ID = "HP-v3-tl6"
PROJECTION_REVISION = "v3-tl6-r1"
SPEC_SECTION = "SPEC-v3.0-PROPOSAL §4（环路健康度仪表，可计算定义）"
GATE_ID = "TL-6-HEALTH-G"
EXIT_GATE_ID = "TL-6-G"
PREDICATE_VERSION = "pv1"

STATUS_VALUE = "value"
STATUS_NOT_AVAILABLE = "not_available"
STATUS_BLOCKED = "blocked"
STATUSES = (STATUS_VALUE, STATUS_NOT_AVAILABLE, STATUS_BLOCKED)

METRIC_IDS = ("manual_queue_length", "critic_agreement_rate",
              "proposer_acceptance_rate", "cross_board_non_regression_rate")

#: SPEC §4 要求的九个描述字段（每条指标必须齐全）
DESCRIPTOR_KEYS = ("dataset", "mode", "definition", "denominator",
                   "baseline", "threshold", "window", "profile", "revision")

#: 计数型指标（非比值）——denominator 允许为 None，但必须声明 basis
COUNT_METRIC_IDS = ("manual_queue_length",)

_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_REPO_REL = re.compile(r"^[A-Za-z0-9._/-]+$")

TERMINAL_EVENTS = queue.TERMINAL_EVENTS          # approve/reject/expire


# ---------------------------------------------------------------------------
# 基础构件
# ---------------------------------------------------------------------------

def evidence_ref(path: str, sha256: str) -> dict:
    """证据指针：仓库相对 POSIX 路径+完整 sha256+前 8 显示位。"""
    if not isinstance(path, str) or not _REPO_REL.match(path) or ".." in path:
        raise ValueError(f"evidence_ref: 非法路径 {path!r}")
    if not isinstance(sha256, str) or not _HEX64.match(sha256):
        raise ValueError(f"evidence_ref: 非法 sha256 for {path!r}")
    return {"path": path, "sha256": sha256, "sha256_8": sha256[:8]}


def _metric_base(metric_id: str, *, dataset: str, definition: str,
                 denominator, baseline, threshold, window, profile: str,
                 reason=None, baseline_basis: str | None = None) -> dict:
    if metric_id not in METRIC_IDS:
        raise ValueError(f"_metric_base: 未知指标 {metric_id!r}")
    rec = {
        "metric_id": metric_id,
        "spec_section": SPEC_SECTION,
        "dataset": dataset,
        "mode": "read_only_ledger_projection",
        "definition": definition,
        "denominator": denominator,
        "baseline": baseline,
        "threshold": threshold,
        "window": window,
        "profile": profile,
        "revision": PROJECTION_REVISION,
        "status": None,
        "value": None,
        "numerator": None,
        "reason": reason,
        "baseline_basis": baseline_basis,
        "aux": {},
        "evidence": [],
    }
    return rec


def _finish_value(rec: dict, numerator: int, denominator, value) -> dict:
    if rec["metric_id"] not in COUNT_METRIC_IDS:
        if not isinstance(denominator, int) or denominator <= 0:
            raise ValueError(
                f"_finish_value: 比值指标 {rec['metric_id']} 的 denominator "
                f"非法 {denominator!r}（value 态要求分母>0）")
    rec["status"] = STATUS_VALUE
    rec["numerator"] = numerator
    rec["denominator"] = denominator
    rec["value"] = value
    return rec


def _finish_not_available(rec: dict, reason: str) -> dict:
    rec["status"] = STATUS_NOT_AVAILABLE
    rec["reason"] = reason
    return rec


def _finish_blocked(rec: dict, reason: str) -> dict:
    rec["status"] = STATUS_BLOCKED
    rec["reason"] = reason
    return rec


# ---------------------------------------------------------------------------
# 指标一：人工队列长度
# ---------------------------------------------------------------------------

def project_manual_queue(events, *, ledger_path: str,
                         ledger_sha256: str) -> dict:
    """当前 revision 中 blocked/disagreement 且未关闭的 queue item 数。

    时间窗以事件序号表达（账本事件无 epoch/wall-clock 字段——D4 口径，
    禁 wall-clock）。链校验失败 → blocked（trust invalid）。
    """
    rec = _metric_base(
        "manual_queue_length",
        dataset=f"queue-event-ledger@{ledger_path}",
        definition=("当前 revision 中 blocked/disagreement 且未关闭的 "
                    "queue item 数（open enqueue 后无终态事件）"),
        denominator=None,
        baseline=None,
        baseline_basis=("首包投影（v3-tl6-r1）：无先前 revision 的队列长度"
                        "度量——基线未建立，如实 null"),
        threshold=("无固定阈值；下降不自动表示质量改善（SPEC §4 原文）；"
                   "抽样审计分流见 queue.audit_decision"),
        window=None,
        profile="training-loop（全项目队列）",
        reason=None,
    )
    # denominator_basis 是本模块对计数型指标的诚实标注（非 SPEC 九字段，
    # 附加键）；九字段中 denominator=None 仅对计数型合法。
    rec["denominator_basis"] = "count_metric_no_denominator"
    rec["evidence"] = [evidence_ref(ledger_path, ledger_sha256)]

    try:
        errs = queue.verify_chain(events)
    except (KeyError, TypeError, ValueError) as exc:
        return _finish_blocked(rec, f"trust_invalid: 账本结构非法（{exc}）")
    if errs:
        return _finish_blocked(rec, f"trust_invalid: 账本链校验失败 {errs}")

    summary = queue.projection_summary(events)
    last_seq = max((ev.get("event_seq", 0) for ev in events), default=None)
    oldest = summary["oldest_item_seq"]
    rec["window"] = {
        "unit": "ledger_event_seq",
        "total_events": summary["total_events"],
        "last_event_seq": last_seq,
        "oldest_open_seq": oldest,
        "events_since_oldest_enqueue": (
            (last_seq - oldest) if (last_seq is not None
                                    and oldest is not None) else None),
        "wall_clock": "not_used（账本无 epoch 字段；事件序号口径，禁 wall-clock）",
    }
    rec["aux"] = {
        "by_reason_code": summary["by_reason_code"],
        "by_last_event": summary["by_last_event"],
        "input_volume": {"events_total": summary["total_events"],
                         "items_enqueued_total": sum(
                             1 for ev in events if ev.get("event")
                             == "enqueue")},
        "human_capacity": ("not_available（账本无人工容量/吞吐字段——"
                           "如实不编造）"),
        "open_items": [it["item_id"] for it in queue.current_queue(events)],
    }
    return _finish_value(rec, numerator=summary["queue_length"],
                         denominator=None, value=summary["queue_length"])


# ---------------------------------------------------------------------------
# 指标二：Critic 一致率
# ---------------------------------------------------------------------------

def project_critic_agreement(critic_runs, queue_events, *,
                             record_evidence) -> dict:
    """人工支持旗标数 / 有效分歧项数（仅已执行+有效+有人工 verdict 项）。

    ``critic_runs``: [{run_id, critic_status, input_hashes_match,
    critic_ref, in_calibrated_range, flags_total, abstain_count,
    board_flag_counts}]（编排侧从 record+raw flags 实测装配）；
    ``record_evidence``: [{run_id, path, sha256}]。
    分母=0 → not_available（SPEC §4：未执行不进分母）。
    """
    rec = _metric_base(
        "critic_agreement_rate",
        dataset="critic-run-record + queue-event-ledger（人工 verdict 侧）",
        definition=("仅在 Critic 已执行、有效且有 Human verdict 的分歧项中，"
                    "人工支持旗标数/有效分歧项数"),
        denominator=None,
        baseline=None,
        baseline_basis=("首次真实 advisory run（run-r1）为首个观测点——"
                        "无先前一致率度量，基线未建立，如实 null"),
        threshold=("85% 只能是附加条件，不能单独晋升（SPEC §4 原文）；"
                   "正式晋升门=TD5 十条件合取"),
        window={"unit": "critic_run_set",
                "runs_considered": [r["run_id"] for r in critic_runs]},
        profile="advisory run 分歧项（run 级，非板级汇总）",
    )
    rec["evidence"] = [evidence_ref(e["path"], e["sha256"])
                       for e in record_evidence]

    # trust invalid：record 声明 hash 不匹配 → blocked
    invalid = [r["run_id"] for r in critic_runs
               if r.get("input_hashes_match") is False]
    if invalid:
        return _finish_blocked(
            rec, f"trust_invalid: record 输入 hash 对账失败 {invalid}")

    # 人工 verdict = 分歧项 queue item 上的终态事件（approve/reject/expire）；
    # item→critic_ref 绑定取自 enqueue 事件（终态事件不必携带 critic_ref）
    item_ref = {ev.get("item_id"): ev.get("critic_ref")
                for ev in queue_events if ev.get("event") == "enqueue"}
    verdict_item_ids = {ev.get("item_id") for ev in queue_events
                        if ev.get("event") in TERMINAL_EVENTS}
    verdict_refs = {item_ref[i] for i in verdict_item_ids
                    if item_ref.get(i)}
    valid_runs = [r for r in critic_runs
                  if r.get("critic_status") == "executed"
                  and r.get("input_hashes_match") is True]
    verdicted = [r for r in valid_runs if r.get("critic_ref") in verdict_refs]
    denominator = len(verdicted)
    if denominator == 0:
        rec["denominator"] = 0
        out = _finish_not_available(
            rec,
            "denominator_zero: 无已执行+有效+有人工 verdict 的分歧项"
            "（ITEM-run-r1 open 无 verdict；「未执行不进分母」）")
        rec["aux"] = _critic_aux(critic_runs, queue_events, verdicted)
        return out
    supported = sum(1 for r in verdicted if r.get("human_supports_flags"))
    return _finish_value(rec, numerator=supported, denominator=denominator,
                         value=supported / denominator)


def _critic_aux(critic_runs, queue_events, verdicted) -> dict:
    """SPEC §4 要求同报的 precision/recall/FPR/FNR/abstain/calibration。

    ``critic_runs`` 各项携带编排侧从 record+raw flags 实测装配的
    flags_total/abstain_count/board_flag_counts（record 合同级投影的
    flags 只保留 category/confidence/location——D21(c)，abstain 与
    per-board 计数由 raw flags 承载）。
    """
    flags_total = sum(int(r.get("flags_total", 0)) for r in critic_runs)
    abstain_total = sum(int(r.get("abstain_count", 0)) for r in critic_runs)
    calibrations = sorted({json_scalar(r.get("in_calibrated_range"))
                           for r in critic_runs})
    worst_board = None
    boards = {}
    for r in critic_runs:
        for pid, n in (r.get("board_flag_counts") or {}).items():
            boards[pid] = boards.get(pid, 0) + int(n)
    if boards:
        worst_board = max(boards, key=lambda k: (boards[k], k))
    return {
        "runs_total": len(critic_runs),
        "runs_executed_valid": sum(
            1 for r in critic_runs
            if r.get("critic_status") == "executed"
            and r.get("input_hashes_match") is True),
        "runs_with_human_verdict": len(verdicted),
        "precision": "not_available（分母 0）",
        "recall": "not_available（分母 0）",
        "fpr": "not_available（分母 0）",
        "fnr": "not_available（分母 0）",
        "abstain_count": abstain_total,
        "flags_total": flags_total,
        "in_calibrated_range_observed": calibrations,
        "calibration_note": ("校准域未建立：in_calibrated_range 恒 False，"
                             "「无旗」语义不可行使（S14 口径）"),
        "worst_board_by_flags": worst_board,
    }


def json_scalar(v):
    return v if (v is None or isinstance(v, (bool, int, float, str))) \
        else str(v)


# ---------------------------------------------------------------------------
# 指标三：Proposer 接受率
# ---------------------------------------------------------------------------

def project_proposer_acceptance(candidates, human_disposition,
                                machine_gate, *, patch_evidence) -> dict:
    """有完整 disposition 的候选中 adoption 数/有效候选数（按 kind/version）。

    ``candidates``: [{patch_id, kind, version, profile}]；
    ``human_disposition``: APR 处置 dict（kind/scope/fact_refs）；
    ``machine_gate``: {predicate_id: bool}（TL-4-G v2 实测谓词值）。
    adoption=人工处置与机器门合取（TD11）；机器门 fail → adoption=0。
    """
    rec = _metric_base(
        "proposer_acceptance_rate",
        dataset="proposal-patch × adoption disposition × TL-4-G v2 谓词",
        definition=("按 patch kind/version 统计有完整 disposition 的候选中 "
                    "adoption 数/有效候选数"),
        denominator=None,
        baseline=None,
        baseline_basis=("首包投影：两个 smoke patch 候选（S3）为唯一观测集"
                        "——无先前接受率度量，基线未建立，如实 null"),
        threshold=("adoption 需人工处置 ∧ 机器门合取全绿（TD11/D18）；"
                   "本指标不是正确性或 authority 度量（SPEC §4 原文）"),
        window={"unit": "patch_set",
                "patches_considered": [c["patch_id"] for c in candidates]},
        profile="patch 来源 profile 全集",
    )
    rec["evidence"] = [evidence_ref(e["path"], e["sha256"])
                       for e in patch_evidence]

    if not isinstance(human_disposition, dict) \
            or "fact_refs" not in human_disposition:
        return _finish_blocked(rec, "trust_invalid: 处置记录缺失 fact_refs")

    covered = [c for c in candidates
               if c["patch_id"] in human_disposition.get("fact_refs", [])
               and human_disposition.get("kind") is not None]
    denominator = len(covered)
    by_kind_version = {}
    for c in covered:
        key = f"{c['kind']}@{c['version']}"
        by_kind_version.setdefault(key, {"candidates": 0, "adopted": 0,
                                         "blocked": 0, "rejected": 0,
                                         "waived": 0})
        by_kind_version[key]["candidates"] += 1
    if denominator == 0:
        rec["denominator"] = 0
        out = _finish_not_available(
            rec, "denominator_zero: 无有完整 disposition 的候选")
        rec["aux"] = {"by_kind_version": by_kind_version}
        return out

    gate_green = all(bool(v) for v in machine_gate.values())
    adopted = sum(1 for _ in covered) if gate_green else 0
    for key in by_kind_version:
        by_kind_version[key]["adopted"] = adopted
        by_kind_version[key]["blocked"] = (
            denominator - adopted if not gate_green else 0)
    value = adopted / denominator
    out = _finish_value(rec, numerator=adopted, denominator=denominator,
                        value=value)
    out["aux"] = {
        "by_kind_version": by_kind_version,
        "adoption_status": ("human_approved_machine_blocked" if not gate_green
                            else "adopted"),
        "machine_gate_predicates": dict(sorted(machine_gate.items())),
        "machine_gate_fail_reason": (
            "机器门 fail（holdout_non_regression_evidenced=False + "
            "judge_post_ok=False → adoption_machine_gate_pass=False；"
            "D18 结构性缺：无逐板不回退执行面）" if not gate_green else None),
        "proposal_coverage": {
            "profiles_with_candidates": len({c["profile"]
                                             for c in candidates}),
            "profiles_in_scope": len({c["profile"] for c in candidates}),
        },
        "proposal_count_floor": ("not_available（未配置提议数量下限策略——"
                                 "如实，不编造）"),
        "reject_blocked_waive_reasons": {
            "reject": 0, "waive": 0,
            "blocked": denominator - adopted,
            "blocked_reason": ("machine_gate_fail（人工 accept 在场"
                               "=APR-0004，机器合取项 fail）"),
        },
    }
    return out


# ---------------------------------------------------------------------------
# 指标四：跨板回测不回退率
# ---------------------------------------------------------------------------

def project_non_regression(holdout_backtests, *, evidence) -> dict:
    """仅留出板中 required metrics+白名单子项均不回退的有效板数/有效板数。

    ``holdout_backtests``: [{board, metrics_ok, whitelist_ok}]（真实
    autotune 回测结果；当前无执行面=空表）。分母 0 → not_available。
    """
    rec = _metric_base(
        "cross_board_non_regression_rate",
        dataset="holdout 板真实 autotune 回测（challenger vs baseline）",
        definition=("仅留出板中所有 required metrics 和白名单子项均不回退的 "
                    "有效板数/有效板数"),
        denominator=len(holdout_backtests),
        baseline="baseline config（immutable 保留）",
        threshold=("100% 是 adoption 硬门，不是趋势项（SPEC §4 原文）"),
        window={"unit": "backtest_run_set",
                "backtests_considered": [b.get("board") for b
                                         in holdout_backtests]},
        profile="逐 profile、逐板、逐指标",
    )
    rec["evidence"] = [evidence_ref(e["path"], e["sha256"])
                       for e in evidence]
    if not holdout_backtests:
        out = _finish_not_available(
            rec,
            "denominator_zero: 无真实 autotune 回测（D18 结构性缺："
            "corpus 四段消费可调参数=0、route/check=D17 参考态验证 "
            "config 无关 → 逐板不回退无执行面）")
        rec["aux"] = {
            "holdout_corpus_available": True,
            "holdout_execution_denominator": 0,
            "note": ("holdout 语料在库（pcbench 11+pcbbm 1+kicad-demos 3）"
                     "≠执行分母——语料可用性与不回退证据解耦（D18 口径）"),
        }
        return out
    ok = [b for b in holdout_backtests
          if b.get("metrics_ok") and b.get("whitelist_ok")]
    return _finish_value(rec, numerator=len(ok),
                         denominator=len(holdout_backtests),
                         value=len(ok) / len(holdout_backtests))


# ---------------------------------------------------------------------------
# 辅助刻度
# ---------------------------------------------------------------------------

def auxiliary_scales(*, tl3_coverage, dag_nodes, queue_summary,
                     physics_report_revision, gate_inputs_revision) -> dict:
    """SPEC §4 辅助刻度当前可计算子集（缺数据源的不出现，不冒充）。"""
    physics_cov = {
        "required_scope": tl3_coverage.get("required_scope", []),
        "covered_scope": tl3_coverage.get("covered_scope", []),
        "missing_scope": tl3_coverage.get("missing_scope", []),
        "coverage_complete": bool(tl3_coverage.get("coverage_complete")),
        "gate_result": "fail",
        "note": ("coverage 只度量报告在场；coverage=100% 不等于结果通过"
                 "（TL-3-G1 fail：uncertainty 超容差+无 approval+"
                 "authority=screening 级）"),
    }
    freshness = {
        "measure": "snapshot_revision_binding",
        "physics_report_revision": physics_report_revision,
        "gate_inputs_revision": gate_inputs_revision,
        "fresh_at_projection": (physics_report_revision
                                == gate_inputs_revision),
        "wall_clock_age": ("not_available（核产物禁 wall-clock；freshness "
                           "以 revision 绑定+账本事件序号表达）"),
    }
    aging = {
        "unit": "ledger_event_seq",
        "oldest_open_item": queue_summary.get("oldest_item_id"),
        "enqueued_event_seq": queue_summary.get("oldest_item_seq"),
        "last_event_seq": queue_summary.get("last_event_seq"),
        "age_events": queue_summary.get("age_events"),
        "wall_clock_age": "not_available（同上：事件序号口径）",
    }
    return {
        "dag_blocked": {
            "count": len(dag_nodes),
            "nodes": dag_nodes,
            "note": ("blocked 节点=机器门 fail/blocked 的 DAG 出口；"
                     "TL-6 blocked 由本投影自身如实记录（自引）"),
        },
        "physics_coverage": physics_cov,
        "required_report_freshness": freshness,
        "queue_aging": aging,
        "not_tracked_here": {
            "precheck_recall_false_positive_cross_board": (
                "not_available（无预检 recall/误报跨板数据源）"),
            "ledger_low_margin": "not_available（账本无 low_margin 字段）",
        },
    }


# ---------------------------------------------------------------------------
# readiness matrix + open blockers
# ---------------------------------------------------------------------------

def readiness_matrix(evidence) -> dict:
    """逐 TL 门+TD7+生产签核总表；每格带证据指针（路径+sha256_8）。

    ``evidence``: {row_key: [{"path","sha256"}, ...]}——编排侧盘上实测。
    TL-6 行=本投影自身（自引，sha256 留 null 由 gate record 对账）。
    """
    rows_spec = [
        ("TL-0-G1", "pass",
         "两个非 Rev-C smoke profile 全链 ok（APR-0001 人工范围已批）"),
        ("TL-1-G1", "pass",
         "ledger/judge/disposition/gate 合同 pass（APR-0002 schema 基线已批）"),
        ("TL-2", "partial_pass_with_open_queue",
         "合同+库级 pass；S14 首次 advisory run run-r1 executed→TD5 分诊 "
         "blocked→人工队列 open 1（judge/checker 缺席+无校准域+flags 非空）；"
         "读取者=子代理代位（untrusted），正式模型接入未发生（APR-0005 "
         "advisory_only）"),
        ("TL-3-G1", "fail",
         "required 实配完成；机器裁决 fail 如实（screening 级合成证据满足 "
         "不了 required 级 authority/容差/批准；coverage=100%≠pass）"),
        ("TL-4-G", "fail",
         "S9 解锁评估（路径 b）+v2 复评 fail 维持：holdout 执行分母 0、"
         "adoption=human_approved_machine_blocked（APR-0004 人工侧在场）、"
         "零 apply"),
        ("TL-5-G", "pass",
         "v4 机器复评 pass（D17 参考态验证口径）：37 profile 主路径 6/6 段 "
         "executed；不构成布线生成/泛化能力主张"),
        ("TD7-QUAL-G", "archived",
         "S13 收档（ARC-0001）：S11 pass=历史资格证据冻结只读，不得引用为"
         "现行能力；质量面终局 9/9 拒收；重开=新引擎/换 backend 重走 "
         "qualification（ARC-0002/0003/0004 挂账全处置）"),
        ("TL-6", "blocked",
         "本包=首投影落档（可计算投影+收口地图）；出口门 blocked 如实，"
         "不申请 closure——open production blockers 见 open_blockers"),
        ("production_signoff_ready", "false",
         "L7 闭门律：TL-3/TL-4 fail+TL-6 blocked+布线引擎缺 → 恒 false；"
         "任何投影/gate pass 不构成产品化声明"),
    ]
    rows = []
    for key, status, note in rows_spec:
        evs = evidence.get(key)
        if not evs and key != "TL-6":
            raise ValueError(f"readiness_matrix: 行 {key} 缺证据指针")
        items = []
        for e in (evs or []):
            ref = evidence_ref(e["path"], e["sha256"])
            items.append(ref)
        if key == "TL-6":
            items = [{"path": "out/v3-tl6/health-projection.json",
                      "sha256": None, "sha256_8": None,
                      "self_reference": True,
                      "note": "本记录自身；sha256 由 gate record inputs 记录"}]
        rows.append({"gate": key, "status": status, "note": note,
                     "evidence": items})
    return {
        "rows": rows,
        "production_signoff_ready": False,
        "self_signoff_forbidden": "L7 缺证据闭门律",
    }


def open_production_blockers() -> list:
    """TL-6 出口门 blocked 的剩余 open production blocker 清单（如实）。"""
    return [
        {
            "blocker_id": "BL-1",
            "title": "v3 布线引擎 / TD7 替代",
            "detail": ("pcbflow 无 v1.x 之外的布线生成引擎；TD7 freerouting "
                       "线 archived（ARC-0001，质量面 9/9 拒收+"
                       "nondeterministic）；重开=新引擎版本/换 backend 重走 "
                       "qualification"),
            "unblocks": ["TL-4 执行面", "TL-5 route 生成语义", "TL-6"],
            "evidence": [{"path": "out/v3-archive/"
                                 "disposition-ARC-0001-td7-line-archive.json",
                          "note": "线关线 archived"}],
        },
        {
            "blocker_id": "BL-2",
            "title": "TL-3 真实物理证据链",
            "detail": ("required 级需要更高 authority 证据（外部分析/"
                       "回板实测）；现为 screening 级合成数据，机器裁决 "
                       "fail 如实"),
            "unblocks": ["TL-3-G1"],
            "evidence": [{"path": "out/v3-tl3/gate-record.json",
                          "note": "TL-3-G1 fail"}],
        },
        {
            "blocker_id": "BL-3",
            "title": "TL-4 执行类谓词",
            "detail": ("holdout_non_regression_evidenced/judge_post_ok/"
                       "adoption_machine_gate_pass 结构性缺（无逐板不回退"
                       "执行面，D18）；adoption 恒 "
                       "human_approved_machine_blocked"),
            "unblocks": ["TL-4-G", "proposer_acceptance_rate"],
            "evidence": [{"path": "out/v3-tl4/"
                                 "gate-record-tl4-v2-smoke-2l.json",
                          "note": "v2 fail 维持"}],
        },
        {
            "blocker_id": "BL-4",
            "title": "Critic 校准域 + 正式模型",
            "detail": ("置信度校准未建立：in_calibrated_range 恒 False、"
                       "「无旗」语义不可行使、自动分流恒 blocked；读取者"
                       "=子代理代位（输出恒 untrusted），正式模型接入未"
                       "发生；ITEM-run-r1 人工处置 open"),
            "unblocks": ["TL-2 自动分流", "critic_agreement_rate 分母"],
            "evidence": [{"path": "out/v3-tl2/critic-runs/run-r1/"
                                 "critic-run-record-CR-run-r1.json",
                          "note": "run-r1 executed→blocked→队列 open"}],
        },
    ]


# ---------------------------------------------------------------------------
# 投影载荷组装
# ---------------------------------------------------------------------------

def build_projection(*, session_date: str, evaluator_code_sha256: str,
                     metrics, aux_scales, matrix, blockers,
                     corpus_denominator) -> dict:
    """全量投影载荷（编排侧注入盘上实测值与解析产物）。"""
    missing = [m["metric_id"] for m in metrics
               if m["metric_id"] not in METRIC_IDS]
    if missing:
        raise ValueError(f"build_projection: 未知指标 {missing}")
    have = {m["metric_id"] for m in metrics}
    if have != set(METRIC_IDS):
        raise ValueError(f"build_projection: 指标缺失 {set(METRIC_IDS)-have}")
    ordered = [next(m for m in metrics if mid == m["metric_id"])
               for mid in METRIC_IDS]
    return {
        "schema_version": SCHEMA_VERSION,
        "projection_id": f"{PROJECTION_ID}-{PROJECTION_REVISION}",
        "revision": PROJECTION_REVISION,
        "session_date": session_date,
        "session_date_basis": "人工会话声明日期常量（非机器 wall-clock）",
        "spec_basis": SPEC_SECTION,
        "mode": ("read_only_projection；本包不申请 TL-6 出口门 closure"
                 "（blocked 如实）"),
        "evaluator": {
            "name": "pcbflow-v3-health-projection",
            "version": "1.0",
            "code_sha256": evaluator_code_sha256,
        },
        "evaluation_metadata": {"evaluated_at": None, "elapsed_s": None,
                                "host": None},
        "corpus_denominator": corpus_denominator,
        "metrics": ordered,
        "auxiliary_scales": aux_scales,
        "readiness_matrix": matrix,
        "open_production_blockers": blockers,
    }


def corpus_denominator_block(by_dataset, by_split) -> dict:
    """语料分母——由编排侧从 dataset manifest 实测装配（total=by_dataset
    实测之和，不硬编码库数/板数；S16 首投影装配为三库 100 板，S23 起经
    :func:`corpus_denominator_block_v3` 并入 corpus-r2-r1 为四库）。

    note 文本为 S16 时代口径（v2/v3 均整字覆写，不外泄到现行投影）；
    by_split 按库透传——允许库间异构键（已定 split 用 train/validation/
    holdout，未定 split 的库以显式键分列，口径见 v3 docstring）。
    real_profiles_in_domain=37 为 TL-5 门分母域内板数（pcbbm 2+pcbench
    35），非语料板数，不随语料入库增长（S23 保守不动，如实注记）。
    """
    total = sum(int(v) for v in by_dataset.values())
    return {
        "total_boards": total,
        "by_dataset": dict(sorted(by_dataset.items())),
        "by_split": by_split,
        "real_profiles_in_domain": 37,
        "note": ("kicad-demos-r1（17 板，KiCad 8.99–10.99 格式）在现行"
                 "转换器兼容域（KiCad5 20171130）外——零转换如实；"
                 "37 profile=域内板（pcbbm 2+pcbench 35）"),
    }


# ---------------------------------------------------------------------------
# 健康度 gate：机器谓词 + gate record
# ---------------------------------------------------------------------------

def gate_predicates(projection, measured_hashes) -> tuple:
    """四机器谓词；返回 (predicates, failure_codes)。

    ``measured_hashes``: {repo_rel_path: sha256}——编排侧盘上实测。
    """
    failures: list = []
    metrics = projection["metrics"]

    # P1 投影可计算性：九描述字段齐全+status 枚举+载荷结构完整
    p1_details = []
    for m in metrics:
        missing = [k for k in DESCRIPTOR_KEYS if k not in m]
        if missing:
            p1_details.append(f"{m['metric_id']}: 缺字段 {missing}")
        if m.get("baseline") is None and not m.get("baseline_basis"):
            p1_details.append(f"{m['metric_id']}: baseline 为 null 须带 "
                              "baseline_basis（诚实标注基线未建立）")
        if m["metric_id"] in COUNT_METRIC_IDS:
            if m.get("denominator") is None and not m.get(
                    "denominator_basis"):
                p1_details.append(f"{m['metric_id']}: 计数型指标 "
                                  "denominator=null 须带 denominator_basis")
        else:
            den = m.get("denominator")
            if not isinstance(den, int) or isinstance(den, bool) or den < 0:
                p1_details.append(f"{m['metric_id']}: 比值指标 denominator "
                                  f"须为非负整数，实测 {den!r}")
        if m.get("status") not in STATUSES:
            p1_details.append(f"{m['metric_id']}: status 非法")
    aux = projection.get("auxiliary_scales", {})
    for key in ("dag_blocked", "physics_coverage",
                "required_report_freshness", "queue_aging"):
        if key not in aux:
            p1_details.append(f"auxiliary_scales 缺 {key}")
    rows = projection.get("readiness_matrix", {}).get("rows", [])
    if len(rows) < 9:
        p1_details.append(f"readiness 行数 {len(rows)} < 9")
    if projection.get("readiness_matrix", {}).get(
            "production_signoff_ready") is not False:
        p1_details.append("production_signoff_ready 非 false")
    if not projection.get("open_production_blockers"):
        p1_details.append("open_production_blockers 空")
    p1 = not p1_details
    if not p1:
        failures.extend(f"projection_incomplete:{d}" for d in p1_details)

    # P2 分母诚实性：not_available ⇔ 分母 0（比值型）；value 算术一致
    p2_details = []
    for m in metrics:
        mid, st = m["metric_id"], m["status"]
        if mid in COUNT_METRIC_IDS:
            if st == STATUS_VALUE and not isinstance(m.get("value"), int):
                p2_details.append(f"{mid}: 计数型 value 非整数")
            continue
        den = m.get("denominator")
        if st == STATUS_VALUE:
            if not den or den <= 0:
                p2_details.append(f"{mid}: value 态但分母 {den}")
            else:
                expect = m.get("numerator", 0) / den
                if abs(m.get("value", -1) - expect) > 1e-9:
                    p2_details.append(f"{mid}: value 与 numerator/denominator "
                                      "不一致")
        elif st == STATUS_NOT_AVAILABLE:
            if den not in (None, 0):
                p2_details.append(f"{mid}: not_available 但分母 {den}≠0")
            if not m.get("reason"):
                p2_details.append(f"{mid}: not_available 缺 reason")
        elif st == STATUS_BLOCKED and not m.get("reason"):
            p2_details.append(f"{mid}: blocked 缺 reason")
    p2 = not p2_details
    if not p2:
        failures.extend(f"denominator_dishonest:{d}" for d in p2_details)

    # P3 not_available 不冒充数值
    p3_details = []
    for m in metrics:
        if m["status"] in (STATUS_NOT_AVAILABLE, STATUS_BLOCKED):
            if m.get("value") is not None or m.get("numerator") is not None:
                p3_details.append(f"{m['metric_id']}: 无值态携带数值")
    aux3 = projection.get("auxiliary_scales", {})
    for key in ("not_tracked_here",):
        for k, v in aux3.get(key, {}).items():
            if "not_available" not in str(v):
                p3_details.append(f"aux.{key}.{k}: 未跟踪项未标 not_available")
    p3 = not p3_details
    if not p3:
        failures.extend(f"na_mimics_value:{d}" for d in p3_details)

    # P4 证据 hash 对账：每个证据指针与编排侧盘上实测一致
    p4_details = []
    for m in metrics:
        for e in m.get("evidence", []):
            p = e.get("path")
            if p not in measured_hashes:
                p4_details.append(f"{m['metric_id']}: 证据 {p} 无实测 hash")
            elif measured_hashes[p] != e.get("sha256"):
                p4_details.append(f"{m['metric_id']}: 证据 {p} hash 不符")
    for row in rows:
        for e in row.get("evidence", []):
            if e.get("self_reference"):
                continue
            p = e.get("path")
            if p not in measured_hashes:
                p4_details.append(f"readiness[{row['gate']}]: 证据 {p} "
                                  "无实测 hash")
            elif measured_hashes[p] != e.get("sha256"):
                p4_details.append(f"readiness[{row['gate']}]: 证据 {p} "
                                  "hash 不符")
    p4 = not p4_details
    if not p4:
        failures.extend(f"evidence_hash_mismatch:{d}" for d in p4_details)

    predicates = [
        {"id": "projection_computability", "value": p1,
         "evidence": ("四指标九描述字段+四辅助刻度+readiness 9 行+"
                      "signoff=false+blockers 非空"
                      if p1 else "; ".join(p1_details))},
        {"id": "denominator_honesty", "value": p2,
         "evidence": ("分母 0⇔not_available；value 态算术一致"
                      if p2 else "; ".join(p2_details))},
        {"id": "not_available_not_value", "value": p3,
         "evidence": ("无值态不带 value/numerator" if p3
                      else "; ".join(p3_details))},
        {"id": "evidence_hash_reconciliation", "value": p4,
         "evidence": ("全部证据指针与盘上实测 sha256 一致" if p4
                      else "; ".join(p4_details))},
    ]
    return predicates, failures


def build_gate_record(*, projection, projection_sha256: str,
                      projection_path: str, predicates, failure_codes,
                      inputs, evaluator_code_sha256: str) -> dict:
    """健康度 gate-record（含 TL-6 出口门 blocked 如实，不申请 closure）。"""
    ok = all(p["value"] for p in predicates)
    return {
        "command": "v3-health-projection",
        "status": "ok",
        "verify_errors": [],
        "gate_core_hash": projection_sha256,
        "gate_record": {
            "schema_version": SCHEMA_VERSION,
            "gate_id": GATE_ID,
            "gate_kind": "health_projection",
            "result": "pass" if ok else "fail",
            "predicate_version": PREDICATE_VERSION,
            "profile_id": "training-loop",
            "project_id": "pcbflow-v3",
            "snapshot_revision": PROJECTION_REVISION,
            "evaluator": {
                "name": "pcbflow-v3-health-projection",
                "version": "1.0",
                "code_sha256": evaluator_code_sha256,
            },
            "evaluation_metadata": {"evaluated_at": None, "elapsed_s": None,
                                    "host": None},
            "projection_ref": {"path": projection_path,
                               "sha256": projection_sha256},
            "inputs": inputs,
            "required_predicates": predicates,
            "failure_codes": failure_codes,
            "exit_gate": {
                "gate_id": EXIT_GATE_ID,
                "result": "blocked",
                "closure_claimed": False,
                "reason": ("open production blockers 未清：BL-1 布线引擎/"
                           "TD7 替代、BL-2 TL-3 真实物理证据、BL-3 TL-4 "
                           "执行类谓词、BL-4 Critic 校准域+正式模型"),
                "open_blockers": [b["blocker_id"] for b
                                  in projection["open_production_blockers"]],
                "note": ("本 gate record 的 result=pass 只断言『投影完整性"
                         "』（可计算/诚实/可对账），不断言 TL-6 出口门通过；"
                         "出口门独立为 blocked 如实"),
            },
            "cycle_check": {"acyclic": True, "topological_order": []},
        },
    }


# ---------------------------------------------------------------------------
# S22（TL-6 健康度重投影 v2）增量装配
# ---------------------------------------------------------------------------
# 纪律：以下全部为 v2 新增纯函数/包装（复用上方 v1 函数并覆写身份字段）；
# v1 函数与其语义零改动——s16 编排脚本以同参重跑仍产出 byte 级一致的
# v3-tl6-r1 投影（S16 冻结件一字不动的机制保障）。

PROJECTION_REVISION_V2 = "v3-tl6-r2"
DIFF_SCHEMA = "projection-diff-v1"
V2_PRIOR_FROZEN_ANCHOR = ("98677d11", "66135e61")  # v1 冻结件 sha256 前 8


def _set_revision(rec: dict, revision: str) -> dict:
    rec["revision"] = revision
    return rec


def project_manual_queue_multi(ledgers, *,
                               revision: str = PROJECTION_REVISION_V2,
                               baseline=None, baseline_basis=None) -> dict:
    """v2：多 run 账本队列投影——各账本独立验链，open 项跨账本合并。

    ``ledgers``: [{path, sha256, events}]（编排侧逐行解析+盘上实测 hash）。
    单账本语义与 :func:`project_manual_queue` 一致（终态事件闭合即出队）；
    任一账本链校验失败 → blocked（trust invalid，无数值）。时间窗仍以
    事件序号表达（禁 wall-clock），按账本分列。
    """
    rec = _metric_base(
        "manual_queue_length",
        dataset=(f"queue-event-ledger × {len(ledgers)}"
                 "（多 run 账本合取，逐账本验链）"),
        definition=("当前 revision 中 blocked/disagreement 且未关闭的 "
                    "queue item 数（open enqueue 后无终态事件；多账本取并集）"),
        denominator=None,
        baseline=baseline,
        baseline_basis=baseline_basis,
        threshold=("无固定阈值；下降不自动表示质量改善（SPEC §4 原文）；"
                   "抽样审计分流见 queue.audit_decision"),
        window=None,
        profile="training-loop（全项目队列）",
        reason=None,
    )
    rec["denominator_basis"] = "count_metric_no_denominator"
    rec["evidence"] = [evidence_ref(l["path"], l["sha256"])
                       for l in ledgers]

    per_ledger = []
    by_reason: dict = {}
    by_last_event: dict = {}
    open_items: list = []
    events_total = 0
    enqueued_total = 0
    for l in ledgers:
        events = l["events"]
        try:
            errs = queue.verify_chain(events)
        except (KeyError, TypeError, ValueError) as exc:
            return _finish_blocked(
                rec, f"trust_invalid: 账本结构非法（{l['path']}：{exc}）")
        if errs:
            return _finish_blocked(
                rec, f"trust_invalid: 账本链校验失败（{l['path']}）{errs}")
        summary = queue.projection_summary(events)
        last_seq = max((ev.get("event_seq", 0) for ev in events),
                       default=None)
        oldest = summary["oldest_item_seq"]
        opens = [it["item_id"] for it in queue.current_queue(events)]
        per_ledger.append({
            "path": l["path"],
            "total_events": summary["total_events"],
            "last_event_seq": last_seq,
            "oldest_open_seq": oldest,
            "events_since_oldest_enqueue": (
                (last_seq - oldest)
                if (last_seq is not None and oldest is not None) else None),
            "queue_length": summary["queue_length"],
            "open_items": opens,
        })
        for k, v in summary["by_reason_code"].items():
            by_reason[k] = by_reason.get(k, 0) + int(v)
        for k, v in summary["by_last_event"].items():
            by_last_event[k] = by_last_event.get(k, 0) + int(v)
        open_items.extend(opens)
        events_total += summary["total_events"]
        enqueued_total += sum(1 for ev in events
                              if ev.get("event") == "enqueue")

    rec["window"] = {
        "unit": "ledger_event_seq_multi",
        "ledgers": per_ledger,
        "wall_clock": "not_used（账本无 epoch 字段；事件序号口径，禁 wall-clock）",
    }
    rec["aux"] = {
        "by_reason_code": by_reason,
        "by_last_event": by_last_event,
        "input_volume": {"events_total": events_total,
                         "items_enqueued_total": enqueued_total,
                         "ledgers": len(ledgers)},
        "human_capacity": ("not_available（账本无人工容量/吞吐字段——"
                           "如实不编造）"),
        "open_items": open_items,
    }
    total_open = sum(p["queue_length"] for p in per_ledger)
    return _set_revision(
        _finish_value(rec, numerator=total_open, denominator=None,
                      value=total_open), revision)


def project_critic_agreement_v2(critic_runs, queue_events, *,
                                record_evidence, calibration_observation,
                                revision: str = PROJECTION_REVISION_V2,
                                baseline=None, baseline_basis=None) -> dict:
    """v2：装配侧一致率（run 级）+ 校准侧实测分列（不混写）。

    装配侧语义与 :func:`project_critic_agreement` 完全一致（复用其值/分母/
    blocked 逻辑）；v2 增量：
    - aux 携带旗标级 precision/recall=not_available 的诚实理由（run 级
      人工处置无逐旗标 verdict——不冒充数值）；
    - ``calibration_observation``（编排侧从冻结校准 record 注入，逐条带
      path+sha256）单列校准侧实测——是 advisory 侧比较器输出，不是本指标
      的 precision/recall，不进门谓词。
    """
    rec = project_critic_agreement(critic_runs, queue_events,
                                   record_evidence=record_evidence)
    _set_revision(rec, revision)
    if baseline_basis is not None:
        rec["baseline_basis"] = baseline_basis
    if baseline is not None:
        rec["baseline"] = baseline

    valid_runs = [r for r in critic_runs
                  if r.get("critic_status") == "executed"
                  and r.get("input_hashes_match") is True]
    item_ref = {ev.get("item_id"): ev.get("critic_ref")
                for ev in queue_events if ev.get("event") == "enqueue"}
    verdict_item_ids = {ev.get("item_id") for ev in queue_events
                        if ev.get("event") in TERMINAL_EVENTS}
    verdict_refs = {item_ref[i] for i in verdict_item_ids
                    if item_ref.get(i)}
    verdicted = [r for r in valid_runs if r.get("critic_ref") in verdict_refs]

    flags_total = sum(int(r.get("flags_total", 0)) for r in critic_runs)
    abstain_total = sum(int(r.get("abstain_count", 0)) for r in critic_runs)
    boards: dict = {}
    for r in critic_runs:
        for pid, n in (r.get("board_flag_counts") or {}).items():
            boards[pid] = boards.get(pid, 0) + int(n)
    worst_board = (max(boards, key=lambda k: (boards[k], k))
                   if boards else None)
    calibrations = sorted({json_scalar(r.get("in_calibrated_range"))
                           for r in critic_runs})
    na_flag = "not_available（run 级人工处置无逐旗标 verdict——无数据源，不冒充）"
    rec["aux"] = {
        "runs_total": len(critic_runs),
        "runs_executed_valid": len(valid_runs),
        "runs_with_human_verdict": len(verdicted),
        "flags_total": flags_total,
        "abstain_count": abstain_total,
        "board_flag_counts_merged": dict(sorted(boards.items())),
        "worst_board_by_flags": worst_board,
        "in_calibrated_range_observed": calibrations,
        "flag_level_metrics": {
            "precision": na_flag, "recall": na_flag,
            "fpr": na_flag, "fnr": na_flag,
            "note": ("人工处置=run 级全量 advisory 登记（APR-0007/0010），"
                     "未对旗标逐条判对错——旗标级混淆矩阵在装配侧无数据源"),
        },
        "calibration_side_measured": calibration_observation,
        "calibration_side_basis": ("校准侧实测=advisory 侧比较器输出"
                                   "（calibration-run-*.json 冻结件，非门、"
                                   "不翻转任何谓词）；度量对象=校准域种子 GT "
                                   "上的 reader 定位能力，与装配侧 run 级"
                                   "一致率分列，不得混写"),
        "calibration_note": ("校准域=种子标注集在案（calibration-domain-v1 "
                             "seed_annotation_only / v2 "
                             "process_formalized_threshold_proposal_pending）；"
                             "两轮实测均未达 proposal_only 提案达标线；正式"
                             "采纳前 in_calibrated_range 谓词语义不变恒 False、"
                             "「无旗」语义不可行使、自动分流恒 blocked"
                             "（fail-closed 如实）"),
    }
    return rec


def project_proposer_acceptance_v2(candidates, human_disposition,
                                   machine_gate, *, patch_evidence,
                                   revision: str = PROJECTION_REVISION_V2,
                                   baseline=None, baseline_basis=None) -> dict:
    """v2 包装：语义与 v1 完全一致（无新 adoption 事件），仅覆写 revision
    与基线（前一 revision 冻结值如实作基线）。"""
    rec = project_proposer_acceptance(candidates, human_disposition,
                                      machine_gate,
                                      patch_evidence=patch_evidence)
    _set_revision(rec, revision)
    if baseline_basis is not None:
        rec["baseline_basis"] = baseline_basis
    if baseline is not None:
        rec["baseline"] = baseline
    return rec


def project_non_regression_v2(holdout_backtests, *, evidence,
                              reference_batch, evidence_extra=None,
                              revision: str = PROJECTION_REVISION_V2) -> dict:
    """v2：语义与 v1 一致（autotune 执行分母仍如实为 0）+ 参考态证据层。

    ``reference_batch``（编排侧从 k9-route-check-batch summary 实测注入）：
    作为 k9 转换域参考态回归证据层单列进 aux——它验证「转换复现原始板
    参考态」，不是 autotune 不回退执行面：不改本指标分母/状态、不入
    TL-5 门分母（BL 清单语义不变）。
    """
    rec = project_non_regression(holdout_backtests, evidence=evidence)
    _set_revision(rec, revision)
    if evidence_extra:
        rec["evidence"] = rec["evidence"] + [
            evidence_ref(e["path"], e["sha256"]) for e in evidence_extra]
    rec["aux"]["reference_state_batch"] = reference_batch
    return rec


def corpus_denominator_block_v2(by_dataset, by_split, *,
                                conversion_coverage) -> dict:
    """v2 语料分母（S22 装配契约=三库 r1 100 板）+ 转换域覆盖更新
    （S18 k9 扩展）。

    note 文本为三库时代口径（对 S22 装配如实）；S23 起四库口径走
    :func:`corpus_denominator_block_v3`。本函数输出对 s22 同参重跑保持
    字节稳定（v1/v2 语义零漂移纪律，s16/s22 冻结件可精确重现）。
    """
    block = corpus_denominator_block(by_dataset, by_split)
    block["conversion_domain_coverage"] = conversion_coverage
    block["note"] = ("kicad-demos-r1 17 板已由 S18 k9 转换器扩展入转换域"
                     "（manifest r2，raw_hash 与 r1 全等）——转换域覆盖 "
                     "83→100 板（S18 入账口径）；r1 manifest 与三库分母 "
                     "100 板不变；37 profile=TL-5 门分母域内板（pcbbm 2+"
                     "pcbench 35），门分母语义不变")
    return block


def readiness_matrix_v2(evidence) -> dict:
    """v2 readiness matrix：逐格重评（与 v1 同 9 行键；状态/依据见各行）。"""
    rows_spec = [
        ("TL-0-G1", "pass",
         "两个非 Rev-C smoke profile 全链 ok（APR-0001 人工范围已批）；"
         "v2 重评无变化"),
        ("TL-1-G1", "pass",
         "ledger/judge/disposition/gate 合同 pass（APR-0002 schema 基线已批）；"
         "v2 重评无变化"),
        ("TL-2", "partial_pass_queue_closed",
         "v2 重评（状态自 v1 partial_pass_with_open_queue 变更）：合同+库级 "
         "pass；两轮 advisory run（run-r1 7 旗/run-r2 12 旗 5 abstain）均 "
         "executed→blocked→人工处置闭合（APR-0007/0010），两账本队列=0；"
         "人工对两 run 旗标全量 advisory 登记（装配侧一致率 2/2）；校准域="
         "种子在案未达标（两轮实测 gt_recall 0.25），达标阈值=proposal_only "
         "待人工批准；读取者=子代理代位（untrusted），正式模型接入未发生"
         "（APR-0005 advisory_only）→ 自动分流仍恒 blocked"),
        ("TL-3-G1", "fail",
         "required 实配完成；机器裁决 fail 如实（screening 级合成证据满足 "
         "不了 required 级 authority/容差/批准；coverage=100%≠pass）；"
         "v2 重评无变化"),
        ("TL-4-G", "fail",
         "S9 解锁评估（路径 b）+v2 复评 fail 维持：holdout 执行分母 0、"
         "adoption=human_approved_machine_blocked（APR-0004 人工侧在场）、"
         "零 apply；S22 无新 adoption 事件，v2 重评无变化"),
        ("TL-5-G", "pass",
         "v4 机器复评 pass（D17 参考态验证口径）：37 profile 主路径 6/6 段 "
         "executed；S18 k9 转换域扩展（转换域覆盖 100 板）+S21 route/check "
         "参考态批（17/17 consistency pass）为补充证据层——不入本门分母"
         "（37 profile 不变）、不构成布线生成/泛化能力主张"),
        ("TD7-QUAL-G", "archived",
         "S13 收档（ARC-0001）：S11 pass=历史资格证据冻结只读，不得引用为"
         "现行能力；质量面终局 9/9 拒收；重开=新引擎/换 backend 重走 "
         "qualification（ARC-0002/0003/0004 挂账全处置）；v2 重评无变化"),
        ("TL-6", "blocked",
         "本包=v2 重投影（S22）：四指标活算更新+readiness 逐格重评+逐格"
         "差异表（projection-diff-v1-to-v2.json）；出口门 blocked 如实，"
         "不申请 closure——open production blockers 见 open_blockers"),
        ("production_signoff_ready", "false",
         "L7 闭门律：TL-3/TL-4 fail+TL-6 blocked+布线引擎缺 → 恒 false；"
         "任何投影/gate pass 不构成产品化声明"),
    ]
    rows = []
    for key, status, note in rows_spec:
        evs = evidence.get(key)
        if not evs and key != "TL-6":
            raise ValueError(f"readiness_matrix_v2: 行 {key} 缺证据指针")
        items = [evidence_ref(e["path"], e["sha256"])
                 for e in (evs or [])]
        if key == "TL-6":
            items = [{"path": "out/v3-tl6/health-projection-v2.json",
                      "sha256": None, "sha256_8": None,
                      "self_reference": True,
                      "note": "本记录自身；sha256 由 gate record inputs 记录"}]
        rows.append({"gate": key, "status": status, "note": note,
                     "evidence": items})
    return {
        "rows": rows,
        "production_signoff_ready": False,
        "self_signoff_forbidden": "L7 缺证据闭门律",
    }


def open_production_blockers_v2() -> list:
    """v2 BL 清单重评：BL-1..BL-3 无变化；BL-4 如实重写（不翻 resolved）。"""
    base = open_production_blockers()
    bl4 = {
        "blocker_id": "BL-4",
        "title": "Critic 校准域 + 正式模型",
        "status": "open（种子在案、未达标、阈值待人工批准）",
        "detail": ("v2 重评（不翻 resolved）：校准域种子在案（"
                   "calibration-domain-v1 seed_annotation_only / v2 "
                   "process_formalized_threshold_proposal_pending；"
                   "APR-0008 批准≠达标）；两轮校准实测未达标"
                   "（v1 gt_recall 0.25/precision 0.2；v2 "
                   "gt_recall 0.25/precision 0.142857，metric v2 面积比"
                   "上限下）；达标阈值与 metric v2 正式化待人工批准"
                   "（calibration-process-v1 §5 proposal_only）——流程规程"
                   "在案不等于 resolved；正式采纳前 critic_calibration_in_range "
                   "谓词语义不变恒 False、「无旗」语义不可行使、自动分流恒 "
                   "blocked；读取者=子代理代位（输出恒 untrusted），正式模型"
                   "接入未发生"),
        "unblocks": ["TL-2 自动分流", "critic_agreement_rate 分母"],
        "evidence": [
            {"path": "out/v3-tl2/calibration/calibration-domain-v2.json",
             "note": "种子在案（status=process_formalized_threshold_"
                     "proposal_pending）"},
            {"path": "out/v3-tl2/calibration/calibration-run-v2.json",
             "note": "v2 实测 gt_recall 0.25 / precision 0.142857（未达提案线）"},
            {"path": "out/v3-tl2/calibration/calibration-process-v1.md",
             "note": "流程规程在案；达标阈值=proposal_only 待人工批准"},
            {"path": "out/v3-tl2/critic-runs/run-r2/"
                     "critic-run-record-CR-run-r2.json",
             "note": "run-r2 executed→blocked→APR-0010 处置闭合"},
        ],
    }
    return [base[0], base[1], base[2], bl4]


def build_projection_v2(*, session_date, evaluator_code_sha256, metrics,
                        aux_scales, matrix, blockers, corpus_denominator,
                        evaluator_version: str = "1.1") -> dict:
    """v2 投影载荷：复用 v1 组装（指标全集校验不变），覆写身份字段。"""
    projection = build_projection(
        session_date=session_date,
        evaluator_code_sha256=evaluator_code_sha256,
        metrics=metrics, aux_scales=aux_scales, matrix=matrix,
        blockers=blockers, corpus_denominator=corpus_denominator)
    projection["revision"] = PROJECTION_REVISION_V2
    projection["projection_id"] = f"{PROJECTION_ID}-{PROJECTION_REVISION_V2}"
    projection["evaluator"]["version"] = evaluator_version
    projection["mode"] = ("read_only_projection；v2 重投影（S22；口径与谓词"
                          "不变，逐格差异见 projection-diff-v1-to-v2.json）；"
                          "本包不申请 TL-6 出口门 closure（blocked 如实）")
    return projection


def build_gate_record_v2(*, projection, projection_sha256: str,
                         projection_path: str, predicates, failure_codes,
                         inputs, evaluator_code_sha256: str) -> dict:
    """v2 gate record：复用 v1 组装，覆写 snapshot_revision。"""
    gate = build_gate_record(
        projection=projection, projection_sha256=projection_sha256,
        projection_path=projection_path, predicates=predicates,
        failure_codes=failure_codes, inputs=inputs,
        evaluator_code_sha256=evaluator_code_sha256)
    gate["gate_record"]["snapshot_revision"] = PROJECTION_REVISION_V2
    return gate


def _diff_walk(a, b, path: str, out: list) -> None:
    """递归逐格比较：dict 按 key 并集、list 按下标对齐、标量按类型+值。"""
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            p = f"{path}.{k}" if path else k
            if k not in a:
                out.append({"path": p, "kind": "added", "after": b[k]})
            elif k not in b:
                out.append({"path": p, "kind": "removed", "before": a[k]})
            else:
                _diff_walk(a[k], b[k], p, out)
    elif isinstance(a, list) and isinstance(b, list):
        for i in range(max(len(a), len(b))):
            p = f"{path}[{i}]"
            if i >= len(a):
                out.append({"path": p, "kind": "added", "after": b[i]})
            elif i >= len(b):
                out.append({"path": p, "kind": "removed", "before": a[i]})
            else:
                _diff_walk(a[i], b[i], p, out)
    elif type(a) is not type(b) or a != b:
        out.append({"path": path, "kind": "changed",
                    "before": a, "after": b})


def build_projection_diff(old, new) -> dict:
    """逐格差异表（纯函数、确定性；v1→v2 的 path 级 before/after）。"""
    changes: list = []
    _diff_walk(old, new, "", changes)
    summary = {"added": 0, "removed": 0, "changed": 0}
    for c in changes:
        summary[c["kind"]] += 1
    return {
        "diff_schema": DIFF_SCHEMA,
        "from_projection_id": old.get("projection_id"),
        "to_projection_id": new.get("projection_id"),
        "from_revision": old.get("revision"),
        "to_revision": new.get("revision"),
        "changes": changes,
        "summary": summary,
    }


# ---------------------------------------------------------------------------
# S23（TL-6 健康度重投影 v3；修正包 P1-C 指标语义更正）增量装配
# ---------------------------------------------------------------------------
# 纪律：以下全部为 v3 新增纯函数（v1/v2 函数与其语义零改动——s16/s22 编排
# 脚本以同参重跑仍产出 byte 级一致的冻结投影）。P1-C 缺陷：v1/v2 的
# critic_agreement_rate 把「编排侧从 APR 处置推导的 run 级
# human_supports_flags 登记」（scripts/s22_health_orchestrate_v2.py apr_
# supports_flags：kind=accept + critic_flags_advisory 在 fact_refs 即 True）
# 计成逐旗标一致率分母 2 分子 2；实际 APR-0007/0010=run 级全量 advisory
# 登记+队列闭合，无任何逐旗标正确性 verdict——队列 approve 不能解释为
# 「人工认可旗标全对」。v3 将其拆分为：
#   - critic_disposition_completion_rate（流程指标：人工处置完成率，
#     队列终态事件口径，预期 2/2=1.0）；
#   - critic_judgment_agreement_rate（质量指标：逐旗标判断一致率，
#     无逐旗标 verdict 数据源 → not_available，不冒充数值）。
# 队列闭合≠旗标正确性结论；无人工逐旗标裁定前不得由修正程序代创标签。

PROJECTION_REVISION_V3 = "v3-tl6-r3"
METRIC_IDS_V3 = ("manual_queue_length", "critic_disposition_completion_rate",
                 "critic_judgment_agreement_rate", "proposer_acceptance_rate",
                 "cross_board_non_regression_rate")
RETIRED_METRIC_ID_V3 = "critic_agreement_rate"
V2_FROZEN_PROJECTION_ANCHOR = "990bbf98"   # v2 冻结件 sha256 前 8（先验锚）
V2_FROZEN_AGGREEMENT_VALUE = 1.0           # v2 冻结 critic_agreement_rate 值
V2_FROZEN_AGGREEMENT_FRACTION = "2/2"
METRIC_CORRECTION_NOTE_SCHEMA = "metric-correction-note-v1"
METRIC_CORRECTION_NOTE_ID = "HP-METRIC-CORRECTION-v1"


def _metric_base_v3(metric_id: str, *, dataset: str, definition: str,
                    denominator, baseline, threshold, window, profile: str,
                    reason=None, baseline_basis: str | None = None) -> dict:
    """v3 指标基座：与 _metric_base 同构，指标 id 校验域=METRIC_IDS_V3
    （不与 v1/v2 的 METRIC_IDS 混域，v1/v2 校验行为零变化）。"""
    if metric_id not in METRIC_IDS_V3:
        raise ValueError(f"_metric_base_v3: 未知指标 {metric_id!r}")
    return {
        "metric_id": metric_id,
        "spec_section": SPEC_SECTION,
        "dataset": dataset,
        "mode": "read_only_ledger_projection",
        "definition": definition,
        "denominator": denominator,
        "baseline": baseline,
        "threshold": threshold,
        "window": window,
        "profile": profile,
        "revision": PROJECTION_REVISION_V3,
        "status": None,
        "value": None,
        "numerator": None,
        "reason": reason,
        "baseline_basis": baseline_basis,
        "aux": {},
        "evidence": [],
    }


def project_critic_disposition_completion(critic_runs, queue_events, *,
                                          record_evidence,
                                          revision: str = PROJECTION_REVISION_V3,
                                          baseline=None,
                                          baseline_basis=None) -> dict:
    """v3 流程指标：人工处置完成率（不表示、不代理任何旗标判断正确性）。

    分母=已执行+有效（critic_status=executed 且 input_hashes_match）的
    run 数；分子=其中已获人工处置终态（critic_ref 经 enqueue 绑定命中
    queue event ledger 终态事件 approve/reject/expire）的 run 数。
    队列闭合只证明处置流程闭环，不构成逐旗标正确性裁决（P1-C 拆分口径）。
    分母 0 → not_available（未执行不进分母）；record hash 不匹配 → blocked。
    """
    rec = _metric_base_v3(
        "critic_disposition_completion_rate",
        dataset="critic-run-record + queue-event-ledger（人工处置终态侧）",
        definition=("流程指标：人工处置完成率——已执行且输入 hash 对账有效的 "
                    "critic run 中，已获人工处置终态（critic_ref 命中 queue "
                    "event ledger 终态事件）的 run 数占比；不表示、不代理"
                    "任何旗标判断正确性"),
        denominator=None,
        baseline=baseline,
        baseline_basis=baseline_basis,
        threshold=("无自动晋升语义：100% 只说明人工处置流程闭环（P1-C 拆分"
                   "口径）；不构成旗标质量、TL-6 晋升或自动分流证据"),
        window={"unit": "critic_run_set",
                "runs_considered": [r["run_id"] for r in critic_runs]},
        profile="advisory run 分歧项（run 级，非板级汇总）",
    )
    if rec["baseline_basis"] is None:
        rec["baseline_basis"] = (
            "P1-C 拆分新增流程指标：前一 revision 无对应度量（v2 的 "
            "critic_agreement_rate=1.0（2/2）为语义混用值，不构成基线）"
            "——基线未建立，如实 null")
    rec["evidence"] = [evidence_ref(e["path"], e["sha256"])
                       for e in record_evidence]

    invalid = [r["run_id"] for r in critic_runs
               if r.get("input_hashes_match") is False]
    if invalid:
        return _set_revision(
            _finish_blocked(
                rec, f"trust_invalid: record 输入 hash 对账失败 {invalid}"),
            revision)

    item_ref = {ev.get("item_id"): ev.get("critic_ref")
                for ev in queue_events if ev.get("event") == "enqueue"}
    terminal_item_ids = {ev.get("item_id") for ev in queue_events
                         if ev.get("event") in TERMINAL_EVENTS}
    terminal_refs = {item_ref[i] for i in terminal_item_ids
                     if item_ref.get(i)}
    valid_runs = [r for r in critic_runs
                  if r.get("critic_status") == "executed"
                  and r.get("input_hashes_match") is True]
    disposed = [r for r in valid_runs if r.get("critic_ref") in terminal_refs]
    rec["aux"] = _disposition_aux(critic_runs, valid_runs, disposed,
                                  queue_events)
    denominator = len(valid_runs)
    if denominator == 0:
        rec["denominator"] = 0
        return _set_revision(
            _finish_not_available(
                rec,
                "denominator_zero: 无已执行+有效的 critic run"
                "（「未执行不进分母」）"),
            revision)
    return _set_revision(
        _finish_value(rec, numerator=len(disposed), denominator=denominator,
                      value=len(disposed) / denominator), revision)


def _disposition_aux(critic_runs, valid_runs, disposed, queue_events) -> dict:
    """处置完成率 aux：run 级处置簿账（不携带任何旗标对错语义）。"""
    terminal_kinds: dict = {}
    for ev in queue_events:
        kind = ev.get("event")
        if kind in TERMINAL_EVENTS:
            terminal_kinds[kind] = terminal_kinds.get(kind, 0) + 1
    disposed_ids = [r["run_id"] for r in disposed]
    return {
        "metric_kind": "process",
        "runs_total": len(critic_runs),
        "runs_executed_valid": len(valid_runs),
        "runs_with_disposition_terminal": len(disposed),
        "disposed_run_ids": disposed_ids,
        "runs_awaiting_disposition": [r["run_id"] for r in valid_runs
                                      if r["run_id"] not in disposed_ids],
        "terminal_event_kinds": dict(sorted(terminal_kinds.items())),
        "note": ("流程指标：人工处置完成率只度量处置闭环（队列终态事件口径），"
                 "不表示、不代理任何旗标判断正确性——旗标级对错见 "
                 "critic_judgment_agreement_rate（P1-C 拆分口径）"),
    }


def project_critic_judgment_agreement(critic_runs, queue_events, *,
                                      record_evidence,
                                      calibration_observation,
                                      revision: str = PROJECTION_REVISION_V3,
                                      baseline=None,
                                      baseline_basis=None) -> dict:
    """v3 质量指标：逐旗标人工判断一致率——当前 not_available（不冒充数值）。

    定义=逐旗标人工正确性裁定中支持旗标数/已裁定旗标数（与流程指标
    critic_disposition_completion_rate 分列）；当前数据源缺失：
    APR-0007/0010=run 级全量 advisory 登记+队列闭合，非逐旗标对错裁决
    ——无人工逐旗标裁定前不得由修正程序代创标签。aux 沿用 v2 的旗标计数
    与 not_available 家族，并保留 calibration 侧实测分列（不混写）。
    record hash 不匹配 → blocked（trust invalid，fail-closed）。
    """
    rec = _metric_base_v3(
        "critic_judgment_agreement_rate",
        dataset="critic-run-record + 逐旗标人工正确性 verdict（当前缺失）",
        definition=("质量指标：逐旗标人工正确性裁定中支持旗标数/已裁定旗标数"
                    "（与流程指标 critic_disposition_completion_rate 分列；"
                    "SPEC §4「人工支持旗标数/有效分歧项数」一致率语义的唯一"
                    "合法载体）；当前缺逐旗标 verdict 数据源 → not_available"),
        denominator=0,
        baseline=baseline,
        baseline_basis=baseline_basis,
        threshold=("85% 只能是附加条件，不能单独晋升（SPEC §4 原文）；正式"
                   "晋升门=TD5 十条件合取；无逐旗标 verdict 前本指标保持 "
                   "not_available，不冒充数值"),
        window={"unit": "critic_run_set",
                "runs_considered": [r["run_id"] for r in critic_runs]},
        profile="advisory run 分歧项（run 级，非板级汇总）",
    )
    if rec["baseline_basis"] is None:
        rec["baseline_basis"] = (
            "前一 revision（v3-tl6-r2）以「agreement」名义冻结 1.0（2/2），"
            "经 P1-C 更正判定为语义混用值——非数值沿承，不作为本指标基线"
            "（基线未建立，如实 null）")
    rec["evidence"] = [evidence_ref(e["path"], e["sha256"])
                       for e in record_evidence]

    invalid = [r["run_id"] for r in critic_runs
               if r.get("input_hashes_match") is False]
    if invalid:
        return _set_revision(
            _finish_blocked(
                rec, f"trust_invalid: record 输入 hash 对账失败 {invalid}"),
            revision)

    flags_total = sum(int(r.get("flags_total", 0)) for r in critic_runs)
    abstain_total = sum(int(r.get("abstain_count", 0)) for r in critic_runs)
    boards: dict = {}
    for r in critic_runs:
        for pid, n in (r.get("board_flag_counts") or {}).items():
            boards[pid] = boards.get(pid, 0) + int(n)
    worst_board = (max(boards, key=lambda k: (boards[k], k))
                   if boards else None)
    calibrations = sorted({json_scalar(r.get("in_calibrated_range"))
                           for r in critic_runs})
    na_flag = "not_available（无逐旗标人工正确性 verdict——无数据源，不冒充）"
    rec["aux"] = {
        "metric_kind": "quality",
        "runs_total": len(critic_runs),
        "runs_executed_valid": sum(
            1 for r in critic_runs
            if r.get("critic_status") == "executed"
            and r.get("input_hashes_match") is True),
        "flags_total": flags_total,
        "abstain_count": abstain_total,
        "board_flag_counts_merged": dict(sorted(boards.items())),
        "worst_board_by_flags": worst_board,
        "in_calibrated_range_observed": calibrations,
        "flag_level_metrics": {
            "precision": na_flag, "recall": na_flag,
            "fpr": na_flag, "fnr": na_flag,
            "note": ("APR-0007/0010=run 级全量 advisory 登记+队列闭合，"
                     "未对旗标逐条判对错——旗标级混淆矩阵无数据源；队列闭合"
                     "≠旗标正确性结论（P1-C 更正）"),
        },
        "calibration_side_measured": calibration_observation,
        "calibration_side_basis": ("校准侧实测=advisory 侧比较器输出"
                                   "（calibration-run-*.json 冻结件，非门、"
                                   "不翻转任何谓词）；度量对象=校准域种子 GT "
                                   "上的 reader 定位能力，与本指标分列，"
                                   "不得混写"),
        "calibration_note": ("校准域=种子标注集在案（calibration-domain-v1 "
                             "seed_annotation_only / v2 "
                             "process_formalized_threshold_proposal_pending）；"
                             "两轮实测均未达 proposal_only 提案达标线；正式"
                             "采纳前 in_calibrated_range 谓词语义不变恒 False、"
                             "「无旗」语义不可行使、自动分流恒 blocked"
                             "（fail-closed 如实）"),
    }
    rec["denominator"] = 0
    return _set_revision(
        _finish_not_available(
            rec,
            "not_available: 缺逐旗标人工正确性 verdict（APR-0007/0010=run 级"
            "全量 advisory 登记+队列闭合，非逐旗标对错裁决）；无人工逐旗标"
            "裁定前不得由修正程序代创标签"),
        revision)


def corpus_denominator_block_v3(by_dataset, by_split, *,
                                conversion_coverage) -> dict:
    """v3 语料分母（S23 起）：四库实测装配——v1/v2 三库 r1 分母并入
    corpus-r2-r1（板数/tier 从该库 manifest counts.boards/counts.by_tier
    实测，不硬编码；v1/v2 函数输出字节稳定，s16/s22 同参重跑不受影响）。

    by_split 口径（诚实分列，不虚报已定 split）：
    - r1 三库：train/validation/holdout（manifest dataset_splits 已定
      split 求和）；
    - corpus-r2-r1：counts.by_tier 的 train/val-candidate（候选未定
      split——不得计入 train/validation）与 holdout-pool（预冻结池——
      永不参与调参、不计入 holdout、不进不回退执行分母）以显式键
      ``train_val_candidate``/``holdout_pool`` 分列；该库 train/
      validation/holdout 如实为 0。
    转换域覆盖口径不变（S18 入账；corpus-r2-r1 为入库级 parse 门证据，
    未注册入覆盖、不回填）；real_profiles_in_domain 沿用 v1 的 37
    （TL-5 门分母域内板 pcbbm 2+pcbench 35，不随语料入库增长）。

    fail-closed：by_split 每库各键合计必须与 by_dataset 该库板数对账、
    by_split 键必须存在于 by_dataset——不符即 raise（分母诚实性）。
    """
    for ds, sp in by_split.items():
        if ds not in by_dataset:
            raise ValueError(
                f"corpus_denominator_block_v3: by_split 键 {ds!r} 不在 "
                f"by_dataset（fail-closed）")
        if sum(int(v) for v in sp.values()) != int(by_dataset[ds]):
            raise ValueError(
                f"corpus_denominator_block_v3: {ds} by_split 各键合计与 "
                f"by_dataset 板数 {by_dataset[ds]!r} 不符（fail-closed）")
    block = corpus_denominator_block(by_dataset, by_split)
    block["conversion_domain_coverage"] = conversion_coverage
    block["note"] = (
        "四库分母实测装配：r1 三库（pcbbenchmarks-r1/pcbench-r1/"
        "kicad-demos-r1，dataset_splits train/validation/holdout 求和）+ "
        "corpus-r2-r1（manifest counts.boards/by_tier 实测）；"
        "total_boards=四库之和。corpus-r2-r1 split 口径如实：by_tier "
        "train/val-candidate=候选未定 split（by_split 显式键 "
        "train_val_candidate 分列，不虚报 train/validation）；"
        "holdout-pool=预冻结池（显式键 holdout_pool，永不参与调参、"
        "不计入 holdout、不进不回退执行分母）；该库 train/validation/"
        "holdout 如实为 0。转换域覆盖口径不变（S18 入账，见 "
        "conversion_domain_coverage；corpus-r2-r1 为入库级 parse 门证据，"
        "未注册入覆盖、不回填）。real_profiles_in_domain=37=TL-5 门分母"
        "域内板（pcbbm 2+pcbench 35），不随 corpus-r2-r1 入库增长；"
        "门分母语义不变")
    return block


def readiness_matrix_v3(evidence) -> dict:
    """v3 readiness matrix：9 行同键；TL-2/TL-6 note 更新（P1-C 口径）。"""
    rows_spec = [
        ("TL-0-G1", "pass",
         "两个非 Rev-C smoke profile 全链 ok（APR-0001 人工范围已批）；"
         "v3 重评无变化"),
        ("TL-1-G1", "pass",
         "ledger/judge/disposition/gate 合同 pass（APR-0002 schema 基线已批）；"
         "v3 重评无变化"),
        ("TL-2", "partial_pass_queue_closed",
         "v3 重评（P1-C 指标更正口径）：合同+库级 pass；两轮 advisory run"
         "（run-r1 7 旗/run-r2 12 旗 5 abstain）均 executed→人工处置闭合"
         "（APR-0007/0010），两账本队列=0；处置完成率 2/2=流程指标（只证明"
         "处置闭环，不表示旗标判断正确性）；判断一致率 not_available=无逐"
         "旗标 verdict；校准域=种子在案未达标（两轮实测 gt_recall 0.25）；"
         "读取者=子代理代位（untrusted），正式模型接入未发生（APR-0005 "
         "advisory_only）→ 自动分流仍 blocked"),
        ("TL-3-G1", "fail",
         "required 实配完成；机器裁决 fail 如实（screening 级合成证据满足"
         "不了 required 级 authority/容差/批准；coverage=100%≠pass）；"
         "v3 重评无变化"),
        ("TL-4-G", "fail",
         "S9 解锁评估（路径 b）+v2 复评 fail 维持：holdout 执行分母 0、"
         "adoption=human_approved_machine_blocked（APR-0004 人工侧在场）、"
         "零 apply；S23 指标语义更正无新 adoption 事件，v3 重评无变化"),
        ("TL-5-G", "pass",
         "v4 机器复评 pass（D17 参考态验证口径）：37 profile 主路径 6/6 段 "
         "executed；S18 k9 转换域扩展+S21 route/check 参考态批（17/17 "
         "consistency pass）为补充证据层——不入本门分母、不构成布线生成/"
         "泛化能力主张；v3 重评无变化"),
        ("TD7-QUAL-G", "archived",
         "S13 收档（ARC-0001）：S11 pass=历史资格证据冻结只读，不得引用为"
         "现行能力；质量面终局 9/9 拒收；重开=新引擎/换 backend 重走 "
         "qualification（ARC-0002/0003/0004 挂账全处置）；v3 重评无变化"),
        ("TL-6", "blocked",
         "本包=v3 指标语义更正重投影（P1-C/S23）：critic_agreement_rate "
         "拆分为处置完成率（流程，2/2）与判断一致率（not_available），"
         "零门翻转；逐格差异见 projection-diff-v2-to-v3.json、更正说明见 "
         "metric-correction-note-v1.json；出口门 blocked 如实，不申请 "
         "closure——open production blockers 见 open_blockers"),
        ("production_signoff_ready", "false",
         "L7 闭门律：TL-3/TL-4 fail+TL-6 blocked+布线引擎缺 → 恒 false；"
         "任何投影/gate pass 不构成产品化声明"),
    ]
    rows = []
    for key, status, note in rows_spec:
        evs = evidence.get(key)
        if not evs and key != "TL-6":
            raise ValueError(f"readiness_matrix_v3: 行 {key} 缺证据指针")
        items = [evidence_ref(e["path"], e["sha256"])
                 for e in (evs or [])]
        if key == "TL-6":
            items = [{"path": "out/v3-tl6/health-projection-v3.json",
                      "sha256": None, "sha256_8": None,
                      "self_reference": True,
                      "note": "本记录自身；sha256 由 gate record inputs 记录"}]
        rows.append({"gate": key, "status": status, "note": note,
                     "evidence": items})
    return {
        "rows": rows,
        "production_signoff_ready": False,
        "self_signoff_forbidden": "L7 缺证据闭门律",
    }


def open_production_blockers_v3() -> list:
    """v3 BL 清单重评：BL-1..BL-3 与 BL-4 其余字段零变化；BL-4 detail 补
    「队列闭合≠旗标正确性结论（P1-C 更正）」（不翻 resolved）。"""
    base = open_production_blockers_v2()
    bl4 = dict(base[3])
    bl4["detail"] = bl4["detail"] + "；队列闭合≠旗标正确性结论（P1-C 更正）"
    return [base[0], base[1], base[2], bl4]


def build_projection_v3(*, session_date, evaluator_code_sha256, metrics,
                        aux_scales, matrix, blockers, corpus_denominator,
                        evaluator_version: str = "1.2") -> dict:
    """v3 投影载荷：五指标集按 METRIC_IDS_V3 fail-closed 校验（缺失/未知
    即 raise），身份字段与 mode 覆写为 P1-C 指标语义更正口径。"""
    missing = [m["metric_id"] for m in metrics
               if m["metric_id"] not in METRIC_IDS_V3]
    if missing:
        raise ValueError(f"build_projection_v3: 未知指标 {missing}")
    have = {m["metric_id"] for m in metrics}
    if have != set(METRIC_IDS_V3):
        raise ValueError(
            f"build_projection_v3: 指标缺失 {set(METRIC_IDS_V3) - have}")
    ordered = [next(m for m in metrics if mid == m["metric_id"])
               for mid in METRIC_IDS_V3]
    return {
        "schema_version": SCHEMA_VERSION,
        "projection_id": f"{PROJECTION_ID}-{PROJECTION_REVISION_V3}",
        "revision": PROJECTION_REVISION_V3,
        "session_date": session_date,
        "session_date_basis": "人工会话声明日期常量（非机器 wall-clock）",
        "spec_basis": SPEC_SECTION,
        "mode": ("read_only_projection；指标语义更正重投影（P1-C）："
                 "critic_agreement_rate 拆分为处置完成率（流程）与判断"
                 "一致率（not_available）；逐格差异见 "
                 "projection-diff-v2-to-v3.json、更正说明见 "
                 "metric-correction-note-v1.json；本包不申请 TL-6 出口门 "
                 "closure（blocked 如实）"),
        "evaluator": {
            "name": "pcbflow-v3-health-projection",
            "version": evaluator_version,
            "code_sha256": evaluator_code_sha256,
        },
        "evaluation_metadata": {"evaluated_at": None, "elapsed_s": None,
                                "host": None},
        "corpus_denominator": corpus_denominator,
        "metrics": ordered,
        "auxiliary_scales": aux_scales,
        "readiness_matrix": matrix,
        "open_production_blockers": blockers,
    }


def build_gate_record_v3(*, projection, projection_sha256: str,
                         projection_path: str, predicates, failure_codes,
                         inputs, evaluator_code_sha256: str) -> dict:
    """v3 gate record：复用 v1 组装，覆写 snapshot_revision（照 v2 模式；
    exit_gate.reason 保持四 BL blocked 如实）。"""
    gate = build_gate_record(
        projection=projection, projection_sha256=projection_sha256,
        projection_path=projection_path, predicates=predicates,
        failure_codes=failure_codes, inputs=inputs,
        evaluator_code_sha256=evaluator_code_sha256)
    gate["gate_record"]["snapshot_revision"] = PROJECTION_REVISION_V3
    return gate


def build_metric_correction_note(*, session_date: str,
                                 v2_projection_sha256: str,
                                 v3_projection: dict,
                                 v3_projection_sha256: str) -> dict:
    """P1-C 指标更正说明（纯函数；更正对象锚定 v2 冻结件 sha256 前 8
    先验锚，不符即 raise——防对非冻结件出证）。"""
    if not v2_projection_sha256.startswith(V2_FROZEN_PROJECTION_ANCHOR):
        raise ValueError(
            "build_metric_correction_note: 更正对象 hash 先验锚不符（实测 "
            f"{v2_projection_sha256[:8]}…，先验 "
            f"{V2_FROZEN_PROJECTION_ANCHOR}）——v2 冻结件身份不配，拒绝出证")
    metrics = {m.get("metric_id"): m
               for m in v3_projection.get("metrics", [])}
    for mid in ("critic_disposition_completion_rate",
                "critic_judgment_agreement_rate"):
        if mid not in metrics:
            raise ValueError(
                f"build_metric_correction_note: v3 载荷缺拆分指标 {mid}")
    disp = metrics["critic_disposition_completion_rate"]
    judg = metrics["critic_judgment_agreement_rate"]
    disp_frac = (f"{disp.get('numerator')}/{disp.get('denominator')}"
                 if disp.get("status") == STATUS_VALUE else None)
    return {
        "schema_version": SCHEMA_VERSION,
        "note_id": METRIC_CORRECTION_NOTE_ID,
        "note_schema": METRIC_CORRECTION_NOTE_SCHEMA,
        "correction_package": "P1-C",
        "correction_kind": "metric_semantic_split",
        "session_date": session_date,
        "session_date_basis": "人工会话声明日期常量（非机器 wall-clock）",
        "corrects": {
            "path": "out/v3-tl6/health-projection-v2.json",
            "sha256": v2_projection_sha256,
            "sha256_8": v2_projection_sha256[:8],
            "projection_id": "HP-v3-tl6-v3-tl6-r2",
            "revision": "v3-tl6-r2",
            "overwritten": False,
            "overwrite_declaration": ("v2 冻结件不覆写：本更正以新增 v3 文件"
                                      "表达，v1/v2 冻结件零写入、零删除"),
        },
        "corrected_metric": {
            "metric_id": RETIRED_METRIC_ID_V3,
            "v2_frozen_status": "value",
            "v2_frozen_value": V2_FROZEN_AGGREEMENT_VALUE,
            "v2_frozen_fraction": V2_FROZEN_AGGREEMENT_FRACTION,
            "defect": ("v2 的 critic_agreement_rate=1.0（2/2）把编排侧从 APR "
                       "处置推导的 run 级 human_supports_flags 登记（kind="
                       "accept + critic_flags_advisory 在 fact_refs 即 True）"
                       "计成逐旗标一致率分母 2 分子 2；实际 APR-0007/0010="
                       "run 级全量 advisory 登记+队列闭合，无任何逐旗标正确"
                       "性 verdict——队列 approve 不能解释为「人工认可旗标"
                       "全对」（指标语义混用）"),
        },
        "split_into": [
            {"metric_id": "critic_disposition_completion_rate",
             "metric_kind": "process",
             "definition": disp.get("definition"),
             "v3_status": disp.get("status"),
             "v3_value": disp.get("value"),
             "v3_fraction": disp_frac},
            {"metric_id": "critic_judgment_agreement_rate",
             "metric_kind": "quality",
             "definition": judg.get("definition"),
             "v3_status": judg.get("status"),
             "v3_value": judg.get("value"),
             "v3_fraction": None,
             "reason": judg.get("reason")},
        ],
        "renames_and_definition_changes": [
            {"metric_id": RETIRED_METRIC_ID_V3,
             "change_kind": "retired_split",
             "before": ("critic_agreement_rate（v1/v2）：仅在已执行+有效+有"
                        "人工 verdict 的分歧项中，人工支持旗标数/有效分歧项数"
                        "——实际分子来源=APR 处置推导的 run 级登记"),
             "after": ("停用（拆分为下述两指标；v1/v2 冻结件中的历史值保留"
                       "原样、不回写）")},
            {"metric_id": "critic_disposition_completion_rate",
             "change_kind": "added",
             "definition_change": ("新增流程指标：人工处置完成率（队列终态"
                                   "事件口径，v3 实测 2/2=1.0）；不表示、"
                                   "不代理任何旗标判断正确性")},
            {"metric_id": "critic_judgment_agreement_rate",
             "change_kind": "added",
             "definition_change": ("新增质量指标：逐旗标人工正确性裁定支持"
                                   "率；当前无逐旗标 verdict 数据源 → "
                                   "not_available（分母 0，不冒充数值）")},
            {"metric_id": "manual_queue_length",
             "change_kind": "unchanged",
             "detail": "口径不变（多账本队列投影）；仅 revision 覆写 "
                       "v3-tl6-r3"},
            {"metric_id": "proposer_acceptance_rate",
             "change_kind": "unchanged",
             "detail": ("复用 v2 语义（adoption=人工处置∧机器门合取；"
                        "human_approved_machine_blocked）不变；仅 revision "
                        "覆写")},
            {"metric_id": "cross_board_non_regression_rate",
             "change_kind": "unchanged",
             "detail": ("复用 v2 语义（autotune 执行分母 0=not_available+k9 "
                        "参考态证据层单列）不变；仅 revision 覆写")},
        ],
        "readiness_impact": {
            "zero_gate_flip": True,
            "declaration": "零门翻转：本更正不改任何门状态",
            "gate_flips": [],
            "tl6_exit_gate": "TL-6-G 仍 blocked",
            "production_signoff_ready": False,
            "auto_triage": "自动分流仍 blocked",
            "note": ("本更正为指标语义拆分与重投影：不翻转任何谓词结果、"
                     "不产生新 adoption/处置事件、不回写任何冻结件"),
        },
        "frozen_files_no_overwrite": {
            "declaration": ("以下 v1/v2 冻结件零写入、零删除；不覆写、"
                            "不回填；本更正仅新增 v3 文件"),
            "files": [
                {"path": "out/v3-tl6/health-projection.json",
                 "sha256_8": "98677d11"},
                {"path": "out/v3-tl6/health-projection-gate.json",
                 "sha256_8": "66135e61"},
                {"path": "out/v3-tl6/health-projection.sha256",
                 "sha256_8": "2d946cef"},
                {"path": "out/v3-tl6/health-projection-v2.json",
                 "sha256_8": "990bbf98"},
                {"path": "out/v3-tl6/health-projection-gate-v2.json",
                 "sha256_8": "827200ff"},
                {"path": "out/v3-tl6/projection-diff-v1-to-v2.json",
                 "sha256_8": "da22f874"},
            ],
        },
        "superseded_metric_ids": [RETIRED_METRIC_ID_V3],
        "successor_metric_ids": ["critic_disposition_completion_rate",
                                 "critic_judgment_agreement_rate"],
        "accompanies": {"path": "out/v3-tl6/health-projection-v3.json",
                        "sha256": v3_projection_sha256,
                        "sha256_8": v3_projection_sha256[:8],
                        "projection_id": v3_projection.get("projection_id"),
                        "revision": v3_projection.get("revision")},
    }
