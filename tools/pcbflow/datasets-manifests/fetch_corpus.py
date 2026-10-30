#!/usr/bin/env python3
"""Fetch the third-party boards used by pcbflow experiments from their
original sources (they are not redistributed in this repository).

Usage:
    python fetch_corpus.py                 # corpus-r2-r1 + holdout-candidates-r1
    python fetch_corpus.py --dataset corpus-r2-r1
    python fetch_corpus.py --list          # show every board and its source

Only GitHub-hosted rows with a pinned commit are downloaded automatically
(raw.githubusercontent.com/<repo>/<commit>/<path>). Where the experiments
recorded a sha256, the download is verified against it and rejected on
mismatch. PCBench / KiCad demos / PCBBenchmarks rows are listed with their
upstream so you can obtain them under their own terms.

Each board keeps its own license (see the "license" field); by downloading
you accept that license from the original author, not from this project.
"""
import argparse
import hashlib
import json
import os
import sys
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
DEST = os.path.normpath(os.path.join(HERE, "..", "datasets"))


def raw_url(row):
    repo = row["repo"].rstrip("/")
    prefix = "https://github.com/"
    if not repo.startswith(prefix) or not row.get("commit") or not row.get("path_in_repo"):
        return None
    slug = repo[len(prefix):]
    return "https://raw.githubusercontent.com/%s/%s/%s" % (
        slug, row["commit"], urllib.parse.quote(row["path_in_repo"]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", action="append")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    src = json.load(open(os.path.join(HERE, "SOURCES.json"), encoding="utf-8"))
    want = set(a.dataset or ["corpus-r2-r1", "holdout-candidates-r1"])
    ok = bad = skipped = 0
    for row in src["boards"]:
        if a.list:
            print("%-22s %-45s %-18s %s" % (row["dataset"], row["board_id"][:45],
                                            str(row["license"])[:18], row["repo"]))
            continue
        if row["dataset"] not in want:
            continue
        url = raw_url(row)
        if url is None:
            skipped += 1
            print("manual  %s/%s  <- %s" % (row["dataset"], row["board_id"], row["repo"]))
            continue
        sub = row.get("local_dir") or os.path.join("raw", row["board_id"])
        out_dir = os.path.join(DEST, row["dataset"], sub)
        out = os.path.join(out_dir, os.path.basename(row["path_in_repo"]))
        os.makedirs(out_dir, exist_ok=True)
        try:
            data = urllib.request.urlopen(url, timeout=120).read()
        except Exception as exc:  # noqa: BLE001
            bad += 1
            print("FAIL    %s: %s" % (row["board_id"], exc))
            continue
        digest = hashlib.sha256(data).hexdigest()
        if row.get("sha256") and digest != row["sha256"]:
            bad += 1
            print("MISMATCH %s: got %s want %s" % (row["board_id"], digest, row["sha256"]))
            continue
        with open(out, "wb") as fh:
            fh.write(data)
        ok += 1
        print("ok      %s (%d bytes)" % (row["board_id"], len(data)))
    if not a.list:
        print("\nfetched=%d failed=%d manual=%d -> %s" % (ok, bad, skipped, DEST))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
