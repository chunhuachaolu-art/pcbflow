"""TD10/v2.1 §17 单写者 lease、崩溃恢复 journal 与板写事务（TL-0）。

确定性纪律：lease/journal 不用 wall-clock——时序用单调 epoch 计数器
（§14.3 运行 metadata 不进核心 hash；lease 对象属运行态治理元数据，
本身即确定性可重放）。

三件合同：
1. lease：scope（如 "<project>/<profile>/<output_root>"）单写者；
   只有持有者可 extend/release；重复 acquire 冲突 fail-closed。
2. journal：追加式事件（acquire/extend/release/heartbeat）；
   replay_journal 幂等重放=崩溃恢复；verify_journal 校验序号单调与
   引用存在性。
3. transaction（§17.2 子集）：source→staging→batches→commit/rollback；
   live_board_touched 恒 false（validator 强制）；rollback 后不可 commit。

生成器模式：纯状态转移，零 IO。
"""

from __future__ import annotations

from . import hashing, schemas

SCHEMA_VERSION = schemas.SCHEMA_V3

# ---------------------------------------------------------------------------
# lease 状态机
# ---------------------------------------------------------------------------

LEASE_KINDS = ("acquire", "extend", "release", "heartbeat")


def empty_state() -> dict:
    return {"schema_version": SCHEMA_VERSION, "epoch": 0,
            "leases": {}, "journal": []}


def _entry(state: dict, kind: str, lease_id: str, scope: str, holder: str,
           detail: str | None = None) -> dict:
    state["epoch"] += 1
    rec = {"entry_seq": len(state["journal"]),
           "kind": kind, "lease_id": lease_id, "scope": scope,
           "holder": holder, "epoch": state["epoch"]}
    if detail:
        rec["detail"] = detail
    state["journal"].append(rec)
    return rec


def acquire(state: dict, scope: str, holder: str) -> tuple[dict, dict | None,
                                                           str | None]:
    """获取 lease；scope 已被他人持有 ⇒ (state, None, 冲突说明) fail-closed。"""
    held = state["leases"].get(scope)
    if held and held["holder"] != holder:
        return state, None, (
            f"scope {scope!r} 已由 {held['holder']!r} 持有"
            f"（lease {held['lease_id']}，epoch {held['epoch']}）——单写者冲突")
    if held and held["holder"] == holder:
        return state, None, f"scope {scope!r} 已由本人持有（幂等拒绝重取）"
    lease_id = "LEASE-%04d" % (len(state["journal"]) + 1)
    state["leases"][scope] = {"lease_id": lease_id, "scope": scope,
                              "holder": holder, "epoch": state["epoch"] + 1,
                              "status": "held"}
    rec = _entry(state, "acquire", lease_id, scope, holder)
    return state, rec, None


def extend(state: dict, lease_id: str, holder: str) \
        -> tuple[dict, dict | None, str | None]:
    lease = _find(state, lease_id)
    if lease is None:
        return state, None, f"lease {lease_id!r} 不存在"
    if lease["holder"] != holder:
        return state, None, f"只有持有者可 extend（{lease_id} 归 " \
                            f"{lease['holder']!r}）"
    rec = _entry(state, "extend", lease_id, lease["scope"], holder)
    lease["epoch"] = state["epoch"]
    return state, rec, None


def release(state: dict, lease_id: str, holder: str) \
        -> tuple[dict, dict | None, str | None]:
    lease = _find(state, lease_id)
    if lease is None:
        return state, None, f"lease {lease_id!r} 不存在或已释放"
    if lease["holder"] != holder:
        return state, None, f"只有持有者可 release（{lease_id} 归 " \
                            f"{lease['holder']!r}）"
    scope = lease["scope"]
    del state["leases"][scope]
    rec = _entry(state, "release", lease_id, scope, holder)
    return state, rec, None


def lease_status(state: dict, scope: str) -> dict:
    lease = state["leases"].get(scope)
    return {"scope": scope, "held": lease is not None,
            "holder": lease["holder"] if lease else None,
            "lease_id": lease["lease_id"] if lease else None}


def _find(state: dict, lease_id: str) -> dict | None:
    for lease in state["leases"].values():
        if lease["lease_id"] == lease_id:
            return lease
    return None


# ---------------------------------------------------------------------------
# journal 重放（崩溃恢复）与校验
# ---------------------------------------------------------------------------

def replay_journal(entries: list) -> dict:
    """从空状态幂等重放 journal ⇒ 恢复 lease 状态（§17.3 crash recovery）。"""
    state = empty_state()
    for rec in entries:
        kind = rec["kind"]
        if kind == "acquire":
            state["leases"][rec["scope"]] = {
                "lease_id": rec["lease_id"], "scope": rec["scope"],
                "holder": rec["holder"], "epoch": rec["epoch"],
                "status": "held"}
            state["journal"].append(dict(rec))
            state["epoch"] = max(state["epoch"], rec["epoch"])
        elif kind in ("extend", "heartbeat"):
            lease = state["leases"].get(rec["scope"])
            if lease and lease["lease_id"] == rec["lease_id"]:
                lease["epoch"] = rec["epoch"]
            state["journal"].append(dict(rec))
            state["epoch"] = max(state["epoch"], rec["epoch"])
        elif kind == "release":
            state["leases"].pop(rec["scope"], None)
            state["journal"].append(dict(rec))
            state["epoch"] = max(state["epoch"], rec["epoch"])
    # 重放后 entry_seq 连续性以实际 journal 长度为准（幂等）
    for i, rec in enumerate(state["journal"]):
        rec["entry_seq"] = i
    return state


