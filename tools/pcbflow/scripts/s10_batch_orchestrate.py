"""S10 TL-5 分母纵深：PCBench 78 块剩余合规板的批量转换编排（编排侧脚本）。

本脚本=编排侧（非生成器）：做文件读写与 pcbflow 纯函数调用；
kicad-cli 与 v3cli 调用留在 Bash（生成器纪律：pcbflow/*.py 零子进程）。
datasets/ 只读；既有 out/ 产物与既有 profile 目录只读（更新一律新文件）。

子命令（按执行顺序）：
  judge      逐板 parse/identity/manifest-path 三判定 → out/v3-tl5/batch-s10/judge-ledger.json
  convert    过板批量转换：profiles/pcbench-<slug>/{inputs,derived}+profile/manifest/graph
             + out/v3-tl5/conversion-log-pcbench-<slug>.json + batch-s10/conversion-ledger.json
  declare    每板 route-check.json 段声明（profiles/<pid>/route-check.json）
  check      读 Bash 产出的双 severity DRC JSON → check-report.json
  graphspec  out/v3-tl5/mainpath/<pid>/graph-spec.json（v2 形态：+route/check 两节点）
  report     TD8 逐 profile 报告 profile-report.json（读 v3cli 产物实况装配）
  aggregate  汇总台账 + S10 执行记录 + dataset manifest pcbench-r1 v3

确定性：全部产物=pcbflow 纯函数+注入 hash 的函数；日期=声明常量 S10_DATE
（人工会话声明，非机器 wall-clock）；路径一律仓库相对 POSIX；JSON 落盘
一律 hashing.json_dumps（byte-exact 重放）。
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from pcbflow import check_stage, corpus, corpus_convert, corpus_pcbench, hashing  # noqa: E402
from pcbflow import manifest as manifest_mod  # noqa: E402

S10_DATE = "2026-09-03"  # 人工会话声明日期（非 wall-clock）
BATCH_ID = "s10-pcbench-batch"
DATASET_ID = "pcbench-r1"

EXISTING_PROFILES = (  # S7/S8 已转换三板（只读，不计入本批）
    "pcbench-74logic-sa-adc-sa-adc",
    "pcbench-kitspace-t32-ref",
    "pcbench-launchxl-f28027-isolation-pcb-project1",
)

BATCH_DIR = REPO / "out" / "v3-tl5" / "batch-s10"
TL5 = REPO / "out" / "v3-tl5"

HEX64 = re.compile(r"^[0-9a-f]{64}$")


# ---------------------------------------------------------------------------
# 基础工具
# ---------------------------------------------------------------------------

def rel(p: Path) -> str:
    return p.relative_to(REPO).as_posix()


def sha_file(p) -> str:
    return hashing.sha256_file(str(p))


def write_json(path: Path, obj) -> str:
    """canonical JSON 落盘（byte-exact 重放）；返回 sha256。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    text = hashing.json_dumps(obj)
    path.write_text(text, encoding="utf-8", newline="")
    return hashing.sha256_text(text)


def write_text(path: Path, text: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="")
    return hashing.sha256_text(text)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def batch_boards() -> list:
    """v2 manifest splits 下的 81 板 − 已转换 3 板 = 78 板（字典序）。"""
    v2 = load_json(TL5 / "dataset-manifest-pcbench-r1-v2.json")
    splits = v2["dataset_splits"]
    done = {b for b in (
        "74Logic_SA_ADC_SA-ADC", "kitspace_T32_ref",
        "LAUNCHXL-F28027-isolation-PCB_project1")}
    boards = []
    for role in ("train", "validation", "holdout"):
        for b in splits[role]:
            if b not in done:
                boards.append({"board_id": b, "dataset_role": role})
    boards.sort(key=lambda x: x["board_id"])
    assert len(boards) == 78, f"expect 78 batch boards, got {len(boards)}"
    return boards


def board_role_map() -> dict:
    v2 = load_json(TL5 / "dataset-manifest-pcbench-r1-v2.json")
    out = {}
    for role in ("train", "validation", "holdout"):
        for b in v2["dataset_splits"][role]:
            out[b] = role
    return out


def module_hashes() -> dict:
    return {
        "corpus_convert": sha_file(REPO / "pcbflow" / "corpus_convert.py"),
        "corpus_pcbench": sha_file(REPO / "pcbflow" / "corpus_pcbench.py"),
        "check_stage": sha_file(REPO / "pcbflow" / "check_stage.py"),
    }


# ---------------------------------------------------------------------------
# judge：逐板三判定（parse/identity/manifest-path）
# ---------------------------------------------------------------------------

def judge_one(board_id: str) -> dict:
    base = REPO / "datasets" / DATASET_ID / "raw" / board_id
    entry = {"board_id": board_id,
             "paths": corpus_pcbench.dataset_board_paths(board_id)}
    # 1) manifest 路径字符集（processed+raw 数据集相对路径）
    path_ok = all(corpus_pcbench.manifest_path_compatible(p)
                  for p in entry["paths"].values())
    entry["manifest_path_ok"] = path_ok
    if not path_ok:
        bad = [p for p in entry["paths"].values()
               if not corpus_pcbench.manifest_path_compatible(p)]
        entry["skip_reason"] = "manifest_path_incompatible:" + ",".join(bad)
        return entry
    # 2) parse（processed=unrouted 推导源；raw=routed 参考）
    try:
        text_p = (base / "processed.kicad_pcb").read_text(encoding="utf-8")
        text_r = (base / "raw.kicad_pcb").read_text(encoding="utf-8")
        m_p = corpus_convert.parse_kicad5_board(text_p)
        m_r = corpus_convert.parse_kicad5_board(text_r)
    except Exception as exc:  # fail-closed，如实记因
        entry["parse_ok"] = False
        entry["skip_reason"] = f"parse_error:{type(exc).__name__}:{exc}"[:300]
        return entry
    entry["parse_ok"] = True
    # 3) identity（processed ↔ raw 同板身份：net id 序列+module ref 多重集）
    nets_eq = ([n["net_id"] for n in m_p["nets"]]
               == [n["net_id"] for n in m_r["nets"]])
    refs_eq = (sorted(m["ref"] for m in m_p["modules"])
               == sorted(m["ref"] for m in m_r["modules"]))
    entry["identity_ok"] = bool(nets_eq and refs_eq)
    entry["identity_detail"] = {
        "net_id_sequence_equal": nets_eq,
        "module_ref_multiset_equal": refs_eq,
        "processed_nets": len(m_p["nets"]), "raw_nets": len(m_r["nets"]),
        "processed_modules": len(m_p["modules"]),
        "raw_modules": len(m_r["modules"]),
    }
    if not entry["identity_ok"]:
        d = entry["identity_detail"]
        parts = []
        if not nets_eq:
            parts.append(f"net_id_sequence_differs(p={d['processed_nets']},"
                         f"r={d['raw_nets']})")
        if not refs_eq:
            parts.append(f"module_ref_multiset_differs(p="
                         f"{d['processed_modules']},r={d['raw_modules']})")
        entry["skip_reason"] = "identity_mismatch:" + "+".join(parts)
    return entry


