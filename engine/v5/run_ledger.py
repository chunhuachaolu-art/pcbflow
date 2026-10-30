# -*- coding: utf-8 -*-
"""L8 逐运行六问理念账本（V5.0-DEV-TASKBOOK §3.8 理念账本与残差、§4 L8；P5③ 交付）。

聚合三个引擎侧数据源为**逐运行**账本工件（进证据链 append-only+原子提交由调用方
按 §3.4 纪律执行；本模块零 I/O、零网络、零 LLM API、零随机零时钟）：

1. **planner generation_trace**（v5.planner 候选的 rule/freedom/effect 留痕，兼容
   selection._normalize_trace 同款两形态：rule 键 / principle_id 键 / 裸字符串）→
   generation_trace_summary：每条被消费的编译规则在哪些候选留痕、涉哪些自由度——
   「生效」问的证据底座（生成侧消费覆盖率 PF 门的逐运行数据源）；
2. **selection 理念账本**（v5.selection select_best 产出的 ledger.principle_ledger，
   六态归类合同）→ six_questions 六问：生效/被忽略/冲突裁决/致淘汰/无可观测影响/
   依据不足，各问给 count + principles + entries（条目=principle_id+evidence 原文）；
3. **executor negotiation_log**（v5.executor 的逐网协商留痕）→ negotiation 节：
   运行裁决、逐网协商/失败计数、log 全文（字符串数组，canonical 稳定）。

工件形状（schema_version="v5.runledger.v1"）：

    {"schema_version", "board_id", "board_sha256",
     "provenance": {"generator", "board_sha256", "inputs": {...}},
     "six_questions": {<六问键>: {"count", "principles", "entries"}, ...六键恒在},
     "generation_trace_summary": [{"rule", "freedoms", "candidate_ids"}],
     "negotiation": {"run": bool, ...}}

文档化最小决定（偏离披露）：
1. 六问键名**逐字沿用** v5.selection 的六态常量（生效/被忽略/冲突裁决/致淘汰/
   无可观测影响/依据不足）——单一事实源，从 selection import，不自造同义词；
   账本条目出现六态之外的 status 一律 fail-closed（上游合同违约早暴露）。
2. 六键恒在（零计数也给空桶）——六问是**必答题**（§3.8：每运行必答六问），
   缺席答案与「答案为零」不可区分即违约。
3. 输入校验 fail-closed 报键路径，但**不重复**上游已做的语义判定（板不重载入、
   候选不再 validate——本模块是账本聚合器，不是第二个裁判）。
4. canonical 序列化稳定：全部迭代 sorted、无时间戳无主机路径；
   run_ledger_bytes(ledger)=canonical.json，同输入双跑字节相等是硬测试。
"""
from . import board as board_mod
from . import canonical
from .selection import (PL_ARBITRATED, PL_EFFECTIVE, PL_ELIMINATED, PL_IGNORED,
                        PL_INSUFFICIENT, PL_NO_OBSERVABLE)

RUN_LEDGER_VERSION = "v5.run_ledger/0.1.0"
RUN_LEDGER_SCHEMA = "v5.runledger.v1"

# 六问键（逐字沿用 selection 六态；顺序=任务书 §3.8 六问口径）
SIX_QUESTIONS = (PL_EFFECTIVE, PL_IGNORED, PL_ARBITRATED, PL_ELIMINATED,
                 PL_NO_OBSERVABLE, PL_INSUFFICIENT)
_FREEDOMS = ("ordering", "allocation", "layer_plan", "corridor")


class RunLedgerError(ValueError):
    """逐运行账本 fail-closed 错误；path=键路径，message=原因。"""

    def __init__(self, path, message):
        self.path = path
        self.message = message
        super().__init__("[%s] %s" % (path or "<root>", message))


def _require(cond, path, msg):
    if not cond:
        raise RunLedgerError(path, msg)


# ---------------------------------------------------------------- 输入校验

def _check_board(board):
    _require(isinstance(board, dict), "board", "须为 dict")
    _require(isinstance(board.get("board_id"), str) and board["board_id"],
             "board.board_id", "须为非空字符串")
    return board_mod.compute_board_sha256(board)


def _check_selection(selection_result):
    _require(isinstance(selection_result, dict), "selection_result",
             "须为 dict（select_best 返回值）")
    _require(isinstance(selection_result.get("verdict"), str)
             and selection_result["verdict"],
             "selection_result.verdict", "须为非空字符串")
    ledger = selection_result.get("ledger")
    _require(isinstance(ledger, dict), "selection_result.ledger", "须为 dict")
    entries = ledger.get("principle_ledger")
    _require(isinstance(entries, list),
             "selection_result.ledger.principle_ledger", "须为 list")
    for i, entry in enumerate(entries):
        base = "selection_result.ledger.principle_ledger[%d]" % i
        _require(isinstance(entry, dict), base, "须为 dict")
        _require(isinstance(entry.get("principle_id"), str) and entry["principle_id"],
                 base + ".principle_id", "须为非空字符串")
        _require(entry.get("status") in SIX_QUESTIONS,
                 base + ".status",
                 "须在六问枚举 %s 内，得到 %r" % (list(SIX_QUESTIONS),
                                                entry.get("status")))
        _require(isinstance(entry.get("evidence"), str) and entry["evidence"],
                 base + ".evidence", "须为非空字符串（六问必附依据）")
    return entries


