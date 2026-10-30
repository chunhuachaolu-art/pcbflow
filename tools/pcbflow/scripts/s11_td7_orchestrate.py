"""S11 TD7 外部执行 backend qualification：freerouting CLI 实配编排（编排侧脚本）。

本脚本=编排侧（非生成器）：文件读写、外部事实度量与 pcbflow 纯函数
调用；freerouting/kicad-cli/pcbnew 调用经 scripts/s11_run_step.py 与
scripts/s11_pcbnew_step.py 由 Bash 逐显式 argv 执行（生成器纪律：
pcbflow/*.py 零子进程）。datasets/ 与既有 out/ 只读；新产物只进
out/v3-td7/；staging=OS 临时目录（收尾清理）；live 板/profile 零写。

子命令（按执行顺序）：
  plan        度量 37 真实 profile → 确定性选板 → staging 布局+步骤清单
              （out/v3-td7/boards/<pid>/plan.json + steps/run-<i>.json）
  sesanalyze  实跑后：SES 解析/确定性/L1/DRC delta/参考对比 →
              run-record.json（boards/<pid>/）
  aggregate   工具链登记+资格报告+judge/ledger/gate+锁提案 →
              out/v3-td7/ 顶层产物

确定性：全部核产物=pcbflow 纯函数+注入 hash；日期=backend_qualification
.Q_DATE（人工会话声明）；路径一律仓库相对 POSIX；JSON 落盘一律
hashing.json_dumps（byte-exact 重放）。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from pcbflow import backend_qualification as bq  # noqa: E402
from pcbflow import check_stage, external_backend, gate as gate_mod  # noqa: E402
from pcbflow import hashing, judge, ledger  # noqa: E402

TD7 = REPO / "out" / "v3-td7"
JAVA = Path(r"<HOME>\.kicad-mcp\jdk-25.0.4+7-jre\bin\java.exe")
JAR = Path(r"<HOME>\.kicad-mcp\freerouting.jar")
KICAD_CLI = Path(r"F:\kicad\bin\kicad-cli.exe")
KICAD_PY = Path(r"F:\kicad\bin\python.exe")
STAGING_ROOT = Path(os.environ.get("TEMP", r"C:\Windows\Temp")) / \
    "pcbflow-td7-qual"
TOOLCHAIN_LOCK = REPO / "toolchain_lock.json"

EXECUTION_PREFIX = "TD7-S11"


def rel(p: Path) -> str:
    return p.relative_to(REPO).as_posix()


def sha_file(p) -> str:
    return hashing.sha256_file(str(p))


def write_json(path: Path, obj) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = hashing.json_dumps(obj)
    path.write_text(text, encoding="utf-8", newline="")
    return hashing.sha256_text(text)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def tool_rel(abs_path: Path) -> str:
    """仓库相对 POSIX（向上穿越以 ../ 表达，与 ASM-8 precheck 同形）；
    跨盘（如 F:\\kicad）无相对路径可表——原样绝对 POSIX+显式标记。"""
    parts = abs_path.resolve().parts
    drive = parts[0]
    repo_parts = REPO.resolve().parts
    if drive != repo_parts[0]:
        return "cross_drive:" + abs_path.resolve().as_posix()
    common = 0
    for a, b in zip(parts, repo_parts):
        if a != b:
            break
        common += 1
    ups = [".."] * (len(repo_parts) - common)
    return "/".join(ups + list(parts[common:]))


# ---------------------------------------------------------------------------
# plan：度量 → 选板 → staging 布局 + 步骤清单
# ---------------------------------------------------------------------------

def board_role(board_id: str, splits: dict) -> str | None:
    for role in ("train", "validation", "holdout"):
        if board_id in splits.get(role, []):
            return role
    return None


def profile_board_id(pid: str, manifest: dict) -> str | None:
    """profile_id → dataset board_id（manifest backtest.reference_route
    的 raw 目录名即 board_id；兜底=slug 去前缀）。"""
    ref = ((manifest.get("backtest") or {}).get("reference_route") or "")
    parts = [p for p in ref.split("/") if p]
    if len(parts) >= 2:
        return parts[-2]
    return pid.split("-", 1)[1] if "-" in pid else pid


def cmd_plan(args) -> int:
    entries = []
    for d in sorted((REPO / "profiles").iterdir()):
        if not (d / "inputs" / "board.kicad_pcb").exists():
            continue
        board = d / "inputs" / "board.kicad_pcb"
        text = board.read_text(encoding="utf-8")
        geom = check_stage.parse_routed_geometry(text)
        manifest = load_json(d / "manifest.json")
        ref = (manifest.get("backtest") or {}).get("reference_route")
        ref_ok = bool(ref) and (REPO / "profiles" / d.name / ref).exists()
        entries.append({
            "profile_id": d.name,
            "named_net_count": geom["named_net_count"],
            "unrouted": (geom["geometry_counts"]["segments"] == 0
                         and geom["geometry_counts"]["vias"] == 0
                         and geom["geometry_counts"]["zones"] == 0),
            "reference_available": ref_ok,
            "dataset_role": board_role(
                profile_board_id(d.name, manifest),
                manifest.get("dataset_splits") or {}),
            "reference_route_repo_rel": (
                (d / ref).resolve().relative_to(REPO).as_posix()
                if ref_ok else None),
        })
    selection = bq.select_qualification_boards(entries)
    write_json(TD7 / "board-selection.json", {
        "artifact_kind": "td7_board_selection",
        "track": bq.TRACK,
        "selection": selection,
        "entries": entries,
    })

    lock_sha = sha_file(TOOLCHAIN_LOCK)
    for slot in ("small", "mid", "large"):
        slot_info = selection["slots"][slot]
        if slot_info.get("status") != "selected":
            continue
        pid = slot_info["profile_id"]
        entry = next(e for e in entries if e["profile_id"] == pid)
        staging = STAGING_ROOT / slot
        if staging.exists():
            shutil.rmtree(staging)
        staging.mkdir(parents=True)
        raw = REPO / entry["reference_route_repo_rel"]
        raw_copy = staging / "reference.kicad_pcb"
        shutil.copyfile(raw, raw_copy)
        assert sha_file(raw_copy) == sha_file(raw)

        plan = {
            "artifact_kind": "td7_qualification_plan",
            "track": bq.TRACK,
            "slot": slot,
            "profile_id": pid,
            "named_net_count": entry["named_net_count"],
            "dataset_role": entry.get("dataset_role"),
            "source_reference_repo_rel": entry["reference_route_repo_rel"],
            "source_reference_sha256": sha_file(raw_copy),
            "input_note": "v3 profile inputs/board.kicad_pcb=corpus 归一化"
                          "文本形态，pcbnew 不可加载（S11 实测，偏差 D20）；"
                          "KiCad-loadable 输入=datasets raw 参考 routed 态"
                          "（只读源，staging 逐字节副本）→ staging 未布线"
                          "推导（删 track/via/arc，保留 zone/footprint）",
            "staging_layout": {
                "reference.kicad_pcb": "datasets raw 逐字节副本（只读源）",
                "board-unrouted.kicad_pcb": "未布线推导（KiCad 10 格式）",
                "board.dsn": "pcbnew ExportSpecctraDSN 产物",
                "run1.ses/run2.ses": "freerouting 同参双跑产物（确定性）",
                "run1.log/run2.log": "引擎日志（stdout 原样留存）",
                "drc-baseline-*.json": "未布线 staging 板 DRC 基线",
                "drc-routed-*.json": "SES 应用板 DRC（对 freerouting 自身"
                                     "产物）",
                "board-freerouting.kicad_pcb": "SES 应用后 staging 板",
            },
            "freerouting_params": {
                "fixed_tail": list(bq.FREEROUTING_FIXED_TAIL),
                "max_passes": bq.FREEROUTING_MAX_PASSES,
                "timeout_s": bq.DEFAULT_FREEROUTING_TIMEOUT_S,
            },
            "step_order": ["unrouted-derive", "pcbnew-dsn-export",
                           "freerouting-run1", "freerouting-run2",
                           "pcbnew-ses-apply", "drc-baseline-error",
                           "drc-baseline-all", "drc-routed-error",
                           "drc-routed-all"],
        }
        write_json(TD7 / "boards" / pid / "plan.json", plan)
        print(f"planned {slot}: {pid} staging={staging}")
    print("selection:", selection["selected_profile_ids"])
    return 0


def next_step_spec(slot: str, pid: str) -> dict | None:
    """按 staging 现场推导下一个待执行步骤（hash 恒取盘上实测）。"""
    staging = STAGING_ROOT / slot
    results = {r["step"] for r in _read_results(staging)}
    repo = str(REPO)
    env = dict(os.environ)
    sel = load_json(TD7 / "board-selection.json")
    entry = next(e for e in sel["entries"] if e["profile_id"] == pid)
    raw_sha = sha_file(staging / "reference.kicad_pcb")
    unrouted = staging / "board-unrouted.kicad_pcb"

    def step(step_id, argv, cwd, timeout_s):
        return {
            "step": step_id, "argv": argv, "cwd": cwd,
            "timeout_s": timeout_s,
            "env": {"PATH": env["PATH"], "SYSTEMROOT":
                    env.get("SYSTEMROOT", "C:\\Windows"),
                    "TEMP": str(staging), "TMP": str(staging)},
            "stdout_file": str(staging / f"{step_id}.stdout"),
            "stderr_file": str(staging / f"{step_id}.stderr"),
        }

    if "unrouted-derive" not in results:
        return step(
            "unrouted-derive",
            [str(KICAD_PY), str(REPO / "scripts" / "s11_pcbnew_step.py"),
             "unrouted_derive", str(staging / "reference.kicad_pcb"),
             str(unrouted), raw_sha],
            repo, bq.DEFAULT_PCBNEW_TIMEOUT_S)
    if "pcbnew-dsn-export" not in results:
        return step(
            "pcbnew-dsn-export",
            [str(KICAD_PY), str(REPO / "scripts" / "s11_pcbnew_step.py"),
             "dsn_export", str(unrouted), str(staging / "board.dsn"),
             sha_file(unrouted)],
            repo, bq.DEFAULT_PCBNEW_TIMEOUT_S)
    for run in (1, 2):
        if f"freerouting-run{run}" not in results:
            return step(
                f"freerouting-run{run}",
                bq.build_freerouting_argv(
                    java_abs=str(JAVA), jar_abs=str(JAR),
                    dsn_abs=str(staging / "board.dsn"),
                    ses_abs=str(staging / f"run{run}.ses")),
                str(staging), bq.DEFAULT_FREEROUTING_TIMEOUT_S)
    if "pcbnew-ses-apply" not in results:
        return step(
            "pcbnew-ses-apply",
            [str(KICAD_PY), str(REPO / "scripts" / "s11_pcbnew_step.py"),
             "ses_apply", str(unrouted), str(staging / "run1.ses"),
             str(staging / "board-freerouting.kicad_pcb"),
             sha_file(unrouted)],
            repo, bq.DEFAULT_PCBNEW_TIMEOUT_S)
    for name, target, sev in (
            ("drc-baseline-error", "board-unrouted.kicad_pcb",
             "--severity-error"),
            ("drc-baseline-all", "board-unrouted.kicad_pcb",
             "--severity-all"),
            ("drc-routed-error", "board-freerouting.kicad_pcb",
             "--severity-error"),
            ("drc-routed-all", "board-freerouting.kicad_pcb",
             "--severity-all")):
        if name not in results:
            return step(
                name,
                [str(KICAD_CLI), "pcb", "drc", "--format", "json", sev,
                 "--output", str(staging / f"{name}.json"),
                 str(staging / target)],
                repo, bq.DEFAULT_KICAD_TIMEOUT_S)
    return None


def cmd_nextstep(args) -> int:
    pid = args.profile_id
    plan = load_json(TD7 / "boards" / pid / "plan.json")
    spec = next_step_spec(plan["slot"], pid)
    if spec is None:
        print(json.dumps({"done": True}))
        return 0
    (STAGING_ROOT / plan["slot"] / "next-step.json").write_text(
        json.dumps(spec), encoding="utf-8")
    print(json.dumps(spec["argv"]))
    return 0


# ---------------------------------------------------------------------------
# sesanalyze：读实跑产物 → 纯函数装配 run record
# ---------------------------------------------------------------------------

def _read_results(staging: Path) -> list:
    results = staging / "steps-results.jsonl"
    if not results.exists():
        return []
    return [json.loads(line) for line in
            results.read_text(encoding="utf-8").splitlines() if line.strip()]


def cmd_sesanalyze(args) -> int:
    pid = args.profile_id
    plan = load_json(TD7 / "boards" / pid / "plan.json")
    slot = plan["slot"]
    staging = STAGING_ROOT / slot
    results = {r["step"]: r for r in _read_results(staging)}
    unrouted = staging / "board-unrouted.kicad_pcb"
    unrouted_sha = (sha_file(unrouted) if unrouted.exists() else None)
    lock_sha = sha_file(TOOLCHAIN_LOCK)
    profile = load_json(REPO / "profiles" / pid / "profile.json")

    fr = results.get("freerouting-run1") or {}
    exit_status = fr.get("exit_status")
    ses_path = staging / "run1.ses"
    ses_text = (open(ses_path, encoding="utf-8", newline="").read()
                if ses_path.exists() else "")
    ses_observed = {
        "present": ses_path.exists() and bool(ses_text),
        "size_bytes": ses_path.stat().st_size if ses_path.exists() else 0,
        "size_bound": bq.MAX_SES_BYTES,
        "truncated": bool(fr.get("truncated")),
        "parsed": False,
        "hash_matches": (hashing.sha256_text(ses_text) if ses_text
                         else None),
    }
    ses_observed["hash_matches"] = (
        ses_observed["hash_matches"]
        == (sha_file(ses_path) if ses_path.exists() else None))
    ses_geom = None
    l1 = {"checks": [], "all_pass": False, "layer_purity_pass": False}
    if ses_observed["present"]:
        try:
            ses_geom = bq.parse_ses_network_out(ses_text)
            ses_observed["parsed"] = True
            l1 = bq.ses_l1_geometry_check(ses_geom, profile)
        except Exception as exc:  # fail-closed
            ses_observed["parse_error"] = str(exc)[:200]

    drc_result = None
    if all((staging / f"drc-{n}.json").exists() for n in
           ("baseline-error", "baseline-all", "routed-error",
            "routed-all")):
        drc_result = bq.drc_dual_severity_delta(
            baseline_error=load_json(staging / "drc-baseline-error.json"),
            actual_error=load_json(staging / "drc-routed-error.json"),
            baseline_all=load_json(staging / "drc-baseline-all.json"),
            actual_all=load_json(staging / "drc-routed-all.json"))
        drc_result["executed"] = True

    # 质量实况（不进资格谓词）
    quality = {}
    if ses_geom is not None:
        quality["ses_geometry"] = {
            "net_count_in_network_out":
                ses_geom["net_count_in_network_out"],
            "totals": ses_geom["totals"],
            "layer_histogram": ses_geom["layer_histogram"],
            "width_min_units": ses_geom["width_min_units"],
        }
    routed_board = staging / "board-freerouting.kicad_pcb"
    reference = staging / "reference.kicad_pcb"
    if routed_board.exists():
        quality["applied_board_metrics"] = bq.board_route_metrics(
            routed_board.read_text(encoding="utf-8"))
        if reference.exists():
            quality["vs_reference"] = bq.compare_to_reference(
                quality["applied_board_metrics"],
                bq.board_route_metrics(
                    reference.read_text(encoding="utf-8")))
    if drc_result is not None:
        quality["drc_dual_severity"] = drc_result
        quality["connectivity"] = drc_result["unconnected_items"]

    argv = bq.build_freerouting_argv(
        java_abs=str(JAVA), jar_abs=str(JAR),
        dsn_abs=str(staging / "board.dsn"),
        ses_abs=str(staging / "run1.ses"))
    run_record = bq.build_run_record(
        execution_id=f"{EXECUTION_PREFIX}-{slot.upper()}",
        project_id=pid, profile_id=pid,
        source_snapshot_sha256=plan["source_reference_sha256"],
        staging_path_sha256=unrouted_sha or plan["source_reference_sha256"],
        tool_version="freerouting-2.3.0_2026-08-07",
        toolchain_lock_sha256=lock_sha,
        request_sha256=(sha_file(staging / "board.dsn")
                        if (staging / "board.dsn").exists() else None),
        response_sha256=(sha_file(ses_path) if ses_path.exists() else None),
        argv=argv, timeout_s=bq.DEFAULT_FREEROUTING_TIMEOUT_S,
        exit_status=exit_status,
        ses_observed=ses_observed, l1_result=l1,
        drc_result=drc_result,
        finalization={"evidence_complete": True,
                      "detail": "staging 板回滚=staging 临时目录收尾清理"
                                "（live 零写由 staging-only 构造保证）；"
                                "产物 hash 入 artifact 登记与 ledger"
                                "（aggregate）"},
        quality=quality)
    write_json(TD7 / "boards" / pid / "run-record.json", run_record)

    # 确定性（run2；launchxl 附第 3 跑强化证据——归档件含 run3.ses）
    det_runs = []
    for run in (1, 2, 3):
        p = staging / f"run{run}.ses"
        if p.exists():
            text = open(p, encoding="utf-8", newline="").read()
            det_runs.append({
                "run_id": f"run{run}",
                "ses_sha256": hashing.sha256_text(text),
                "normalized_sha256":
                    bq.normalize_ses_for_determinism(text)
                    ["normalized_sha256"]})
    write_json(TD7 / "boards" / pid / "determinism.json", {
        "artifact_kind": "td7_determinism",
        "track": bq.TRACK,
        "runs": det_runs,
        "assessment": bq.assess_determinism(det_runs),
    })
    print(f"run record written: boards/{pid}/run-record.json "
          f"(pipeline={(run_record['pipeline'] or {}).get('pipeline_status')})")
    return 0


# ---------------------------------------------------------------------------
# aggregate：registry + 资格报告 + judge/ledger/gate + 锁提案
# ---------------------------------------------------------------------------

def observed_freerouting_version() -> str | None:
    """从归档的引擎日志提取版本串（引擎 banner 自报；仅作版本证据，
    不作布线 authority）。"""
    for d in sorted((TD7 / "boards").iterdir()):
        log = d / "artifacts" / "freerouting-run1.stdout"
        if not log.exists():
            continue
        m = re.search(r"Freerouting (v[\d.]+) \(build-date: ([\d-]+)\)",
                      log.read_text(encoding="utf-8", errors="replace"))
        if m:
            return f"{m.group(1)} (build {m.group(2)})"
    return None


def cmd_aggregate(args) -> int:
    lock_sha = sha_file(TOOLCHAIN_LOCK)
    fr_version = observed_freerouting_version()
    registry = bq.build_toolchain_registry(
        jar={"rel_path": tool_rel(JAR),
             "abs_path_exists": JAR.exists(),
             "sha256": sha_file(JAR) if JAR.exists() else None,
             "version": fr_version},
        java={"rel_path": tool_rel(JAVA.parent.parent),
              "abs_path_exists": JAVA.exists(),
              "sha256": sha_file(JAVA) if JAVA.exists() else None,
              "version": "25.0.4+7"},
        kicad_cli={"rel_path": tool_rel(KICAD_CLI),
                   "abs_path_exists": KICAD_CLI.exists(),
                   "sha256": sha_file(KICAD_CLI) if KICAD_CLI.exists()
                   else None,
                   "version": "10.0.5"})
    write_json(TD7 / "toolchain-registry.json", registry)

    run_records, det_all = [], []
    for d in sorted((TD7 / "boards").iterdir()):
        rr = d / "run-record.json"
        det = d / "determinism.json"
        if rr.exists():
            run_records.append(load_json(rr))
        if det.exists():
            det_all.extend(load_json(det)["runs"])
    selection = load_json(TD7 / "board-selection.json")["selection"]
    report = bq.build_qualification_report(
        toolchain_registry=registry, selection=selection,
        run_records=run_records, determinism_runs=det_all)
    report_sha = write_json(TD7 / "qualification-report.json", report)
    write_json(TD7 / "toolchain-lock-proposal.json",
               bq.build_toolchain_lock_proposal(registry))

    # judge_pre / judge_post / ledger / gate（TL-1 链同构）
    pid = "multi:" + "+".join(selection.get("selected_profile_ids") or [])
    execution_id = f"{EXECUTION_PREFIX}-QUAL"
    run_ref = hashing.sha256_bytes(hashing.canonical_json_bytes(
        run_records))
    pre = judge.build_pre(
        execution_id=execution_id, project_id=pid, profile_id=pid,
        candidate_id="TD7-QUAL-freerouting-cli",
        source_snapshot_sha256=hashing.sha256_text(
            json.dumps([r["execution_record"]["source_snapshot_sha256"]
                        for r in run_records])),
        toolchain_lock_sha256=lock_sha,
        executor={"backend": bq.BACKEND, "protocol": bq.PROTOCOL,
                  "version": bq.ASM8_EXPECTED_JAR_VERSION,
                  "capability": "external_router_qualification"},
        write_scope="staging_only",
        allowlist=["freerouting-cli-jar"],
        required_checks=["schema_size_validation", "l1_layer_purity",
                         "drc_batch_severity_error",
                         "drc_final_severity_all"],
        upstream_hashes={})
    pre_eval = judge.evaluate_pre(pre, {
        "toolchain_lock_sha256": lock_sha,
        "source_snapshot_sha256": pre["source_snapshot_sha256"]})
    all_pipeline_ok = all(
        (r.get("pipeline") or {}).get("pipeline_status")
        == external_backend.PIPELINE_VERIFIED_CANDIDATE
        for r in run_records) if run_records else False
    l1_ok = all(
        next((s for s in r.get("stages", [])
              if s.get("stage") == "l1_layer_purity"), {})
        .get("status") == "pass"
        for r in run_records) if run_records else False
    post = judge.build_post(
        execution_id=execution_id, pre_record=pre, output_hash=report_sha,
        l1_legal=l1_ok,
        layer_pure=l1_ok,
        drc_batch_ref=run_ref, drc_final_ref=run_ref,
        solver=None, external_status="ok" if all_pipeline_ok else "fail",
        physics_status="not_required", bring_up_status="not_required",
        rollback_status="executed",
        facts=judge.build_facts([
            {"fact_id": "FACT-TD7-QUALIFICATION-VERDICT",
             "observer": "external_backend",
             "observation": {"kind": "text_ref",
                             "value": f"verdict={report['verdict']}; "
                                      f"reason={report['verdict_reason']}",
                             "ref_sha256": report_sha}}]))
    post_eval = judge.evaluate_post(post)

    base = {"authority": "deterministic_evaluator",
            "trust_level": "observed",
            "project_id": pid, "profile_id": pid,
            "snapshot_revision": "td7-qual-r1",
            "actor": "pcbflow-v3-s11-orchestrate", "actor_role":
            "orchestrator"}
    entry_schema = ledger.make_schema_validation("decision_ledger_entry")
    entries: list = []
    entries, _ = ledger.append(entries, {
        "entry_id": "TD7-E-0001", "entry_kind": "proposal",
        "schema_validation": entry_schema,
        "proposal_id": "TD7-QUAL-freerouting-cli",
        "proposal_sha256": report_sha,
        "artifact_hashes": {"toolchain_registry": sha_file(
            TD7 / "toolchain-registry.json")}, **base})
    entries, _ = ledger.append(entries, {
        "entry_id": "TD7-E-0002", "entry_kind": "judge_pre",
        "schema_validation": ledger.make_schema_validation(
            "judge_pre_record"),
        "judge_pre_hash": judge.pre_record_sha256(pre),
        "artifact_hashes": {"toolchain_lock": lock_sha}, **base})
    entries, _ = ledger.append(entries, {
        "entry_id": "TD7-E-0003", "entry_kind": "execution",
        "schema_validation": entry_schema,
        "execution_ref": run_ref,
        "artifact_hashes": {"run_records": run_ref}, **base})
    entries, _ = ledger.append(entries, {
        "entry_id": "TD7-E-0004", "entry_kind": "judge_post",
        "schema_validation": ledger.make_schema_validation(
            "judge_post_record"),
        "judge_pre_hash": judge.pre_record_sha256(pre),
        "judge_post_hash": hashing.sha256_bytes(
            hashing.canonical_json_bytes(post)),
        "artifact_hashes": {"qualification_report": report_sha}, **base})
    ledger_prefix_sha = _ledger_sha(entries)

    record = gate_mod.evaluate_gate(
        gate_id="TD7-QUAL-G", gate_kind="training_loop", project_id=pid,
        profile_id=pid, snapshot_revision="td7-qual-r1",
        predicate_version="pv1",
        inputs=[
            {"artifact_id": "toolchain_registry", "sha256": sha_file(
                TD7 / "toolchain-registry.json"), "status": "present"},
            {"artifact_id": "toolchain_lock", "sha256": lock_sha,
             "status": "present"},
            {"artifact_id": "qualification_report", "sha256": report_sha,
             "status": "present"},
            {"artifact_id": "decision_ledger_prefix",
             "sha256": ledger_prefix_sha, "status": "present"},
            {"artifact_id": f"run_records", "sha256": run_ref,
             "status": "present" if run_records else "missing"},
        ],
        required_predicates=bq.qualification_gate_predicates(report),
        evaluator={"name": "pcbflow-v3-gate", "version": "1.0",
                   "code_sha256": sha_file(REPO / "pcbflow" / "gate.py")})
    verify_errors = gate_mod.verify_gate_record(record)
    entries, _ = ledger.append(entries, {
        "entry_id": "TD7-E-0005", "entry_kind": "gate",
        "schema_validation": ledger.make_schema_validation("gate_record"),
        "gate_record_hash": gate_mod.gate_core_hash(record),
        "artifact_hashes": {"qualification_report": report_sha,
                            "decision_ledger_prefix": ledger_prefix_sha},
        **base})
    write_json(TD7 / "decision-ledger.json", {"entries": entries})
    bundle = {
        "command": "s11-td7-aggregate",
        "status": "ok",
        "gate_record": record,
        "gate_verify_errors": verify_errors,
        "gate_core_hash": gate_mod.gate_core_hash(record),
        "judge_pre_ok": pre_eval["pre_ok"],
        "judge_post_ok": post_eval["post_ok"],
        "qualification_verdict": report["verdict"],
    }
    write_json(TD7 / "gate-record-td7.json", bundle)
    checkpoint = ledger.make_checkpoint(entries, "CKPT-TD7-QUAL-R1")
    write_json(TD7 / "ledger-checkpoint.json", checkpoint)
    print(json.dumps({k: bundle[k] for k in
                      ("gate_core_hash", "judge_pre_ok", "judge_post_ok",
                       "qualification_verdict")}))
    print("gate result:", record.get("result"),
          "verify_errors:", verify_errors)
    return 0


def _ledger_sha(entries) -> str:
    text = "".join(hashing.json_dumps(e) + "\n" for e in entries)
    return hashing.sha256_text(text)


def cmd_archive(args) -> int:
    """staging 证据归档到 out/v3-td7/boards/<pid>/artifacts/（含台账）。"""
    pid = args.profile_id
    plan = load_json(TD7 / "boards" / pid / "plan.json")
    staging = STAGING_ROOT / plan["slot"]
    dst = TD7 / "boards" / pid / "artifacts"
    manifest = []
    keep = ["board.dsn", "run1.ses", "run2.ses", "run3.ses",
            "board-unrouted.kicad_pcb", "board-freerouting.kicad_pcb",
            "drc-baseline-error.json", "drc-baseline-all.json",
            "drc-routed-error.json", "drc-routed-all.json",
            "steps-results.jsonl"]
    keep += [f"{s}.stdout" for s in (
        "unrouted-derive", "pcbnew-dsn-export", "freerouting-run1",
        "freerouting-run2", "freerouting-run3", "pcbnew-ses-apply",
        "drc-baseline-error", "drc-baseline-all", "drc-routed-error",
        "drc-routed-all")]
    for name in keep:
        src = staging / name
        if not src.exists():
            continue
        target = dst / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, target)
        manifest.append({"file": name, "sha256": sha_file(target),
                         "size_bytes": target.stat().st_size})
    record = {
        "artifact_kind": "td7_staging_archive",
        "track": bq.TRACK,
        "profile_id": pid,
        "note": "staging 证据归档（外部工具输出原样留存——含其自身"
                "wall-clock/路径字段，按 S6 先例声明；核产物不嵌这些"
                "字段）",
        "files": manifest,
    }
    write_json(TD7 / "boards" / pid / "staging-archive.json", record)
    print(f"archived {len(manifest)} files for {pid}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("plan")
    p2 = sub.add_parser("sesanalyze")
    p2.add_argument("--profile-id", required=True)
    p3 = sub.add_parser("nextstep")
    p3.add_argument("--profile-id", required=True)
    p4 = sub.add_parser("archive")
    p4.add_argument("--profile-id", required=True)
    sub.add_parser("aggregate")
    args = parser.parse_args()
    return {"plan": cmd_plan, "sesanalyze": cmd_sesanalyze,
            "nextstep": cmd_nextstep, "archive": cmd_archive,
            "aggregate": cmd_aggregate}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