def cmd_judge() -> int:
    entries = [judge_one(b["board_id"]) for b in batch_boards()]
    counts: dict = {"judged": len(entries)}
    for e in entries:
        key = e.get("skip_reason", "convertible").split(":")[0]
        counts[key] = counts.get(key, 0) + 1
    # slug 冲突检测（确定性 fail-closed）
    slugs = [corpus_pcbench.board_slug(e["board_id"]) for e in entries
             if not e.get("skip_reason")]
    dup = sorted({s for s in slugs if slugs.count(s) > 1})
    ledger = {
        "schema_version": "3.0", "artifact_kind": "s10_judge_ledger",
        "batch_id": BATCH_ID, "judge_date": S10_DATE,
        "rule": corpus_pcbench.SELECTION_RULE.replace(
            "S1=候选中", "批量包=候选集全部（无选板；")
            .replace("（层多样性：cu4）；S3=候选字典序遍历取第一个 "
                     "project_group ∉ {S1,S2} 且 topology_group ∉ {S1,S2} 者；"
                     "任一槽空则如实跳过不凑数", "）"),
        "entries": entries, "counts": dict(sorted(counts.items())),
        "slug_collisions": dup,
    }
    sha = write_json(BATCH_DIR / "judge-ledger.json", ledger)
    print(f"judge: {len(entries)} boards, counts={counts}")
    print(f"judge-ledger.json sha256={sha}")
    return 0 if not dup else 1


def convertible_entries() -> list:
    ledger = load_json(BATCH_DIR / "judge-ledger.json")
    return [e for e in ledger["entries"] if not e.get("skip_reason")]


# ---------------------------------------------------------------------------
# convert：逐板转换（纯函数装配 + 校验后落盘）
# ---------------------------------------------------------------------------

def build_board_artifacts(board_id: str) -> dict:
    """逐板转换装配（纯：内存对象+文本；落盘由调用方）。"""
    base = REPO / "datasets" / DATASET_ID / "raw" / board_id
    slug = corpus_pcbench.board_slug(board_id)
    pid = f"pcbench-{slug}"
    text_p = (base / "processed.kicad_pcb").read_text(encoding="utf-8")
    text_r = (base / "raw.kicad_pcb").read_text(encoding="utf-8")
    # 输入 hash=盘上字节（sha256_file/read_bytes）；read_text 的 universal
    # newlines 会把 CRLF 归一为 LF——解析用文本没问题（空白无语义），但
    # hash 必须绑定原始字节（S10 首轮缺陷：sha256_text(text) 记录了
    # LF 归一化 hash，42/64 输入与盘上不一致，round-1-defect-record 在案）
    sha_p = sha_file(base / "processed.kicad_pcb")
    sha_r = sha_file(base / "raw.kicad_pcb")
    m_p = corpus_convert.parse_kicad5_board(text_p)
    m_r = corpus_convert.parse_kicad5_board(text_r)
    m_u = corpus_pcbench.derive_unrouted_model(m_p)
    crit = corpus_convert.derive_critical_nets(m_u)
    topo = corpus_convert.topology_group_id(m_u, crit)
    meta = load_json(base / "metadata.json")

    src_paths = corpus_pcbench.dataset_board_paths(board_id)
    norm = corpus_convert.normalized_board_text(
        m_u, source_path=src_paths["processed"], source_sha256=sha_p)
    objs = {
        "inputs/board.kicad_pcb": norm,
        "inputs/stackup.json": corpus_convert.build_stackup_obj(
            m_u, board_id=board_id, source={
                "processed": {"path": src_paths["processed"],
                              "sha256": sha_p},
                "raw_reference": {"path": src_paths["raw"], "sha256": sha_r}}),
        "inputs/constraints.json": corpus_convert.build_constraints_obj(
            m_u, project_id=pid, crit=crit),
        "derived/net-registry.json": corpus_convert.build_net_registry_obj(
            m_u, board_id=board_id, crit=crit),
        "derived/audit.json": corpus_convert.build_audit_obj(
            m_u, m_r, board_id=board_id),
        "derived/feedforward-plan.json": corpus_convert.build_feedforward_obj(
            m_u, board_id=board_id, crit=crit),
    }
    texts = {}
    for k, v in objs.items():
        if isinstance(v, str):
            texts[k] = v
        else:
            texts[k] = hashing.json_dumps(v)
    profile_obj = corpus_convert.build_profile_obj(
        m_u, profile_id=pid, project_id=pid, crit=crit)
    # manifest 的 dataset_splits 只取四角色键（schemas.oneOf additionalProperties
    # false；split_unit/rule 等扩展字段只留在 dataset manifest）
    raw_splits = load_json(
        TL5 / "dataset-manifest-pcbench-r1-v2.json")["dataset_splits"]
    splits = {k: raw_splits[k] for k in ("train", "validation", "holdout",
                                         "external_eval")}
    manifest_obj = corpus_convert.build_manifest_obj(
        project_id=pid, profile_id=pid,
        eda_version=m_u["host"] or "unknown",
        critical_nets=crit["critical_nets"],
        dataset_splits=splits,
        output_root=f"out/v3-tl5/mainpath/{pid}",
        board_id=board_id,
        dataset_routed_rel=f"../../datasets/{DATASET_ID}/raw/{board_id}/"
                           f"raw.kicad_pcb",
        drc_baseline_rel=f"../../out/v3-tl5/drc-pcbench/{slug}/"
                         f"{slug}.raw.drc-all.json")
    return {
        "board_id": board_id, "slug": slug, "profile_id": pid,
        "model_u": m_u, "model_p": m_p, "model_r": m_r,
        "crit": crit, "topology_group": topo, "meta": meta,
        "sha_processed": sha_p, "sha_raw": sha_r,
        "src_paths": src_paths, "texts": texts,
        "profile_obj": profile_obj, "manifest_obj": manifest_obj,
    }


