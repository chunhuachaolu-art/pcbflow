#!/usr/bin/env python
"""S18-DEMO-CONVERT 编排：KiCad 8.99–10.99 demo 板转换器扩展（r2）。

编排侧职责（库侧 pcbflow/corpus_convert.py k9 路径保持纯函数零落盘）。
纪律（S18 红线 3）：本脚本 stdin→stdout——请求经 stdin JSON 传入，
产物一律写 stdout（canonical JSON 或构件原文文本）；盘上落盘全部由
Bash 重定向完成；本脚本零写盘、零子进程、零网络、零 wall-clock
（S18_DATE=声明常量）、零主机路径（一律仓库相对 POSIX）。
只读输入：datasets/kicad-demos-r1|pcbbenchmarks-r1|pcbench-r1/（字节读）
与 out/v3-tl5/ 既有冻结件（r1 manifest/retention-ledger/r4；S15 审计
结论不重开，license 指针沿用）。

ops（stdin JSON 的 "op" 键分派）：
  plan      {} → 17 板转换计划（board_id/source_rel/sha256/profile_id/
                  split_role/license 指针/版本 token/splits 快照）
  artifact  {board, artifact, splits?, drc_baseline?} → 单构件文本
            （board=规范化板文本；其余=canonical JSON）
  audit     {board_u, board_r} → multichannel 双态 audit 构件 JSON
  graph     {board, file_hashes, has_audit} → graph spec JSON
  convlog   {board, board_r?, inputs, outputs, module_sha256,
             audit_result, route_check_status} → conversion log JSON
  leakage   {} → kicad-demos-r2 泄漏/去重审计（库内+跨库全量）
  manifest  {per_board, module_sha256, leakage_ref, ...} → r2 TD8
                  manifest（corpus.build_dataset_manifest 实算）

用法（示例）：
  python scripts/s18_demo_convert.py <<'EOF' > /tmp/plan.json
  {"op": "plan"}
  EOF
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from pcbflow import corpus, corpus_convert as cc, corpus_kicad_demo as kcd  # noqa: E402

DATASET = "datasets/kicad-demos-r1"
R1_MANIFEST = REPO / "out" / "v3-tl5" / "dataset-manifest-kicad-demos-r1.json"
RETENTION_LEDGER = (REPO / "out" / "v3-tl5" /
                    "retention-ledger-kicad-demos-r1.json")
R4_JSON = REPO / "out" / "v3-tl5" / "source-research-r4.json"

S18_DATE = "2026-09-05"
R2_TRACK = "tl5-kicad-demos-r2"
PROFILE_PREFIX = "kicaddemo-"
#: 数据集级审计指针（S15 结论；sha 由 plan/manifest 时实测注入）
S15_AUDIT_REL = "out/v3-tl5/kicad-demo-license-audit.json"
S15_LEDGER_REL = "out/v3-tl5/retention-ledger-kicad-demos-r1.json"

BOARD_PRODUCTS = (
    "inputs/board.kicad_pcb", "inputs/stackup.json",
    "inputs/constraints.json", "derived/net-registry.json",
    "derived/feedforward-plan.json", "profile.json", "manifest.json",
)


def _fail(msg: str) -> None:
    print(f"[s18-demo-convert] FAIL: {msg}", file=sys.stderr)
    sys.exit(1)


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def _read_req() -> dict:
    req = json.loads(sys.stdin.read())
    if not isinstance(req, dict) or "op" not in req:
        _fail("stdin request must be a JSON object with 'op'")
    return req


def _emit_json(obj) -> None:
    sys.stdout.write(corpus.dumps_canonical(obj))
    sys.stdout.write("\n")


def _emit_text(text: str) -> None:
    sys.stdout.write(text)


def _load_r1() -> dict:
    return json.loads(R1_MANIFEST.read_text(encoding="utf-8"))


def _dataset_rel_of(demo_id: str, board_file: str) -> str:
    """上游 demos 相对路径 → datasets 留存相对路径（分量安全化同 S15）。"""
    tail = board_file.split("/", 1)[1] if "/" in board_file else board_file
    parts = []
    for comp in tail.split("/"):
        import re
        if re.fullmatch(r"[A-Za-z0-9._+-]+", comp):
            parts.append(comp)
        else:
            s = re.sub(r"[^A-Za-z0-9._+-]+", "_", comp).strip("_")
            if not s:
                _fail(f"unsanitizable component: {comp!r}")
            parts.append(s)
    return f"{DATASET}/raw/{demo_id}/" + "/".join(parts)


def op_plan(req: dict) -> None:
    r1 = _load_r1()
    splits = r1["dataset_splits"]
    role_of = {}
    for role in ("train", "validation", "holdout", "external_eval"):
        for b in splits.get(role, []):
            role_of[b] = role
    audit_sha = _sha256_file(REPO / S15_AUDIT_REL)
    ledger_sha = _sha256_file(REPO / S15_LEDGER_REL)
    boards = []
    for e in kcd.build_demo_audit_ledger(
        [{"demo_id": d, "board_files": bfs}
         for d, bfs in sorted(kcd.BOARD_FILES.items())
         if d not in ("simulation", "stickhub", "cm5_minima")]
    )["retained"]:
        demo_id = e["demo_id"]
        lic = kcd.DIR_LICENSE_ID.get(demo_id, kcd.DEFAULT_DEMO_LICENSE_ID)
        # 主源文件：as_shipped/routed 态；-unrouted 变体为次源（双态板）
        primary = [bf for bf in e["board_files"]
                   if kcd.board_revision(bf) != "unrouted"]
        secondary = [bf for bf in e["board_files"]
                     if kcd.board_revision(bf) == "unrouted"]
        for bf in primary:
            bid = kcd.demo_board_id(demo_id, bf)
            src_rel = _dataset_rel_of(demo_id, bf)
            src_path = REPO / src_rel
            if not src_path.is_file():
                _fail(f"board file missing: {src_rel}")
            slug = bid.replace("/", "-").lower()
            sv = kcd.survey_board_text(
                src_path.read_text(encoding="utf-8"))
            entry = {
                "board_id": bid, "demo_id": demo_id,
                "revision": kcd.board_revision(bf),
                "profile_id": PROFILE_PREFIX + slug,
                "project_id": bid,
                "source_rel": src_rel,
                "source_sha256": _sha256_file(src_path),
                "version_token": sv["version_token"],
                "generator_version": sv["generator_version"],
                "split_role": role_of.get(bid),
                "license_id": lic,
                "license_pointer": {
                    "basis": "S15 audit（结论不重开）",
                    "license_id": lic,
                    "audit_ref": {"path": S15_AUDIT_REL,
                                  "sha256": audit_sha},
                    "ledger_ref": {"path": S15_LEDGER_REL,
                                   "sha256": ledger_sha},
                },
                "secondary_file": None,
            }
            if secondary:
                sbf = secondary[0]
                srel = _dataset_rel_of(demo_id, sbf)
                if not (REPO / srel).is_file():
                    _fail(f"secondary file missing: {srel}")
                ssv = kcd.survey_board_text(
                    (REPO / srel).read_text(encoding="utf-8"))
                entry["secondary_file"] = {
                    "board_file": f"demos/{sbf}",
                    "source_rel": srel,
                    "source_sha256": _sha256_file(REPO / srel),
                    "revision": kcd.board_revision(sbf),
                    "version_token": ssv["version_token"],
                }
            boards.append(entry)
    if len(boards) != 17:
        _fail(f"plan board count {len(boards)} != 17")
    _emit_json({
        "track": R2_TRACK, "declared_date": S18_DATE,
        "version_gate": {"supported": list(cc.K9_SUPPORTED_VERSIONS),
                         "path": cc.K9_CONVERTER_VERSION},
        "r1_manifest_ref": {"path": "out/v3-tl5/dataset-manifest-"
                                    "kicad-demos-r1.json",
                            "sha256": _sha256_file(R1_MANIFEST)},
        "splits_snapshot": {k: r1["dataset_splits"][k]
                            for k in ("train", "validation", "holdout",
                                      "external_eval")},
        "boards": boards,
    })


def _parse_board(entry: dict):
    src = REPO / entry["source_rel"]
    text = src.read_text(encoding="utf-8")
    model = cc.parse_kicad9_board(text)
    return model, text


def op_artifact(req: dict) -> None:
    entry = req["board"]
    model, text = _parse_board(entry)
    crit = cc.derive_critical_nets(model)
    kind = req["artifact"]
    out_root = f"profiles/{entry['profile_id']}"
    if kind == "board":
        _emit_text(cc.normalized_k9_board_text(
            model, source_path=entry["source_rel"],
            source_sha256=entry["source_sha256"]))
        return
    if kind == "stackup":
        obj = cc.build_stackup_obj(
            model, board_id=entry["board_id"],
            source={"path": entry["source_rel"],
                    "sha256": entry["source_sha256"]})
    elif kind == "constraints":
        obj = cc.build_constraints_obj(
            model, project_id=entry["project_id"], crit=crit)
    elif kind == "net_registry":
        obj = cc.build_net_registry_obj(
            model, board_id=entry["board_id"], crit=crit)
    elif kind == "feedforward":
        obj = cc.build_feedforward_obj(
            model, board_id=entry["board_id"], crit=crit)
    elif kind == "profile":
        obj = cc.build_profile_obj(
            model, profile_id=entry["profile_id"],
            project_id=entry["project_id"], crit=crit)
    elif kind == "manifest":
        obj = cc.build_manifest_obj(
            project_id=entry["project_id"],
            profile_id=entry["profile_id"],
            eda_version=(model["generator_tokens"]["generator_version"]
                         or "not_available"),
            critical_nets=crit["critical_nets"],
            dataset_splits=req["splits"],
            output_root=out_root,
            board_id=entry["board_id"],
            dataset_routed_rel=entry["source_rel"],
            drc_baseline_rel=req.get("drc_baseline"))
    else:
        _fail(f"unknown artifact kind: {kind}")
    _emit_json(obj)


def op_audit(req: dict) -> None:
    eu, er = req["board_u"], req["board_r"]
    mu, _ = _parse_board(eu)
    mr, _ = _parse_board(er)
    _emit_json(cc.build_audit_obj(mu, mr, board_id=eu["board_id"]))


def op_graph(req: dict) -> None:
    entry = req["board"]
    _emit_json(cc.build_k9_graph_spec(
        project_id=entry["project_id"], profile_id=entry["profile_id"],
        revision="r1", file_hashes=req["file_hashes"],
        has_audit=req["has_audit"]))


def op_convlog(req: dict) -> None:
    entry = req["board"]
    model, _ = _parse_board(entry)
    model_r = None
    if req.get("board_r"):
        model_r, _ = _parse_board(req["board_r"])
    crit = cc.derive_critical_nets(model)
    _emit_json(cc.build_k9_conversion_log(
        board_id=entry["board_id"], profile_id=entry["profile_id"],
        module_sha256=req["module_sha256"], inputs=req["inputs"],
        outputs=req["outputs"], model=model, model_r=model_r, crit=crit,
        topology_group=cc.topology_group_id(model, crit),
        audit_result=req.get("audit_result"),
        route_check_status=req.get("route_check_status", "not_executed")))


def _collect_items() -> tuple:
    own, other = [], []
    for fp in sorted((REPO / DATASET / "raw").rglob("*.kicad_pcb")):
        rel = fp.relative_to(REPO).as_posix()
        own.append({"library": "kicad-demos-r1",
                    "board_id": rel[len(DATASET) + 5:].rsplit(".", 1)[0],
                    "file_role": "board_file",
                    "text": fp.read_text(encoding="utf-8")})
    for base in ("datasets/pcbbenchmarks-r1", "datasets/pcbench-r1"):
        for fp in sorted((REPO / base).rglob("*.kicad_pcb")):
            rel = fp.relative_to(REPO).as_posix()
            other.append({"library": base.split("/")[-1],
                          "board_id": rel[len("datasets/"):].rsplit(".", 1)[0],
                          "file_role": "board_file",
                          "text": fp.read_text(encoding="utf-8")})
    return own, other


def op_leakage(req: dict) -> None:
    r1 = _load_r1()
    splits = r1["dataset_splits"]
    own, other = _collect_items()
    # 库内：17 板（board_id 维度，主源文件文本）
    content_items, topo_sigs, variant_items = [], [], []
    for b in req["boards"]:
        text = (REPO / b["source_rel"]).read_text(encoding="utf-8")
        content_items.append({"board_id": b["board_id"],
                              "file_role": b["revision"],
                              "content_sha256":
                                  corpus.content_fingerprint(text)})
        sig = kcd.survey_board_text(text)["signature"]
        topo_sigs.append(dict(sig, board_id=b["board_id"]))
        variant_items.append({"board_id": b["board_id"],
                              "project_group": b["demo_id"],
                              "revision_id": b["revision"]})
    board_groups = [(b["board_id"], b["demo_id"]) for b in req["boards"]]
    in_library = corpus.audit_leakage(splits, board_groups, content_items,
                                      variant_items, topo_sigs)
    cross = kcd.audit_cross_library(own, other)
    _emit_json({
        "track": R2_TRACK, "audit_date": S18_DATE,
        "dataset_id": "kicad-demos-r1",
        "relation_to_r1_audit": {
            "note": "r1 审计（leakage-audit-kicad-demos-r1.json）原样保留；"
                    "本审计=S18 重跑（同批 raw 字节零改动）+跨库全量三库",
            "path": "out/v3-tl5/leakage-audit-kicad-demos-r1.json",
            "sha256": _sha256_file(REPO / "out" / "v3-tl5" /
                                   "leakage-audit-kicad-demos-r1.json"),
        },
        "in_library": in_library,
        "cross_library_dedup": cross,
        "result": ("pass" if in_library["result"] == "pass"
                   and cross["content_duplicate_group_count"] == 0
                   else "fail"),
        "denominator_note": f"库内审计=17 板（主源文件）；跨库并集="
                            f"{len(own)} own（kicad-demos-r1 全部 18 板文件）"
                            f"+ {len(other)} other（pcbbenchmarks-r1 4 + "
                            f"pcbench-r1 162）",
    })


def op_manifest(req: dict) -> None:
    r1 = _load_r1()
    per_board = req["per_board"]
    if len(per_board) != 17:
        _fail(f"per_board count {len(per_board)} != 17")
    raw_files = []
    for fp in sorted((REPO / DATASET).rglob("*")):
        if fp.is_file():
            raw_files.append({"path": fp.relative_to(REPO).as_posix(),
                              "sha256": _sha256_file(fp)})
    conv_entries = []
    norm_entries = []
    converted = 0
    for row in per_board:
        if row["conversion_status"] == "converted":
            converted += 1
        conv_entries.append({"board_id": row["board_id"],
                             "path": row["conversion_log_rel"],
                             "sha256": row["conversion_log_sha256"]})
        if row.get("normalized_rel"):
            norm_entries.append({"board_id": row["board_id"],
                                 "path": row["normalized_rel"],
                                 "sha256": row["normalized_sha256"]})
    vt = {}
    for b in req.get("version_tokens", []):
        vt[b] = vt.get(b, 0) + 1
    record = {
        "dataset_id": "kicad-demos-r1",
        "version": "2",
        "source_uri_or_archive_sha256": r1["source_uri_or_archive_sha256"],
        "license": r1["license"],
        "license_scope": r1["license_scope"],
        "redistribution_allowed": r1["redistribution_allowed"],
        "derivative_allowed": r1["derivative_allowed"],
        "attribution": r1["attribution"],
        "collection_date": r1["collection_date"],
        "board_ids": r1["board_ids"],
        "revision_ids": r1["revision_ids"],
        "project_groups": r1["project_groups"],
        "topology_groups": r1["topology_groups"],
        "vendor_groups": r1["vendor_groups"],
        "consent_or_provenance": r1["consent_or_provenance"],
        "conversion_script": {
            "modules": {
                cc.MODULE_NAME: {
                    "role": "KiCad 8.99–10.99 解析路径（k9，版本门显式）/"
                            "规范化板/构件/graph/conversion log（纯函数；"
                            "S18 新增节，既有 KiCad5 路径零改动）",
                    "module_sha256": req["module_sha256"],
                    "converter_version": cc.K9_CONVERTER_VERSION,
                },
                kcd.MODULE_NAME: {
                    "role": "S15 逐 demo 许可分类/审计账本/split/跨库去重"
                            "（纯函数；结论沿用不重开）",
                    "module_sha256": req["kcd_module_sha256"],
                },
            },
            "entry_points": [
                "corpus_convert.parse_kicad9_board",
                "corpus_convert.normalized_k9_board_text",
                "corpus_convert.build_k9_graph_spec",
                "corpus_convert.build_k9_conversion_log",
                "corpus_convert.build_stackup_obj",
                "corpus_convert.build_constraints_obj",
                "corpus_convert.build_net_registry_obj",
                "corpus_convert.build_feedforward_obj",
                "corpus_convert.build_profile_obj",
                "corpus_convert.build_manifest_obj",
            ],
            "replay_contract": "纯函数：输入=datasets 板文件文本+注入 hash；"
                               "输出=规范化板与构件；落盘由编排侧 Bash 重定向"
                               "完成（scripts/s18_demo_convert.py "
                               "stdin→stdout；零子进程/零自身落盘/零网络）",
            "tests": "tests/test_tl5_convert_k9.py",
            "track": R2_TRACK,
        },
        "kicad_version": (
            "mixed KiCad 8.99–10.99（18 板文件 version tokens："
            + "、".join(f"{k}={v}" for k, v in sorted(vt.items()))
            + "）；S18 起转换器 k9 路径覆盖 version tokens "
            + str(list(cc.K9_SUPPORTED_VERSIONS))
            + "（版本门显式；20260206+ 顶层 net 声明取消→nets 由 pad 引用"
              "推导，net_id 结构性不可得如实）"),
        "raw_files": raw_files,
        "normalized_hash": norm_entries,
        "conversion_log": conv_entries,
        "field_missingness": {
            "DRC_baseline": "not_available（S18 未跑 kicad-cli DRC；r1 同）",
            "route_check": "not_executed（S18 范围=转换域扩展；无 kicad-cli "
                           "参考态验证运行；D17 口径不变、TL-5 门不改写）",
            "profile_dirs": "profiles/kicaddemo-*/ 为 S18 新增转换产物"
                            "（不入 TL-5 门 37 profile 分母、不回填 r1）；"
                            "route-check.json 段声明与 derived/audit.json "
                            "（双态板除外）不生成=如实",
            "audit_pair_check": "仅 multichannel/multichannel_mixer 有双态"
                                "对（-unrouted 文件自带 140 segment/19 via"
                                "→unrouted_state_pristine=fail 如实入账；"
                                "同板身份检查 pass）；其余 16 板单态 "
                                "as_shipped——audit 构件不生成（不虚构）",
            "net_ids_pad_derived": "pic_programmer（20260206）与 constraints"
                                   "（20260624）顶层 net 声明在该格式取消；"
                                   "nets 由 pad 引用推导（constraints 板 0 "
                                   "net/0 footprint=退化板如实）",
            "conversion_domain_coverage": (
                f"转换域覆盖 83→{83 + converted} 板（37 profile 域外新增 "
                f"{converted} 板的转换产物）；全局分母仍=100 板"
                "（pcbbenchmarks 2+pcbench 81+kicad-demos 17）；"
                "新产物不入 TL-5 门分母（红线 6）"),
            "dataset_splits.external_eval": "空（无外部评测源）",
            "dataset_splits.validation": "空（15 demo 简分，同 r1）",
            "excluded_boards_full_ledger": r1["excluded_boards"],
        },
        "DRC_baseline": "not_available（S18 未跑 kicad-cli DRC）",
        "dataset_splits": r1["dataset_splits"],
        "excluded_boards": r1["excluded_boards"],
        "source_research_ref": {
            "path": "out/v3-tl5/source-research-r4.json",
            "sha256": _sha256_file(R4_JSON),
            "note": "license 结论沿用 S15 审计（不重开）",
        },
        "relation_to_v1": {
            "note": "r1 manifest（version 1）一字不动；本文件=version 2"
                    "（版本递增；转换域扩展记录）",
            "path": "out/v3-tl5/dataset-manifest-kicad-demos-r1.json",
            "sha256": _sha256_file(R1_MANIFEST),
            "manifest_sha256_field": r1["manifest_sha256"],
        },
    }
    manifest = corpus.build_dataset_manifest(record)
    _emit_json(manifest)


def main() -> None:
    req = _read_req()
    op = req["op"]
    handlers = {
        "plan": op_plan, "artifact": op_artifact, "audit": op_audit,
        "graph": op_graph, "convlog": op_convlog, "leakage": op_leakage,
        "manifest": op_manifest,
    }
    if op not in handlers:
        _fail(f"unknown op: {op}")
    handlers[op](req)


if __name__ == "__main__":
    main()