def verify_journal(entries: list) -> list:
    errs = []
    seen_seq = -1
    active: dict = {}
    for i, rec in enumerate(entries):
        if rec.get("entry_seq") != i:
            errs.append(f"entry[{i}]: entry_seq 应为 {i}，得到 "
                        f"{rec.get('entry_seq')}")
        if rec["kind"] not in LEASE_KINDS:
            errs.append(f"entry[{i}]: 未知 kind {rec['kind']!r}")
            continue
        if rec["kind"] == "acquire" and rec["scope"] in active:
            errs.append(f"entry[{i}]: scope {rec['scope']} 重复 acquire")
        if rec["kind"] in ("extend", "release", "heartbeat"):
            lease = active.get(rec["scope"])
            if lease is None or lease["lease_id"] != rec["lease_id"]:
                errs.append(f"entry[{i}]: {rec['kind']} 引用不存在/不匹配的 "
                            f"lease {rec['lease_id']!r}")
        if rec["kind"] == "acquire":
            active[rec["scope"]] = rec
        elif rec["kind"] == "release":
            active.pop(rec["scope"], None)
        seen_seq = i
    del seen_seq
    return errs


# ---------------------------------------------------------------------------
# 板写事务（§17.2 子集；live_board_touched 恒 false）
# ---------------------------------------------------------------------------

_TXN_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["schema_version", "transaction_id", "project_id",
                 "source_board_sha256", "staging_board_sha256",
                 "write_scope", "batches", "rollback",
                 "final_board_sha256", "live_board_touched"],
    "properties": {
        "schema_version": {"const": SCHEMA_VERSION},
        "transaction_id": {"type": "string", "minLength": 1},
        "project_id": {"type": "string", "minLength": 1},
        "source_board_sha256": {"type": "string",
                                "pattern": "^[0-9a-f]{64}$"},
        "staging_board_sha256": {"type": ["string", "null"]},
        "write_scope": {"type": "object", "additionalProperties": False,
                        "required": ["rows", "segments", "vias", "footprints"],
                        "properties": {
                            "rows": {"type": "integer", "minimum": 0},
                            "segments": {"type": "integer", "minimum": 0},
                            "vias": {"type": "integer", "minimum": 0},
                            "footprints": {"type": "integer",
                                           "minimum": 0}}},
        "batches": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "required": ["batch_id", "staging_sha256"],
            "properties": {
                "batch_id": {"type": "string", "minLength": 1},
                "staging_sha256": {"type": "string",
                                   "pattern": "^[0-9a-f]{64}$"},
                "drc_batch_status": {"enum": ["pass", "fail",
                                              "not_executed"]}}}},
        "rollback": {"enum": ["none", "armed", "executed", "failed"]},
        "final_board_sha256": {"type": ["string", "null"]},
        "live_board_touched": {"type": "boolean"},
    },
}


def open_transaction(transaction_id: str, project_id: str,
                     source_board_sha256: str, write_scope: dict) -> dict:
    txn = {
        "schema_version": SCHEMA_VERSION,
        "transaction_id": transaction_id, "project_id": project_id,
        "source_board_sha256": source_board_sha256,
        "staging_board_sha256": None,
        "write_scope": {"rows": int(write_scope.get("rows", 0)),
                        "segments": int(write_scope.get("segments", 0)),
                        "vias": int(write_scope.get("vias", 0)),
                        "footprints": int(write_scope.get("footprints", 0))},
        "batches": [], "rollback": "none", "final_board_sha256": None,
        "live_board_touched": False,
    }
    errs = schemas.validate_spec(_TXN_SCHEMA, txn)
    if errs:
        raise ValueError(f"transaction 非法: {errs}")
    return txn


def stage_batch(txn: dict, batch_id: str, staging_sha256: str,
                drc_batch_status: str = "not_executed") -> dict:
    if txn["rollback"] != "none":
        raise ValueError("rollback 状态下禁止继续 staging")
    if any(b["batch_id"] == batch_id for b in txn["batches"]):
        raise ValueError(f"batch_id 重复: {batch_id}")
    txn["batches"].append({"batch_id": batch_id,
                           "staging_sha256": staging_sha256,
                           "drc_batch_status": drc_batch_status})
    txn["staging_board_sha256"] = staging_sha256
    return txn


def commit_transaction(txn: dict, final_board_sha256: str) -> dict:
    """提交：要求 ≥1 批、全部批 DRC pass、rollback=none（§17.4：DRC 前
    不得宣称 committed）。"""
    if not txn["batches"]:
        raise ValueError("空事务不可 commit")
    if txn["rollback"] != "none":
        raise ValueError("rollback 非 none 不可 commit")
    failed = [b["batch_id"] for b in txn["batches"]
              if b["drc_batch_status"] != "pass"]
    if failed:
        raise ValueError(f"批 DRC 未全 pass，禁止 commit: {failed}")
    txn["final_board_sha256"] = final_board_sha256
    return txn


def rollback_transaction(txn: dict, reason: str) -> dict:
    if txn.get("final_board_sha256") is not None:
        raise ValueError("已 commit 的事务不可回滚（新事务另起）")
    txn["rollback"] = "executed"
    txn.setdefault("rollback_reason", reason)
    return txn


def verify_transaction(txn: dict) -> list:
    errs = schemas.validate_spec(_TXN_SCHEMA, txn)
    if txn.get("live_board_touched"):
        errs.append("live_board_touched=true 违反零写见证（恒 false）")
    if txn.get("final_board_sha256") and txn["rollback"] != "none":
        errs.append("已 commit 与 rollback 状态互斥")
    return errs


def txn_sha256(txn: dict) -> str:
    return hashing.sha256_bytes(hashing.canonical_json_bytes(txn))
