#!/usr/bin/env python
"""replay_r13_r16.py — chain-replay verification of the abstention-typology
rubric against its registered base chain (release copy, PAPER-P2-3 package).

Chain-replay rule (as registered): before the rubric is applied to any new
corpus, the classifier is replayed on the registered base corpus (development
rounds r13-r16, 48 reader files, 132 abstain flags) and every replayed count
must equal the registered value — fail-closed: any mismatch stops the run;
no keyword is ever loosened to force a match.

What is replayed and compared
-----------------------------
1. per-round family counts        (contact chain r13-r16 = 8/15/5/10 and the
                                   other four families; key
                                   registered_chain.per_round.{r}.families)
2. per-(round,view) family counts (registered_chain.per_round_view)
3. grand family totals            (registered_chain.grand_families)
4. abstain-flag total             (132)
5. per-instance (abstain, flags)  (24 cells; both vs registered_chain and vs
                                   the 4 calibration-run-{r13..r16}.json
                                   instances.{view}-{i}.combined records)
6. per-flag family assignment     (132 flags; vs the local frozen typology
                                   file when available — this check needs
                                   the internal frozen file and is skipped,
                                   with a note, when it is absent)

Inputs (NOT redistributed with this package — PR-2: no frozen reader
readings ship in the release): the 48 reader-raw-r1[3456]-*.txt files and
4 calibration-run-{r13,r14,r15,r16}.json files under ``--cal-dir``.
Default layout = the development repo:
  <repo>/out/v3-tl2/calibration/
where <repo> is four levels above this script
(tools/pcbflow/artifact-release/paper2-protocol/rubric/ -> tools/pcbflow).

External reproducers without the corpus can still validate the release
JSON's registered aggregates for internal consistency (``--registered-only``).

Usage:
  python replay_r13_r16.py [--cal-dir DIR] [--rubric JSON] [--out PATH]
                           [--registered-only]

Exit code 0 = all replays equal; 1 = mismatch (fail-closed); 2 = usage error.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from abstain_classifier import (  # noqa: E402
    FAMILIES, classify, verify_rubric_json,
)

HERE = Path(__file__).resolve().parent
RELEASE_RUBRIC = HERE / "abstain-rubric-r13-r16.json"
DEFAULT_REPO = HERE.parents[2]  # .../tools/pcbflow
DEFAULT_CAL = DEFAULT_REPO / "out" / "v3-tl2" / "calibration"
DEFAULT_FROZEN = DEFAULT_CAL / "abstain-typology-r13-r16.json"

ROUNDS = ("r13", "r14", "r15", "r16")
VIEWS = ("top", "bottom")
VARIANTS = ("applied", "prep1")
INSTANCES = ("i1", "i2", "i3")

DECLARED_DATE = "2026-09-12"


def _fail(msg: str) -> None:
    print(f"[replay-r13-r16] FAIL: {msg}")
    sys.exit(1)


def parse_stem(stem: str) -> dict:
    """reader-raw-r13-applied-top-i1 -> round/view/variant/instance."""
    if not stem.startswith("reader-raw-"):
        _fail(f"unexpected filename prefix: {stem}")
    parts = stem[len("reader-raw-"):].split("-")
    if len(parts) != 4:
        _fail(f"unexpected filename structure: {stem}")
    rnd, variant, view, inst = parts
    if rnd not in ROUNDS or variant not in VARIANTS \
            or view not in VIEWS or inst not in INSTANCES:
        _fail(f"filename field out of range: {stem}")
    return {"round": rnd, "variant": variant, "view": view, "instance": inst}


def canonical_json_bytes(obj) -> bytes:
    return (json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=1)
            + "\n").encode("utf-8")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def replay(cal_dir: Path) -> dict:
    files = sorted(cal_dir.glob("reader-raw-r1[3456]-*.txt"))
    if len(files) != 48:
        _fail(f"reader-raw r13-r16 should be 48 files, found {len(files)} "
              f"in {cal_dir}")

    per_flag = []
    inst_counts = {}
    for path in files:
        meta = parse_stem(path.stem)
        data = json.loads(path.read_text(encoding="utf-8"))
        ik = (meta["round"], meta["view"], meta["instance"])
        inst_counts.setdefault(ik, [0, 0])
        for img in data.get("per_image", []):
            for fl in img.get("flags", []):
                ik = (meta["round"], meta["view"], meta["instance"])
                inst_counts[ik][1] += 1
                if fl.get("abstain") is True:
                    family, _hits = classify(fl.get("location_evidence", ""))
                    inst_counts[ik][0] += 1
                    per_flag.append({
                        "round": meta["round"], "view": meta["view"],
                        "board": meta["variant"],
                        "instance": meta["instance"],
                        "source_file": path.name,
                        "flag_id": fl.get("flag_id"),
                        "family": family,
                    })
    return {"per_flag": per_flag, "inst_counts": inst_counts,
            "files": [p.name for p in files]}


def aggregates(replay_doc: dict) -> dict:
    per_flag = replay_doc["per_flag"]
    per_round = {r: {f: 0 for f in FAMILIES} for r in ROUNDS}
    for pf in per_flag:
        per_round[pf["round"]][pf["family"]] += 1
    per_round_view = {}
    for r in ROUNDS:
        for v in VIEWS:
            fams = {f: 0 for f in FAMILIES}
            abst = 0
            for pf in per_flag:
                if pf["round"] == r and pf["view"] == v:
                    fams[pf["family"]] += 1
                    abst += 1
            per_round_view[f"{r}|{v}"] = {"abstain": abst, "families": fams}
    grand = {f: sum(per_round[r][f] for r in ROUNDS) for f in FAMILIES}
    total_abstain = per_flag_pf_shape(per_flag)
    return {"per_round": per_round, "per_round_view": per_round_view,
            "grand": grand, "total_abstain": total_abstain}


def per_flag_pf_shape(per_flag) -> int:
    return len(per_flag)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cal-dir", default=str(DEFAULT_CAL))
    ap.add_argument("--rubric", default=str(RELEASE_RUBRIC))
    ap.add_argument("--out", default=None,
                    help="write canonical replay-report JSON to PATH")
    ap.add_argument("--registered-only", action="store_true",
                    help="skip corpus replay; only check release JSON "
                         "internal consistency")
    args = ap.parse_args()

    rubric_path = Path(args.rubric)
    if not rubric_path.exists():
        _fail(f"rubric JSON not found: {rubric_path}")
    check = verify_rubric_json(rubric_path)
    doc = json.loads(rubric_path.read_text(encoding="utf-8"))
    reg = doc["registered_chain"]

    print(f"[replay-r13-r16] rubric JSON verified against classifier "
          f"constants: {sorted(check['keyword_tables_verified'])}")
    print(f"[replay-r13-r16] priority orders: registered="
          f"{check['priority_as_registered']} implemented="
          f"{check['priority_as_implemented']}")

    report = {
        "artifact": "rubric-chain-replay-r13-r16",
        "declared_date": DECLARED_DATE,
        "rubric_json": rubric_path.name,
        "rubric_json_sha256": sha256_file(rubric_path),
        "keyword_tables_vs_code": "equal",
        "checks": {},
        "fail_closed": True,
    }

    # -- registered-only mode: consistency of aggregates in the JSON ------
    pr = reg["per_round"]
    s = sum(pr[r]["families"]["contact"] for r in ROUNDS)
    if s != reg["grand_families"]["contact"]:
        _fail("registered JSON inconsistent: contact chain sum != grand")
    if sum(pr[r]["abstain"] for r in ROUNDS) != reg["abstain_flag_total"]:
        _fail("registered JSON inconsistent: abstain sums != total")
    n_inst = len(reg["per_instance"])
    if n_inst != 24:
        _fail(f"registered JSON per_instance cells = {n_inst}, expected 24")
    if sum(e["abstain_count"] for e in reg["per_instance"]) \
            != reg["abstain_flag_total"]:
        _fail("registered JSON inconsistent: per-instance abstain sum "
              "!= total")
    report["checks"]["registered_json_internal_consistency"] = "pass"
    print("[replay-r13-r16] registered JSON internal consistency: pass")

    if args.registered_only:
        report["conclusion"] = "registered-only mode: consistency pass"
        _finish(report, args.out)
        return 0

    # -- full corpus replay ------------------------------------------------
    cal_dir = Path(args.cal_dir)
    if not cal_dir.exists():
        _fail(f"calibration corpus dir not found: {cal_dir} "
              "(pass --cal-dir; the corpus is not redistributed)")
    replay_doc = replay(cal_dir)
    agg = aggregates(replay_doc)

    # 1-3: per-round / per-view / grand family counts vs registered
    for r in ROUNDS:
        for f in FAMILIES:
            got, want = agg["per_round"][r][f], reg["per_round"][r]["families"][f]
            if got != want:
                _fail(f"chain replay mismatch: {r} family {f} "
                      f"replayed={got} registered={want}")
    report["checks"]["per_round_family_counts"] = {
        "result": "equal",
        "contact_chain_replayed": {r: agg["per_round"][r]["contact"]
                                   for r in ROUNDS},
        "contact_chain_registered": {r: reg["per_round"][r]["families"]
                                     ["contact"] for r in ROUNDS},
    }
    print(f"[replay-r13-r16] per-round family counts: equal for all "
          f"{len(ROUNDS)}x{len(FAMILIES)} cells; contact chain "
          f"replayed={[agg['per_round'][r]['contact'] for r in ROUNDS]}")
    for key, val in agg["per_round_view"].items():
        want = reg["per_round_view"][key]
        if val["abstain"] != want["abstain"] or \
                val["families"] != want["families"]:
            _fail(f"chain replay mismatch: {key} replayed={val} "
                  f"registered={want}")
    report["checks"]["per_round_view_family_counts"] = "equal"
    if agg["grand"] != reg["grand_families"]:
        _fail(f"grand family totals mismatch: {agg['grand']} vs "
              f"{reg['grand_families']}")
    if agg["total_abstain"] != reg["abstain_flag_total"]:
        _fail(f"abstain total mismatch: {agg['total_abstain']} vs "
              f"{reg['abstain_flag_total']}")
    report["checks"]["grand_family_totals"] = "equal"
    report["checks"]["abstain_flag_total"] = {
        "replayed": agg["total_abstain"],
        "registered": reg["abstain_flag_total"],
    }
    print(f"[replay-r13-r16] grand families + abstain total "
          f"({agg['total_abstain']}): equal")

    # 5: per-instance vs registered AND vs run files
    for e in reg["per_instance"]:
        ik = (e["round"], e["view"], e["instance"])
        got = replay_doc["inst_counts"][ik]
        if got[0] != e["abstain_count"] or got[1] != e["flag_count"]:
            _fail(f"per-instance mismatch {ik}: replayed={got} "
                  f"registered=({e['abstain_count']},{e['flag_count']})")
    run_cells = 0
    for r in ROUNDS:
        run_path = cal_dir / f"calibration-run-{r}.json"
        if not run_path.exists():
            _fail(f"missing run file: {run_path.name}")
        run = json.loads(run_path.read_text(encoding="utf-8"))
        inst = run.get("instances", {})
        for view in VIEWS:
            for i in INSTANCES:
                ref = inst.get(f"{view}-{i}", {}).get("combined", {})
                got = replay_doc["inst_counts"][(r, view, i)]
                if got[0] != ref.get("abstain_count") or \
                        got[1] != ref.get("flag_count"):
                    _fail(f"cross-check mismatch {r}|{view}-{i}: "
                          f"replayed={got} run=({ref.get('abstain_count')},"
                          f"{ref.get('flag_count')})")
                run_cells += 1
    report["checks"]["per_instance_counts"] = {
        "vs_registered": "equal (24/24)",
        "vs_run_files": f"equal ({run_cells}/{run_cells})",
    }
    print(f"[replay-r13-r16] per-instance (abstain,flags): 24/24 registered "
          f"+ {run_cells}/{run_cells} run-file cells equal")

    # 6: per-flag family vs frozen typology (only when the internal frozen
    #    file is present; skipped otherwise with an explicit note)
    if DEFAULT_FROZEN.exists():
        frozen = json.loads(DEFAULT_FROZEN.read_text(encoding="utf-8"))
        reg_map = {(pf["round"], pf["view"], pf["board"], pf["instance"],
                    pf["flag_id"]): pf["family"]
                   for pf in frozen["per_flag"]}
        n_equal = 0
        for pf in replay_doc["per_flag"]:
            key = (pf["round"], pf["view"], pf["board"], pf["instance"],
                   pf["flag_id"])
            if reg_map.get(key) != pf["family"]:
                _fail(f"per-flag family mismatch: {key} replayed="
                      f"{pf['family']} frozen={reg_map.get(key)}")
            n_equal += 1
        if n_equal != len(frozen["per_flag"]):
            _fail(f"per-flag count mismatch: replayed {n_equal} vs frozen "
                  f"{len(frozen['per_flag'])}")
        report["checks"]["per_flag_family_vs_frozen_typology"] = {
            "result": "equal", "flags": n_equal,
            "frozen_file": DEFAULT_FROZEN.name,
            "frozen_file_sha256": sha256_file(DEFAULT_FROZEN),
        }
        print(f"[replay-r13-r16] per-flag family assignment: {n_equal}/"
              f"{n_equal} equal to frozen typology per_flag")
    else:
        report["checks"]["per_flag_family_vs_frozen_typology"] = \
            "skipped (frozen typology file not present on this machine)"
        print("[replay-r13-r16] per-flag check: skipped (frozen file "
              "absent)")

    report["conclusion"] = (
        "chain replay PASS: classifier replayed on the registered base "
        "chain r13-r16 reproduces every registered count (fail-closed "
        "comparison; no keyword loosened). The rubric may be applied to a "
        "new corpus under the registered rule.")
    report["input_files"] = {
        "reader_raw_count": len(replay_doc["files"]),
        "run_files": [f"calibration-run-{r}.json" for r in ROUNDS],
    }
    report["per_flag_family_assignments_no_text"] = [
        {k: pf[k] for k in ("round", "view", "board", "instance",
                            "flag_id", "family")}
        for pf in replay_doc["per_flag"]
    ]
    _finish(report, args.out)
    return 0


def _finish(report: dict, out) -> None:
    if out:
        path = Path(out)
        path.write_bytes(canonical_json_bytes(report))
        print(f"[replay-r13-r16] report written: {path} sha256="
              f"{hashlib.sha256(canonical_json_bytes(report)).hexdigest()}")
    print(f"[replay-r13-r16] CONCLUSION: {report['conclusion']}")


if __name__ == "__main__":
    sys.exit(main())
