#!/usr/bin/env python
"""S17-T4：三项人工批准/处置登记（r2 bundle）落盘 out/v3-approvals/。

库侧 pcbflow/approvals_r2.py 纯函数构造；本脚本只做磁盘实读对账 +
canonical 落盘（防覆写）：

- approvals-bundle-r2.json（bundle；含 ledger_verify/checkpoint 投影）
- decision-ledger-r2.jsonl（3 条 disposition entry；与 r1 账本文件独立）
- ledger-checkpoint-r2.json（make_checkpoint 投影）
- ledger-verify-r2.json（verify_chain/verify_supersedes 结果记录）
- disposition-APR-0007/0008/0009-*.json（处置记录单件）

evidence 磁盘实读 fail-closed；批准日期=声明常量 2026-09-05；
r1 既有文件字节不动（防覆写守卫）。

用法：python scripts/s17_approvals_r2.py   （仓库根执行）
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from pcbflow import approvals_r2, hashing, ledger  # noqa: E402

OUT = REPO / "out" / "v3-approvals"


def _fail(msg: str) -> None:
    print(f"[s17-apr2] FAIL: {msg}")
    sys.exit(1)


def _write_canonical(path: Path, obj) -> str:
    data = hashing.canonical_json_bytes(obj)
    path.write_bytes(data)
    return hashing.sha256_bytes(data)


def main() -> None:
    hashes, errors = approvals_r2.collect_evidence_hashes(str(REPO))
    if errors:
        _fail(f"evidence 磁盘实读缺失（fail-closed）：{errors}")
    bundle = approvals_r2.build_approvals_bundle_r2(hashes)
    targets = [OUT / approvals_r2.disposition_filename(spec)
               for spec in approvals_r2.APPROVAL_SPECS_R2] + [
        OUT / "approvals-bundle-r2.json",
        OUT / "decision-ledger-r2.jsonl",
        OUT / "ledger-checkpoint-r2.json",
        OUT / "ledger-verify-r2.json",
    ]
    for t in targets:
        if t.exists():
            _fail(f"{t.name} 已存在（防覆写；发布产物不可覆写）")

    if bundle["ledger_verify"]["chain_errors"] \
            or bundle["ledger_verify"]["supersedes_errors"]:
        _fail(f"r2 账本校验失败：{bundle['ledger_verify']}")
    for scan_apr, scan in bundle["gate_write_scan"].items():
        if scan:
            _fail(f"{scan_apr} 门写扫描非空（不可落盘）")

    for spec in approvals_r2.APPROVAL_SPECS_R2:
        rec = next(d for d in bundle["dispositions"]
                   if d["disposition_id"] == spec["approval_id"])
        sha = _write_canonical(
            OUT / approvals_r2.disposition_filename(spec), rec)
        print(f"[s17-apr2] 处置单件：{approvals_r2.disposition_filename(spec)}"
              f" sha256={sha[:16]}…")

    bundle_sha = _write_canonical(OUT / "approvals-bundle-r2.json", bundle)
    ledger_bytes = approvals_r2.ledger_file_bytes(bundle["ledger_entries"])
    (OUT / "decision-ledger-r2.jsonl").write_bytes(ledger_bytes)
    if hashing.sha256_bytes(ledger_bytes) != bundle["ledger_file_sha256"]:
        _fail("decision-ledger-r2.jsonl 字节与 bundle 声明不符")
    entries = [json.loads(line) for line in
               (OUT / "decision-ledger-r2.jsonl").read_text(
                   encoding="utf-8").splitlines()]
    if ledger.verify_chain(entries) != [] or len(entries) != 3:
        _fail("账本落盘复读校验失败")
    _write_canonical(OUT / "ledger-checkpoint-r2.json",
                     bundle["ledger_checkpoint"])
    _write_canonical(OUT / "ledger-verify-r2.json", {
        "command": "scripts/s17_approvals_r2.py",
        "entry_count": len(entries),
        "errors": [],
        "select": "verify",
        "status": "ok",
        "chain_errors": bundle["ledger_verify"]["chain_errors"],
        "supersedes_errors": bundle["ledger_verify"]["supersedes_errors"],
        "ledger_file_sha256": bundle["ledger_file_sha256"],
    })
    print(f"[s17-apr2] bundle：approvals-bundle-r2.json "
          f"sha256={bundle_sha[:16]}… | ledger 3 entries "
          f"file_sha256={bundle['ledger_file_sha256'][:16]}… | "
          f"checkpoint={bundle['ledger_checkpoint']['checkpoint_id']}")
    print("[s17-apr2] APR-0007/0008/0009 登记完成（r2 批次；r1 字节不动）")


if __name__ == "__main__":
    main()
