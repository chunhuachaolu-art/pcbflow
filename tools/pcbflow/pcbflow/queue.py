"""TD5 queue-event-ledger（TL-2；SPEC-v3.0-PROPOSAL §TD5）。

追加式人工队列事件账本（queue-event-ledger.jsonl 的纯函数内核）：
- 每个事件绑定 item/actor，可挂 board/profile/snapshot 与
  fact/gate/critic hash（refs 参数）；
- hash 链与 TD1 decision-ledger 同构：event_seq 连续、
  prev_event_sha256 指向前一事件 event_sha256（首条为 None）、
  event_sha256 = 剔除自身（event_sha256）与链字段
  （prev_event_sha256/event_seq）后的 canonical hash；
- 状态机 ALLOWED_TRANSITIONS：enqueue 仅当 item 不存在；
  assign/review/escalate/expire 要求 open/assigned；approve/reject 仅从
  assigned 且为终态；downgrade 从 assigned 回 open；expire 为终态。
  终态后该 item 不得再有任何新事件（新 item 的 enqueue 不受影响）；
- actor 角色约束：approve/reject 必须人工裁决角色
  （human_reviewer/human_final）；机器角色只能 enqueue/assign（assign
  仅是分配建议），不得 review/escalate/downgrade/expire/approve/reject；
- current_queue/projection_summary 是「当前摘要」投影（NEXT.md 只保留
  当前摘要的机器实现），投影前先 verify（fail-closed）；
- 抽样审计独立配置：audit_config 校验，audit_decision 三分支——上次
  审计失败 → 降级 fallback（默认全量陪审）；队列低于最小样本 →
  full_jury；否则 sampled。抽样是审计分流，不是质量放行。

生成器模式：纯函数、零 IO、零子进程、零网络、无 wall-clock；
标准库 + 包内 schemas/hashing。
"""

from __future__ import annotations

from . import hashing, schemas

SCHEMA_VERSION = schemas.SCHEMA_V3
QUEUE_EVENT_SCHEMA = "queue_event"

# 事件全集（schemas.queue_event 同步）
EVENT_KINDS = ("enqueue", "assign", "review", "escalate",
               "approve", "reject", "downgrade", "expire")

# 终态事件：之后该 item 不得再有任何新事件
TERMINAL_EVENTS = frozenset({"approve", "reject", "expire"})

# 状态机：事件 → 允许的前置状态（enqueue 特殊：item 必须不存在）
ALLOWED_TRANSITIONS = {
    "enqueue": (),                     # item 未存在才能 enqueue
    "assign": ("open", "assigned"),
    "review": ("open", "assigned"),
    "escalate": ("open", "assigned"),
    "approve": ("assigned",),          # 终态
    "reject": ("assigned",),           # 终态
    "downgrade": ("assigned",),        # 降级回 open（仍在队列）
    "expire": ("open", "assigned"),    # 终态
}

# 事件后的目标状态（review/escalate 不改状态）
_NEXT_STATE = {
    "enqueue": "open",
    "assign": "assigned",
    "review": None,          # 状态不变
    "escalate": None,        # 状态不变
    "approve": "closed",
    "reject": "closed",
    "downgrade": "open",
    "expire": "closed",
}

# actor 角色约束：人工裁决角色；其余一律按机器角色处理（只能 enqueue/assign）
HUMAN_DECISION_ROLES = frozenset({"human_reviewer", "human_final"})
MACHINE_ALLOWED_EVENTS = frozenset({"enqueue", "assign"})

# 链字段（含自身）：不进入 event body hash
_CHAIN_EXCLUDED = ("event_sha256", "prev_event_sha256", "event_seq")

# refs 允许键（schema 可选属性；绑定 board/profile/snapshot 与
# fact/gate/critic hash）
_REF_KEYS = ("project_id", "profile_id", "snapshot_revision",
             "fact_ref", "gate_ref", "critic_ref", "supersedes")

# current_queue 条目里 refs 投影的绑定键
_BINDING_KEYS = ("project_id", "profile_id", "snapshot_revision",
                 "fact_ref", "gate_ref", "critic_ref")


def empty_ledger() -> dict:
    """空账本（追加式；events 为事件列表）。"""
    return {"events": []}


# ---------------------------------------------------------------------------
# hash 链
# ---------------------------------------------------------------------------

def event_body_sha256(ev: dict) -> str:
    """事件体 canonical hash：剔除自身与链字段（event_sha256/
    prev_event_sha256/event_seq）后的 canonical JSON sha256。"""
    body = {k: v for k, v in ev.items() if k not in _CHAIN_EXCLUDED}
    return hashing.sha256_bytes(hashing.canonical_json_bytes(body))