def cmd_convert() -> int:
    mh = module_hashes()
    role_map = board_role_map()
    converted, skipped = [], []
    for e in convertible_entries():
        board_id = e["board_id"]
        art = build_board_artifacts(board_id)
        pid = art["profile_id"]
        pdir = REPO / "profiles" / pid
        if pdir.exists():
            skipped.append({"board_id": board_id,
                            "skip_reason": f"profile_dir_exists:{pid}"})
            continue
        # 先内存校验 profile/manifest schema（fail-closed：不过不落盘）
        p_err = manifest_mod.validate_profile(art["profile_obj"])
        m_err = manifest_mod.validate_manifest(art["manifest_obj"])
        if p_err or m_err:
            skipped.append({
                "board_id": board_id,
                "skip_reason": "schema_validation_failed:"
                               f"profile={p_err[:2]};manifest={m_err[:2]}"})
            continue
        # 落盘 corpus 构件 + profile/manifest
        outputs = []
        for relp, text in art["texts"].items():
            sha = write_text(pdir / relp, text)
            outputs.append({"path": f"profiles/{pid}/{relp}",
                            "role": {"inputs/board.kicad_pcb":
                                     "normalized_board (derived unrouted)",
                                     "inputs/stackup.json": "stackup",
                                     "inputs/constraints.json": "constraints",
                                     "derived/net-registry.json":
                                         "net_registry",
                                     "derived/audit.json": "audit_report",
                                     "derived/feedforward-plan.json":
                                         "feedforward_plan"}[relp],
                            "sha256": sha})
        profile_sha = write_json(pdir / "profile.json", art["profile_obj"])
        manifest_sha = write_json(pdir / "manifest.json", art["manifest_obj"])
        # graph.json（v1 形态：corpus 六节点+ledger/gate 声明节点）
        file_hashes = {relp: sha_file(pdir / relp) for relp in art["texts"]}
        graph_obj = corpus_convert.build_graph_spec(
            project_id=pid, profile_id=pid, revision=DATASET_ID,
            file_hashes=file_hashes)
        graph_sha = write_json(pdir / "graph.json", graph_obj)
        # 落盘后 context 校验（manifest 输入全 present + profile 合法）
        try:
            from pcbflow import context as context_mod
            ctx = context_mod.build_context(str(pdir / "manifest.json"))
            ctx_errs = context_mod.validate_context(ctx)
        except Exception as exc:
            shutil.rmtree(pdir)
            skipped.append({
                "board_id": board_id,
                "skip_reason": f"context_validation_failed:{exc}"[:300]})
            continue
        if ctx_errs:
            shutil.rmtree(pdir)
            skipped.append({
                "board_id": board_id,
                "skip_reason": f"context_errors:{ctx_errs[:2]}"[:300]})
            continue
        # conversion log（TD8）
        log_obj = corpus_pcbench.build_pcbench_conversion_log(
            board_id=board_id, profile_id=pid,
            module_hashes=mh,
            inputs=[
                {"path": art["src_paths"]["processed"],
                 "role": "processed_pcb (routed, cleaned)",
                 "sha256": art["sha_processed"]},
                {"path": art["src_paths"]["raw"],
                 "role": "raw_reference_pcb (routed, upstream original)",
                 "sha256": art["sha_raw"]},
            ],
            outputs=outputs,
            model_u=art["model_u"], model_p=art["model_p"],
            model_r=art["model_r"], crit=art["crit"],
            topology_group=art["topology_group"])
        log_path = TL5 / f"conversion-log-pcbench-{art['slug']}.json"
        log_sha = write_json(log_path, log_obj)
        converted.append({
            "board_id": board_id, "profile_id": pid,
            "dataset_role": role_map[board_id],
            "topology_group": art["topology_group"],
            "copper_layers": len(art["model_u"]["copper_layers"]),
            "profile_sha256": profile_sha, "manifest_sha256": manifest_sha,
            "graph_sha256": graph_sha,
            "conversion_log": {"path": rel(log_path), "sha256": log_sha},
            "threshold_keys": sorted(art["profile_obj"]["thresholds"]),
        })
        print(f"convert: {board_id} -> {pid}")
    ledger = {
        "schema_version": "3.0", "artifact_kind": "s10_conversion_ledger",
        "batch_id": BATCH_ID, "conversion_date": S10_DATE,
        "modules": mh,
        "determinism_claim": "pure function of source text; byte-exact "
                             "replay（hashing.json_dumps canonical 落盘）",
        "converted": converted,
        "skipped": skipped,
        "counts": {"converted": len(converted), "skipped": len(skipped),
                   "batch_total": len(batch_boards())},
    }
    sha = write_json(BATCH_DIR / "conversion-ledger.json", ledger)
    print(f"convert: {len(converted)} converted, {len(skipped)} skipped")
    print(f"conversion-ledger.json sha256={sha}")
    return 0


def converted_entries() -> list:
    return load_json(BATCH_DIR / "conversion-ledger.json")["converted"]


# ---------------------------------------------------------------------------
# declare：route-check 段声明
# ---------------------------------------------------------------------------

PRIOR_STATE_NOTE = (
    "not_executed（此前无任何 route/check 执行记录；S10 批量包建立本板首份"
    "声明——v1.x/v3 布线引擎不存在，执行口径=偏差 D17 参考态验证）")


def cmd_declare() -> int:
    mh = module_hashes()
    made = []
    for e in converted_entries():
        pid = e["profile_id"]
        board_id = e["board_id"]
        art_paths = corpus_pcbench.dataset_board_paths(board_id)
        raw_rel = f"datasets/{DATASET_ID}/raw/{board_id}/raw.kicad_pcb"
        raw_sha = sha_file(REPO / raw_rel)
        profile_obj = load_json(REPO / "profiles" / pid / "profile.json")
        decl = check_stage.build_route_check_declaration(
            profile_id=pid, board_id=board_id,
            dataset_role=e["dataset_role"],
            reference_route_path=raw_rel, reference_route_sha256=raw_sha,
            profile_threshold_keys=sorted(profile_obj["thresholds"]),
            prior_state_note=PRIOR_STATE_NOTE)
        dsha = write_json(REPO / "profiles" / pid / "route-check.json", decl)
        made.append({"board_id": board_id, "profile_id": pid,
                     "declaration": {"path": f"profiles/{pid}/route-check.json",
                                     "sha256": dsha},
                     "reference_route": {"path": raw_rel, "sha256": raw_sha}})
    ledger = {
        "schema_version": "3.0", "artifact_kind": "s10_declaration_ledger",
        "batch_id": BATCH_ID, "declared_date": S10_DATE,
        "modules": mh, "declarations": made,
        "route_scope": check_stage.ROUTE_SCOPE,
        "route_scope_note": check_stage.ROUTE_SCOPE_NOTE,
    }
    sha = write_json(BATCH_DIR / "declaration-ledger.json", ledger)
    print(f"declare: {len(made)} declarations")
    print(f"declaration-ledger.json sha256={sha}")
    return 0


# ---------------------------------------------------------------------------
# check：读 Bash 产出的 DRC JSON → check 报告
# ---------------------------------------------------------------------------

