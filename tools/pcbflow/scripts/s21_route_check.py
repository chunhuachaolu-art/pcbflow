#!/usr/bin/env python
"""S21-K9-ROUTE-CHECK 编排：KiCad 8.99–10.99 demo 板 17 板 route/check 参考
态验证（批 k9-route-check-batch-r1）。

编排侧职责（库侧 pcbflow/check_stage.py 与 pcbflow/corpus_convert.py k9 路径
保持纯函数零落盘；pcbflow/ 既有模块零改动）。纪律（S21 红线）：本脚本
stdin→stdout——请求经 stdin JSON 传入，产物一律写 stdout（canonical JSON）；
盘上落盘全部由 Bash 重定向完成；本脚本零写盘、零子进程、零网络、零
wall-clock（S21_DATE=声明常量）、零主机路径（一律仓库相对 POSIX）。

只读输入：datasets/kicad-demos-r1/（字节读）、profiles/kicaddemo-*/、
out/v3-tl5/{dataset-manifest-kicad-demos-r2.json,
conversion-log-kicad-demos-r2-*.json}、toolchain_lock.json。

ops（stdin JSON 的 "op" 键分派）：
  plan     {} → 17 板验证计划（board_id/profile_id/split_role/version_token/
                  source_rel/sha256_before_drc/conversion_log 与 normalized
                  绑定；盘上 hash 实测=byte 口径 sha256_file）
  baseline {board} → 单板 DRC baseline 记录（staging 逐字节断言+前后 hash
                  分记+双 severity DRC 摘要+D19(b) 类双运行稳定性登记）
  verify   {board} → 单板 S18 转换产物一致性验证（计数对账+byte-exact 重放
                  +log/manifest hash 链绑定）——verdict=「转换复现参考态」，
                  非板干净（参考态自带违例不构成 fail，D17 非判罚口径）
  summary  {plan_rel?} → 批汇总（分布/异常/上游实况登记/语义注记）

kicad-cli 10.0.5 调用与 staging 拷贝全部由 Bash 侧完成（本脚本只读其产物
JSON 与实测 hash）；DRC 口径：批门=severity-error、终检=severity-all、
refill=不填区（as-shipped 区填充原样；未传 --refill-zones/--save-board）、
staging 隔离运行（kicad-cli 不触 datasets/ 路径）。

口径边界（D17，本批=补充证据层）：route/check 参考态验证，不是布线生成
能力；kicad-cli 唯一 DRC authority；本批产物不入 TL-5 门分母（37 profile
不变）、不回填 r2 manifest、不改 TL-5-G。
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from pcbflow import check_stage, corpus_convert as cc, hashing  # noqa: E402
from pcbflow import sexpr_min  # noqa: E402

S21_DATE = "2026-09-05"  # 人工会话声明日期（非 wall-clock）
BATCH_ID = "k9-route-check-batch-r1"
TRACK = "tl5-k9-route-check-r1"
MODULE_NAME = "scripts.s21_route_check"

R2_MANIFEST_REL = "out/v3-tl5/dataset-manifest-kicad-demos-r2.json"
R1_MANIFEST_REL = "out/v3-tl5/dataset-manifest-kicad-demos-r1.json"
PLAN_REL_DEFAULT = "out/v3-tl5/k9-route-check-batch-r1/plan.json"

#: kicad-cli 版本（声明常量；实况以 DRC JSON kicad_version 字段复核）
KICAD_CLI_DECLARED_VERSION = "10.0.5"

#: DRC 双 severity 口径（profile.kicad_cli 合同同构）
SEVERITY_BATCH = "severity-error"
SEVERITY_FINAL = "severity-all"

#: refill 口径显式：as-shipped 参考态不填区（未传 --refill-zones/
#: --save-board——填区会改写参考态区填充，违背 as-shipped 事实源语义）
REFILL_MODE = ("not_refilled（未传 --refill-zones/--save-board；"
               "as-shipped 参考态区填充原样）")

D17_NOTE = (
    "route/check 段=参考 routed 态验证口径（D17）：连通性 authority=kicad-cli"
    " DRC unconnected_items/连通类违例 + DRC 双 severity 计数；本批验证的是"
    "「S18 k9 转换产物复现原始板参考态」，不是板干净——参考态自带违例如实"
    "计数登记（S10 先例 fail-closed），不构成 fail、非判罚")

VERIFICATION_QUESTION = (
    "S18 转换产物（normalized/profile 构件/conversion log）是否与 datasets "
    "原始板参考态一致复现：计数对账一致+byte-exact 重放+hash 链绑定=pass，"
    "不一致=fail 带差值证据；禁凑数")

_HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
_GEOM_RE = re.compile(r"segments=(\d+) vias=(\d+) arcs=(\d+)")
_ZONE_RE = re.compile(r"zones=(\d+)")


def _fail(msg: str) -> None:
    print(f"[s21-route-check] FAIL: {msg}", file=sys.stderr)
    sys.exit(1)


def _read_req() -> dict:
    req = json.loads(sys.stdin.read())
    if not isinstance(req, dict) or "op" not in req:
        _fail("stdin request must be a JSON object with 'op'")
    return req


def _emit_json(obj) -> None:
    sys.stdout.write(hashing.json_dumps(obj))
    sys.stdout.write("\n")


def _sha_file(rel: str) -> str:
    _require_repo_relative(rel, "path")
    return hashing.sha256_file(str(REPO / rel))


def _require_repo_relative(path: str, what: str) -> str:
    """仓库相对 POSIX 路径强制（禁主机形态；红线同 check_stage）。"""
    if not isinstance(path, str) or "\\" in path or re.match(
            r"^[A-Za-z]:", path) or path.startswith("/"):
        raise ValueError(f"{what}: host/absolute path forbidden: {path!r}")
    return path


def _read_text_raw(rel: str) -> str:
    """字节读+utf-8 解码（无换行归一；S12 先例写法）。"""
    _require_repo_relative(rel, "path")
    return (REPO / rel).read_bytes().decode("utf-8")


def _read_text_optional(rel: str):
    """同 _read_text_raw，但文件不在场返回 None（DRC JSON 缺失=fail-closed
    登记，不崩溃、不虚构）。"""
    _require_repo_relative(rel, "path")
    p = REPO / rel
    return p.read_bytes().decode("utf-8") if p.is_file() else None


def _read_json(rel: str):
    _require_repo_relative(rel, "path")
    return json.loads((REPO / rel).read_bytes().decode("utf-8"))


# ---------------------------------------------------------------------------
# 纯函数：参考态计数 / 规范化板计数 / 一致性判定（可测）
# ---------------------------------------------------------------------------

def reference_counts_from_model(model: dict) -> dict:
    """parse_kicad9_board 模型 → 参考态一阶计数（纯函数）。"""
    per_ref: dict = {}
    pad_net_names: list = []
    pads_without_net = 0
    for m in model["modules"]:
        per_ref[m["ref"]] = per_ref.get(m["ref"], 0)
        for p in m["pads"]:
            per_ref[m["ref"]] += 1
            if p["net"] is None:
                pads_without_net += 1
            else:
                pad_net_names.append(p["net"]["name"])
    return {
        "net_names": sorted(n["name"] for n in model["nets"]),
        "net_count": len(model["nets"]),
        "footprint_refs": sorted(per_ref),
        "footprint_count": len(model["modules"]),
        "pad_count_by_ref": dict(sorted(per_ref.items())),
        "pad_total": sum(per_ref.values()),
        "pad_net_names": sorted(pad_net_names),
        "pads_without_net": pads_without_net,
        "geometry": {"segments": model["segment_count"],
                     "vias": model["via_count"],
                     "arcs": model["arc_count"],
                     "zones": model["zone_count"]},
    }


def parse_normalized_counts(text: str) -> dict:
    """S18 规范化板文本（pcbflow k9 方言）→ 一阶计数（纯函数）。

    独立解析路径（sexpr_min 直读盘上规范化板，不经 corpus_convert 装配
    函数）——与参考态计数对账的第二源。解析失败 fail-closed。
    """
    top = sexpr_min.parse(text)
    roots = [n for n in top if isinstance(n, list) and n and n[0]
             == "kicad_pcb"]
    if len(roots) != 1:
        raise ValueError(f"expect exactly one kicad_pcb root, got "
                         f"{len(roots)}")
    root = roots[0]
    net_names: list = []
    net_ids: list = []
    per_ref: dict = {}
    pad_net_names: list = []
    pads_without_net = 0
    for c in root[1:]:
        if not isinstance(c, list) or not c:
            continue
        if c[0] == "net":
            strs = [t for t in c[1:] if isinstance(t, str)]
            if len(strs) == 2 and strs[0].isdigit():
                net_ids.append(int(strs[0]))
                net_names.append(strs[1])
            elif len(strs) == 1:
                net_names.append(strs[0])
            else:
                raise ValueError(f"normalized net node malformed: {c!r}")
        elif c[0] == "footprint":
            if len(c) < 2 or not isinstance(c[1], str):
                raise ValueError(f"normalized footprint without ref: {c!r}")
            ref = c[1]
            n_pads = 0
            for p in sexpr_min.find_all(c, "pad"):
                n_pads += 1
                nn = sexpr_min.find_first(p, "net")
                if nn is None or len(nn) < 2:
                    pads_without_net += 1
                else:
                    strs = [t for t in nn[1:] if isinstance(t, str)]
                    if not strs:
                        raise ValueError(f"pad net node malformed: {nn!r}")
                    pad_net_names.append(strs[-1])
            per_ref[ref] = per_ref.get(ref, 0) + n_pads
    return {
        "net_names": sorted(net_names),
        "net_ids": sorted(net_ids),
        "net_count": len(net_names),
        "footprint_refs": sorted(per_ref),
        "footprint_count": len(per_ref),
        "pad_count_by_ref": dict(sorted(per_ref.items())),
        "pad_total": sum(per_ref.values()),
        "pad_net_names": sorted(pad_net_names),
        "pads_without_net": pads_without_net,
    }


def _multiset_diff(a: list, b: list) -> dict:
    """a−b 与 b−a 多重集差（排序列表口径；空=一致）。"""
    ca, cb = Counter(a), Counter(b)
    return {
        "missing_in_second": sorted((ca - cb).elements()),
        "extra_in_second": sorted((cb - ca).elements()),
    }


def log_geometry_counts(log_obj: dict) -> dict:
    """conversion log dropped 文本 → routed 几何计数（fail-closed）。"""
    dropped = log_obj.get("dropped") or {}
    g = _GEOM_RE.search(dropped.get("routed_geometry") or "")
    z = _ZONE_RE.search(dropped.get("zones") or "")
    if g is None or z is None:
        raise ValueError("conversion log dropped 文本缺 routed_geometry/"
                         "zones 计数（fail-closed）")
    return {"segments": int(g.group(1)), "vias": int(g.group(2)),
            "arcs": int(g.group(3)), "zones": int(z.group(1))}


def _check(cid: str, ok: bool, evidence: str) -> dict:
    return {"id": cid, "pass": bool(ok), "evidence": evidence}


def _norm_newlines(s: str) -> str:
    """换行归一（CRLF/CR→LF；重放 canonical 口径）。"""
    return s.replace("\r\n", "\n").replace("\r", "\n")


def evaluate_consistency(*, ref_counts: dict, norm_counts: dict,
                         replay_text: str, normalized_disk_bytes: bytes,
                         normalized_disk_sha: str,
                         log_obj: dict, log_disk_sha: str,
                         log_manifest_sha: str, source_rel: str,
                         source_sha: str, outputs_disk_shas: dict,
                         manifest_norm_sha: str) -> dict:
    """S18 转换产物 ↔ 原始板参考态一致性判定（纯函数；fail-closed）。

    ref_counts=reference_counts_from_model(原始板 parse_kicad9_board)；
    norm_counts=parse_normalized_counts(盘上规范化板文本)；replay_text=
    normalized_k9_board_text 重放文本；normalized_disk_bytes=盘上规范化板
    原始字节；normalized_disk_sha=盘上原始字节 sha256_file（绑定 r2
    manifest）。outputs_disk_shas={repo_rel_path: disk_sha256}（conversion
    log outputs 全件）。

    重放口径（S18 落盘实况）：S18 文本构件经 Windows stdout 重定向落盘=
    CRLF 行尾，纯函数重放=LF——重放判定以换行归一（CRLF/CR→LF）后的
    canonical 文本 byte-exact 为准；盘上原始字节不做任何改写，由
    normalized_board_manifest_binding 直接绑定 r2 manifest normalized_hash。
    换行差异如实入证据（禁虚构 byte 口径一致）。
    参考态自带违例不进本判定（D17 非判罚口径——facts 在 baseline 记录）。
    """
    checks = []
    # 1) conversion log 三向绑定（盘上字节↔r2 manifest↔datasets 源）
    checks.append(_check(
        "conversion_log_manifest_binding", log_disk_sha == log_manifest_sha,
        f"log 盘上 sha256={log_disk_sha[:16]}… vs r2 manifest 记录="
        f"{log_manifest_sha[:16]}…"))
    log_inputs = log_obj.get("inputs") or []
    src_ok = bool(log_inputs) and log_inputs[0].get("path") == source_rel \
        and log_inputs[0].get("sha256") == source_sha
    in0 = log_inputs[0] if log_inputs else {}
    checks.append(_check(
        "log_input_binds_dataset_source", src_ok,
        f"log inputs[0]={in0.get('path')}"
        f"（sha256={(in0.get('sha256') or '')[:16]}…）vs 实测源 "
        f"{source_rel}（sha256={source_sha[:16]}…）"))
    # 2) 规范化板绑定（原始字节→manifest）+ 重放（换行归一 canonical）
    checks.append(_check(
        "normalized_board_manifest_binding",
        normalized_disk_sha == manifest_norm_sha,
        f"盘上规范化板 sha256={normalized_disk_sha[:16]}… vs r2 manifest "
        f"normalized_hash={manifest_norm_sha[:16]}…"))
    disk_text = normalized_disk_bytes.decode("utf-8")
    crlf_count = normalized_disk_bytes.count(b"\r\n")
    disk_canon_sha = hashing.sha256_text(_norm_newlines(disk_text))
    replay_canon_sha = hashing.sha256_text(_norm_newlines(replay_text))
    newline_note = (f"盘上换行=CRLF×{crlf_count}（S18 stdout 文本落盘平台"
                    f"惯例）+重放=LF——换行归一后 byte-exact；盘上原始字节"
                    f"零改写，由 normalized_board_manifest_binding 绑定 r2 "
                    f"manifest" if crlf_count else
                    "盘上=LF（无 CRLF 行）——与重放同为 LF byte-exact；盘上"
                    "原始字节零改写，由 normalized_board_manifest_binding "
                    "绑定 r2 manifest")
    checks.append(_check(
        "normalized_board_replay_matches_disk",
        replay_canon_sha == disk_canon_sha,
        f"重放 canonical sha256={replay_canon_sha[:16]}… vs 盘上 canonical="
        f"{disk_canon_sha[:16]}…；{newline_note}"))
    # 3) 计数对账（参考态 ↔ 规范化板独立解析）
    nets = _multiset_diff(ref_counts["net_names"], norm_counts["net_names"])
    nets_ok = not nets["missing_in_second"] and not nets["extra_in_second"]
    checks.append(_check(
        "net_multiset_matches_reference", nets_ok,
        f"参考态 {ref_counts['net_count']} 网 vs 规范化板 "
        f"{norm_counts['net_count']} 网；差 {nets}"))
    fps = _multiset_diff(ref_counts["footprint_refs"],
                         norm_counts["footprint_refs"])
    fps_ok = not fps["missing_in_second"] and not fps["extra_in_second"]
    checks.append(_check(
        "footprint_ref_multiset_matches_reference", fps_ok,
        f"参考态 {ref_counts['footprint_count']} 封装 vs 规范化板 "
        f"{norm_counts['footprint_count']}；差 {fps}"))
    per_ref_diffs = {
        ref: {"reference": ref_counts["pad_count_by_ref"].get(ref, 0),
              "normalized": norm_counts["pad_count_by_ref"].get(ref, 0)}
        for ref in sorted(set(ref_counts["pad_count_by_ref"])
                          | set(norm_counts["pad_count_by_ref"]))
        if ref_counts["pad_count_by_ref"].get(ref, 0)
        != norm_counts["pad_count_by_ref"].get(ref, 0)}
    pads_ok = (ref_counts["pad_total"] == norm_counts["pad_total"]
               and ref_counts["pads_without_net"]
               == norm_counts["pads_without_net"] and not per_ref_diffs)
    checks.append(_check(
        "pad_account_matches_reference", pads_ok,
        f"焊盘总数 {ref_counts['pad_total']} vs {norm_counts['pad_total']}；"
        f"无网焊盘 {ref_counts['pads_without_net']} vs "
        f"{norm_counts['pads_without_net']}；逐 ref 差 {per_ref_diffs}"))
    pnets = _multiset_diff(ref_counts["pad_net_names"],
                           norm_counts["pad_net_names"])
    pnets_ok = not pnets["missing_in_second"] and not pnets["extra_in_second"]
    checks.append(_check(
        "pad_net_multiset_matches_reference", pnets_ok,
        f"焊盘网名多重集差 {pnets}"))
    # 4) routed 几何计数（参考态实数 ↔ conversion log dropped 记录）
    try:
        log_geo = log_geometry_counts(log_obj)
        geo_ok = log_geo == ref_counts["geometry"]
        checks.append(_check(
            "routed_geometry_counts_match_conversion_log", geo_ok,
            f"参考态 {ref_counts['geometry']} vs log dropped 记录 {log_geo}"
            + ("" if geo_ok else "（routed 几何不进规范化板——参考态以源 "
                                "hash 绑定，计数须与 log 一致）")))
    except ValueError as exc:
        geo_ok = False
        checks.append(_check("routed_geometry_counts_match_conversion_log",
                             False, str(exc)))
    # 5) conversion log outputs 全件盘上字节绑定
    log_outputs = {o["path"]: o["sha256"] for o in (log_obj.get("outputs")
                                                    or [])}
    if not log_outputs:
        outputs_ok = False
        out_evidence = "conversion log outputs 空（fail-closed）"
    elif set(log_outputs) != set(outputs_disk_shas):
        outputs_ok = False
        out_evidence = (f"outputs 路径集不等：log={sorted(log_outputs)} vs "
                        f"盘上={sorted(outputs_disk_shas)}")
    else:
        bad = {p: (log_outputs[p], outputs_disk_shas[p])
               for p in sorted(log_outputs)
               if log_outputs[p] != outputs_disk_shas[p]}
        outputs_ok = not bad
        out_evidence = (f"{len(log_outputs)} 件全绑定一致"
                        if outputs_ok else f"不符件 {bad}")
    checks.append(_check("conversion_log_outputs_disk_binding", outputs_ok,
                         out_evidence))
    result = "pass" if all(c["pass"] for c in checks) else "fail"
    fail_classes = sorted(c["id"] for c in checks if not c["pass"])
    return {"checks": checks, "result": result, "fail_classes": fail_classes}


def evaluate_baseline_integrity(*, source_sha_before: str, source_sha_after: str,
                                staging_sha: str, drc_error_text: str,
                                drc_all_text: str) -> dict:
    """baseline 完整性判定（纯函数；fail-closed）。

    独立于一致性：staging 逐字节断言+参考态前后 hash 不变+DRC JSON 可解析
    +双运行 error 计数稳定性（D19(b) 类登记）。drc_error_text/drc_all_text
    为 None=DRC 产物不在场（kicad-cli 加载失败等）——drc_json_wellformed
    fail、dual_run_stable=None（不可判定，不虚构 0=0 一致）。
    """
    checks = []
    staging_ok = staging_sha == source_sha_after
    checks.append(_check(
        "staging_copy_byte_identical", staging_ok,
        f"staging sha256={staging_sha[:16]}… vs datasets 源 "
        f"{source_sha_after[:16]}…（kicad-cli 输入=参考态逐字节拷贝）"))
    unchanged = source_sha_before == source_sha_after
    checks.append(_check(
        "reference_unchanged_pre_post_drc", unchanged,
        f"datasets 源 before={source_sha_before[:16]}… after="
        f"{source_sha_after[:16]}…（只读运行、零回写；前后 hash 分记）"))
    parsed = {}
    for name, text in (("severity_error", drc_error_text),
                       ("severity_all", drc_all_text)):
        if text is None:
            parsed[name] = {"ok": False,
                            "error": "DRC JSON 不在场（kicad-cli 运行未产出）"}
            continue
        try:
            d = json.loads(text)
            if not isinstance(d, dict) or "violations" not in d \
                    or "unconnected_items" not in d:
                raise ValueError("缺 violations/unconnected_items 键")
            parsed[name] = {"ok": True, "json": d}
        except (ValueError, json.JSONDecodeError) as exc:
            parsed[name] = {"ok": False, "error": str(exc)[:200]}
    parse_ok = all(v["ok"] for v in parsed.values())
    checks.append(_check(
        "drc_json_wellformed", parse_ok,
        "双 severity DRC JSON 可解析且含 violations/unconnected_items"
        if parse_ok else
        f"解析失败 {[(k, v.get('error')) for k, v in parsed.items() if not v['ok']]}"))
    if parse_ok:
        err_by = {}
        for name in ("severity_error", "severity_all"):
            d = parsed[name]["json"]
            err_by[name] = sum(1 for v in (d.get("violations") or [])
                               if v.get("severity") == "error")
        stable = err_by["severity_error"] == err_by["severity_all"]
        checks.append(_check(
            "dual_run_error_count_stable", stable,
            f"severity-error 运行 error={err_by['severity_error']}、"
            f"severity-all 运行 error={err_by['severity_all']}（不一致=D19(b) "
            f"类 kicad-cli 跨运行实况，如实登记）"))
    else:
        err_by = {"severity_error": None, "severity_all": None}
        stable = None
    return {"checks": checks,
            "integrity_result":
                "pass" if all(c["pass"] for c in checks) else "fail",
            "fail_classes": sorted(c["id"] for c in checks if not c["pass"]),
            "parsed": parsed, "error_counts": err_by,
            "dual_run_stable": stable}


def _median(values: list):
    if not values:
        return None
    s = sorted(values)
    n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2


def build_batch_summary(*, plan: dict, board_rows: list, refs: dict) -> dict:
    """批汇总装配（纯函数；board_rows=逐板两记录注入）。

    board_rows: [{board_id, profile_id, split_role, version_token,
                  baseline: <drc-baseline 记录>, verify: <一致性记录>}]
    refs: {r2_manifest:{path,sha256}, toolchain_lock_sha256,
           module_sha256:{corpus_convert,check_stage}, script_sha256}
    fail-closed：plan/rows 板数闭合、记录键缺失即 ValueError。
    """
    boards = plan.get("boards") or []
    if not boards:
        raise ValueError("plan.boards 空（fail-closed）")
    by_pid = {r.get("profile_id"): r for r in board_rows}
    if len(by_pid) != len(board_rows):
        raise ValueError("board_rows profile_id 重复（fail-closed）")
    missing = [b["profile_id"] for b in boards if b["profile_id"]
               not in by_pid]
    if missing:
        raise ValueError(f"逐板记录缺失: {missing}")
    extra = sorted(set(by_pid) - {b["profile_id"] for b in boards})
    if extra:
        raise ValueError(f"计划外逐板记录: {extra}")

    table = []
    anomalies = []
    conn_boards = []
    unstable_boards = []
    drc_unavailable = []
    err_counts = []
    dist: dict = {}
    for b in boards:
        base = by_pid[b["profile_id"]]["baseline"]
        ver = by_pid[b["profile_id"]]["verify"]
        if not isinstance(base, dict) or "integrity_result" not in base \
                or "connectivity" not in base:
            raise ValueError(f"{b['profile_id']} baseline 记录缺键"
                             "（fail-closed）")
        if not isinstance(ver, dict) or "result" not in ver \
                or "checks" not in ver:
            raise ValueError(f"{b['profile_id']} verify 记录缺 result/checks"
                             "（fail-closed）")
        conn = base.get("connectivity") or {}
        err_b = base.get("dual_run_error_stability", {}).get("error_batch")
        err_f = base.get("dual_run_error_stability", {}).get("error_final")
        drc = base.get("drc_baseline") or {}
        ds = drc.get("dual_severity") or {}
        all_total = (ds.get("severity_all_final") or {}).get("total")
        warn_total = (ds.get("severity_all_final") or {}).get(
            "violations_by_severity", {}).get("warning", 0)
        if isinstance(err_b, int):
            err_counts.append(err_b)
        stable = base.get("dual_run_error_stability", {}).get("stable")
        row = {
            "board_id": b["board_id"], "profile_id": b["profile_id"],
            "split_role": b["split_role"],
            "version_token": b["version_token"],
            "unconnected_items": conn.get("unconnected_items"),
            "connectivity_type_violation_total":
                conn.get("connectivity_type_violation_total"),
            "error_count_batch_run": err_b,
            "error_count_final_run": err_f,
            "violations_total_final_run": all_total,
            "warning_count_final_run": warn_total,
            "dual_run_error_stable": stable,
            "baseline_integrity": base.get("integrity_result"),
            "consistency": ver.get("result"),
            "fail_classes": ver.get("fail_classes"),
        }
        table.append(row)
        dist[ver.get("result")] = dist.get(ver.get("result"), 0) + 1
        if ver.get("result") != "pass":
            anomalies.append({
                "profile_id": b["profile_id"], "board_id": b["board_id"],
                "consistency": ver.get("result"),
                "failed_checks": [c["id"] for c in ver.get("checks", [])
                                  if not c["pass"]],
                "evidence": [c["evidence"] for c in ver.get("checks", [])
                             if not c["pass"]]})
        if (conn.get("unconnected_items") or 0) > 0 or \
                (conn.get("connectivity_type_violation_total") or 0) > 0:
            conn_boards.append({"board_id": b["board_id"],
                                "profile_id": b["profile_id"],
                                "unconnected_items":
                                    conn.get("unconnected_items"),
                                "connectivity_type_violation_total":
                                    conn.get(
                                        "connectivity_type_violation_total")})
        if stable is False:
            unstable_boards.append({"board_id": b["board_id"],
                                    "profile_id": b["profile_id"],
                                    "error_batch": err_b,
                                    "error_final": err_f})
        present = base.get("drc_artifacts_present") or {}
        if present and not all(present.values()):
            drc_unavailable.append({
                "board_id": b["board_id"], "profile_id": b["profile_id"],
                "board_version": b.get("version_token"),
                "missing_severities": [k for k, v in sorted(present.items())
                                       if not v],
                "exit_codes": base.get("exit_codes"),
                "note": "kicad-cli 加载失败（exit=3）、DRC JSON 不在场——"
                        "如实登记，不虚构计数"})
    versions: dict = {}
    roles: dict = {}
    for b in boards:
        versions[b["version_token"]] = versions.get(b["version_token"], 0) + 1
        roles[b["split_role"]] = roles.get(b["split_role"], 0) + 1
    kicad_versions = sorted({(by_pid[b["profile_id"]]["baseline"]
                              .get("drc_invocation") or {})
                             .get("observed_version")
                             for b in boards} - {None})
    return {
        "schema_version": "3.0",
        "artifact_kind": "s21_k9_route_check_batch_summary",
        "batch_id": BATCH_ID, "batch_date": S21_DATE, "track": TRACK,
        "scope": ("KiCad 8.99–10.99 demo 板 17 板 route/check 参考态验证"
                  "（kicad-cli 10.0.5；S18 k9 转换域的 route/check 补充证据"
                  "层 r1）"),
        "verification_question": VERIFICATION_QUESTION,
        "d17_note": D17_NOTE,
        "denominator": {"boards": len(boards),
                        "split_roles": dict(sorted(roles.items())),
                        "version_tokens": dict(sorted(versions.items())),
                        "tl5_gate_note": "本批结果只作为 k9 转换域的补充"
                                         "证据层：不入 TL-5 门分母（37 "
                                         "profile 不变）、不回填 r2 "
                                         "manifest、不改 TL-5-G"},
        "toolchain": {
            "kicad_cli_declared_version": KICAD_CLI_DECLARED_VERSION,
            "kicad_cli_observed_versions": kicad_versions,
            "drc_dual_severity": {"batch": SEVERITY_BATCH,
                                  "final": SEVERITY_FINAL},
            "refill_mode": REFILL_MODE,
            "invocation_shape": ("cwd=staging/<pid>；kicad-cli pcb drc "
                                 "--format json (--severity-error|"
                                 "--severity-all) --output drc-error.json|"
                                 "drc-all.json reference.kicad_pcb（staging "
                                 "隔离+相对路径调用；kicad-cli 不触 datasets/ "
                                 "路径、零主机路径入产物）"),
        },
        "reference_check": {
            "consistency_distribution": dict(sorted(dist.items())),
            "all_consistency_pass":
                dist.get("pass", 0) == len(boards),
            "baseline_integrity_distribution": dict(sorted(
                Counter(row["baseline_integrity"]
                        for row in table).items())),
            "boards": table,
            "anomalies": anomalies,
            "semantics": ("consistency=「转换复现参考态」判定：计数对账一致"
                          "+byte-exact 重放+hash 链绑定=pass；fail 带差值"
                          "证据（禁凑数）。参考态自带违例不进此判定——见 "
                          "upstream_reference_state"),
        },
        "upstream_reference_state": {
            "connectivity_violation_boards": conn_boards,
            "connectivity_violation_board_count": len(conn_boards),
            "dual_severity_unstable_boards": unstable_boards,
            "drc_unavailable_boards": drc_unavailable,
            "drc_unavailable_board_count": len(drc_unavailable),
            "registration_note": (
                "上游参考态实况 fail-closed 如实登记（S10 先例：连通类违例"
                "板+kicad-cli 双 severity error 分类跨运行不稳定=D19(b)）；"
                "计数与原始板一致=pass——验证的是转换复现参考态，不是板干净"),
        },
        "drc_error_stats": {
            "run": SEVERITY_BATCH,
            "min": min(err_counts) if err_counts else None,
            "median": _median(err_counts),
            "max": max(err_counts) if err_counts else None,
            "zero_error_boards": sum(1 for c in err_counts if c == 0),
        },
        "provenance": {
            "r2_manifest": refs.get("r2_manifest"),
            "toolchain_lock": {"path": "toolchain_lock.json",
                               "sha256": refs.get("toolchain_lock_sha256")},
            "module_sha256": refs.get("module_sha256"),
            "script": {"path": "scripts/s21_route_check.py",
                       "sha256": refs.get("script_sha256")},
            "datasets_readonly": "datasets/ 严格只读（staging 拷贝+前后 hash "
                                 "分记断言零回写）",
        },
        "field_missingness": {
            "drc_json_date": "kicad-cli 输出自身 date 字段=外部工具原样留存"
                             "（跨运行变化，violations 计数可复算）",
            "kicad_prl_side_effect": "kicad-cli 在 staging 目录生成/更新 "
                                     ".kicad_prl（项目本地设置副作用；"
                                     "staging 隔离，不触 datasets/）",
            "d19b_analog": "kicad-cli 10.0.5 双 severity error 分类跨运行"
                           "可能不稳定（S10 cleanhawk250 先例）——双运行 "
                           "error 计数逐板登记，不稳定如实标 fail（D19(b) "
                           "类，非转换缺陷）",
            "kicad_cli_format_boundary": "kicad-cli 10.0.5 拒绝加载 "
                                         "20260624+ 格式板（工具自报：需 "
                                         "KiCad ≥10.99）——该板 DRC "
                                         "baseline 不可得（exit=3），如实"
                                         "登记于 drc_unavailable_boards，"
                                         "不虚构计数",
            "validation_split": "kicad-demos-r1 validation 空（S15 简分）"
                                "——本批沿用 r1/r2 splits 不变",
        },
        "producer": MODULE_NAME,
    }


# ---------------------------------------------------------------------------
# ops（stdin→stdout；盘上读取只读、hash 实测=byte 口径）
# ---------------------------------------------------------------------------

def op_plan(_req: dict) -> None:
    r2 = _read_json(R2_MANIFEST_REL)
    r2_sha = _sha_file(R2_MANIFEST_REL)
    r1 = _read_json(R1_MANIFEST_REL)
    r1_sha = _sha_file(R1_MANIFEST_REL)
    board_ids = r2.get("board_ids") or []
    if len(board_ids) != 17:
        _fail(f"r2 manifest board_ids={len(board_ids)} != 17")
    norm_by_bid = {e["board_id"]: e for e in r2.get("normalized_hash") or []}
    log_by_bid = {e["board_id"]: e for e in r2.get("conversion_log") or []}
    if set(norm_by_bid) != set(board_ids) or set(log_by_bid) != set(board_ids):
        _fail("r2 manifest normalized_hash/conversion_log 与 board_ids "
              "不闭合")
    role_of = {}
    for role in ("train", "validation", "holdout", "external_eval"):
        for b in r1["dataset_splits"].get(role) or []:
            role_of[b] = role
    boards = []
    for bid in board_ids:
        log_rel = log_by_bid[bid]["path"]
        log_disk_sha = _sha_file(log_rel)
        if log_disk_sha != log_by_bid[bid]["sha256"]:
            _fail(f"conversion log 盘上字节与 r2 manifest 不符: {bid}")
        log_obj = _read_json(log_rel)
        inputs = log_obj.get("inputs") or []
        if not inputs or not str(inputs[0].get("role", "")).startswith(
                "source_pcb"):
            _fail(f"conversion log inputs[0] 非 source_pcb: {bid}")
        source_rel = inputs[0]["path"]
        source_sha = _sha_file(source_rel)
        if source_sha != inputs[0]["sha256"]:
            _fail(f"datasets 源 hash 与 conversion log 不符: {bid}")
        norm_rel = norm_by_bid[bid]["path"]
        pid = norm_rel.split("/")[1]
        if not pid.startswith("kicaddemo-"):
            _fail(f"profile_id 解析异常: {norm_rel}")
        version_token = (log_obj.get("version_gate") or {}).get(
            "board_version")
        net_src = (log_obj.get("version_gate") or {}).get(
            "net_declaration_source")
        boards.append({
            "board_id": bid, "profile_id": pid,
            "split_role": role_of.get(bid),
            "version_token": version_token,
            "net_declaration_source": net_src,
            "source_rel": source_rel,
            "source_sha256_before_drc": source_sha,
            "normalized_rel": norm_rel,
            "normalized_sha256": norm_by_bid[bid]["sha256"],
            "conversion_log_rel": log_rel,
            "conversion_log_sha256": log_by_bid[bid]["sha256"],
            "staging_rel": f"out/v3-tl5/{BATCH_ID}/staging/{pid}/"
                           f"reference.kicad_pcb",
        })
    roles: dict = {}
    versions: dict = {}
    for b in boards:
        roles[b["split_role"]] = roles.get(b["split_role"], 0) + 1
        versions[b["version_token"]] = versions.get(b["version_token"], 0) + 1
    _emit_json({
        "schema_version": "3.0", "artifact_kind": "s21_batch_plan",
        "batch_id": BATCH_ID, "declared_date": S21_DATE, "track": TRACK,
        "d17_note": D17_NOTE, "verification_question": VERIFICATION_QUESTION,
        "kicad_cli_declared_version": KICAD_CLI_DECLARED_VERSION,
        "drc_dual_severity": {"batch": SEVERITY_BATCH,
                              "final": SEVERITY_FINAL},
        "refill_mode": REFILL_MODE,
        "r2_manifest": {"path": R2_MANIFEST_REL, "sha256": r2_sha},
        "r1_manifest": {"path": R1_MANIFEST_REL, "sha256": r1_sha},
        "boards": boards,
        "counts": {"boards": len(boards),
                   "split_roles": dict(sorted(roles.items())),
                   "version_tokens": dict(sorted(versions.items()))},
        "producer": MODULE_NAME,
    })


def op_baseline(req: dict) -> None:
    b = req["board"]
    staging_rel = b["staging_rel"]
    staging_sha = _sha_file(staging_rel)
    source_sha_after = _sha_file(b["source_rel"])
    drc_dir = staging_rel.rsplit("/", 1)[0]
    err_rel = f"{drc_dir}/drc-error.json"
    all_rel = f"{drc_dir}/drc-all.json"
    err_text = _read_text_optional(err_rel)
    all_text = _read_text_optional(all_rel)
    exits = {}
    for name, rel in (("severity_error", f"{drc_dir}/drc-error.exit"),
                      ("severity_all", f"{drc_dir}/drc-all.exit")):
        try:
            exits[name] = int(_read_text_raw(rel).strip())
        except (FileNotFoundError, ValueError):
            exits[name] = None
    ev = evaluate_baseline_integrity(
        source_sha_before=b["source_sha256_before_drc"],
        source_sha_after=source_sha_after, staging_sha=staging_sha,
        drc_error_text=err_text, drc_all_text=all_text)
    drc_summary = None
    conn = {"unconnected_items": None,
            "connectivity_type_violations": None,
            "connectivity_type_violation_total": None}
    observed_version = None
    if all(v["ok"] for v in ev["parsed"].values()):
        drc_summary = check_stage.summarize_drc(
            ev["parsed"]["severity_all"]["json"],
            ev["parsed"]["severity_error"]["json"])
        c = drc_summary["connectivity_authority_input"]
        conn = {"unconnected_items": c["unconnected_items"],
                "connectivity_type_violations":
                    c["connectivity_type_violations"],
                "connectivity_type_violation_total":
                    c["connectivity_type_violation_total"]}
        observed_version = drc_summary.get("kicad_version")
    rec = {
        "schema_version": "3.0", "artifact_kind": "s21_drc_baseline",
        "track": TRACK, "batch_id": BATCH_ID, "record_date": S21_DATE,
        "board_id": b["board_id"], "profile_id": b["profile_id"],
        "split_role": b["split_role"],
        "version_token": b["version_token"],
        "net_declaration_source": b["net_declaration_source"],
        "reference_state": {
            "path": b["source_rel"],
            "sha256_before_drc": b["source_sha256_before_drc"],
            "sha256_after_drc": source_sha_after,
            "unchanged": source_sha_after == b["source_sha256_before_drc"],
            "fact_source_note": "as-shipped 参考态事实源（D17：参考 routed "
                                "态验证；本记录=该板 DRC baseline）",
        },
        "staging": {"path": staging_rel, "sha256": staging_sha,
                    "byte_identical_to_reference":
                        staging_sha == source_sha_after},
        "drc_invocation": {
            "tool": "kicad-cli",
            "declared_version": KICAD_CLI_DECLARED_VERSION,
            "observed_version": observed_version,
            "severity": {"batch": SEVERITY_BATCH, "final": SEVERITY_FINAL},
            "refill_mode": REFILL_MODE,
            "run_scope": "staging 拷贝（datasets/ 严格只读；kicad-cli 不触 "
                         "datasets/ 路径）",
            "argv_shape": ("cwd=staging/<pid>；kicad-cli pcb drc --format "
                           "json (--severity-error|--severity-all) --output "
                           "drc-error.json|drc-all.json reference.kicad_pcb"
                           "（相对路径调用，零主机路径入 JSON）"),
        },
        "exit_codes": exits,
        "drc_artifacts_present": {"severity_error": err_text is not None,
                                  "severity_all": all_text is not None},
        "drc_baseline": drc_summary,
        "connectivity": conn,
        "dual_run_error_stability": {
            "stable": ev["dual_run_stable"],
            "error_batch": ev["error_counts"]["severity_error"],
            "error_final": ev["error_counts"]["severity_all"],
            "note": "双运行 error 计数一致性（D19(b) 类登记：kicad-cli "
                    "跨运行不稳定=工具实况如实记录，非判罚）",
        },
        "upstream_reference_state": {
            "connectivity_violation_present":
                (conn.get("unconnected_items") or 0) > 0
                or (conn.get("connectivity_type_violation_total") or 0) > 0,
            "error_level_violations_present":
                (ev["error_counts"].get("severity_error") or 0) > 0,
            "registration_note": "上游参考态自带违例=上游设计实况如实计数"
                                 "登记（S10 先例 fail-closed；D17 非判罚"
                                 "口径），不构成一致性 fail",
        },
        "checks": ev["checks"],
        "integrity_result": ev["integrity_result"],
        "fail_classes": ev["fail_classes"],
        "field_missingness": {
            "drc_json_date": "kicad-cli 输出自身 date 字段原样留存（跨运行"
                             "变化，violations 计数可复算）",
            "schematic_parity": "未启用 --schematic-parity（板级参考态验证"
                                "口径；无原理图对账要求）",
            "drc_json_absent": ("DRC JSON 不在场时（kicad-cli 加载失败，"
                                "exit=3）integrity=fail+error_counts=None"
                                "（不可判定，不虚构 0=0）；本板参考态其余"
                                "绑定检查照常"),
        },
        "producer": MODULE_NAME,
    }
    _emit_json(rec)


def op_verify(req: dict) -> None:
    b = req["board"]
    source_rel = b["source_rel"]
    source_sha = _sha_file(source_rel)
    raw_text = _read_text_raw(source_rel)
    model = cc.parse_kicad9_board(raw_text)
    ref_counts = reference_counts_from_model(model)
    norm_disk_bytes = (REPO / b["normalized_rel"]).read_bytes()
    norm_disk_sha = _sha_file(b["normalized_rel"])
    replay_text = cc.normalized_k9_board_text(
        model, source_path=source_rel, source_sha256=source_sha)
    replay_canon_sha = hashing.sha256_text(_norm_newlines(replay_text))
    disk_canon_sha = hashing.sha256_text(
        _norm_newlines(norm_disk_bytes.decode("utf-8")))
    crlf_count = norm_disk_bytes.count(b"\r\n")
    log_rel = b["conversion_log_rel"]
    log_obj = _read_json(log_rel)
    log_disk_sha = _sha_file(log_rel)
    norm_disk_text = norm_disk_bytes.decode("utf-8")
    norm_counts = parse_normalized_counts(norm_disk_text)
    outputs_disk_shas = {}
    for o in log_obj.get("outputs") or []:
        try:
            outputs_disk_shas[o["path"]] = _sha_file(o["path"])
        except (FileNotFoundError, ValueError):
            outputs_disk_shas[o["path"]] = None
    r2 = _read_json(R2_MANIFEST_REL)
    norm_by_bid = {e["board_id"]: e["sha256"]
                   for e in r2.get("normalized_hash") or []}
    ev = evaluate_consistency(
        ref_counts=ref_counts, norm_counts=norm_counts,
        replay_text=replay_text, normalized_disk_bytes=norm_disk_bytes,
        normalized_disk_sha=norm_disk_sha,
        log_obj=log_obj, log_disk_sha=log_disk_sha,
        log_manifest_sha=b["conversion_log_sha256"],
        source_rel=source_rel, source_sha=source_sha,
        outputs_disk_shas=outputs_disk_shas,
        manifest_norm_sha=norm_by_bid.get(b["board_id"]))
    rec = {
        "schema_version": "3.0",
        "artifact_kind": "s21_conversion_consistency_record",
        "track": TRACK, "batch_id": BATCH_ID, "record_date": S21_DATE,
        "board_id": b["board_id"], "profile_id": b["profile_id"],
        "split_role": b["split_role"],
        "version_token": b["version_token"],
        "net_declaration_source": b["net_declaration_source"],
        "verification_question": VERIFICATION_QUESTION,
        "reference_state": {"path": source_rel, "sha256": source_sha,
                            "board_version": model["board_version"],
                            "host": model["host"]},
        "count_reconciliation": {
            "reference_counts": ref_counts,
            "normalized_counts": {k: v for k, v in norm_counts.items()
                                  if k != "net_ids"},
            "net_id_note": ("规范化板 net 带显式 id（top_level 声明板）"
                            if norm_counts["net_ids"] else
                            "规范化板 net 为 pad_derived name-only（"
                            "20260206+ 板；id 结构性不可得不虚构）"),
        },
        "replay": {
            "replay_canonical_sha256": replay_canon_sha,
            "disk_canonical_sha256": disk_canon_sha,
            "disk_sha256_raw": norm_disk_sha,
            "disk_newline_convention": "crlf" if crlf_count else "lf",
            "crlf_line_count": crlf_count,
            "newline_note": ("S18 文本构件经 Windows stdout 落盘=CRLF 行尾"
                             "（平台惯例）；纯函数重放=LF——重放判定=换行"
                             "归一 canonical byte-exact，盘上原始字节零改写"
                             "（raw hash 绑定 r2 manifest normalized_hash）"),
        },
        "checks": ev["checks"], "result": ev["result"],
        "fail_classes": ev["fail_classes"],
        "result_semantics": (
            "pass=S18 转换产物与原始板参考态一致复现（计数对账+byte-exact "
            "重放+hash 链绑定）；非板干净声明——参考态自带违例见 baseline "
            "记录（D17 非判罚口径）"),
        "reference_baseline_pointer": {
            "path": f"out/v3-tl5/{BATCH_ID}/boards/{b['profile_id']}/"
                    f"drc-baseline.json"},
        "producer": MODULE_NAME,
    }
    _emit_json(rec)


def op_summary(req: dict) -> None:
    plan_rel = req.get("plan_rel") or PLAN_REL_DEFAULT
    _require_repo_relative(plan_rel, "plan_rel")
    plan = _read_json(plan_rel)
    rows = []
    for b in plan["boards"]:
        base = _read_json(f"out/v3-tl5/{BATCH_ID}/boards/"
                          f"{b['profile_id']}/drc-baseline.json")
        ver = _read_json(f"out/v3-tl5/{BATCH_ID}/boards/"
                         f"{b['profile_id']}/verify-record.json")
        rows.append({"board_id": b["board_id"],
                     "profile_id": b["profile_id"],
                     "split_role": b["split_role"],
                     "version_token": b["version_token"],
                     "baseline": base, "verify": ver})
    refs = {
        "r2_manifest": {"path": R2_MANIFEST_REL,
                        "sha256": _sha_file(R2_MANIFEST_REL)},
        "toolchain_lock_sha256": _sha_file("toolchain_lock.json"),
        "module_sha256": {
            "corpus_convert": _sha_file("pcbflow/corpus_convert.py"),
            "check_stage": _sha_file("pcbflow/check_stage.py"),
        },
        "script_sha256": _sha_file("scripts/s21_route_check.py"),
    }
    _emit_json(build_batch_summary(plan=plan, board_rows=rows, refs=refs))


def main() -> None:
    req = _read_req()
    op = req["op"]
    handlers = {"plan": op_plan, "baseline": op_baseline,
                "verify": op_verify, "summary": op_summary}
    if op not in handlers:
        _fail(f"unknown op: {op}")
    handlers[req["op"]](req)


if __name__ == "__main__":
    main()
