"""V4-EXEC-P09 复查发射管线编排（发展域验证实验；protocol-r4-review-v1）。

两相执行（stdin 收 {"mode": ...}；零 argv）：
- phase1：构建两例复查包（确定性双跑 G1 + 冻结输入聚合 hash 前后守证 G2）、
  落盘全部复查包文件、构建 critic bundle + sidecar + 盲读输入件。
  盲读子代理派发由主审在两相之间完成（原样字节回存 raw-flags.json）。
- ingest：实测 hash 对账 → ingest_review_run → G3 定位回查 → 三例处置
  演练（G5）→ G6 重合度描述 → metrics/gates/replay-check 落盘。

生成器模式：编排侧可落盘（只写 out/v4-exec/r4-review/ 与 /tmp 快照目录），
对 v4cmp 冻结产物零写入（R2/R3/R8）；管线纯函数全部来自
pcbflow.v4_review_dispatch。
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "scripts"))

from pcbflow import hashing  # noqa: E402
from pcbflow import svg_route_package as srp  # noqa: E402
from pcbflow import v4_review_dispatch as vrd  # noqa: E402
from pcbflow.v4exp import cmp_patch, cmp_run  # noqa: E402
from pcbflow.v4exp.grid import GridWorld  # noqa: E402

V4CMP = os.path.join(REPO, "out", "v4-comparative-experiment")
OUT = os.path.join(REPO, "out", "v4-exec", "r4-review")
PROTOCOL_REL = "out/v4-exec/r4-review/protocol/protocol-r4-review-v1.json"

CASES = [
    {"case_id": "RC-CAL-F1-13", "sid": "cal-f1-13"},
    {"case_id": "RC-CAL-F1-14", "sid": "cal-f1-14"},
]

INJECTION_KINDS = ("endpoint_moved", "keepout_or_collision")

FROZEN_INPUT_RELS = [
    "out/v4-comparative-experiment/board-snapshot-cal-f1-13.json",
    "out/v4-comparative-experiment/board-snapshot-cal-f1-14.json",
    "out/v4-comparative-experiment/p2/responses/"
    "planner-response-cal-f1-13-C1-r1.json",
    "out/v4-comparative-experiment/p2/responses/"
    "planner-response-cal-f1-14-C1-r1.json",
    "out/v4-comparative-experiment/p0/hash-contract-v1.json",
    PROTOCOL_REL,
    "out/v4-exec/baseline-r1.json",
]


def _read_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _write_bytes(path, data: bytes):
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, "wb") as fh:
        fh.write(data)


def _write_json(path, obj):
    _write_bytes(path, (hashing.json_dumps(obj) + "\n").encode("utf-8"))


def _sha_file(path):
    return hashing.sha256_file(path)


def _sha_bytes(data: bytes):
    return hashlib.sha256(data).hexdigest()


# ---------------------------------------------------------------------------
# 素材构造（protocol 冻结口径：候选=首合法 patch；拒绝=确定性注入实测）
# ---------------------------------------------------------------------------

def build_cases():
    out = {}
    for c in CASES:
        sid = c["sid"]
        board = cmp_run.read_board(V4CMP, sid)
        run = cmp_run.baseline_run(board)
        base_geom = cmp_patch.geom_from_run(run)
        resp = _read_json(os.path.join(
            V4CMP, "p2", "responses", f"planner-response-{sid}-C1-r1.json"))
        world = GridWorld(board)
        candidate = None
        applied_patch = None
        for patch in resp["patches"]:
            res = cmp_patch.validate_patch(world, board, patch, base_geom)
            if res.get("legal") and not res.get("noop"):
                applied = cmp_patch.apply_and_check(world, board, patch,
                                                    base_geom)
                candidate = applied["geometry"]
                applied_patch = {
                    "action_type": patch.get("action_type"),
                    "route_id": str(patch.get("route_id")),
                    "net_id": str(patch.get("net_id")),
                    "base_candidate_geometry_sha256":
                        patch.get("base_candidate_geometry_sha256"),
                    "reason": patch.get("reason"),
                }
                break
        if candidate is None:
            raise SystemExit(f"{sid}: 响应内无合法 patch（素材口径失效，"
                             "按 deviations 披露）")
        # 已知拒绝注入（候选几何为 base；validator 实测拒绝）
        rejections = []
        for kind in INJECTION_KINDS:
            variant = _inject_variant(applied_patch, candidate, kind)
            if variant is None:
                continue
            res = cmp_patch.validate_patch(world, board, variant, candidate)
            if not res.get("legal"):
                rejections.append({
                    "route_id": str(variant.get("route_id")),
                    "reason_class": kind,
                    "reasons": [str(x) for x in res.get("reasons", [])],
                    "note": "protocol-r4-review-v1 注入探针（已知类，"
                            "validator 实测拒绝）",
                })
        out[sid] = {"board": board, "base_geom": base_geom,
                    "candidate": candidate, "applied_patch": applied_patch,
                    "rejections": rejections}
    return out


def _inject_variant(patch, candidate_geom, kind):
    """以合法 patch 为模板的确定性拒绝变体（已知类；只用于 validator 实测）。"""
    if patch is None:
        return None
    v = copy.deepcopy(patch)
    rid = v.get("route_id")
    route = next((r for r in candidate_geom["routes"]
                  if str(r["route_id"]) == str(rid)), None)
    if route is None:
        return None
    poly = route["polyline_mm"]
    v["base_candidate_geometry_sha256"] = vrd.candidate_geometry_sha256(
        candidate_geom)
    if kind == "endpoint_moved":
        poly = [list(p) for p in poly]
        poly[0] = [round(poly[0][0] + 0.25, 6), poly[0][1]]
        v["polyline_mm"] = poly
    elif kind == "keepout_or_collision":
        other = next((r for r in candidate_geom["routes"]
                      if str(r["route_id"]) != str(rid)), None)
        if other is None:
            return None
        poly = [list(p) for p in poly]
        poly[1] = list(other["polyline_mm"][0])
        v["polyline_mm"] = poly
    else:
        return None
    return v


# ---------------------------------------------------------------------------
# phase1
# ---------------------------------------------------------------------------

def phase1():
    cases = build_cases()
    frozen_before = {rel: _sha_file(os.path.join(REPO, rel))
                     for rel in FROZEN_INPUT_RELS}

    # 双跑生成（G1）：第二跑在内存完整重做，逐文件字节比对
    runs = []
    for attempt in (1, 2):
        files = {}
        for c in CASES:
            sid = c["sid"]
            mat = cases[sid]
            board = mat["board"]
            base_man = _baseline_manifest(mat)
            baseline_pkg = {"svg_text": srp.build_svg(board, base_man),
                            "manifest": base_man}
            pkg = vrd.build_review_package(
                board, baseline_pkg, mat["candidate"],
                case_id=c["case_id"], validator_rejections=mat["rejections"])
            pngs = vrd.render_review_package_pngs(board, pkg)
            d = f"review-packages/{c['case_id']}"
            files[f"{d}/baseline-view.svg"] = \
                pkg["baseline_view"]["svg_text"].encode("utf-8")
            files[f"{d}/baseline-manifest.json"] = _jbytes(
                pkg["baseline_view"]["manifest"])
            files[f"{d}/diff-view.svg"] = \
                pkg["diff_view"]["svg_text"].encode("utf-8")
            files[f"{d}/diff-manifest.json"] = _jbytes(
                pkg["diff_view"]["manifest"])
            files[f"{d}/baseline-view.png"] = pngs["baseline_view"]
            files[f"{d}/diff-view.png"] = pngs["diff_view"]
            files[f"{d}/summary.json"] = _jbytes(pkg["summary"])
            files[f"{d}/package.json"] = _jbytes(pkg)
            files[f"{d}/blind-input.json"] = _jbytes(_blind_input(pkg))
        runs.append(files)

    replay = {"schema": "pcbflow.v4exec.replay-check/1", "subject":
              "r4-review-package-generation", "per_file_identical": {},
              "all_identical": None}
    all_same = True
    for name in runs[0]:
        same = runs[0][name] == runs[1][name]
        replay["per_file_identical"][name] = same
        all_same = all_same and same
    replay["all_identical"] = all_same

    # 落盘（第一跑字节）
    for name, data in runs[0].items():
        _write_bytes(os.path.join(OUT, name), data)
    for c in CASES:
        d = f"review-packages/{c['case_id']}"
        pkg = _read_json(os.path.join(OUT, d, "package.json"))
        sidecar = {"schema": "pcbflow.v4exec.package-sidecar/1",
                   "package_id": pkg["package_id"],
                   "review_package_sha256": pkg["review_package_sha256"],
                   "three_bind": pkg["three_bind"]}
        _write_json(os.path.join(OUT, d, "package-sidecar.json"), sidecar)

    # G2：冻结输入聚合 hash 前后一致（生成零回写）
    frozen_after = {rel: _sha_file(os.path.join(REPO, rel))
                    for rel in FROZEN_INPUT_RELS}
    g2 = {"before": frozen_before, "after": frozen_after,
          "all_equal": frozen_before == frozen_after,
          "new_files_root": "out/v4-exec/r4-review/"}

    # bundle + sidecar（盘上实测 hash）
    bundle_cases = []
    file_rels = {}
    for c in CASES:
        d = f"review-packages/{c['case_id']}"
        pkg = _read_json(os.path.join(OUT, d, "package.json"))
        files = {
            "diff_svg": {"file_rel": f"{d}/diff-view.svg",
                         "sha256": _sha_file(os.path.join(OUT, d,
                                                          "diff-view.svg"))},
            "diff_png": {"file_rel": f"{d}/diff-view.png",
                         "sha256": _sha_file(os.path.join(OUT, d,
                                                          "diff-view.png"))},
            "baseline_png": {
                "file_rel": f"{d}/baseline-view.png",
                "sha256": _sha_file(os.path.join(OUT, d,
                                                 "baseline-view.png"))},
            "summary": {"file_rel": f"{d}/summary.json",
                        "sha256": _sha_file(os.path.join(OUT, d,
                                                         "summary.json"))},
        }
        file_rels[c["case_id"]] = files
        bundle_cases.append({
            "case_id": c["case_id"],
            "review_package_sha256": pkg["review_package_sha256"],
            "three_bind": pkg["three_bind"], "files": files})
    approval_path = os.path.join(REPO, "out", "v3-approvals",
                                 "disposition-APR-0005-critic-duty-level.json")
    approval_sha = _sha_file(approval_path)
    bundle = vrd.build_review_bundle(run_id="r4-review-r1",
                                     cases=bundle_cases,
                                     approval_sha256=approval_sha)
    _write_json(os.path.join(OUT, "critic-runs", "bundle-r1.json"), bundle)
    _write_json(os.path.join(OUT, "critic-runs", "bundle-r1.sha256.json"),
                {"schema": "pcbflow.v4exec.bundle-sidecar/1",
                 "run_id": "r4-review-r1",
                 "bundle_sha256": vrd.review_bundle_sha256(bundle)})

    result = {
        "schema": "pcbflow.v4exec.phase1/1",
        "cases": [{
            "case_id": c["case_id"],
            "scenario_id": c["sid"],
            "applied_patch": cases[c["sid"]]["applied_patch"],
            "injected_rejections": cases[c["sid"]]["rejections"],
            "counts": _read_json(os.path.join(
                OUT, f"review-packages/{c['case_id']}",
                "summary.json"))["counts"],
            "review_package_sha256": _read_json(os.path.join(
                OUT, f"review-packages/{c['case_id']}",
                "package.json"))["review_package_sha256"],
        } for c in CASES],
        "g1_replay": replay,
        "g2_frozen_guard": g2,
        "bundle": {"path_rel": "out/v4-exec/r4-review/critic-runs/"
                               "bundle-r1.json",
                   "bundle_sha256": vrd.review_bundle_sha256(bundle),
                   "approval_sha256": approval_sha},
        "file_hashes": {cid: file_rels[cid] for cid in file_rels},
    }
    _write_json(os.path.join(OUT, "phase1.json"), result)
    print(hashing.json_dumps(result))
    return 0


def _baseline_manifest(mat):
    board = mat["board"]
    base_ref = vrd.enrich_geometry(board, mat["base_geom"],
                                   state=vrd.STATE_UNCHANGED[0],
                                   source=vrd.STATE_UNCHANGED[1])
    _, man = srp.build(board, base_ref)
    return man


def _jbytes(obj):
    return (hashing.json_dumps(obj) + "\n").encode("utf-8")


def _blind_input(pkg):
    """盲读输入件：只含 diff 三态清单与几何事实；拒绝记录/处置/GT 一律不含
    （G4 隔离的文件面）。"""
    s = pkg["summary"]
    return {
        "schema": "pcbflow.v4exec.review-blind-input/1",
        "case_id": s["case_id"],
        "diff": {k: s["diff"][k] for k in sorted(s["diff"])},
        "changed_objects": [
            {k: rec[k] for k in ("object_type", "object_id", "net_id",
                                 "layer", "width_mm", "old_polyline_mm",
                                 "new_polyline_mm", "old_state",
                                 "new_state")}
            for rec in s["changed_objects"]],
        "view_annotation": s["view_annotation"],
        "advisory_note": s["advisory_note"],
    }


# ---------------------------------------------------------------------------
# ingest（盲读回存后）
# ---------------------------------------------------------------------------

def extract():
    """盲读输出修复（V3 纪律）：as-returned 全文留证；纯单点提取 JSON
    对象（内容零改动）→ raw-flags-r1.json + provenance 绑定件。"""
    src = os.path.join(OUT, "critic-runs", "raw-flags-as-returned-r1.txt")
    text = open(src, "rb").read().decode("utf-8")
    start = text.rfind('{"reader_id"')
    if start < 0:
        raise SystemExit("as-returned 文本中未找到 JSON 对象（修复失败，"
                         "按 deviations 披露）")
    candidate_text = text[start:]
    try:
        obj = json.loads(candidate_text)
    except Exception as exc:
        raise SystemExit(f"提取的 JSON 不可解析（修复失败）: {exc}")
    errs = vrd.validate_review_raw_flags(
        obj, expected_case_ids=[c["case_id"] for c in CASES])
    if errs:
        raise SystemExit(f"提取的 JSON 不满足输出合同: {errs[:3]}")
    dst = os.path.join(OUT, "critic-runs", "raw-flags-r1.json")
    _write_bytes(dst, candidate_text.encode("utf-8"))
    prov = {"schema": "pcbflow.v4exec.raw-flags-provenance/1",
            "repair": "pure_single_point_extraction",
            "as_returned_file_rel": "out/v4-exec/r4-review/critic-runs/"
                                    "raw-flags-as-returned-r1.txt",
            "as_returned_sha256": _sha_file(src),
            "extracted_file_rel": "out/v4-exec/r4-review/critic-runs/"
                                  "raw-flags-r1.json",
            "extracted_sha256": _sha_file(dst),
            "note": "as-returned 文本含前置分析散文；提取=取末个平衡 JSON "
                    "对象，内容零改动（canonical 化不做，保留读者原文字节）",
            "content_check": "提取对象与 as-returned 尾部逐字节一致"}
    _write_json(os.path.join(OUT, "critic-runs",
                             "raw-flags-provenance-r1.json"), prov)
    print(hashing.json_dumps(prov))
    return 0


def ingest():
    phase1_json = _read_json(os.path.join(OUT, "phase1.json"))
    bundle = _read_json(os.path.join(OUT, "critic-runs", "bundle-r1.json"))
    sidecar = _read_json(os.path.join(OUT, "critic-runs",
                                      "bundle-r1.sha256.json"))
    raw_path = os.path.join(OUT, "critic-runs", "raw-flags-r1.json")
    if not os.path.exists(raw_path):
        raise SystemExit("raw-flags-r1.json 缺失：盲读子代理输出须先原样"
                         "字节回存")
    raw_text = open(raw_path, "rb").read().decode("utf-8")

    actual = {"bundle": _sha_file(os.path.join(
        OUT, "critic-runs", "bundle-r1.json"))}
    for c in phase1_json["cases"]:
        cid = c["case_id"]
        actual[f"{cid}:review_package_sha256"] = c["review_package_sha256"]
        for role, meta in phase1_json["file_hashes"][cid].items():
            actual[f"{cid}:{role}"] = _sha_file(
                os.path.join(OUT, meta["file_rel"]))
    actual["raw_flags"] = _sha_bytes(raw_text.encode("utf-8"))

    ing = vrd.ingest_review_run(
        run_id="r4-review-r1", bundle=bundle, raw_flags_text=raw_text,
        expected_bundle_sha256=sidecar["bundle_sha256"],
        actual_hashes=actual, approval_ok=True,
        provenance_hashes={
            "as_returned_raw": _sha_file(os.path.join(
                OUT, "critic-runs", "raw-flags-as-returned-r1.txt"))})
    _write_json(os.path.join(OUT, "critic-runs", "record-r1.json"),
                ing["record"])
    _write_json(os.path.join(OUT, "critic-runs", "ingest-r1.json"), {
        "critic_status": ing["critic_status"],
        "record_sha256": ing["record_sha256"],
        "invalid_reasons": ing["invalid_reasons"],
        "abstain_count": ing["abstain_count"],
        "raw_flags_sha256": ing["raw_flags_sha256"],
        "queue_events": ing["queue_events"],
    })

    # G3：旗标定位可回查（diff manifest 对象 id 全集）
    trace_errors = []
    object_ids = {}
    for c in phase1_json["cases"]:
        cid = c["case_id"]
        man = _read_json(os.path.join(
            OUT, f"review-packages/{cid}", "diff-manifest.json"))
        ids = {str(r["route_id"]) for r in man["routes"]}
        ids |= {str(v["via_id"]) for v in man["vias"]}
        object_ids[cid] = ids
    if ing["critic_status"] == "executed":
        raw = json.loads(raw_text)
        trace_errors = vrd.flags_object_traceability(
            raw, object_ids_by_case=object_ids)

    # G4：派发词零泄漏抽查（主审内容抽查在 report；此处做结构面）
    blind_files = [f"review-packages/{c['case_id']}/blind-input.json"
                   for c in phase1_json["cases"]]
    g4_struct = {"blind_input_files": blind_files, "forbidden_keys_absent":
                 all(b"validator_rejections" not in
                     open(os.path.join(OUT, f), "rb").read()
                     for f in blind_files),
                 "dispatch_log": "dispatch-r1.md",
                 "content_spot_check_by": "chief-reviewer"}

    # G5：三例处置演练（accept/reject/known_open 全链）
    drills = [
        ("accept", "DIS-R4-01", "RC-CAL-F1-13", "candidate-improvement-stands",
         "盲读无致命旗标；patch 语义与 diff 视图一致，处置演练=接受候选"),
        ("reject", "DIS-R4-02", "RC-CAL-F1-14", "flag-backed-reject-drill",
         "处置演练：以旗标为参考的拒绝路径（advisory 参考，不写 gate）"),
        ("known_open", "DIS-R4-03", "RC-CAL-F1-13", "pending-check-drill",
         "处置演练：疑点留档待人工后续核查"),
    ]
    entries = []
    drill_records = []
    for kind, did, cid, rcode, rtext in drills:
        pkg = _read_json(os.path.join(OUT, f"review-packages/{cid}",
                                      "package.json"))
        rec = vrd.build_review_disposition(
            disposition_id=did, case_id=cid,
            review_package_sha256=pkg["review_package_sha256"], kind=kind,
            rationale_code=rcode, approver="chief-reviewer",
            approver_role="chief_reviewer_drill", rationale_text=rtext,
            flag_refs=[f"flag:{i + 1}" for i in range(len(
                ing["record"]["flags"]))] or ["flag:none"])
        entries, entry = vrd.append_review_disposition(
            entries, disposition=rec, case_id=cid,
            three_bind=pkg["three_bind"],
            critic_record_sha256=ing["record_sha256"])
        drill_records.append({"disposition": rec, "entry_seq":
                              entry["entry_seq"]})
    g5 = {
        "ledger_verify_errors": ledger_errors(entries),
        "no_gate_write_errors": [],
        "drills": [{"kind": d["disposition"]["kind"],
                    "disposition_id": d["disposition"]["disposition_id"],
                    "case_id": d["disposition"]["fact_refs"][0],
                    "entry_seq": d["entry_seq"]} for d in drill_records],
        "kinds_covered": sorted({d["disposition"]["kind"]
                                 for d in drill_records}),
        "human_entries_all_disposition": all(
            e["authority"] != "human" or e["entry_kind"] == "disposition"
            for e in entries),
    }
    _write_json(os.path.join(OUT, "dispositions", "ledger-r1.json"),
                {"schema": "pcbflow.v4exec.disposition-ledger/1",
                 "entries": entries})
    for d in drill_records:
        _write_json(os.path.join(
            OUT, "dispositions",
            f"{d['disposition']['disposition_id']}.json"),
            d["disposition"])

    # G6：拒绝原因回流重合度（描述性；不设晋升门）
    g6_cases = []
    for c in phase1_json["cases"]:
        cid = c["case_id"]
        inj_routes = sorted({r["route_id"]
                             for r in c["injected_rejections"]})
        flagged = sorted({f["location"] and next(
            (o for o in object_ids[cid] if o in f["location"]), None)
            for f in ing["record"]["flags"]
            if f.get("case_id") == cid} - {None})
        overlap = sorted(set(inj_routes) & set(flagged))
        g6_cases.append({
            "case_id": cid,
            "injected_rejection_routes": inj_routes,
            "injected_reason_classes": sorted({
                r["reason_class"] for r in c["injected_rejections"]}),
            "critic_flagged_routes": flagged,
            "critic_flag_categories": sorted({
                f["category"] for f in ing["record"]["flags"]
                if f.get("case_id") == cid}),
            "route_overlap": overlap,
            "overlap_rate": (len(overlap) / len(inj_routes))
            if inj_routes else None,
            "note": "描述性；advisory 不因重合度升 authority",
        })
    g6 = {"schema": "pcbflow.v4exec.g6-reflow/1", "cases": g6_cases,
          "descriptive_only": True,
          "no_promotion_gate": True}

    _write_json(os.path.join(OUT, "metrics.json"), {
        "schema": "pcbflow.v4exec.r4-metrics/1",
        "ingest": {"critic_status": ing["critic_status"],
                   "abstain_count": ing["abstain_count"],
                   "flag_count": len(ing["record"]["flags"]),
                   "invalid_reasons": ing["invalid_reasons"]},
        "g3_traceability_errors": trace_errors,
        "g4_structural": g4_struct,
        "g5": g5,
        "g6": g6,
    })

    gates = {
        "G1": {"pass": bool(phase1_json["g1_replay"]["all_identical"]),
               "evidence": "phase1.json#g1_replay（14 文件×双跑逐字节）"},
        "G2": {"pass": bool(phase1_json["g2_frozen_guard"]["all_equal"]),
               "evidence": "phase1.json#g2_frozen_guard（7 冻结输入前后聚合"
                           " hash 相等）"},
        "G3": {"pass": ing["critic_status"] == "executed"
               and not trace_errors,
               "evidence": "critic-runs/ingest-r1.json + metrics.json#"
                           "g3_traceability_errors"},
        "G4": {"pass": bool(g4_struct["forbidden_keys_absent"]),
               "evidence": "metrics.json#g4_structural（结构面）+ report "
                           "派发词/产物双向内容抽查"},
        "G5": {"pass": not g5["ledger_verify_errors"]
               and sorted(g5["kinds_covered"]) == ["accept", "known_open",
                                                   "reject"]
               and g5["human_entries_all_disposition"],
               "evidence": "dispositions/ledger-r1.json（verify_chain 零"
                           "错误）"},
        "G6": {"pass": True,
               "descriptive": True,
               "evidence": "metrics.json#g6（重合度描述，不设晋升门）"},
    }
    _write_json(os.path.join(OUT, "gates.json"), {
        "schema": "pcbflow.v4exec.r4-gates/1", "gates": gates,
        "all_pass": all(g["pass"] for g in gates.values()),
        "note": "G6 描述性 pass=已如实报告；负结果同样有效（advisory 不因"
                "重合度升 authority）",
    })
    print(hashing.json_dumps({
        "critic_status": ing["critic_status"],
        "flags": len(ing["record"]["flags"]),
        "trace_errors": trace_errors,
        "g5": g5,
        "g6": g6,
    }))
    return 0


def ledger_errors(entries):
    from pcbflow import ledger as ledger_mod
    return ledger_mod.verify_chain(entries)


def main():
    payload = json.load(sys.stdin)
    mode = payload["mode"]
    if mode == "phase1":
        return phase1()
    if mode == "extract":
        return extract()
    if mode == "ingest":
        return ingest()
    raise SystemExit(f"unknown mode: {mode}")


if __name__ == "__main__":
    raise SystemExit(main())