def _check_executor(executor_result):
    """executor_result 轻校验（None=执行器未运行，合法）。返回归一化摘要输入。"""
    if executor_result is None:
        return None
    _require(isinstance(executor_result, dict), "executor_result",
             "须为 dict 或 None（execute_candidate 返回值）")
    _require(isinstance(executor_result.get("verdict"), str)
             and executor_result["verdict"],
             "executor_result.verdict", "须为非空字符串（ROUTED/FAILED）")
    log = executor_result.get("negotiation_log")
    _require(isinstance(log, list) and all(isinstance(x, str) for x in log),
             "executor_result.negotiation_log", "须为字符串数组")
    per_net = executor_result.get("per_net")
    _require(isinstance(per_net, list), "executor_result.per_net", "须为 list")
    for i, item in enumerate(per_net):
        base = "executor_result.per_net[%d]" % i
        _require(isinstance(item, dict), base, "须为 dict")
        _require(isinstance(item.get("status"), str) and item["status"],
                 base + ".status", "须为非空字符串")
        _require(isinstance(item.get("negotiated"), bool),
                 base + ".negotiated", "须为 bool")
    return {"verdict": executor_result["verdict"],
            "negotiation_log": list(log),
            "per_net": list(per_net)}


# ---------------------------------------------------------------- 聚合

def _trace_summary(candidates):
    """generation_trace 聚合：每条留痕规则 → {freedoms, candidate_ids}（sorted）。

    留痕形态兼容 selection._normalize_trace 同款三形态：dict(rule=...)/
    dict(principle_id=...)（可附 freedom）/ 裸字符串（principle_id，无 freedom）。
    """
    acc = {}

    def note(rule_id, freedom, cid):
        cell = acc.setdefault(rule_id, {"freedoms": set(), "candidate_ids": set()})
        if freedom in _FREEDOMS:
            cell["freedoms"].add(freedom)
        cell["candidate_ids"].add(cid)

    for idx, cand in enumerate(candidates):
        cid = "cand[%d]" % idx
        trace = None
        if isinstance(cand, dict):
            cid = cand.get("candidate_id") if isinstance(cand.get("candidate_id"), str) \
                and cand.get("candidate_id") else cid
            trace = cand.get("generation_trace")
        if not isinstance(trace, list):
            continue
        for item in trace:
            if isinstance(item, str) and item:
                note(item, None, cid)
            elif isinstance(item, dict):
                rid = item.get("rule") or item.get("principle_id")
                if isinstance(rid, str) and rid:
                    freedom = item.get("freedom")
                    note(rid, freedom if isinstance(freedom, str) else None, cid)
    return [{"rule": rid, "freedoms": sorted(acc[rid]["freedoms"]),
             "candidate_ids": sorted(acc[rid]["candidate_ids"])}
            for rid in sorted(acc)]


def _negotiation_block(executor_summary):
    if executor_summary is None:
        return {"run": False}
    per_net = executor_summary["per_net"]
    return {
        "run": True,
        "verdict": executor_summary["verdict"],
        "nets_total": len(per_net),
        "nets_negotiated": sum(1 for it in per_net if it["negotiated"]),
        "nets_failed": sum(1 for it in per_net if it["status"] == "failed"),
        "negotiation_log": list(executor_summary["negotiation_log"]),
    }


# ---------------------------------------------------------------- 入口

def build_run_ledger(board, candidates, selection_result, executor_result=None):
    """L8 逐运行六问账本（纯函数；工件合同见模块 docstring）。

    board：v5.board.v1 板（取 board_id + provenance 哈希链复算 board_sha256）；
    candidates：本运行送 L6 的候选列表（取 generation_trace 聚合）；
    selection_result：select_best 返回值（取 verdict + ledger.principle_ledger）；
    executor_result：execute_candidate 返回值或 None（未运行，negotiation.run=False）。
    """
    board_sha = _check_board(board)
    entries = _check_selection(selection_result)
    _require(isinstance(candidates, list), "candidates", "须为 list")
    executor_summary = _check_executor(executor_result)

    six = {}
    for status in SIX_QUESTIONS:
        bucket = [e for e in entries if e["status"] == status]
        six[status] = {
            "count": len(bucket),
            "principles": sorted({e["principle_id"] for e in bucket}),
            "entries": [{"principle_id": e["principle_id"],
                         "evidence": e["evidence"]}
                        for e in sorted(bucket, key=lambda e: e["principle_id"])],
        }

    return {
        "schema_version": RUN_LEDGER_SCHEMA,
        "board_id": board["board_id"],
        "board_sha256": board_sha,
        "provenance": {
            "generator": RUN_LEDGER_VERSION,
            "board_sha256": board_sha,
            "inputs": {
                "planner_candidates": len(candidates),
                "selection_verdict": selection_result["verdict"],
                "executor": ("not_run" if executor_summary is None
                             else executor_summary["verdict"]),
                "ledger_entries": len(entries),
            },
        },
        "six_questions": six,
        "generation_trace_summary": _trace_summary(candidates),
        "negotiation": _negotiation_block(executor_summary),
    }


def run_ledger_bytes(ledger):
    """账本 canonical 序列化（§3.4：同输入双跑字节相等；键序固定、无时钟）。"""
    _require(isinstance(ledger, dict) and ledger.get("schema_version") == RUN_LEDGER_SCHEMA,
             "ledger.schema_version", "须为 %r 的账本工件" % RUN_LEDGER_SCHEMA)
    return canonical.canonical_json(ledger)
