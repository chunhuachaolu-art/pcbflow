"""pcbflow.v4_1.e6g61 -- G6.1 编排（staging/审计/advisory 披露/双口径
oracle/divergence/汇总）。

用法（编排侧）：

    python -m pcbflow.v4_1.e6g61 stage-g61 --e6-dir out/v4.1-engineering/e6 \
        [--e4-staging-pcb <E4 staging 板>] [--e4-staging-pro <E4 staging pro>]
    python -m pcbflow.v4_1.e6g61 run-g61 --e6-dir out/v4.1-engineering/e6 \
        [--watch <受监护目录> ...]

run-g61 每场景产物：<scenario>/g61-result.json（canonical）；汇总
g61-refill/g61-summary.json。kicad-cli 全部经 e6prl.KicadCliGuard（prl
卫生制度化先吃狗食）；guard 事故在 post_restore_matches_before=true 时
按复原后状态继续（台账留痕），不可复原=中止（fail-closed）。
"""

from __future__ import annotations

import json
import os

from . import DECLARED_DATE
from .canonical import write_canonical_json
from .e6prl import KicadCliGuard, PrlHygieneIncident
from .e6zone import (audit_zone_refill_interactions,
                     build_scenario_boards, candidate_zone_exposure,
                     refill_divergence)

__all__ = ["op_stage_g61", "op_run_g61", "_g61_candidate_defs"]


def _g61_candidate_defs():
    """场景内「引擎后置候选」定义（advisory 披露+暴露旗标判据用）。"""
    return {
        "ZN-0-no-zone-negative-control": {
            "kind": "segment", "net": "nA", "layer": "F.Cu",
            "bbox": (9.4, 9.4, 20.6, 10.6),
            "via": None,
            "segment": (10.0, 10.0, 20.0, 10.0, 0.25),
        },
        "ZN-1-stale-fill-foreign-via": {
            "kind": "via", "net": "SIG", "layers": ["F.Cu", "B.Cu"],
            "bbox": (29.7, 19.7, 30.3, 20.3),
            "via": (30.0, 20.0, 0.6),
            "segment": None,
        },
        "ZN-4-stale-fill-foreign-track": {
            "kind": "segment", "net": "SIG", "layer": "F.Cu",
            "bbox": (19.875, 19.875, 55.125, 20.125),
            "via": None,
            "segment": (20.0, 20.0, 55.0, 20.0, 0.25),
        },
    }


def op_stage_g61(e6_dir, e4_staging_pcb=None, e4_staging_pro=None):
    """G6.1 staging：合成板落盘 + ZN-5 真板快照副本（零写源，不带 prl）。"""
    base = os.path.join(e6_dir, "g61-refill")
    os.makedirs(base, exist_ok=True)
    sc = build_scenario_boards()
    for sid, s in sc.items():
        d = os.path.join(base, sid)
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "case.kicad_pcb"), "w",
                  encoding="utf-8", newline="\n") as f:
            f.write(s["board_text"])
        write_canonical_json(os.path.join(d, "case.kicad_pro"),
                             s["pro_obj"])
    copied = None
    if e4_staging_pcb and e4_staging_pro:
        import hashlib
        import shutil
        d5 = os.path.join(base, "ZN-5-revc-staging-real")
        os.makedirs(d5, exist_ok=True)
        shutil.copyfile(e4_staging_pcb, os.path.join(d5, "revc.kicad_pcb"))
        shutil.copyfile(e4_staging_pro, os.path.join(d5, "revc.kicad_pro"))
        with open(e4_staging_pcb, "rb") as f:
            sha = hashlib.sha256(f.read()).hexdigest()
        copied = {"scenario": "ZN-5-revc-staging-real",
                  "src_pcb_sha256": sha, "prl_excluded": True}
    return {"staged": sorted(sc), "real_board_copy": copied}


def _advisory_disclosure(board_text, pro_obj, cand):
    """既有 advisory 链（precheck+checker）对 zone 交互候选的结果+披露。"""
    from .board_parse import parse_board_text
    from .board_parse_alt import parse_board_text_alt
    from .checker import IndependentGeometryChecker, build_check_items
    from .netclasses import netclass_table_from_kicad_pro
    from .precheck import AdvisoryPrecheckV41, build_geom_items
    table = netclass_table_from_kicad_pro(pro_obj)
    parsed_a = parse_board_text(board_text)
    parsed_b = parse_board_text_alt(board_text)
    pre = AdvisoryPrecheckV41(build_geom_items(parsed_a), table)
    chk = IndependentGeometryChecker(build_check_items(parsed_b), table)
    if cand["via"] is not None:
        x, y, size = cand["via"]
        r_pre = pre.check_via(cand["net"], cand["layers"], size, x, y)
        r_chk = chk.check_via(cand["net"], cand["layers"], size, x, y)
    else:
        x1, y1, x2, y2, w = cand["segment"]
        r_pre = pre.check_segment(cand["net"], cand["layer"], w,
                                  x1, y1, x2, y2)
        r_chk = chk.check_segment(cand["net"], cand["layer"], w,
                                  x1, y1, x2, y2)
    return {
        "precheck_verdict": r_pre["verdict"],
        "checker_verdict": r_chk["verdict"],
        "zone_limitation_disclosed": bool(
            [l for l in r_pre["limitations"] if "zone" in l]),
        "limitations": r_pre["limitations"],
        "interpretation": "advisory clean 对 zone 交互几何不可作终判"
                          "（E1 登记 limitation；终判=kicad-cli 双口径 "
                          "DRC+E6 暴露旗标）",
    }