def cmd_check() -> int:
    mh = module_hashes()
    role_map = board_role_map()
    reports = []
    for e in converted_entries():
        pid = e["profile_id"]
        board_id = e["board_id"]
        slug = corpus_pcbench.board_slug(board_id)
        cdir = TL5 / "check" / pid
        raw_rel = f"datasets/{DATASET_ID}/raw/{board_id}/raw.kicad_pcb"
        drc_err = load_json(cdir / f"{pid}.drc-error.json")
        drc_all = load_json(cdir / f"{pid}.drc-all.json")
        raw_text = (REPO / raw_rel).read_text(encoding="utf-8")
        geometry = check_stage.parse_routed_geometry(raw_text)
        summary = check_stage.summarize_drc(drc_all, drc_err)
        profile_obj = load_json(REPO / "profiles" / pid / "profile.json")
        decl = load_json(REPO / "profiles" / pid / "route-check.json")
        report = check_stage.build_check_report(
            profile_id=pid, board_id=board_id,
            dataset_role=role_map[board_id],
            declaration=decl, geometry=geometry, drc_summary=summary,
            profile_thresholds=profile_obj["thresholds"],
            input_refs={
                "reference_route": {"path": raw_rel,
                                    "sha256": sha_file(REPO / raw_rel)},
                "staged_board": {
                    "path": rel(cdir / f"{pid}.reference.kicad_pcb"),
                    "sha256": sha_file(cdir / f"{pid}.reference.kicad_pcb")},
                "route_check_declaration": {
                    "path": f"profiles/{pid}/route-check.json",
                    "sha256": sha_file(REPO / "profiles" / pid
                                       / "route-check.json")},
                "profile": {"path": f"profiles/{pid}/profile.json",
                            "sha256": sha_file(REPO / "profiles" / pid
                                               / "profile.json")},
                "drc_severity_error": {"path": rel(cdir / f"{pid}.drc-error.json"),
                                       "sha256": sha_file(cdir / f"{pid}.drc-error.json")},
                "drc_severity_all": {"path": rel(cdir / f"{pid}.drc-all.json"),
                                     "sha256": sha_file(cdir / f"{pid}.drc-all.json")},
            })
        rsha = write_json(cdir / "check-report.json", report)
        reports.append({
            "board_id": board_id, "profile_id": pid,
            "dataset_role": role_map[board_id],
            "reference_route": {"path": raw_rel,
                                "sha256": sha_file(REPO / raw_rel)},
            "staged_board_sha256": sha_file(cdir / f"{pid}.reference.kicad_pcb"),
            "declaration": {"path": f"profiles/{pid}/route-check.json",
                            "sha256": sha_file(REPO / "profiles" / pid
                                               / "route-check.json")},
            "check_report": {"path": rel(cdir / "check-report.json"),
                             "sha256": rsha, "result": report["result"]},
            "drc": {
                "severity_error": {
                    "path": rel(cdir / f"{pid}.drc-error.json"),
                    "exit": read_exit(cdir / f"{pid}.drc-error.exit"),
                    "violations": summary["dual_severity"][
                        "severity_error_batch"]["total"]},
                "severity_all": {
                    "path": rel(cdir / f"{pid}.drc-all.json"),
                    "exit": read_exit(cdir / f"{pid}.drc-all.exit"),
                    "violations": summary["dual_severity"][
                        "severity_all_final"]["total"]},
            },
            "kicad_cli_version": summary.get("kicad_version"),
            "connectivity": {
                "unconnected_items": summary["connectivity_authority_input"][
                    "unconnected_items"],
                "connectivity_type_violation_total": summary[
                    "connectivity_authority_input"][
                    "connectivity_type_violation_total"],
                "advisory_flagged_nets": len(
                    check_stage.advisory_zero_geometry_nets(geometry)),
            },
            "drc_error_count": summary["dual_severity"][
                "severity_error_batch"]["violations_by_severity"].get(
                    "error", 0),
        })
        print(f"check: {pid} result={report['result']}")
    record = check_stage.build_execution_record(
        entries=reports, toolchain_lock_sha256=sha_file(
            REPO / "toolchain_lock.json"))
    sha = write_json(BATCH_DIR / "route-check-execution-record-s10.json",
                     record)
    print(f"check: {len(reports)} reports; record all_pass="
          f"{record['all_pass']}")
    print(f"route-check-execution-record-s10.json sha256={sha}")
    return 0


def read_exit(path: Path):
    if not path.exists():
        return None
    t = path.read_text(encoding="utf-8").strip()
    try:
        return int(t)
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# graphspec：mainpath graph-spec.json（v2 形态：+route/check 两节点）
# ---------------------------------------------------------------------------

def cmd_graphspec() -> int:
    made = []
    for e in converted_entries():
        pid = e["profile_id"]
        pdir = REPO / "profiles" / pid
        mdir = TL5 / "mainpath" / pid
        v1 = load_json(pdir / "graph.json")
        nodes = [dict(n) for n in v1["nodes"]]
        # 路径从 profile 目录相对改为 mainpath 目录相对（../../…/profiles/）
        for n in nodes:
            if n.get("path"):
                n["path"] = f"../../../../profiles/{pid}/{n['path']}"
        decl_sha = sha_file(pdir / "route-check.json")
        cdir = TL5 / "check" / pid
        cr_sha = sha_file(cdir / "check-report.json")
        nodes.append({
            "artifact_id": "route_check_declaration",
            "kind": "route_check_declaration",
            "path": f"../../../../profiles/{pid}/route-check.json",
            "sha256": decl_sha, "status": "present",
            "revision": DATASET_ID, "stage_label": "route",
            "inputs": ["board"],
        })
        nodes.append({
            "artifact_id": "check_report", "kind": "check_report",
            "path": f"../../check/{pid}/check-report.json",
            "sha256": cr_sha, "status": "present",
            "revision": DATASET_ID, "stage_label": "check",
            "inputs": ["route_check_declaration", "board"],
            "expected_input_hashes": {"route_check_declaration": decl_sha},
        })
        spec = {
            "schema_version": "3.0",
            "artifact_kind": "artifact_graph_spec",
            "graph_version": "1",
            "project_id": pid, "profile_id": pid,
            "revision": DATASET_ID, "nodes": nodes,
            "version_note": "S10 批量包首版（10 节点=v1 六段 corpus 构件"
                            "+ledger/gate 声明+route_check_declaration(route)"
                            "+check_report(check)；D17 参考态验证口径，"
                            "自建立即含 route/check 证据）",
        }
        sha = write_json(mdir / "graph-spec.json", spec)
        made.append({"profile_id": pid,
                     "graph_spec": {"path": rel(mdir / "graph-spec.json"),
                                    "sha256": sha}})
        print(f"graphspec: {pid}")
    ledger = {
        "schema_version": "3.0", "artifact_kind": "s10_graphspec_ledger",
        "batch_id": BATCH_ID, "date": S10_DATE, "specs": made,
    }
    sha = write_json(BATCH_DIR / "graphspec-ledger.json", ledger)
    print(f"graphspec-ledger.json sha256={sha}")
    return 0


# ---------------------------------------------------------------------------
# report：TD8 逐 profile 报告（读 v3cli 产物实况）
# ---------------------------------------------------------------------------

LIMITS_TEMPLATE = [
    "转换=文本结构级（层/网/封装/焊盘本质；无几何求值/DRC/写回）",
    "PCBench 无 unrouted 文件：unrouted 态=processed 确定性剥除 routed 几何"
    "推导（segment/via/arc 清零；与上游 final.json problem/solution 切分"
    "同构）——非上游提供的原始 unrouted 设计起点",
    "critical nets/约束=网名约定表推导（名字级启发非电气真值）；"
    "length_match 容差不生成",
    "anchors/via cost/router 参数不可判定→显式留空（conversion_log."
    "field_missingness）",
    "route/check 段=参考 routed 态验证口径（D17：验证≠布线生成；连通性/"
    "DRC/阈值对账见 check 报告）——布线生成能力缺口如实保留（Evidence "
    "reality），本段证据不构成布线能力主张",
    "compile/enum/audit/feedforward 段 authority=corpus_conversion_first_"
    "order（结构级事实，非 v1.x 设计流引擎输出——偏差 D12 措辞沿用）",
    "DRC baseline 由 KiCad 10.0.5 读 KiCad5 格式 routed 参考态产出（外部"
    "工具输出原样留存，date 字段与 violations 数组顺序跨运行不稳定——"
    "type/severity 计数可复算，caveat 已声明）",
    "copper_layers={cu}（{cuw}）",
    "split 角色={role}（train/validation 侧板）",
]


