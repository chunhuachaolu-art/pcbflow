#!/usr/bin/env python
"""S13-ARCHIVE 编排：TD7 线收档 disposition 入账（写 out/v3-archive/）。

编排侧职责（库侧 pcbflow/archive.py 保持零子进程零落盘）：
1. 对账（fail-closed，任一不符即拒绝落盘）：
   - out/v3-td7/gate-record-td7.json 实测 gate_core_hash == 模块声明
     常量、qualification_verdict == pass（被引用资格结论与产物一致）；
   - toolchain_lock.json 实测 sha256 前缀 == d43dad89c1559ff0（收档时点
     零改动见证，受保护文件既有 hash）；
   - S12 三份被引用产物实测 sha256 前缀 == V3-NEXT S12 已发布记录
     （quality-matrix/ab-report/dsn-rule-triangulation）；
2. collect_evidence_hashes（缺文件 fail-closed）→ build_archive_bundle；
3. 链/处置/chkpt 全绿校验后原子性写出 out/v3-archive/ 九件：
   archive-bundle.json + disposition-ARC-000{1..4}-*.json +
   decision-ledger.jsonl + ledger-checkpoint.json + ledger-verify.json +
   checkpoint-verify.json；
4. 目标已存在即拒绝（追加式纪律：发布产物不可覆写）。

用法：python scripts/s13_archive.py            （仓库根执行）
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from pcbflow import archive as arc            # noqa: E402
from pcbflow import hashing, ledger           # noqa: E402

OUT = REPO / "out" / "v3-archive"

#: V3-NEXT S12 摘要已发布的产物 sha16（对账基准，非本轮实测）
PUBLISHED_SHA16 = {
    "out/v3-td7/s12/quality-matrix.json": "b4e55ba7b0cd445e",
    "out/v3-td7/s12/ab-report.json": "3cac2126ddced342",
    "out/v3-td7/s12/dsn-rule-triangulation.json": "60ade1299c932e66",
}


def _fail(msg: str) -> None:
    print(f"[s13-archive] FAIL: {msg}")
    sys.exit(1)


def reconcile() -> dict:
    """对账：被引用结论与盘上产物一致后才允许入账。"""
    gate = json.loads((REPO / "out/v3-td7/gate-record-td7.json")
                      .read_text(encoding="utf-8"))
    if gate.get("gate_core_hash") != arc.TD7_QUAL_GATE_CORE_HASH:
        _fail(f"gate_core_hash 对账不符：盘上 {gate.get('gate_core_hash')}"
              f" != 声明 {arc.TD7_QUAL_GATE_CORE_HASH}")
    if gate.get("qualification_verdict") != "pass":
        _fail(f"qualification_verdict 应为 pass，得到 "
              f"{gate.get('qualification_verdict')!r}")
    lock_sha = hashing.sha256_file(str(REPO / "toolchain_lock.json"))
    if not lock_sha.startswith(arc.TOOLCHAIN_LOCK_SHA256_16):
        _fail(f"toolchain_lock.json 零改动对账不符：实测 {lock_sha[:16]}…"
              f" != 受保护前缀 {arc.TOOLCHAIN_LOCK_SHA256_16}")
    for rel, sha16 in PUBLISHED_SHA16.items():
        got = hashing.sha256_file(str(REPO / rel))
        if not got.startswith(sha16):
            _fail(f"{rel} 对账不符：实测 {got[:16]}… != 已发布 {sha16}")
    print("[s13-archive] 对账通过：TD7-QUAL-G core "
          f"{arc.TD7_QUAL_GATE_CORE_HASH16}… = pass；toolchain_lock "
          f"{arc.TOOLCHAIN_LOCK_SHA256_16}… 零改动；S12 三产物 sha16 全符")
    return gate


def write_json(path: Path, obj) -> str:
    """canonical JSON 落盘（与 out/v3-approvals 口径一致：sort_keys、
    indent=1、UTF-8、LF 结尾换行——payload_ref 绑定的正是这些字节）。"""
    data = hashing.canonical_json_bytes(obj)
    path.write_bytes(data)
    return hashing.sha256_bytes(data)


def main() -> int:
    reconcile()
    hashes, errors = arc.collect_evidence_hashes(str(REPO))
    if errors:
        _fail("; ".join(errors))
    bundle = arc.build_archive_bundle(hashes)

    verify = bundle["ledger_verify"]
    if verify["chain_errors"] or verify["supersedes_errors"]:
        _fail(f"账本校验失败: {verify}")
    if any(bundle["gate_write_scan"].values()):
        _fail("处置记录触发门写禁区")
    entries = bundle["ledger_entries"]
    ckpt_errors = ledger.verify_against_checkpoint(
        entries, bundle["ledger_checkpoint"])
    if ckpt_errors:
        _fail(f"checkpoint 校验失败: {ckpt_errors}")

    targets = [OUT / f for f in (
        "archive-bundle.json",
        *(arc.disposition_filename(s) for s in arc.ARCHIVE_SPECS),
        "decision-ledger.jsonl", "ledger-checkpoint.json",
        "ledger-verify.json", "checkpoint-verify.json")]
    if any(p.exists() for p in targets):
        _fail("out/v3-archive/ 已有产物（追加式纪律：发布产物不可覆写）")

    OUT.mkdir(parents=True, exist_ok=True)
    ledger_bytes = arc.ledger_file_bytes(entries)

    out_bundle = dict(bundle)
    out_bundle.update({"command": "v3-archive", "select": "build",
                       "status": "ok"})
    written = {"archive-bundle.json":
               write_json(OUT / "archive-bundle.json", out_bundle)}
    for spec, disp in zip(arc.ARCHIVE_SPECS, bundle["dispositions"]):
        name = arc.disposition_filename(spec)
        written[name] = write_json(OUT / name, disp)
    (OUT / "decision-ledger.jsonl").write_bytes(ledger_bytes)
    written["decision-ledger.jsonl"] = hashing.sha256_bytes(ledger_bytes)
    written["ledger-checkpoint.json"] = write_json(
        OUT / "ledger-checkpoint.json", bundle["ledger_checkpoint"])
    written["ledger-verify.json"] = write_json(
        OUT / "ledger-verify.json",
        {"command": "v3-ledger", "select": "verify", "status": "ok",
         "errors": [], "entry_count": len(entries)})
    written["checkpoint-verify.json"] = write_json(
        OUT / "checkpoint-verify.json",
        {"command": "v3-ledger", "select": "verify_checkpoint",
         "status": "ok", "errors": []})

    print("[s13-archive] 落盘完成（out/v3-archive/）：")
    for name in sorted(written):
        print(f"  {written[name][:16]}  {name}")
    summary = json.dumps(bundle["decision_summary"], ensure_ascii=False)
    print(f"[s13-archive] dispositions={bundle['disposition_count']} "
          f"decision_summary={summary}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