def op_run_g61(e6_dir, live_watch_dirs=()):
    """G6.1 全量执行：audit→advisory 披露→guard 双口径 DRC→divergence。"""
    base = os.path.join(e6_dir, "g61-refill")
    guard = KicadCliGuard(os.path.join(base, "kicad-cli-calls.log"),
                          watch_dirs=list(live_watch_dirs))
    sc = build_scenario_boards()
    cands = _g61_candidate_defs()
    scenarios = [("ZN-0", "ZN-0-no-zone-negative-control"),
                 ("ZN-1", "ZN-1-stale-fill-foreign-via"),
                 ("ZN-2", "ZN-2-unfilled-zone-pour"),
                 ("ZN-3", "ZN-3-awaiting-refill-same-net"),
                 ("ZN-4", "ZN-4-stale-fill-foreign-track")]
    z5dir = os.path.join(base, "ZN-5-revc-staging-real")
    if os.path.isfile(os.path.join(z5dir, "revc.kicad_pcb")):
        scenarios.append(("ZN-5", "ZN-5-revc-staging-real"))
    results = []
    for short, sid in scenarios:
        d = os.path.join(base, sid)
        board_file = ("case.kicad_pcb" if short != "ZN-5"
                      else "revc.kicad_pcb")
        with open(os.path.join(d, board_file), encoding="utf-8") as f:
            board_text = f.read()
        audit = audit_zone_refill_interactions(board_text)
        entry = {"scenario_id": sid, "audit": audit}
        if sid in sc:
            entry["guard_expect"] = sc[sid]["guard_expect"]
            entry["oracle_expect"] = sc[sid]["oracle_expect"]
        if sid in cands:
            cand = cands[sid]
            entry["advisory_disclosure"] = _advisory_disclosure(
                board_text, sc[sid]["pro_obj"], cand)
            layers = ([cand["layer"]] if cand.get("layer")
                      else cand["layers"])
            entry["candidate_exposure"] = candidate_zone_exposure(
                cand["kind"], cand["net"], layers, cand["bbox"],
                board_text)
        calls = []
        drc_a = drc_b = None
        for tag, extra in (("norefill", []),
                           ("refill", ["--refill-zones"])):
            out_name = "drc-%s-all.json" % tag
            argv = ["pcb", "drc", "--format", "json", "--severity-all",
                    "--output", out_name] + extra + [board_file]
            try:
                _rc, _stdout, rec = guard.call(argv, d,
                                               cwd_role="g61-" + short)
                hygiene = {"verdict": rec["verdict"],
                           "call_seq": rec["call_seq"],
                           "returncode": rec["returncode"]}
            except PrlHygieneIncident as exc:
                rec = exc.record
                sub = [h for h in rec["hygiene"].values()
                       if h["role"] == "cwd"][0]
                if not sub["post_restore_matches_before"]:
                    raise  # 不可复原=fail-closed 中止
                hygiene = {"verdict": rec["verdict"],
                           "call_seq": rec["call_seq"],
                           "returncode": rec["returncode"],
                           "restored_incident": True}
            calls.append({"tag": tag, "output": out_name,
                          "hygiene": hygiene})
            with open(os.path.join(d, out_name), encoding="utf-8") as f:
                drc = json.load(f)
            entry["drc_%s" % tag] = {
                "violations": len(drc.get("violations", [])),
                "unconnected": len(drc.get("unconnected_items", [])),
            }
            if tag == "norefill":
                drc_a = drc
            else:
                drc_b = drc
        entry["kicad_cli_calls"] = calls
        entry["divergence"] = refill_divergence(drc_a, drc_b)
        results.append(entry)
        write_canonical_json(os.path.join(d, "g61-result.json"), entry)
    summary = {
        "schema": "pcbflow.v4_1.e6-g61-summary/1",
        "declared_date": DECLARED_DATE,
        "scenarios": results,
        "guard_calls_total": guard._seq,
    }
    write_canonical_json(os.path.join(base, "g61-summary.json"), summary)
    return summary


def main(argv=None):
    """CLI：python -m pcbflow.v4_1.e6g61 stage-g61|run-g61 ..."""
    import argparse
    ap = argparse.ArgumentParser(prog="pcbflow.v4_1.e6g61")
    sub = ap.add_subparsers(dest="op", required=True)
    p1 = sub.add_parser("stage-g61")
    p1.add_argument("--e6-dir", required=True)
    p1.add_argument("--e4-staging-pcb")
    p1.add_argument("--e4-staging-pro")
    p2 = sub.add_parser("run-g61")
    p2.add_argument("--e6-dir", required=True)
    p2.add_argument("--watch", action="append", default=[])
    ns = ap.parse_args(argv)
    if ns.op == "stage-g61":
        print(json.dumps(op_stage_g61(ns.e6_dir, ns.e4_staging_pcb,
                                      ns.e4_staging_pro),
                         ensure_ascii=False, sort_keys=True))
        return 0
    if ns.op == "run-g61":
        s = op_run_g61(ns.e6_dir, live_watch_dirs=ns.watch)
        for r in s["scenarios"]:
            print(r["scenario_id"],
                  "flags=", r["audit"]["flag_classes_present"],
                  "div=", r["divergence"]["verdict"],
                  "viol=%d/%d unc=%d/%d" % (
                      r["drc_norefill"]["violations"],
                      r["drc_refill"]["violations"],
                      r["drc_norefill"]["unconnected"],
                      r["drc_refill"]["unconnected"]))
        print("guard_calls_total=", s["guard_calls_total"])
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
