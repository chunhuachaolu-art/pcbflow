#!/usr/bin/env python
"""S20-T1：人工队列 ITEM-run-r2 关闭（queue-event-ledger append-only 追加）。

2026-09-05 用户人工决策（语义以原文为准）：ITEM-run-r2 的 12 条旗标
（天线出界/端子贴边/JLC 占位丝印/拼板缝等观察，其中 5 条 abstain）全量
作为 advisory 登记入处置台账并关闭队列项；语料板只读，处置≠改板
（APR-0010，登记见 pcbflow/approvals_r3.py + scripts/s20_approvals_r3.py）。

本脚本只做追加：既有 1 行（QE-000000 enqueue，event_sha256=8d45c429…）
原始字节逐字节保留，仅在其后追加两行（与 run-r1 关闭先例同构）：
- QE-000001 = assign（actor=user、actor_role=human_final）；
- QE-000002 = approve（actor=user、actor_role=human_final——approve 强制
  人工裁决角色；reason_code=item_dispositioned_apr_0010 引用 APR-0010）。

fail-closed：既有事件非恰好 1 条/enqueue 非法/链校验不过/追加后
queue_length≠0 一律拒绝写盘。账本写盘口径与 s14/s17 一致：每事件单行
json.dumps(ensure_ascii=False, sort_keys=True)+LF，二进制 append 模式
（既有字节零触碰）。

用法：python scripts/s20_queue_close_r2.py   （仓库根执行）
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from pcbflow import hashing, queue  # noqa: E402

LEDGER = REPO / "out" / "v3-tl2" / "critic-runs" / "run-r2" / \
    "queue-event-ledger.jsonl"
ITEM_ID = "ITEM-run-r2"
EXPECTED_ENQUEUE_SHA = ("8d45c42927d23028bf8a77813cb65519d5c28782a1e13c1d8"
                        "ea9aa813c1f3a73")
APPROVE_REASON = "item_dispositioned_apr_0010"


def _fail(msg: str) -> None:
    print(f"[s20-close] FAIL: {msg}")
    sys.exit(1)


def main() -> None:
    if not LEDGER.is_file():
        _fail(f"账本缺失：{LEDGER.name}")
    existing_bytes = LEDGER.read_bytes()
    if not existing_bytes.endswith(b"\n"):
        _fail("既有账本末行无换行（append 口径前提不成立）")
    lines = existing_bytes.decode("utf-8").splitlines()
    existing = [json.loads(line) for line in lines]
    if len(existing) != 1:
        _fail(f"既有事件数={len(existing)}（本包前提=恰好 1 条 enqueue；"
              "已关闭或非预期状态时拒绝追加）")
    head = existing[0]
    if (head.get("event") != "enqueue" or head.get("item_id") != ITEM_ID
            or head.get("event_sha256") != EXPECTED_ENQUEUE_SHA):
        _fail("既有事件与预期 enqueue（ITEM-run-r2/8d45c429…）不符")
    errs = queue.verify_chain(existing)
    if errs:
        _fail(f"既有账本链校验失败：{errs}")

    ev_assign = queue.make_event(
        existing, event="assign", item_id=ITEM_ID,
        actor="user", actor_role="human_final")
    events, _ = queue.append(existing, ev_assign)
    ev_approve = queue.make_event(
        events, event="approve", item_id=ITEM_ID,
        actor="user", actor_role="human_final",
        reason_code=APPROVE_REASON)
    events, _ = queue.append(events, ev_approve)

    errs = queue.verify_chain(events)
    if errs:
        _fail(f"追加后链校验失败：{errs}")
    summary = queue.projection_summary(events)
    if summary["queue_length"] != 0:
        _fail(f"追加后 queue_length={summary['queue_length']}（应为 0）")
    closed = [ev for ev in events
              if ev["item_id"] == ITEM_ID and ev["event"] == "approve"]
    if not closed:
        _fail("approve 事件缺失")

    # 逐字节保留既有行：二进制 append，只写新行
    new_bytes = b"".join(
        (json.dumps(ev, ensure_ascii=False, sort_keys=True) + "\n").encode(
            "utf-8") for ev in events[len(existing):])
    with open(LEDGER, "ab") as f:
        f.write(new_bytes)

    reread_bytes = LEDGER.read_bytes()
    if reread_bytes[:len(existing_bytes)] != existing_bytes:
        _fail("既有字节被改动（append-only 违例）")
    reread = [json.loads(line)
              for line in reread_bytes.decode("utf-8").splitlines()]
    errs = queue.verify_chain(reread)
    if errs or len(reread) != 3:
        _fail(f"落盘复读校验失败：errs={errs} n={len(reread)}")
    post = queue.projection_summary(reread)
    print(hashing.json_dumps({
        "kind": "tl2_queue_item_closed_report",
        "item_id": ITEM_ID,
        "appended_events": [events[1], events[2]],
        "ledger_sha256_after": hashing.sha256_file(str(LEDGER)),
        "ledger_bytes_before": len(existing_bytes),
        "ledger_bytes_after": len(reread_bytes),
        "existing_bytes_unchanged": True,
        "projection_summary_after": post,
        "chain_verify": queue.verify_chain(reread),
        "decision_basis": (
            "2026-09-05 用户人工决策：ITEM-run-r2 的 12 条旗标（天线出界/"
            "端子贴边/JLC 占位丝印/拼板缝等观察，其中 5 条 abstain）全量"
            "作为 advisory 登记入处置台账并关闭队列项（APR-0010）；语料"
            "板只读，处置≠改板；critic 输出恒 untrusted。"),
    }))
    print(f"[s20-close] ITEM-run-r2 已关闭：assign+approve 追加，"
          f"queue_length={post['queue_length']}，"
          f"head={reread[-1]['event_sha256'][:16]}…")


if __name__ == "__main__":
    main()