def make_event(events, *, event: str, item_id: str, actor: str,
               actor_role: str, reason_code: str | None = None,
               refs: dict | None = None) -> dict:
    """构造下一个事件（event_seq=len(events)；prev 指向链头）。

    构造后即做 schema + 语义（含状态机与角色约束）检查，非法
    ValueError（fail-closed，不产出非法事件）。event_id 确定性生成
    （QE-<seq>，与 lease.py 的顺序 id 风格一致）。
    """
    if event not in EVENT_KINDS:
        raise ValueError(f"make_event: 未知事件 {event!r}"
                         f"（合法集 {EVENT_KINDS}）")
    if refs is not None:
        unknown = sorted(set(refs) - set(_REF_KEYS))
        if unknown:
            raise ValueError(f"make_event: refs 未知键 {unknown}"
                             f"（合法集 {_REF_KEYS}）")
    seq = len(events)
    ev = {
        "schema_version": SCHEMA_VERSION,
        "event_id": f"QE-{seq:06d}",
        "event_seq": seq,
        "event": event,
        "item_id": item_id,
        "actor": actor,
        "actor_role": actor_role,
        "prev_event_sha256": (events[-1]["event_sha256"]
                              if events else None),
    }
    if reason_code is not None:
        ev["reason_code"] = reason_code
    if refs:
        for k, v in refs.items():
            if v is not None:
                ev[k] = v
    ev["event_sha256"] = event_body_sha256(ev)
    errs = schemas.validate(QUEUE_EVENT_SCHEMA, ev)
    if errs:
        raise ValueError(f"make_event: 事件 schema 非法: {errs}")
    sem = _semantic_errors(list(events) + [ev])
    if sem:
        raise ValueError(f"make_event: 事件违反链/状态机/角色约束: {sem}")
    return ev


def append(events, ev: dict) -> tuple:
    """verify 后追加：返回 (new_events, ev)；verify 失败 ValueError。"""
    combined = list(events) + [ev]
    errs = verify_chain(combined)
    if errs:
        raise ValueError(f"append: 拒绝追加（fail-closed）: {errs}")
    return combined, ev


def verify_chain(events) -> list:
    """schema + seq 连续 + 链 hash 一致 + 状态机/角色合法（[] = 合法）。"""
    errs: list = []
    for i, ev in enumerate(events):
        for e in schemas.validate(QUEUE_EVENT_SCHEMA, ev):
            errs.append(f"event[{i}]: {e}")
    errs.extend(_semantic_errors(events))
    return errs


def _semantic_errors(events) -> list:
    """seq 连续性、prev 链、event_sha256 一致性、状态机与角色约束。"""
    errs: list = []
    prev_hash = None
    states: dict = {}
    for i, ev in enumerate(events):
        if not isinstance(ev, dict):
            errs.append(f"event[{i}]: 事件不是对象")
            prev_hash = None
            continue
        if ev.get("event_seq") != i:
            errs.append(f"event[{i}]: event_seq 应为 {i}，"
                        f"得到 {ev.get('event_seq')!r}")
        if ev.get("prev_event_sha256") != prev_hash:
            errs.append(f"event[{i}]: prev_event_sha256 与前一事件 "
                        f"event_sha256 不一致（链断裂）")
        try:
            body_hash = event_body_sha256(ev)
        except (TypeError, ValueError) as exc:
            errs.append(f"event[{i}]: 记录体不可规范化（{exc}）")
            body_hash = None
        eh = ev.get("event_sha256")
        if body_hash is not None and eh != body_hash:
            errs.append(f"event[{i}]: event_sha256 与记录体 canonical "
                        f"hash 不一致（篡改或构造错误）")
        prev_hash = eh    # 沿自报值续链：篡改会在下一事件 prev 比对暴露

        kind = ev.get("event")
        iid = ev.get("item_id")
        role = ev.get("actor_role")
        if kind in ("approve", "reject") and role not in HUMAN_DECISION_ROLES:
            errs.append(f"event[{i}]: {kind} 的 actor_role 必须为人工裁决"
                        f"角色 {sorted(HUMAN_DECISION_ROLES)}，"
                        f"得到 {role!r}")
        if (kind in EVENT_KINDS
                and kind not in MACHINE_ALLOWED_EVENTS
                and role not in HUMAN_DECISION_ROLES):
            errs.append(f"event[{i}]: 机器角色 {role!r} 只能 "
                        f"enqueue/assign（assign 仅建议），不得 {kind}")
        if kind == "enqueue":
            if iid in states:
                errs.append(f"event[{i}]: item {iid!r} 重复 enqueue"
                            f"（item 已存在，含终态后重入）")
            else:
                states[iid] = "open"
        elif kind in EVENT_KINDS:
            st = states.get(iid)
            if st is None:
                errs.append(f"event[{i}]: item {iid!r} 的 {kind} "
                            f"先于 enqueue（item 不存在）")
            elif st not in ALLOWED_TRANSITIONS[kind]:
                errs.append(f"event[{i}]: item {iid!r} 状态 {st!r} "
                            f"不允许 {kind}（终态后不得再有事序）")
            else:
                nxt = _NEXT_STATE[kind]
                if nxt is not None:
                    states[iid] = nxt
        # kind 不在 EVENT_KINDS：schema 层已报未知事件
    return errs


# ---------------------------------------------------------------------------
# 当前摘要投影（NEXT.md 只保留当前摘要）
# ---------------------------------------------------------------------------