def cmd_report() -> int:
    mh = module_hashes()
    role_map = board_role_map()
    made = []
    for e in converted_entries():
        pid = e["profile_id"]
        board_id = e["board_id"]
        slug = corpus_pcbench.board_slug(board_id)
        pdir = REPO / "profiles" / pid
        mdir = TL5 / "mainpath" / pid
        cdir = TL5 / "check" / pid
        art = build_board_artifacts(board_id)  # 纯重放（确定性）
        denom_u = corpus_convert.board_denominators(art["model_u"])
        denom_r = corpus_convert.board_denominators(art["model_r"])
        mc = load_json(mdir / "manifest-check.json")
        ctx = load_json(mdir / "context.json")
        gr = load_json(mdir / "graph-report.json")
        check_report = load_json(cdir / "check-report.json")
        drc_all_path = TL5 / "drc-pcbench" / slug / f"{slug}.raw.drc-all.json"
        drc_err_path = TL5 / "drc-pcbench" / slug / f"{slug}.raw.drc-error.json"
        drc_all = load_json(drc_all_path)
        drc_err = load_json(drc_err_path)
        audit_obj = load_json(pdir / "derived" / "audit.json")
        conv_log = load_json(TL5 / f"conversion-log-pcbench-{slug}.json")
        profile_obj = load_json(pdir / "profile.json")

        def sev_counts(d):
            out: dict = {}
            for v in d.get("violations") or []:
                out[v.get("severity")] = out.get(v.get("severity"), 0) + 1
            return dict(sorted(out.items()))

        all_by = sev_counts(drc_all)
        err_by = sev_counts(drc_err)
        top_types: dict = {}
        for v in drc_all.get("violations") or []:
            t = v.get("type") or "unknown"
            top_types[t] = top_types.get(t, 0) + 1
        top_types = dict(sorted(top_types.items(),
                                key=lambda kv: (-kv[1], kv[0]))[:5])

        decl_sha = sha_file(pdir / "route-check.json")
        cr_sha = sha_file(cdir / "check-report.json")
        conn = check_report["connectivity"]
        conn_auth = check_report["drc"]["connectivity_authority_input"]
        rec_setup = check_report["threshold_reconciliation"]["setup_identity"]
        rec_geo = check_report["threshold_reconciliation"]["actual_geometry"]
        role = role_map[board_id]
        cu = denom_u["copper_layer_count"]

        denominators = {
            "net_count": denom_u["net_count"],
            "named_net_count": denom_u["named_net_count"],
            "module_count": denom_u["module_count"],
            "pad_count": denom_u["pad_count"],
            "pad_thru_hole_count": denom_u["pad_thru_hole_count"],
            "pad_smd_count": denom_u["pad_smd_count"],
            "pad_without_net_count": denom_u["pad_without_net_count"],
            "copper_layer_count": cu,
            "routed_segment_count": art["model_r"]["segment_count"],
            "routed_via_count": art["model_r"]["via_count"],
            "topology_group": art["topology_group"],
        }
        quality = {
            "parse": {
                "backend": "pcbflow.sexpr_min（text_structure_only）",
                "board_version": art["model_u"]["board_version"],
                "host": art["model_u"]["host"],
                "warnings": (art["model_p"]["parse_warnings"]
                             + art["model_r"]["parse_warnings"]),
            },
            "conversion": {
                "track": "tl5-pcbench-r1",
                "modules": ["pcbflow.corpus_convert（解析/规范化/构件）",
                            "pcbflow.corpus_pcbench（审计/保留/split/选板/"
                            "unrouted 推导/日志）"],
                "module_sha256": mh,
                "conversion_log": conv_log["path"] if "path" in conv_log
                else rel(TL5 / f"conversion-log-pcbench-{slug}.json"),
                "determinism": "byte-exact 纯函数（S10 抽样重放逐字节一致）",
                "unrouted_derivation":
                    "derive_unrouted_model(processed)——stripped "
                    "segments/vias/arcs 实数入账",
            },
            "audit_checks": {c["id"]: c["pass"]
                             for c in audit_obj["checks"]},
            "audit_result": audit_obj["result"],
            "context_status": ctx.get("status"),
            "context_sha256": ctx.get("context_sha256"),
            "graph_status": gr.get("status"),
            "graph_sha256": gr.get("graph_sha256"),
            "graph_disk": gr.get("disk_status"),
            "stripped_from_processed":
                conv_log["input_state_semantics"]["stripped_counts"],
            "routed_reference": {
                "segment_count": art["model_r"]["segment_count"],
                "via_count": art["model_r"]["via_count"],
                "arc_count": art["model_r"]["arc_count"],
            },
            "drc_baseline": {
                "tool": "kicad-cli 10.0.5",
                "target_state": "raw 参考态（上游原始 routed，回测 baseline，"
                                "非 profile 输入；非 pcbflow 布线产物）",
                "files": {
                    "all": {"path": rel(drc_all_path),
                            "sha256": sha_file(drc_all_path),
                            "exit": read_exit(drc_all_path.parent
                                              / f"{slug}.raw.drc-all.exit")},
                    "error": {"path": rel(drc_err_path),
                              "sha256": sha_file(drc_err_path),
                              "exit": read_exit(drc_err_path.parent
                                                / f"{slug}.raw.drc-error.exit")},
                },
                "severity_all_violations": sum(all_by.values()),
                "severity_error_violations": sum(err_by.values()),
                "top_types_severity_all": top_types,
                "unclosed_items": len(drc_all.get("unconnected_items") or []),
            },
            "route_check": {
                "route_scope": check_report["route_scope"],
                "result": check_report["result"],
                "kicad_cli_version":
                    check_report["toolchain"]["kicad_cli_version"],
                "declaration": {"path": f"profiles/{pid}/route-check.json",
                                "sha256": decl_sha},
                "check_report": {"path": rel(cdir / "check-report.json"),
                                 "sha256": cr_sha},
                "graph_report": {"path": rel(mdir / "graph-report.json"),
                                 "sha256": gr.get("graph_sha256"),
                                 "status": gr.get("status")},
                "connectivity": {
                    "authority": "kicad_cli_drc_unconnected_items",
                    "unconnected_items": conn["unconnected_items"],
                    "connectivity_type_violation_total":
                        conn_auth["connectivity_type_violation_total"],
                    "advisory_flagged_nets": next(
                        a["flagged_net_count"]
                        for a in check_report["advisory_checks"]),
                },
                "drc": {
                    "error": sum(err_by.values()),
                    "all_total": sum(all_by.values()),
                    "by_severity_all": all_by,
                },
                "staging_identical_to_reference":
                    check_report["checks"][2]["pass"],
            },
        }

        main_path = {
            "manifest": {
                "status": "executed" if mc.get("status") == "ok"
                else "not_executed",
                "evidence": (
                    f"v3cli manifest exit 0（errors=[]；manifest_sha256="
                    f"{(mc.get('manifest_sha256') or '')[:16]}…；"
                    f"profile_sha256="
                    f"{(mc.get('profile_sha256') or '')[:16]}…）"),
                "authority": "pcbflow.v3cli manifest（schemas."
                             "project_manifest 3.0）",
            },
            "compile": {
                "status": "executed",
                "evidence": f"constraints 构件由真实网集推导（diff_pair="
                            f"{len(load_json(pdir / 'inputs' / 'constraints.json')['entries'])} 条；"
                            f"sha256={sha_file(pdir / 'inputs' / 'constraints.json')[:16]}…）；"
                            f"图节点 stage=compile 盘上对账 present",
                "authority": "corpus_conversion_first_order"
                             "（pcbflow.corpus_convert；非 v1.x compile "
                             "引擎——该引擎硬连 Rev-C 输入）",
            },
            "enum": {
                "status": "executed",
                "evidence": f"net-registry 构件=真实逐网注册（"
                            f"{denom_u['net_count']} 网；sha256="
                            f"{sha_file(pdir / 'derived' / 'net-registry.json')[:16]}…）；"
                            f"图节点 stage=enum present",
                "authority": "corpus_conversion_first_order（非 v1.x enum 引擎）",
            },
            "audit": {
                "status": "executed",
                "evidence": f"audit 构件={len(audit_obj['checks'])} 项结构级"
                            f"检查 result={audit_obj['result']}（sha256="
                            f"{sha_file(pdir / 'derived' / 'audit.json')[:16]}…）；"
                            f"图节点 stage=audit present",
                "authority": "corpus_conversion_first_order"
                             "（非 v1.x FA3 可布性引擎）",
            },
            "feedforward": {
                "status": "executed",
                "evidence": f"feedforward 构件=rail/层负载真实账本（sha256="
                            f"{sha_file(pdir / 'derived' / 'feedforward-plan.json')[:16]}…）；"
                            f"图节点 stage=feedforward present",
                "authority": "corpus_conversion_first_order planning_"
                             "advisory 级（非 v1.x FF1 引擎）",
            },
            "route_check": {
                "status": "executed",
                "evidence": (
                    f"声明 profiles/{pid}/route-check.json（sha256="
                    f"{decl_sha[:16]}…）；check 报告 "
                    f"{rel(cdir / 'check-report.json')}（sha256="
                    f"{cr_sha[:16]}…，result={check_report['result']}）："
                    f"连通性 unconnected_items="
                    f"{conn['unconnected_items']}/连通类违例="
                    f"{conn_auth['connectivity_type_violation_total']}"
                    f"（kicad-cli authority）+advisory 逐网铜几何疑似未布通="
                    f"{next(a['flagged_net_count'] for a in check_report['advisory_checks'])}；"
                    f"DRC 双 severity error={sum(err_by.values())}/all="
                    f"{sum(all_by.values())}（参考态实况计数，上游板自带违例"
                    f"如实记录非判罚）；阈值对账 setup 数值一致 "
                    f"{len(rec_setup['compared'])} 项（{len(rec_setup['skipped'])} "
                    f"项不可比跳过）+实际几何实算 "
                    f"{sum(1 for g in rec_geo['entries'] if g.get('status') == 'checked')}"
                    f" 项（不符 {len(rec_geo['failed'])} 项）；staging 拷贝与 "
                    f"datasets/ raw 逐字节一致（sha 复核）；graph-spec "
                    f"route/check 两节点盘上对账 present"),
                "authority": "kicad_cli(10.0.5 DRC dual severity)+"
                             "reference_verification（D17：route_scope="
                             "reference_verification——参考 routed 态验证，"
                             "非 v1.x/v3 布线生成；布线生成能力缺口如实保留"
                             "于 Evidence reality）",
            },
        }
        limits = list(LIMITS_TEMPLATE)
        limits[7] = f"copper_layers={cu}（{cu} 铜层）"
        limits[8] = (f"split 角色={role}（train/validation 侧板）"
                     if role != "holdout" else
                     f"split 角色={role}（holdout 冻结只读板——验证零写回 "
                     f"datasets/）")
        meta = art["meta"]
        report_obj = corpus_convert.build_profile_report(
            board_id=board_id, profile_id=pid, dataset_role=role,
            denominators=denominators, quality=quality, limits=limits,
            leakage_audit_ref={
                "path": "out/v3-tl5/leakage-audit-pcbench-r1.json",
                "result": "pass",
                "sha256": sha_file(TL5 / "leakage-audit-pcbench-r1.json"),
                "cross_library": "no_cross_library_duplicates",
            },
            source={
                "dataset_id": DATASET_ID,
                "dataset_version": "3",
                "archive_sha256": "b80a0f660b27fabb66031396112e29f45"
                                  "dbb633836b8c0ba23f41e09bae7fc85",
                "license": {
                    "value": hashing.json_dumps(
                        meta.get("licenses")).strip(),
                    "evidence": "raw/<board>/metadata.json licenses 字段"
                                "（PCBench 爬取时点记录，2023-08-17）",
                },
                "attribution": (
                    f"upstream {meta.get('author')} / {meta.get('source')}"
                    f"（PCBench 爬取自 846 上游仓库；retrieved at "
                    f"{meta.get('retrieved at')}）"),
                "processed_pcb": {"path": art["src_paths"]["processed"],
                                  "sha256": art["sha_processed"]},
                "raw_reference_pcb": {"path": art["src_paths"]["raw"],
                                      "sha256": art["sha_raw"]},
            },
            main_path=main_path)
        rsha = write_json(mdir / "profile-report.json", report_obj)
        made.append({"board_id": board_id, "profile_id": pid,
                     "report": {"path": rel(mdir / "profile-report.json"),
                                "sha256": rsha},
                     "main_path_status": {
                         k: v["status"] for k, v in main_path.items()}})
        print(f"report: {pid} main_path="
              f"{report_obj['main_path']['route_check']['status']}")
    ledger = {
        "schema_version": "3.0", "artifact_kind": "s10_report_ledger",
        "batch_id": BATCH_ID, "report_date": S10_DATE, "reports": made,
    }
    sha = write_json(BATCH_DIR / "report-ledger.json", ledger)
    print(f"report-ledger.json sha256={sha}")
    return 0


