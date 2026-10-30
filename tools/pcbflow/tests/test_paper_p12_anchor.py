# -*- coding: utf-8 -*-
"""P1-2 / P06 holdout 补覆盖锚终态测试（prereg-p12-r1 §6 / DV-P2）。

锚定：本批协议 hash、覆盖 120/120、holdout 触碰计数=2、触碰后冻结复封。
只读取证，不写任何实验域文件。
"""
from __future__ import annotations

import hashlib
import json
import os
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO)

OUT = os.path.join(REPO, "out", "v4-comparative-experiment", "p1-2-coverage")

PREREG_SHA256 = ("5b13e13db0d76976c2b120e7ff43a965dae67c8cbe4b"
                 "36e504a48125b1043ec5")
SIDS_20 = 20
ARMS = ("B1", "C1", "D1")


def _sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def test_prereg_frozen_hash():
    assert _sha(os.path.join(OUT, "prereg-p12-r1.md")) == PREREG_SHA256


def test_coverage_120():
    miss = []
    for sid_file in os.listdir(os.path.join(OUT, "inputs")):
        pass
    import re
    pat = re.compile(r"planner-input-(hol-f\d+-\d+)-([BCD]1)-r([12])\.json")
    sids = set()
    for fn in os.listdir(os.path.join(OUT, "inputs")):
        m = pat.match(fn)
        if m:
            sids.add(m.group(1))
    assert len(sids) == SIDS_20, "场景数 %d != 20" % len(sids)
    for sid in sids:
        for arm in ARMS:
            for rnd in (1, 2):
                for d, pref in (("inputs", "planner-input-"),
                                ("responses", "planner-response-")):
                    p = os.path.join(OUT, d, "%s%s-%s-r%d.json" % (pref, sid, arm, rnd))
                    if not os.path.exists(p):
                        miss.append(os.path.relpath(p, REPO))
    assert not miss, "缺失 %d 件: %s" % (len(miss), miss[:5])
    dl = [json.loads(l) for l in open(os.path.join(OUT, "dispatch-log.jsonl"),
                                      encoding="utf-8") if l.strip()]
    ok = sum(1 for e in dl if e.get("status") == "wrapper_ok")
    assert ok >= 120, "dispatch-log wrapper_ok=%d < 120" % ok


def test_holdout_touch_count_2():
    tl = json.load(open(os.path.join(OUT, "touch-ledger.json"), encoding="utf-8"))
    assert tl["count"] == 2, "holdout 触碰计数 %s != 2" % tl["count"]


def test_posttouch_freeze_sealed():
    pt = json.load(open(os.path.join(OUT, "post-touch-freeze.json"),
                        encoding="utf-8"))
    assert pt["batch"]["inputs_n"] == 120
    assert pt["batch"]["responses_n"] == 120
    assert all(pt["protected_files_ok"].values())
    gates = json.load(open(os.path.join(OUT, "gates-pooled.json"),
                           encoding="utf-8"))
    assert gates["pg_g9_no_posthoc_change"]["pass"] is True
    assert gates["pg_g8_replay_byte_exact"]["pass"] is True


if __name__ == "__main__":
    for fn in (test_prereg_frozen_hash, test_coverage_120,
               test_holdout_touch_count_2, test_posttouch_freeze_sealed):
        fn()
        print("PASS", fn.__name__)