def current_queue(events) -> list:
    """open items（enqueue 后无终态事件），按入队顺序。

    每项 {item_id, enqueued_event_seq, last_event, reason_code, refs}；
    refs 为 enqueue 事件上非空的绑定键（board/profile/snapshot 与
    fact/gate/critic hash）。投影前 verify（fail-closed）。
    """
    errs = verify_chain(events)
    if errs:
        raise ValueError(f"current_queue: 账本非法，拒绝投影: {errs}")
    records: dict = {}
    order: list = []
    closed: dict = {}
    for ev in events:
        kind, iid = ev["event"], ev["item_id"]
        if kind == "enqueue":
            records[iid] = {
                "item_id": iid,
                "enqueued_event_seq": ev["event_seq"],
                "last_event": kind,
                "reason_code": ev.get("reason_code"),
                "refs": {k: ev[k] for k in _BINDING_KEYS
                         if ev.get(k) is not None},
            }
            order.append(iid)
        else:
            records[iid]["last_event"] = kind
            if kind in TERMINAL_EVENTS:
                closed[iid] = True
    return [records[iid] for iid in order if not closed.get(iid)]


def projection_summary(events) -> dict:
    """当前摘要：{queue_length, by_reason_code, by_last_event,
    oldest_item_seq, total_events}。

    by_* 与 oldest 只统计当前 open items（当前摘要，不是历史台账）；
    reason_code 为空计入 "none"。
    """
    open_items = current_queue(events)
    by_reason: dict = {}
    by_last: dict = {}
    for it in open_items:
        rkey = it["reason_code"] if it["reason_code"] else "none"
        by_reason[rkey] = by_reason.get(rkey, 0) + 1
        by_last[it["last_event"]] = by_last.get(it["last_event"], 0) + 1
    return {
        "queue_length": len(open_items),
        "by_reason_code": by_reason,
        "by_last_event": by_last,
        "oldest_item_seq": (min(it["enqueued_event_seq"] for it in open_items)
                            if open_items else None),
        "total_events": len(events),
    }


# ---------------------------------------------------------------------------
# 抽样审计（独立质量控制；不替代 fail-closed）
# ---------------------------------------------------------------------------

def audit_config(*, sample_rate, min_samples,
                 fallback: str = "full_jury") -> dict:
    """校验抽样审计配置：0 < sample_rate ≤ 1、min_samples ≥ 1、
    fallback 非空字符串（失败降级模式可配置，默认全量陪审）。"""
    if (isinstance(sample_rate, bool)
            or not isinstance(sample_rate, (int, float))
            or not 0 < float(sample_rate) <= 1):
        raise ValueError(f"audit_config: sample_rate 非法 {sample_rate!r}"
                         f"（要求 0 < rate ≤ 1）")
    if (isinstance(min_samples, bool) or not isinstance(min_samples, int)
            or min_samples < 1):
        raise ValueError(f"audit_config: min_samples 非法 {min_samples!r}"
                         f"（要求 ≥1）")
    if not isinstance(fallback, str) or not fallback:
        raise ValueError("audit_config: fallback 必须为非空字符串")
    return {"sample_rate": float(sample_rate),
            "min_samples": int(min_samples),
            "fallback": fallback}


def audit_decision(config: dict, queue_length: int,
                   failed_last_audit: bool) -> dict:
    """审计模式三分支（fail-closed 优先级：上次失败 > 低于最小样本 > 抽样）。

    - failed_last_audit=True → {mode: fallback,
      reason: audit_failed_full_jury}（上次审计失败：降级全量陪审）；
    - queue_length < min_samples → {mode: "full_jury",
      reason: below_min_samples}；
    - 否则 {mode: "sampled", sample_rate}。

    抽样是审计分流，不是质量放行——note 写明。config 非法 ValueError。
    """
    if not isinstance(config, dict):
        raise ValueError("audit_decision: config 必须为 dict")
    rate = config.get("sample_rate")
    mins = config.get("min_samples")
    fallback = config.get("fallback", "full_jury")
    if (isinstance(rate, bool) or not isinstance(rate, (int, float))
            or not 0 < float(rate) <= 1):
        raise ValueError(f"audit_decision: sample_rate 非法 {rate!r}")
    if (isinstance(mins, bool) or not isinstance(mins, (int, float))
            or mins < 1):
        raise ValueError(f"audit_decision: min_samples 非法 {mins!r}")
    if (isinstance(queue_length, bool)
            or not isinstance(queue_length, (int, float)) or queue_length < 0):
        raise ValueError(f"audit_decision: queue_length 非法 {queue_length!r}")
    if failed_last_audit is True:
        return {"mode": fallback, "reason": "audit_failed_full_jury",
                "note": "上次审计失败：降级全量陪审（fail-closed），"
                        "抽样分流不可用"}
    if queue_length < mins:
        return {"mode": "full_jury", "reason": "below_min_samples",
                "note": "队列长度低于最小审计样本：全量陪审"
                        "（抽样是分流不是放行）"}
    return {"mode": "sampled", "sample_rate": float(rate),
            "note": "抽样审计是质量控制分流，不是质量放行"
                    "（fail-closed 不因此放松）"}
