#!/usr/bin/env python
"""PAPER-P1-1B Rev-C staging 配对实验编排（protocol-p3-revc-v1）。

职责边界（S21/r4_review_run 同款纪律）：纯函数内核在
pcbflow/p3_revc_staging.py 与 pcbflow/v4_review_dispatch.py；本脚本做编排
落盘——只写 out/v4-exec/p3-revc/ 包内新文件（R7 追加式），零子进程、零
网络（kicad-cli DRC 调用由 Bash 侧在批 staging 目录内相对路径执行，本脚本
只读其产物 JSON 与 hash 留证文件）。

ops（argv 分派）：
  plan                     → plan.json + board-model.json（冻结规则选网）
  candidates --batch B     → candidates.json + challenger.kicad_pcb
                             + baseline/candidate scope geom + paired 指标
  drill-prepare --batch B  → rollback 演练副本（post/restored + pre hash）
  drill-finish             → rollback-drill.json（恢复后 DRC 计数断言）
  record --batch B         → batch-record.json（paired DRC 判定 + hash 链）
  review --batch B         → review-packages/RP-P3REVC-<B>（diff SVG+PNG+摘要）
  disposition-drill --batch B → dispositions/ 3 例演练 + ledger.json
  gates                    → gates.json（终态独立复算判定）

fail-closed：任何输入缺失/不一致 → ValueError（blocked 语义交 Bash 侧记录），
绝不渲染为 pass（R5）。声明日期常量，无 wall-clock。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from pcbflow import hashing, ledger, check_stage  # noqa: E402
from pcbflow import p3_revc_staging as pr  # noqa: E402
from pcbflow import svg_route_package as srp  # noqa: E402
from pcbflow import v4_review_dispatch as vrd  # noqa: E402

ROOT = REPO / "out" / "v4-exec" / "p3-revc"
PERNET = ROOT / "per-net-batch"
DECLARED_DATE = "2026-09-12"
PROTOCOL_REL = ("out/v4-exec/p3-revc/protocol/"
                "protocol-p3-revc-v1.json")
SNAPSHOT_REL = "out/v4-exec/p3-revc/per-net-batch/snapshot-pristine.kicad_pcb"


def _read_bytes(rel: Path) -> bytes:
    if not rel.is_file():
        raise ValueError("输入不在场（fail-closed）: %s" % rel)
    return rel.read_bytes()


def _read_json(rel: Path):
    return json.loads(_read_bytes(rel).decode("utf-8"))


def _write_json(rel: Path, obj) -> None:
    rel.parent.mkdir(parents=True, exist_ok=True)
    rel.write_bytes(hashing.json_dumps(obj).encode("utf-8") + b"\n")


def _sha_file(rel: Path) -> str:
    return hashing.sha256_file(str(rel))


def _snapshot_state():
    text = _read_bytes(REPO / SNAPSHOT_REL).decode("utf-8")
    sha = _sha_file(REPO / SNAPSHOT_REL)
    parsed = pr.parse_board_text(text)
    chains = pr.build_chains(parsed)
    rows, batches = pr.plan_pool(parsed, chains)
    return text, sha, parsed, chains, rows, batches


def _batch_dir(batch: str) -> Path:
    d = PERNET / batch
    if not d.is_dir() and not batch.startswith("batch-"):
        raise ValueError("批名非法: %r" % batch)
    return d


def _protocol() -> dict:
    return _read_json(REPO / PROTOCOL_REL)


# ---------------------------------------------------------------- ops

def op_plan(_req: dict) -> None:
    proto = _protocol()
    text, sha, parsed, chains, rows, batches = _snapshot_state()
    pre = proto["board_source"]["pre_hash_sha256"]
    if sha != pre:
        raise ValueError("快照 hash %s ≠ 协议 pre-hash %s（fail-closed）"
                         % (sha, pre))
    plan = {
        "schema": "pcbflow.paperexec.p3revc-plan/1",
        "protocol": PROTOCOL_REL,
        "declared_date": DECLARED_DATE,
        "snapshot_sha256": sha,
        "board_facts": {
            "net_count": len(parsed["copper_layers"]) and len(
                {s["net"] for s in parsed["segments"]}),
            "segment_count": len(parsed["segments"]),
            "via_count": len(parsed["vias"]),
            "pad_count": len(parsed["pads"]),
            "zone_nets": parsed["zone_nets"],
            "copper_layers": parsed["copper_layers"],
            "chain_count": len(chains),
        },
        "pool": rows,
        "batches": batches,
        "insert_via_candidate_note": (
            "池网全部单铜层且零 via → 协议冻结前置（双铜层既有几何）结构性"
            "不满足 → 0 提案（如实登记，不虚构）"),
    }
    _write_json(PERNET / "plan.json", plan)
    _write_json(PERNET / "board-model.json",
                pr.build_board_model(parsed, sha))


def op_candidates(req: dict) -> None:
    batch = req["batch"]
    _write_json(PERNET / "last-op.json",
                {"op": "candidates", "batch": batch})
    text, sha, parsed, chains, _rows, batches = _snapshot_state()
    if batch not in batches:
        raise ValueError("批 %r 不在冻结计划内（fail-closed）" % batch)
    nets = batches[batch]
    out = pr.generate_batch_candidates(parsed, chains, nets, sha,
                                        board_text=text)
    cand_text = pr.apply_patches(text, out["patches"])
    bd = _batch_dir(batch)
    bd.mkdir(parents=True, exist_ok=True)
    (bd / "challenger.kicad_pcb").write_bytes(cand_text.encode("utf-8"))
    # 重解析一致性断言（结构守恒：段数=基线+插入数；via 数不变）
    p2 = pr.parse_board_text(cand_text)
    n_ins = sum(1 for p in out["patches"]
                if p["text_ops"].get("insert_segment"))
    if len(p2["segments"]) != len(parsed["segments"]) + n_ins:
        raise ValueError("challenger 段数不守恒（fail-closed）")
    if len(p2["vias"]) != len(parsed["vias"]):
        raise ValueError("challenger via 数变化（fail-closed）")
    bg, cg = pr.candidate_scope_geom(parsed, chains, nets, out["patches"])
    _write_json(bd / "candidates.json", {
        "schema": "pcbflow.paperexec.p3revc-candidates/1",
        "batch": batch, "net_ids": nets,
        "snapshot_sha256": sha,
        "patches": out["patches"], "rejections": out["rejections"],
        "structural_asserts": {
            "segment_count_base": len(parsed["segments"]),
            "segment_count_challenger": len(p2["segments"]),
            "inserted_segments": n_ins,
            "via_count_unchanged": True,
        },
    })
    _write_json(bd / "baseline-geom.json", bg)
    _write_json(bd / "candidate-geom.json", cg)
    _write_json(bd / "paired-metrics.json",
                pr.paired_metrics(bg, cg, out["patches"], nets))


def op_drill_prepare(req: dict) -> None:
    batch = req["batch"]
    text, sha, parsed, chains, _rows, batches = _snapshot_state()
    if batch not in batches:
        raise ValueError("批 %r 不在冻结计划内（fail-closed）" % batch)
    cdir = _batch_dir(batch)
    cand = _read_json(cdir / "candidates.json")
    patches = cand["patches"]
    cand_text = pr.apply_patches(text, patches)
    dd = PERNET / "rollback-drill"
    dd.mkdir(parents=True, exist_ok=True)
    (dd / "drill-post.kicad_pcb").write_bytes(cand_text.encode("utf-8"))
    (dd / "drill-restored.kicad_pcb").write_bytes(text.encode("utf-8"))
    _write_json(dd / "drill-pre.json", {
        "schema": "pcbflow.paperexec.p3revc-drill-pre/1",
        "batch": batch, "declared_date": DECLARED_DATE,
        "pre_hash_sha256": sha,
        "post_hash_sha256": _sha_file(dd / "drill-post.kicad_pcb"),
        "restored_hash_sha256": _sha_file(dd / "drill-restored.kicad_pcb"),
        "post_differs_from_pre":
            _sha_file(dd / "drill-post.kicad_pcb") != sha,
        "restored_equals_pre": _sha_file(dd / "drill-restored.kicad_pcb")
        == sha,
    })


def op_drill_finish(_req: dict) -> None:
    dd = PERNET / "rollback-drill"
    pre = _read_json(dd / "drill-pre.json")
    err = _read_json(dd / "drc-error.json")
    allj = _read_json(dd / "drc-all.json")
    base_err = _read_json(PERNET / "baseline" / "drc-error.json")
    base_all = _read_json(PERNET / "baseline" / "drc-all.json")

    def counts(d):
        vs = d.get("violations") or []
        return {"severity_error": sum(1 for v in vs
                                      if v.get("severity") == "error"),
                "violations_total": len(vs),
                "unconnected_items": len(d.get("unconnected_items") or [])}

    ce, ca, be, ba = counts(err), counts(allj), counts(base_err), \
        counts(base_all)
    checks = {
        "post_differs_from_pre": pre["post_differs_from_pre"],
        "restored_equals_pre": pre["restored_equals_pre"],
        "restored_drc_equals_baseline": ce == be and ca == ba,
    }
    _write_json(dd / "rollback-drill.json", {
        "schema": "pcbflow.paperexec.p3revc-drill/1",
        "batch": pre["batch"], "declared_date": DECLARED_DATE,
        "pre_hash_sha256": pre["pre_hash_sha256"],
        "post_hash_sha256": pre["post_hash_sha256"],
        "restored_hash_sha256": pre["restored_hash_sha256"],
        "drill_drc_counts": {"severity_error_run": ce,
                             "severity_all_run": ca},
        "baseline_drc_counts": {"severity_error_run": be,
                                "severity_all_run": ba},
        "checks": checks,
        "verdict": "pass" if all(checks.values()) else "blocked",
    })


def op_record(req: dict) -> None:
    batch = req["batch"]
    bd = _batch_dir(batch)
    plan = _read_json(PERNET / "plan.json")
    if batch not in plan["batches"]:
        raise ValueError("批 %r 不在冻结计划内（fail-closed）" % batch)
    cand = _read_json(bd / "candidates.json")
    metrics = _read_json(bd / "paired-metrics.json")
    pre_hash = _read_json(PERNET / "plan.json")["snapshot_sha256"]
    post_hash = _sha_file(bd / "challenger.kicad_pcb")
    berr = _read_json(PERNET / "baseline" / "drc-error.json")
    ball = _read_json(PERNET / "baseline" / "drc-all.json")
    cerr = _read_json(bd / "drc-error.json")
    call = _read_json(bd / "drc-all.json")

    def counts(d):
        vs = d.get("violations") or []
        return {"severity_error": sum(1 for v in vs
                                      if v.get("severity") == "error"),
                "violations_total": len(vs),
                "unconnected_items": len(d.get("unconnected_items") or [])}

    be, ba, ce, ca = counts(berr), counts(ball), counts(cerr), counts(call)
    sidecar_path = bd / "sidecar-check.json"
    sidecar = _read_json(sidecar_path) if sidecar_path.is_file() else None
    if sidecar is None:
        raise ValueError("sidecar-check.json 不在场（R2 检查未执行，"
                         "fail-closed）: %s" % batch)
    checks = {
        "pre_hash_matches_snapshot": pre_hash == cand["snapshot_sha256"],
        "post_hash_differs": post_hash != pre_hash,
        "zero_new_severity_error":
            ce["severity_error"] == be["severity_error"],
        "connectivity_not_degraded":
            ca["unconnected_items"] <= ba["unconnected_items"],
        "dual_severity_error_stable":
            ce["severity_error"] == ca["severity_error"],
        "sidecar_checked": True,
    }
    _write_json(bd / "batch-record.json", {
        "schema": "pcbflow.paperexec.p3revc-batch-record/1",
        "batch": batch, "declared_date": DECLARED_DATE,
        "protocol": PROTOCOL_REL,
        "net_ids": cand["net_ids"],
        "hash_chain": {
            "live_board_pre_hash_sha256":
                _protocol()["board_source"]["pre_hash_sha256"],
            "snapshot_sha256": pre_hash,
            "challenger_post_hash_sha256": post_hash,
            "snapshot_byte_identical_to_live":
                pre_hash == _protocol()["board_source"]["pre_hash_sha256"],
        },
        "drc_dual_severity": {
            "baseline": {"severity_error_run": be, "severity_all_run": ba},
            "challenger": {"severity_error_run": ce,
                           "severity_all_run": ca},
            "deltas": {"severity_error": ce["severity_error"]
                       - be["severity_error"],
                       "unconnected_items": ca["unconnected_items"]
                       - ba["unconnected_items"]},
        },
        "drc_summary_challenger": check_stage.summarize_drc(call, cerr),
        "paired_target_metrics": metrics,
        "candidates": {"patch_count": len(cand["patches"]),
                       "rejection_count": len(cand["rejections"]),
                       "rejections": cand["rejections"]},
        "sidecar_check": sidecar,
        "checks": checks,
        "paired_result": "pass" if all(checks.values()) else "blocked",
    })


def op_review(req: dict) -> None:
    batch = req["batch"]
    bd = _batch_dir(batch)
    board = _read_json(PERNET / "board-model.json")
    bg = _read_json(bd / "baseline-geom.json")
    cg = _read_json(bd / "candidate-geom.json")
    cand = _read_json(bd / "candidates.json")
    case_id = "P3REVC-%s" % batch.upper()
    base_ref = vrd.enrich_geometry(board, bg, state="baseline",
                                   source="baseline")
    base_svg, base_man = srp.build(board, base_ref)
    baseline_pkg = {"svg_text": base_svg, "manifest": base_man}
    pkg = vrd.build_review_package(
        board, baseline_pkg, cg, case_id=case_id,
        validator_rejections=cand["rejections"])
    errs = vrd.verify_review_package(pkg)
    if errs:
        raise ValueError("复查包 verify 失败（fail-closed）: %s" % errs[:3])
    rdir = ROOT / "review-packages" / case_id
    rdir.mkdir(parents=True, exist_ok=True)
    pngs = vrd.render_review_package_pngs(board, pkg)
    (rdir / "package.json").write_bytes(
        hashing.json_dumps(pkg).encode("utf-8") + b"\n")
    (rdir / "baseline-view.svg").write_text(
        pkg["baseline_view"]["svg_text"], encoding="utf-8", newline="\n")
    (rdir / "diff-view.svg").write_text(
        pkg["diff_view"]["svg_text"], encoding="utf-8", newline="\n")
    for view, name in (("baseline_view", "baseline-view.png"),
                       ("diff_view", "diff-view.png")):
        if pngs.get(view):
            (rdir / name).write_bytes(pngs[view])
    _write_json(rdir / "manifest.json", {
        "schema": "pcbflow.paperexec.p3revc-review-manifest/1",
        "case_id": case_id, "batch": batch,
        "batch_result": _read_json(bd / "batch-record.json")
        ["paired_result"],
        "batch_record_pointer": ("out/v4-exec/p3-revc/per-net-batch/"
                                 + batch + "/batch-record.json"),
        "evidence_status_note": "批=blocked 时本包为 blocked-batch 证据包："
                                "diff 视图展示被回滚的 challenger；真实"
                                "处置恒待人工权威（human-disposition-"
                                "pending.md），处置演练≠真实处置",
        "review_package_sha256": pkg["review_package_sha256"],
        "three_bind": pkg["three_bind"],
        "counts": pkg["summary"]["counts"],
        "files": {
            "package": "package.json",
            "baseline_svg": "baseline-view.svg",
            "diff_svg": "diff-view.svg",
            "baseline_png": rec_avail(pkg, "baseline_view"),
            "diff_png": rec_avail(pkg, "diff_view"),
        },
    })


def rec_avail(pkg, view):
    return {"available": pkg[view]["png"].get("available", False),
            "png_sha256": pkg[view]["png"].get("png_sha256")}


def op_disposition_drill(req: dict) -> None:
    batch = req["batch"]
    case_id = "P3REVC-%s" % batch.upper()
    pkg = _read_json(ROOT / "review-packages" / case_id / "package.json")
    sha = pkg["review_package_sha256"]
    three = pkg["three_bind"]
    drills = [
        ("DIS-P3R-01", "accept", "candidate-improvement-stands",
         "处置演练=接受候选：倒角语义与 diff 视图一致；本例为机制演练，"
         "非真实处置（真实处置见 human-disposition-pending.md）"),
        ("DIS-P3R-02", "reject", "candidate-risk-not-accepted",
         "处置演练=拒绝候选：演练理由=假设审阅者不接受折角形态变更；"
         "本例为机制演练，非真实处置"),
        ("DIS-P3R-03", "known_open", "defer-to-human-authority",
         "处置演练=known_open：真实处置权在人工权威，本轮挂起；"
         "本例为机制演练，非真实处置"),
    ]
    entries = []
    records = []
    for (did, kind, code, text) in drills:
        disp = vrd.build_review_disposition(
            disposition_id=did, case_id=case_id,
            review_package_sha256=sha, kind=kind, rationale_code=code,
            approver="chief-reviewer", approver_role="chief_reviewer_drill",
            rationale_text=text)
        entries, _entry = vrd.append_review_disposition(
            entries, disposition=disp, case_id=case_id, three_bind=three)
        records.append(disp)
    chain_errs = ledger.verify_chain(entries)
    if chain_errs:
        raise ValueError("演练账本链不合法（fail-closed）: %s"
                         % chain_errs[:3])
    ddir = ROOT / "dispositions"
    ddir.mkdir(parents=True, exist_ok=True)
    _write_json(ddir / "ledger.json",
                {"schema": "pcbflow.v4exec.disposition-ledger/1",
                 "entries": entries})
    for disp in records:
        _write_json(ddir / ("%s.json" % disp["disposition_id"]), disp)
    _write_json(ddir / "drill-record.json", {
        "schema": "pcbflow.paperexec.p3revc-disposition-drill/1",
        "case_id": case_id, "declared_date": DECLARED_DATE,
        "drills": [d["disposition_id"] for d in records],
        "kinds": [d["kind"] for d in records],
        "verify_chain_errors": chain_errs,
        "note": "三例均为机制演练（P09 disposition 挂钩首次真实板消费）；"
                "真实处置未做——待批件 human-disposition-pending.md",
    })


def op_gates(_req: dict) -> None:
    plan = _read_json(PERNET / "plan.json")
    drill = _read_json(PERNET / "rollback-drill" / "rollback-drill.json")
    batch_records = []
    for batch in plan["batches"]:
        rec = _read_json(_batch_dir(batch) / "batch-record.json")
        # DRC 独立可复核：从留证 DRC JSON 重算计数（不信任 record 字段），
        # 断言重算结果与已记录 verdict 逻辑一致（blocked 亦须可复算成立）
        bd = _batch_dir(batch)
        berr = _read_json(PERNET / "baseline" / "drc-error.json")
        cerr = _read_json(bd / "drc-error.json")
        ball = _read_json(PERNET / "baseline" / "drc-all.json")
        call = _read_json(bd / "drc-all.json")

        def rc(d):
            vs = d.get("violations") or []
            return (sum(1 for v in vs if v.get("severity") == "error"),
                    len(d.get("unconnected_items") or []))

        be, bu = rc(berr)
        ba_u = rc(ball)[1]
        ce, cu = rc(cerr)
        ca_u = rc(call)[1]
        recomputed_zero_new = (ce == be)
        recomputed_conn_ok = (ca_u <= ba_u)
        expected = "pass" if (recomputed_zero_new
                              and recomputed_conn_ok) else "blocked"
        recompute = {
            "baseline_error": be, "challenger_error": ce,
            "baseline_unconnected": bu, "challenger_unconnected_all": ca_u,
            "recomputed_zero_new_error": recomputed_zero_new,
            "recomputed_connectivity_not_degraded": recomputed_conn_ok,
            "recomputed_verdict": expected,
            "verdict_matches_recomputation":
                rec["paired_result"] == expected,
        }
        rolled_back = (bd / "rollback.json").is_file()
        record_complete = all([
            rec["hash_chain"]["snapshot_sha256"],
            rec["hash_chain"]["challenger_post_hash_sha256"],
            rec["drc_dual_severity"]["deltas"]["severity_error"]
            is not None,
            rec["paired_target_metrics"]["totals"] is not None,
            rec["sidecar_check"] is not None,
            rec["paired_result"] in ("pass", "blocked"),
            (rec["paired_result"] == "blocked") <= rolled_back,
        ])
        batch_records.append({"batch": batch,
                              "paired_result": rec["paired_result"],
                              "record_complete": record_complete,
                              "rolled_back": rolled_back,
                              "recomputed": recompute,
                              "net_count": len(rec["net_ids"])})
    drill_rec = _read_json(ROOT / "dispositions" / "drill-record.json")
    ledger_entries = _read_json(ROOT / "dispositions" / "ledger.json")
    chain_errs = ledger.verify_chain(ledger_entries["entries"])
    checks = {
        "G1_paired_records_complete":
            bool(batch_records)
            and all(r["record_complete"] for r in batch_records),
        "G2_drc_independently_recomputable":
            all(r["recomputed"]["verdict_matches_recomputation"]
                for r in batch_records),
        "G3_rollback_drill_pass": drill["verdict"] == "pass",
        "G4_disposition_drills_at_least_3":
            len(drill_rec["drills"]) >= 3 and not chain_errs,
        "G5_zero_sidecar_residue": _sidecar_gate(),
    }
    experiment_result = "blocked" if any(
        r["paired_result"] == "blocked" for r in batch_records) \
        else "pass"
    _write_json(ROOT / "gates.json", {
        "schema": "pcbflow.paperexec.p3revc-gates/1",
        "declared_date": DECLARED_DATE, "protocol": PROTOCOL_REL,
        "gate_semantics": "门=包完整性/可复核性（任务书 §5）；批次结果"
                          "（pass/blocked）是实验结果，如实落账，不与"
                          "包门混同",
        "experiment_result": experiment_result,
        "batches": batch_records,
        "checks": checks,
        "all_pass": all(checks.values()),
        "blocked": [k for k, v in checks.items() if not v],
    })


def _sidecar_gate() -> bool:
    log = PERNET / "sidecar-log.jsonl"
    if not log.is_file():
        return False
    ok = True
    for line in log.read_bytes().decode("utf-8").splitlines():
        if not line.strip():
            continue
        entry = json.loads(line)
        if not entry.get("live_prl_unchanged", False):
            ok = False
        if entry.get("datasets_prl_count", 1) != 0:
            ok = False
    return ok


def op_rollback(req: dict) -> None:
    """整批回滚留证（协议 §criteria.failure_path）：challenger 撤出终局
    候选域，staging 活跃文本=snapshot-pristine（hash 亲验）；不修补、
    不换候选重试。R7 追加式：batch-record.json 零字节不动。"""
    batch = req["batch"]
    bd = _batch_dir(batch)
    rec = _read_json(bd / "batch-record.json")
    if rec["paired_result"] != "blocked":
        raise ValueError("批 %s 非 blocked，无回滚语义（fail-closed）"
                         % batch)
    snap = PERNET / "snapshot-pristine.kicad_pcb"
    staging_active_hash = _sha_file(snap)
    proto = _protocol()
    _write_json(bd / "rollback.json", {
        "schema": "pcbflow.paperexec.p3revc-rollback/1",
        "batch": batch, "declared_date": DECLARED_DATE,
        "rollback_reason": "zero_new_severity_error violated "
                           "(+%d error; protocol §criteria.failure_path)"
                           % rec["drc_dual_severity"]["deltas"]
                           ["severity_error"],
        "challenger_withdrawn": True,
        "challenger_kept_as_evidence": "challenger.kicad_pcb（留证，"
                                       "不入终局候选）",
        "staging_active_text": "snapshot-pristine.kicad_pcb",
        "staging_active_hash_sha256": staging_active_hash,
        "staging_equals_live_pre_hash":
            staging_active_hash
            == proto["board_source"]["pre_hash_sha256"],
        "no_repair_no_retry": True,
        "diagnosis": {
            "new_violation": "clearance: challenger 倒角对角段 "
                             "[LTDC_R7] (48.126,23.15) vs U1.109 "
                             "[FMC_BA1] 焊盘，KiCad 实测 0.1571 < 0.2",
            "advisory_precheck_root_cause": "预检 pad 模型取 "
                                            "min(w,h)/2=0.15，长条焊盘 "
                                            "1.5×0.3 长轴半程实为 0.75 "
                                            "——advisory 预检过弱，"
                                            "kicad-cli authority 拦截",
            "violation_reanchoring": "FDCAN1_TX 既有 track_width 违例"
                                     "（0.15<0.2 板约束）因段端点修改 "
                                     "GONE+NEW 重锚定，计数 ±0",
        },
    })


OPS = {"plan": op_plan, "candidates": op_candidates,
       "drill-prepare": op_drill_prepare, "drill-finish": op_drill_finish,
       "record": op_record, "rollback": op_rollback, "review": op_review,
       "disposition-drill": op_disposition_drill, "gates": op_gates}


def main() -> None:
    req = {"op": sys.argv[1]}
    if "--batch" in sys.argv:
        req["batch"] = sys.argv[sys.argv.index("--batch") + 1]
    if req["op"] not in OPS:
        raise SystemExit("unknown op: %r" % req["op"])
    OPS[req["op"]](req)


if __name__ == "__main__":
    main()
