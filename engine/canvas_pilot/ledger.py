# -*- coding: utf-8 -*-
"""ledger —— 台账链式哈希（v5.run_ledger 形态复用: canonical bytes + sha256 链）。

ledger.jsonl 每行: {seq, kind, ts, payload_sha256, prev_hash, entry_hash};
entry_hash = sha256(prev_hash + canonical_json(本行除 entry_hash 外字段))。
verify 重算全链（G-CP 收口前置门）。
"""
import datetime
import json
import os
import sys

sys.path.insert(0, os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..")))

from v5.canonical import canonical_json, sha256_bytes  # noqa: E402

GENESIS = "0" * 64


class Ledger(object):
    def __init__(self, path):
        self.path = path
        self._tail = GENESIS
        self._seq = 0
        if os.path.exists(path):
            self._rescan()

    def _rescan(self):
        with open(self.path, "rb") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line.decode("utf-8"))
                self._tail = rec["entry_hash"]
                self._seq = rec["seq"]

    def append(self, kind, payload):
        rec = {
            "seq": self._seq + 1,
            "kind": kind,
            "ts": datetime.datetime.now().isoformat(timespec="seconds"),
            "payload_sha256": sha256_bytes(canonical_json(payload)),
            "prev_hash": self._tail,
        }
        # entry_hash 覆盖含 prev_hash 的 body（canonical bytes）→ 链成立
        rec["entry_hash"] = sha256_bytes(canonical_json(rec))
        line = canonical_json(rec) + b"\n"
        with open(self.path, "ab") as f:
            f.write(line)
        self._tail = rec["entry_hash"]
        self._seq = rec["seq"]
        return rec

    def verify(self):
        """全链重算 → (ok, n_records, first_bad_seq)。"""
        prev = GENESIS
        n = 0
        with open(self.path, "rb") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                n += 1
                rec = json.loads(line.decode("utf-8"))
                body = dict(rec)
                eh = body.pop("entry_hash")
                if rec["prev_hash"] != prev:
                    return (False, n, rec["seq"])
                calc = sha256_bytes(canonical_json(body))
                if calc != eh:
                    return (False, n, rec["seq"])
                prev = eh
        return (True, n, None)