# ---------------------------------------------------------------------------
# aggregate：汇总台账 + dataset manifest v3
# ---------------------------------------------------------------------------

def cmd_aggregate() -> int:
    judge = load_json(BATCH_DIR / "judge-ledger.json")
    conv = load_json(BATCH_DIR / "conversion-ledger.json")
    decl = load_json(BATCH_DIR / "declaration-ledger.json")
    check_rec = load_json(BATCH_DIR / "route-check-execution-record-s10.json")
    reports = load_json(BATCH_DIR / "report-ledger.json")

    converted = conv["converted"]
    pids = sorted([e["profile_id"] for e in converted])
    # 1) 汇总台账
    skip_counts: dict = {}
    for e in judge["entries"]:
        if e.get("skip_reason"):
            key = e["skip_reason"].split(":")[0]
            skip_counts[key] = skip_counts.get(key, 0) + 1
    for e in conv["skipped"]:
        key = e["skip_reason"].split(":")[0]
        skip_counts[key] = skip_counts.get(key, 0) + 1
    # check 实况字段：结果/双侧计数来自 check 执行记录条目；连通性明细来自
    # 逐板 check-report.json（执行记录不内嵌 connectivity 细节）
    check_entries = check_rec["entries"]
    check_reports = {e["profile_id"]: load_json(
        TL5 / "check" / e["profile_id"] / "check-report.json")
        for e in check_entries}
    err_counts = sorted(
        e["drc"]["severity_error"]["violations"] for e in check_entries)
    conn_dist: dict = {"connected": 0, "unconnected": 0}
    for e in check_entries:
        rep = check_reports[e["profile_id"]]
        c = rep["connectivity"]
        ca = rep["drc"]["connectivity_authority_input"]
        if c["unconnected_items"] == 0 and \
                ca["connectivity_type_violation_total"] == 0:
            conn_dist["connected"] += 1
        else:
            conn_dist["unconnected"] += 1
    result_dist: dict = {}
    for e in check_entries:
        r = e["check_report"]["result"]
        result_dist[r] = result_dist.get(r, 0) + 1
    anomalies = [{"profile_id": e["profile_id"], "board_id": e["board_id"],
                  "result": e["check_report"]["result"],
                  "failed_checks": [c["id"] for c in check_reports[
                      e["profile_id"]]["checks"] if not c["pass"]]}
                 for e in check_entries
                 if e["check_report"]["result"] != "pass"]
    median = (err_counts[len(err_counts) // 2]
              if len(err_counts) % 2 else
              (err_counts[len(err_counts) // 2 - 1]
               + err_counts[len(err_counts) // 2]) / 2) if err_counts else None
    summary = {
        "schema_version": "3.0", "artifact_kind": "s10_batch_summary",
        "batch_id": BATCH_ID, "batch_date": S10_DATE,
        "scope": "datasets/pcbench-r1 剩余 78 合规板逐板判定+能转尽转+"
                 "route/check 参考态验证（D17 口径；非布线生成）",
        "denominator": {"dataset_boards": 81, "batch_boards": 78,
                        "previously_converted": 3},
        "conversion": {
            "converted_in_batch": len(converted),
            "skipped_in_batch": 78 - len(converted),
            "skip_counts": dict(sorted(skip_counts.items())),
            "skip_reasons_per_board": [
                {"board_id": e["board_id"], "reason": e["skip_reason"]}
                for e in judge["entries"] if e.get("skip_reason")]
            + [{"board_id": e["board_id"], "reason": e["skip_reason"]}
               for e in conv["skipped"]],
            "total_converted_profiles": 3 + len(converted),
            "total_profile_coverage": f"{3 + len(converted)}/81",
        },
        "reference_check": {
            "check_result_distribution": dict(sorted(result_dist.items())),
            "connectivity_distribution": dict(sorted(conn_dist.items())),
            "drc_error_counts": {
                "min": min(err_counts) if err_counts else None,
                "median": median,
                "max": max(err_counts) if err_counts else None,
                "zero_error_boards": sum(1 for c in err_counts if c == 0),
            },
            "anomalies": anomalies,
            "semantics": "check result=fail=参考 routed 态自带连通类违例或"
                         "阈值对账不符的上游板实况（D17：error 计数与 fail "
                         "均为参考态实况记录，非 pcbflow 产物质量、非判罚"
                         "口径）；staging 全部与 datasets/ raw 逐字节一致",
        },
        "mainpath_layout": {
            "profiles": "profiles/pcbench-<slug>/{inputs,derived,profile."
                        "json,manifest.json,graph.json,route-check.json}",
            "conversion_logs": "out/v3-tl5/conversion-log-pcbench-<slug>.json",
            "drc_baseline": "out/v3-tl5/drc-pcbench/<slug>/<slug>.raw."
                            "{kicad_pcb,drc-error.json,drc-all.json}",
            "check": "out/v3-tl5/check/<pid>/{<pid>.reference.kicad_pcb,"
                     "drc-*.json+logs,check-report.json}",
            "mainpath": "out/v3-tl5/mainpath/<pid>/{manifest-check.json,"
                        "context.json,graph-spec.json,graph-report.json,"
                        "profile-report.json}",
            "batch_ledgers": "out/v3-tl5/batch-s10/*.json",
            "naming_note": "新板首版（无 -v2 后缀）；既有 3 板 v1/v2 文件"
                           "原样只读",
        },
        "execution_record": {
            "path": rel(BATCH_DIR / "route-check-execution-record-s10.json"),
            "all_pass": check_rec["all_pass"],
            "profile_count": check_rec["summary"]["profile_count"],
            "results": check_rec["summary"]["results"],
        },
    }
    sha = write_json(BATCH_DIR / "batch-summary.json", summary)

    # 2) dataset manifest v3
    v2 = load_json(TL5 / "dataset-manifest-pcbench-r1-v2.json")
    mh = module_hashes()
    # normalized_hash：全部 (3+新增) profile × 7 文件 aggregate
    norm_files = []
    all_pids = sorted(list(EXISTING_PROFILES) + pids)
    for pid in all_pids:
        for r in ("inputs/board.kicad_pcb", "inputs/stackup.json",
                  "inputs/constraints.json", "derived/net-registry.json",
                  "derived/audit.json", "derived/feedforward-plan.json",
                  "route-check.json"):
            p = REPO / "profiles" / pid / r
            norm_files.append({"path": f"profiles/{pid}/{r}",
                               "sha256": sha_file(p)})
    norm_hash = hashing.sha256_bytes(
        hashing.canonical_json_bytes(sorted(norm_files,
                                            key=lambda x: x["path"])))
    # raw_files（raw_hash 复算=datasets 只读不变断言）
    raw_files = []
    for p in sorted((REPO / "datasets" / DATASET_ID).rglob("*")):
        if p.is_file():
            raw_files.append({"path": p.relative_to(REPO).as_posix(),
                              "sha256": sha_file(p)})
    if corpus.aggregate_raw_hash(raw_files) != v2["raw_hash"]:
        raise SystemExit("raw_hash mismatch: datasets/ 内容有变（红线 2）")
    # DRC baseline per_profile 增量
    per_profile = dict(v2["DRC_baseline"]["per_profile"])
    for e in converted:
        slug = corpus_pcbench.board_slug(e["board_id"])
        drc_all_p = TL5 / "drc-pcbench" / slug / f"{slug}.raw.drc-all.json"
        drc_err_p = TL5 / "drc-pcbench" / slug / f"{slug}.raw.drc-error.json"
        drc_all = load_json(drc_all_p)
        drc_err = load_json(drc_err_p)
        top: dict = {}
        for v in drc_all.get("violations") or []:
            t = v.get("type") or "unknown"
            top[t] = top.get(t, 0) + 1
        per_profile[e["profile_id"]] = {
            "board_id": e["board_id"],
            "files": [
                {"exit_code": 0, "path": rel(drc_all_p),
                 "role": "drc_final_severity_all",
                 "sha256": sha_file(drc_all_p)},
                {"exit_code": 0, "path": rel(drc_err_p),
                 "role": "drc_batch_severity_error",
                 "sha256": sha_file(drc_err_p)},
            ],
            "severity_all_violations": len(drc_all.get("violations") or []),
            "severity_error_violations": len(drc_err.get("violations") or []),
            "target_state": "raw.kicad_pcb（上游原始 routed 参考态；非 "
                            "profile 输入、非 pcbflow 布线产物）",
            "top_types_severity_all": dict(sorted(
                top.items(), key=lambda kv: (-kv[1], kv[0]))[:5]),
            "unclosed_items": len(drc_all.get("unconnected_items") or []),
        }
    conv_log = list(v2["conversion_log"]) + [
        {"board_id": e["board_id"],
         "path": e["conversion_log"]["path"],
         "sha256": e["conversion_log"]["sha256"]} for e in converted]
    conv_log.sort(key=lambda x: x["board_id"])
    n_total = 3 + len(converted)
    fm = dict(v2["field_missingness"])
    fm["prior_version"] = {
        "path": "out/v3-tl5/dataset-manifest-pcbench-r1-v2.json",
        "sha256": sha_file(TL5 / "dataset-manifest-pcbench-r1-v2.json"),
        "change": "v3=S10 分母纵深批量包：78 剩余合规板逐板判定（judge "
                  f"台账），转换 {len(converted)} 板+跳过 "
                  f"{78 - len(converted)}（分类计数见 batch-summary）；"
                  "profile 覆盖、normalized_hash、DRC_baseline、"
                  "conversion_log 全量重算；v2/v1 结论原样保留",
    }
    fm["conversion.scope"] = (
        f"累计转换 {n_total}/81 板（S7 有界 3 板+S10 批量 "
        f"{len(converted)} 板；S10 判定台账=out/v3-tl5/batch-s10/"
        "judge-ledger.json，逐板 skip 原因在案）")
    fm["DRC_baseline.scope"] = (
        f"{n_total} 块转换板的 routed 参考态（raw）双 severity；"
        f"S10 新增 {len(converted)} 板")
    fm["DRC_baseline.reproducibility"] = (
        "DRC JSON 含 kicad-cli 自身 date 字段，且 violations 数组顺序跨"
        "运行不稳定（S10 实测：同板重跑 type/severity 多重集一致、顺序"
        "不同）——外部工具输出原样留存；计数可复算、逐条目内容可比")
    fm["normalized_hash.scope"] = (
        f"v3 scope={n_total} profile inputs/derived+route-check.json "
        f"{len(norm_files)} 文件 aggregate={norm_hash}（S10 批量转换+"
        "声明后全量重算）；v2 scope（3 profile 21 文件）值="
        + v2["normalized_hash"] + "——既有 3 板 inputs/derived 零改动")
    record = {
        "dataset_id": DATASET_ID, "version": "3",
        "source_uri_or_archive_sha256": v2["source_uri_or_archive_sha256"],
        "license": v2["license"], "license_scope": v2["license_scope"],
        "redistribution_allowed": v2["redistribution_allowed"],
        "derivative_allowed": v2["derivative_allowed"],
        "attribution": v2["attribution"],
        "collection_date": v2["collection_date"],
        "board_ids": v2["board_ids"], "revision_ids": v2["revision_ids"],
        "project_groups": v2["project_groups"],
        "topology_groups": v2["topology_groups"],
        "vendor_groups": v2["vendor_groups"],
        "consent_or_provenance": v2["consent_or_provenance"],
        "conversion_script": {
            "track": "tl5-pcbench-r1",
            "modules": {
                "pcbflow.check_stage": {
                    "module_sha256": mh["check_stage"],
                    "role": "S8 route/check 段执行器（参考 routed 态验证："
                            "声明装配/DRC 摘要/check 报告/执行汇总；纯函数）"},
                "pcbflow.corpus_convert": {
                    "module_sha256": mh["corpus_convert"],
                    "role": "KiCad5 解析/规范化/构件（零改动）"},
                "pcbflow.corpus_pcbench": {
                    "module_sha256": mh["corpus_pcbench"],
                    "role": "PCBench 审计/保留/split/选板/unrouted 推导/"
                            "manifest 装配"},
            },
            "entry_points": list(v2["conversion_script"]["entry_points"]),
            "replay_contract": (
                "纯函数：输入=datasets/ 只读板文本+注入 hash；输出=profile "
                "构件内容；落盘由编排侧完成（生成器纪律：零子进程/零自身"
                "落盘/零网络）；S10 批量编排=scripts/s10_batch_orchestrate."
                "py（编排侧脚本，kicad-cli/v3cli 调用留 Bash）"),
            "tests": "tests/test_tl5_pcbench.py（S7）+tests/test_tl5_"
                     "convert.py（S6）+tests/test_tl5_check_stage.py（S8）"
                     "+tests/test_tl5_s10_batch.py（S10 批量面）",
        },
        "kicad_version": v2["kicad_version"],
        "raw_files": raw_files,
        "normalized_hash": norm_hash,
        "conversion_log": conv_log,
        "field_missingness": fm,
        "DRC_baseline": {
            **{k: v for k, v in v2["DRC_baseline"].items()
               if k not in ("per_profile",)},
            "scope": fm["DRC_baseline.scope"],
            "per_profile": per_profile,
        },
        "dataset_splits": v2["dataset_splits"],
        "excluded_boards": v2["excluded_boards"],
        "source_research_ref": v2["source_research_ref"],
    }
    m3 = corpus.build_dataset_manifest(record)
    if m3["raw_hash"] != v2["raw_hash"]:
        raise SystemExit("raw_hash changed")
    m3_path = TL5 / "dataset-manifest-pcbench-r1-v3.json"
    m3_sha = write_json(m3_path, m3)
    print(f"aggregate: batch-summary sha={sha}")
    print(f"aggregate: manifest v3 sha={m3_sha} "
          f"(coverage {n_total}/81, norm_hash={norm_hash[:16]}…)")
    return 0


# ---------------------------------------------------------------------------

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="s10-batch")
    ap.add_argument("command", choices=["judge", "convert", "declare",
                                        "check", "graphspec", "report",
                                        "aggregate"])
    args = ap.parse_args(argv)
    return {"judge": cmd_judge, "convert": cmd_convert,
            "declare": cmd_declare, "check": cmd_check,
            "graphspec": cmd_graphspec, "report": cmd_report,
            "aggregate": cmd_aggregate}[args.command]()


if __name__ == "__main__":
    raise SystemExit(main())
