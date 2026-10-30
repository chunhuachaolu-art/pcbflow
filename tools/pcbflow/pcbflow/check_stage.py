"""TL-5 第四包：route/check 段执行器——参考 routed 态验证口径（偏差 D17）。

声明范围（本模块唯一口径，ROUTE_SCOPE）：
- route/check executed 的含义=**对数据集参考 routed 态**执行连通性与 DRC
  双 severity 验证（reference_verification），**不生成布线**；
- 布线生成能力缺口如实保留于 V3-MATRIX Evidence reality——本模块与
  全部产物不得出现"已具备布线能力/route generation executed"语义；
- 连通性 authority=kicad-cli pcb drc 的 unconnected_items/连通类违例
  （S6/S7 已验证可行）；corpus 侧文本解析（逐网铜几何账）只作 advisory
  第二源，authority 恒归 kicad-cli；
- check result=pass 的语义=「参考 routed 态验证完成且全部对账检查通过」，
  非制造签核、非布线产物 DRC 干净——参考态自带 error 级违例如实计数记录。

输入侧（全部由编排侧注入，本模块零 I/O）：
- profiles/<id>/route-check.json 声明（build_route_check_declaration 产）；
- 参考 routed 板文本（datasets/ 只读；staging 拷贝与 raw 逐字节一致由
  编排侧断言，本模块以 hash 相等复核并落检查项）；
- kicad-cli 双 severity DRC JSON（编排侧对 staging 板实跑；JSON 自身
  date 字段=kicad-cli 外部输出原样留存，见 field_missingness）。

生成器纪律：纯函数、零子进程、零自身落盘、零网络、零 wall-clock
（CHECK_DATE 为声明常量）、零主机路径（输入路径必须仓库相对 POSIX，
fail-closed）；JSON 输出一律 canonical（hashing.json_dumps）。
"""

from __future__ import annotations

import re

from . import hashing, sexpr_min

TRACK = "tl5-check-r1"
MODULE_NAME = "pcbflow.check_stage"

#: 执行声明日期（人工会话声明，非机器 wall-clock）
CHECK_DATE = "2026-09-03"

#: route/check 段声明范围（D17 语义收窄的唯一合法值）
ROUTE_SCOPE = "reference_verification"

ROUTE_SCOPE_NOTE = (
    "route/check 段声明范围=对数据集参考 routed 态执行连通性与 DRC 双 "
    "severity 验证（reference_verification）；不生成布线——布线生成能力"
    "缺口如实保留于 V3-MATRIX Evidence reality（偏差 D17：route/check "
    "executed 的含义=参考态验证执行，非 route generation executed）")

#: profile.thresholds 键 → 参考板 setup 块键（S6/S7 转换推导的同源映射）
THRESHOLD_TO_SETUP = {
    "min_track_width_mm": "trace_min",
    "min_clearance_mm": "trace_clearance",
    "via_min_size_mm": "via_min_size",
    "via_min_drill_mm": "via_min_drill",
}

#: kicad-cli DRC 违例 type 中的连通类关键词（unclosed/unconnected 家族）
_CONNECTIVITY_TYPE_KEYS = ("unconnected", "unclosed")

_HEX64_RE = re.compile(r"^[0-9a-f]{64}$")


def _require_repo_relative(path: str, what: str) -> str:
    """仓库相对 POSIX 路径强制（禁主机形态；红线同 corpus._require_relative）。"""
    if not isinstance(path, str) or "\\" in path or re.match(
            r"^[A-Za-z]:", path) or path.startswith("/"):
        raise ValueError(f"{what}: host/absolute path forbidden: {path!r}")
    return path


def _tok(node: list, key: str):
    n = sexpr_min.find_first(node, key)
    if n is None or len(n) < 2:
        return None
    return n[1]


def _num_or_none(tok):
    try:
        return float(tok)
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------------------
# 1. 参考 routed 板文本解析（advisory 第二源 + 阈值对账数据；纯函数）
# ---------------------------------------------------------------------------

def parse_routed_geometry(board_text: str) -> dict:
    """routed 参考板文本 → 逐网铜几何账 + 实际最小几何 + setup 声明值。

    能力边界：文本结构级（数值=源字面量 float 化；无几何求值——clearance
    不可从文本判定）。逐网连通判定 authority 不在此（advisory only）。
    解析失败 fail-closed（sexpr_min/ValueError 原样上抛，不猜）。
    """
    top = sexpr_min.parse(board_text)
    roots = [n for n in top if isinstance(n, list) and n and n[0] == "kicad_pcb"]
    if len(roots) != 1:
        raise ValueError(f"expect exactly one kicad_pcb root, got {len(roots)}")
    root = roots[0]

    nets: dict = {}
    for n in root[1:]:
        if isinstance(n, list) and n and n[0] == "net" and len(n) >= 3:
            nets[int(n[1])] = n[2]

    setup: dict = {}
    s = sexpr_min.find_first(root, "setup")
    if s is not None:
        for c in s[1:]:
            if isinstance(c, list) and len(c) == 2 and isinstance(c[1], str):
                setup[c[0]] = c[1]

    pads_per_net: dict = {}
    for m in sexpr_min.find_all(root, "module"):
        for p in sexpr_min.find_all(m, "pad"):
            nn = sexpr_min.find_first(p, "net")
            if nn is not None and len(nn) >= 3:
                pads_per_net[int(nn[1])] = pads_per_net.get(int(nn[1]), 0) + 1

    geom: dict = {}  # net_id → [seg, arc, via, zone]
    widths: list = []
    vias_without_drill = 0
    via_sizes: list = []
    via_drills: list = []
    unbound = 0

    def _acc(net_id, idx):
        nonlocal unbound
        if net_id not in nets:
            unbound += 1
            return None
        geom.setdefault(net_id, [0, 0, 0, 0])
        geom[net_id][idx] += 1
        return net_id

    for seg in sexpr_min.find_all(root, "segment"):
        nn = sexpr_min.find_first(seg, "net")
        _acc(int(nn[1]) if nn and len(nn) >= 2 else -1, 0)
        w = _num_or_none(_tok(seg, "width"))
        if w is not None:
            widths.append(w)
    for arc in sexpr_min.find_all(root, "arc"):
        nn = sexpr_min.find_first(arc, "net")
        _acc(int(nn[1]) if nn and len(nn) >= 2 else -1, 1)
        w = _num_or_none(_tok(arc, "width"))
        if w is not None:
            widths.append(w)
    for via in sexpr_min.find_all(root, "via"):
        nn = sexpr_min.find_first(via, "net")
        _acc(int(nn[1]) if nn and len(nn) >= 2 else -1, 2)
        sz = _num_or_none(_tok(via, "size"))
        dr = _tok(via, "drill")
        if sz is not None:
            via_sizes.append(sz)
        if dr is None:
            vias_without_drill += 1
        else:
            d = _num_or_none(dr)
            if d is not None:
                via_drills.append(d)
    for zone in sexpr_min.find_all(root, "zone"):
        nn = sexpr_min.find_first(zone, "net")
        _acc(int(nn[1]) if nn and len(nn) >= 2 else -1, 3)

    per_net = []
    for net_id in sorted(set(nets) | set(geom) | set(pads_per_net)):
        g = geom.get(net_id, [0, 0, 0, 0])
        per_net.append({
            "net_id": net_id, "name": nets.get(net_id, ""),
            "pad_count": pads_per_net.get(net_id, 0),
            "segment_count": g[0], "arc_count": g[1],
            "via_count": g[2], "zone_count": g[3],
            "copper_item_count": g[0] + g[1] + g[2] + g[3],
        })

    return {
        "net_count": len(nets),
        "named_net_count": sum(1 for v in nets.values() if v != ""),
        "per_net": per_net,
        "geometry_counts": {
            "segments": sum(g[0] for g in geom.values()),
            "arcs": sum(g[1] for g in geom.values()),
            "vias": sum(g[2] for g in geom.values()),
            "zones": sum(g[3] for g in geom.values()),
        },
        "items_bound_outside_declared_nets": unbound,
        "actual_min": {
            "track_width_mm": min(widths) if widths else None,
            "via_size_mm": min(via_sizes) if via_sizes else None,
            "via_drill_mm": min(via_drills) if via_drills else None,
        },
        "vias_without_drill_token": vias_without_drill,
        "setup": dict(setup),
    }


def advisory_zero_geometry_nets(geometry: dict) -> list:
    """advisory：命名多焊盘（pad_count≥2）网在参考 routed 态无任何铜几何。

    第二源交叉核验（authority 归 kicad-cli unconnected_items）：零几何多
    焊盘网=疑似未布通信号，列出供人核；不计入 verdict（区填充/文本盲区
    由 kicad-cli 权威口径兜底）。
    """
    return [{"net_id": n["net_id"], "name": n["name"],
             "pad_count": n["pad_count"]}
            for n in geometry["per_net"]
            if n["name"] != "" and n["pad_count"] >= 2
            and n["copper_item_count"] == 0]


# ---------------------------------------------------------------------------
# 2. kicad-cli DRC 双 severity JSON → 规范化计数（纯函数）
# ---------------------------------------------------------------------------

def _violations_by_severity(drc: dict) -> dict:
    out: dict = {}
    for v in drc.get("violations") or []:
        sev = v.get("severity")
        out[sev] = out.get(sev, 0) + 1
    return dict(sorted(out.items()))


def _violations_by_type(drc: dict) -> dict:
    out: dict = {}
    for v in drc.get("violations") or []:
        t = v.get("type") or "unknown"
        sev = v.get("severity")
        entry = out.setdefault(t, {})
        entry[sev] = entry.get(sev, 0) + 1
    return dict(sorted(out.items()))


def summarize_drc(drc_all: dict, drc_error: dict) -> dict:
    """双 severity DRC JSON → 规范化摘要（计数/一致性/连通类违例/top types）。

    drc_all=severity-all 终检产物；drc_error=severity-error 批产物
    （profile.kicad_cli 合同：drc_batch_severity=severity-error、
    drc_final_severity=severity-all）。两者须为同一 staged 板的两次运行。
    """
    for name, d in (("drc_all", drc_all), ("drc_error", drc_error)):
        if not isinstance(d, dict) or "violations" not in d \
                or "unconnected_items" not in d:
            raise ValueError(f"{name}: 非 kicad-cli DRC JSON（缺 "
                             f"violations/unconnected_items）——fail-closed")
    by_sev_all = _violations_by_severity(drc_all)
    by_sev_err = _violations_by_severity(drc_error)
    by_type_all = _violations_by_type(drc_all)
    connectivity_types = {
        t: cnt for t, cnt in by_type_all.items()
        if any(k in t for k in _CONNECTIVITY_TYPE_KEYS)}
    top = sorted(by_type_all.items(),
                 key=lambda kv: (-sum(kv[1].values()), kv[0]))[:8]
    return {
        "kicad_version": drc_all.get("kicad_version"),
        "source": drc_all.get("source"),
        "coordinate_units": drc_all.get("coordinate_units"),
        "dual_severity": {
            "severity_error_batch": {
                "included_severities": list(
                    drc_error.get("included_severities") or []),
                "violations_by_severity": by_sev_err,
                "total": sum(by_sev_err.values()),
            },
            "severity_all_final": {
                "included_severities": list(
                    drc_all.get("included_severities") or []),
                "violations_by_severity": by_sev_all,
                "total": sum(by_sev_all.values()),
            },
        },
        "consistency": {
            "error_count_equal_across_runs":
                by_sev_err.get("error", 0) == by_sev_all.get("error", 0),
            "schematic_parity_items": len(
                drc_all.get("schematic_parity") or []),
        },
        "connectivity_authority_input": {
            "unconnected_items": len(drc_all.get("unconnected_items") or []),
            "connectivity_type_violations": dict(
                sorted(connectivity_types.items())),
            "connectivity_type_violation_total": sum(
                sum(sevs.values()) for sevs in connectivity_types.values()),
        },
        "violations_by_type": by_type_all,
        "top_violation_types": [
            {"type": t, "count": sum(sevs.values()),
             "by_severity": dict(sorted(sevs.items()))} for t, sevs in top],
        "reference_state_note": "error/warning 计数=参考 routed 态自带违例"
                                "的如实记录（第三方上游设计实况），非 pcbflow "
                                "布线产物检查结果",
    }


# ---------------------------------------------------------------------------
# 3. route/check 段声明（profiles/<id>/route-check.json 内容；纯装配）
# ---------------------------------------------------------------------------

def build_route_check_declaration(*, profile_id: str, board_id: str,
                                  dataset_role: str,
                                  reference_route_path: str,
                                  reference_route_sha256: str,
                                  profile_threshold_keys: list,
                                  prior_state_note: str) -> dict:
    """route/check 段声明内容（route_scope=reference_verification 显式落档）。

    本声明是该 profile 首份 route/check 段范围声明（S8/D17 建立）；此前
    状态=not_executed（S6/S7 profile-report v1 记录，无引擎），由
    prior_state_note 如实衔接。drc_max_error_severity 缺省 None=不设
    error 计数上限（参考态违例计数只记录不判罚；如声明上限则超限判 fail）。
    """
    _require_repo_relative(reference_route_path, "reference_route_path")
    if not _HEX64_RE.search(reference_route_sha256 or ""):
        raise ValueError("reference_route_sha256 required (64 hex)")
    if dataset_role not in ("train", "validation", "holdout",
                            "external_eval"):
        raise ValueError(f"dataset_role 非法: {dataset_role!r}")
    holdout_note = ("holdout 板：验证只读参考态（staging 拷贝+hash 复核）；"
                    "零写回 datasets/" if dataset_role in ("holdout",
                                                           "external_eval")
                    else "非 holdout 板：验证同样只读 datasets/ 参考态")
    return {
        "schema_version": "3.0",
        "artifact_kind": "route_check_declaration",
        "track": TRACK,
        "declaration_version": "1",
        "declared_date": CHECK_DATE,
        "profile_id": profile_id, "board_id": board_id,
        "dataset_role": dataset_role,
        "route_scope": ROUTE_SCOPE,
        "route_scope_note": ROUTE_SCOPE_NOTE,
        "prior_state": prior_state_note,
        "reference_route": {"path": reference_route_path,
                            "sha256": reference_route_sha256},
        "connectivity_authority":
            "kicad_cli_drc_unconnected_items（S6/S7 已验证可行）",
        "advisory_second_source":
            "corpus_parse_per_net_copper_geometry（advisory；authority 恒归 "
            "kicad-cli）",
        "drc_dual_severity": {"batch": "severity-error",
                              "final": "severity-all"},
        "drc_max_error_severity": None,
        "threshold_reconciliation": {
            "profile_threshold_keys": sorted(profile_threshold_keys),
            "setup_identity_basis":
                "参考 routed 板 setup 块声明值（trace_min/trace_clearance/"
                "via_min_size/via_min_drill）与 profile.thresholds 数值一致",
            "actual_geometry_basis":
                "参考 routed 板实际 segment/arc width、via size/drill 字面量"
                "最小值 ≥ profile.thresholds（clearance 不可文本判定→仅记录）",
        },
        "holdout_note": holdout_note,
        "producer": MODULE_NAME,
    }


# ---------------------------------------------------------------------------
# 4. 规范化 check 报告（verdict 评估内联；纯装配+实算）
# ---------------------------------------------------------------------------

def _check(cid: str, ok: bool, evidence: str) -> dict:
    return {"id": cid, "pass": bool(ok), "evidence": evidence}


def _reconcile_setup(profile_thresholds: dict, setup: dict) -> dict:
    """profile.thresholds ↔ 参考板 setup 数值一致性对账。"""
    compared, skipped = [], []
    for tkey, skey in sorted(THRESHOLD_TO_SETUP.items()):
        if tkey not in profile_thresholds:
            continue
        if skey not in setup:
            skipped.append({"threshold": tkey, "setup_key": skey,
                            "reason": "setup 缺该声明键（不可比，如实跳过）"})
            continue
        actual = _num_or_none(setup[skey])
        declared = profile_thresholds[tkey]
        match = actual is not None and float(declared) == actual
        compared.append({
            "threshold": tkey, "setup_key": skey,
            "profile_value": declared, "setup_literal": setup[skey],
            "setup_value": actual, "match": match,
        })
    return {"compared": compared, "skipped": skipped,
            "mismatches": [c for c in compared if not c["match"]]}


def _reconcile_actual_geometry(profile_thresholds: dict, geometry: dict) -> dict:
    """参考板实际几何最小值 ↔ profile.thresholds 对账（字面量实算）。"""
    amin = geometry["actual_min"]
    entries = []

    def one(tkey, actual, basis):
        if tkey not in profile_thresholds:
            entries.append({"check": tkey, "status": "skipped",
                            "reason": "profile 未声明该阈值"})
            return
        if actual is None:
            entries.append({"check": tkey, "status": "skipped",
                            "reason": basis + "：无可比数据（如实跳过）"})
            return
        limit = float(profile_thresholds[tkey])
        entries.append({
            "check": tkey, "status": "checked",
            "actual_min": actual, "threshold": limit,
            "pass": actual >= limit,
        })

    one("min_track_width_mm", amin["track_width_mm"],
        "参考板无 segment/arc width 字面量")
    one("via_min_size_mm", amin["via_size_mm"], "参考板无 via size 字面量")
    one("via_min_drill_mm", amin["via_drill_mm"],
        f"参考板 via 均无 drill 字面量（{geometry['vias_without_drill_token']}"
        " 个 via 缺 drill token——上游文件实况，kicad-cli DRC 孔类检查覆盖）")
    return {
        "entries": entries,
        "not_verifiable": {
            "min_clearance_mm": "clearance 需两两几何求值，文本级不可判定"
                                "（kicad-cli DRC clearance 违例计数已另行记录）",
        },
        "vias_without_drill_token": geometry["vias_without_drill_token"],
        "failed": [e for e in entries
                   if e.get("status") == "checked" and not e["pass"]],
    }


def build_check_report(*, profile_id: str, board_id: str, dataset_role: str,
                       declaration: dict, geometry: dict, drc_summary: dict,
                       profile_thresholds: dict, input_refs: dict) -> dict:
    """规范化 check 报告（含 verdict；字段缺一即 ValueError，不静默）。

    input_refs: {reference_route|staged_board|route_check_declaration|profile|
    drc_severity_error|drc_severity_all: {path, sha256}}——hash 绑定输入；
    staged_board 与 reference_route 的 sha 相等即 staging 逐字节一致复核。
    """
    for key in ("reference_route", "staged_board", "route_check_declaration",
                "profile", "drc_severity_error", "drc_severity_all"):
        ref = input_refs.get(key)
        if not isinstance(ref, dict) or not _HEX64_RE.search(
                ref.get("sha256") or ""):
            raise ValueError(f"input_refs[{key!r}] 缺 path/sha256(64hex)"
                             "——输入 hash 绑定不可省（fail-closed）")
        _require_repo_relative(ref["path"], f"input_refs[{key}].path")
    if declaration.get("route_scope") != ROUTE_SCOPE:
        raise ValueError("declaration.route_scope 必须=reference_verification"
                         "（D17 唯一合法口径；非本口径不产 check 报告）")
    for key in ("per_net", "actual_min", "setup"):
        if key not in geometry:
            raise ValueError(f"geometry missing: {key}")
    for key in ("dual_severity", "connectivity_authority_input",
                "consistency"):
        if key not in drc_summary:
            raise ValueError(f"drc_summary missing: {key}")

    checks = []
    conn = drc_summary["connectivity_authority_input"]
    unconn = conn["unconnected_items"]
    conn_viol = conn["connectivity_type_violation_total"]
    checks.append(_check(
        "route_scope_reference_verification",
        declaration.get("route_scope") == ROUTE_SCOPE,
        f"声明 route_scope={declaration.get('route_scope')!r}（D17：验证≠"
        f"布线生成；本报告不含任何布线产物）"))
    checks.append(_check(
        "reference_route_hash_binding",
        declaration.get("reference_route", {}).get("sha256")
        == input_refs["reference_route"]["sha256"],
        "声明绑定 sha256="
        + repr(declaration.get("reference_route", {}).get("sha256"))
        + " vs 实测 " + input_refs["reference_route"]["sha256"]))
    checks.append(_check(
        "staging_copy_byte_identical",
        input_refs["staged_board"]["sha256"]
        == input_refs["reference_route"]["sha256"],
        f"staged_board sha256={input_refs['staged_board']['sha256']} == "
        f"reference_route（kicad-cli 输入=datasets/ 参考态逐字节拷贝）"))
    ds = drc_summary["dual_severity"]
    batch, final = ds["severity_error_batch"], ds["severity_all_final"]
    err_equal = drc_summary["consistency"]["error_count_equal_across_runs"]
    checks.append(_check(
        "dual_severity_contract",
        batch["included_severities"] == ["error"]
        and final["included_severities"] == ["error", "warning", "exclusion"]
        and err_equal,
        f"batch included={batch['included_severities']}（error="
        f"{batch['violations_by_severity'].get('error', 0)}）、final "
        f"included={final['included_severities']}（error="
        f"{final['violations_by_severity'].get('error', 0)}）；双运行 error "
        f"计数一致={err_equal}"))
    checks.append(_check(
        "connectivity_kicad_cli",
        unconn == 0 and conn_viol == 0,
        f"authority=kicad-cli：unconnected_items={unconn}、连通类违例="
        f"{conn_viol}{json_types(conn)}（S6/S7 口径；unclosed/unconnected "
        f"家族）"))
    rec = _reconcile_setup(profile_thresholds, geometry["setup"])
    checks.append(_check(
        "threshold_identity_with_reference_setup",
        not rec["mismatches"] and bool(rec["compared"]),
        (f"{len(rec['compared'])} 项数值一致、{len(rec['mismatches'])} 项"
         f"不符、{len(rec['skipped'])} 项不可比跳过"
         + ("（无可比项——fail-closed）" if not rec["compared"] else ""))))
    geo = _reconcile_actual_geometry(profile_thresholds, geometry)
    checked_geo = [e for e in geo["entries"] if e.get("status") == "checked"]
    checks.append(_check(
        "actual_geometry_meets_thresholds",
        not geo["failed"] and bool(checked_geo),
        (f"{len(checked_geo)} 项实算对账全部 ≥ 阈值"
         if checked_geo and not geo["failed"] else
         f"不符 {len(geo['failed'])} 项/实算 {len(checked_geo)} 项"
         + ("（无实算项——fail-closed）" if not checked_geo else ""))))
    limit = declaration.get("drc_max_error_severity")
    limit_note = ("未声明 drc_max_error_severity：error 级计数只记录不判罚"
                  "（参考态自带违例=上游设计实况，非 pcbflow 产物）")
    if limit is not None:
        err_n = batch["violations_by_severity"].get("error", 0)
        checks.append(_check(
            "drc_error_count_within_declared_limit", err_n <= limit,
            f"error 级计数 {err_n} vs 声明上限 {limit}"))

    zero_nets = advisory_zero_geometry_nets(geometry)
    advisory = [{
        "id": "advisory_per_net_copper_geometry",
        "advisory": True, "authority": "kicad-cli（本项仅第二源交叉核验）",
        "flagged_net_count": len(zero_nets),
        "flagged_nets": zero_nets,
        "evidence": f"命名多焊盘网零铜几何={len(zero_nets)}（corpus 文本"
                    f"解析第二源；不参与 verdict——区填充/文本盲区由 "
                    f"kicad-cli unconnected_items 权威口径兜底）",
    }]

    result = "pass" if all(c["pass"] for c in checks) else "fail"
    return {
        "schema_version": "3.0",
        "artifact_kind": "tl5_check_report",
        "track": TRACK, "check_date": CHECK_DATE,
        "profile_id": profile_id, "board_id": board_id,
        "dataset_role": dataset_role,
        "route_scope": ROUTE_SCOPE,
        "route_scope_note": ROUTE_SCOPE_NOTE,
        "authority": {
            "execution": "reference_verification（D17：参考 routed 态验证，"
                         "非布线生成）",
            "connectivity": "kicad_cli_drc_unconnected_items",
            "drc": "kicad_cli_pcb_drc_dual_severity（severity-error 批 + "
                   "severity-all 终检）",
            "advisory_second_source":
                "corpus_parse_per_net_copper_geometry（advisory）",
        },
        "toolchain": {"kicad_cli_version": drc_summary.get("kicad_version"),
                      "toolchain_lock": "toolchain_lock.json（kicad_cli "
                                        "锁内路径；编排侧 Bash 调用）"},
        "inputs": {k: dict(v) for k, v in sorted(input_refs.items())},
        "denominators": {
            "net_count": geometry["net_count"],
            "named_net_count": geometry["named_net_count"],
            "geometry_counts": geometry["geometry_counts"],
            "items_bound_outside_declared_nets":
                geometry["items_bound_outside_declared_nets"],
        },
        "connectivity": {
            "authority": "kicad_cli_drc_unconnected_items",
            "unconnected_items": unconn,
            "connectivity_type_violations":
                conn["connectivity_type_violations"],
            "named_multi_pad_net_count": sum(
                1 for n in geometry["per_net"]
                if n["name"] != "" and n["pad_count"] >= 2),
            "per_net_status": "connected（kicad-cli 无 unconnected 项；逐网"
                              "铜几何账见 advisory）",
        },
        "drc": drc_summary,
        "threshold_reconciliation": {
            "setup_identity": rec, "actual_geometry": geo,
            "profile_thresholds": dict(sorted(
                profile_thresholds.items())),
        },
        "checks": checks,
        "advisory_checks": advisory,
        "drc_limit_note": limit if limit is not None else limit_note,
        "result": result,
        "result_semantics": "pass=参考 routed 态验证完成且全部对账检查通过；"
                            "非制造签核、非布线能力声明（error 级违例计数"
                            "为参考态实况记录）",
        "field_missingness": {
            "drc_json_date": "kicad-cli 输出自身 date 字段=外部工具原样"
                             "留存（重跑仅该字段变化，violations 可复算）",
            "min_clearance_mm": geo["not_verifiable"]["min_clearance_mm"],
            "via_drill_token": (f"{geometry['vias_without_drill_token']} 个 "
                                "via 无 drill 字面量（上游实况；drill 对账"
                                "仅覆盖有字面量者）") if geometry[
                                    "vias_without_drill_token"] else
                               "全部 via 均有 drill 字面量",
            "drc_max_error_severity": ("null=未声明上限（计数只记录不判罚）"
                                       if limit is None else
                                       f"声明上限={limit}"),
        },
        "producer": MODULE_NAME,
        "determinism_claim": "pure function of injected inputs; byte-exact "
                             "replay（canonical JSON；数值=源字面量 float 化）",
    }


def json_types(conn: dict) -> str:
    detail = conn.get("connectivity_type_violations") or {}
    return f"（types={sorted(detail)}）" if detail else ""


# ---------------------------------------------------------------------------
# 5. 汇总执行记录（out/v3-tl5/check/route-check-execution-record.json）
# ---------------------------------------------------------------------------

def build_execution_record(*, entries: list,
                           toolchain_lock_sha256: str) -> dict:
    """5 profile route/check 段执行汇总（TL-5-G v3 的 route_check 输入）。

    entries: [{profile_id, board_id, dataset_role, reference_route:{path,
    sha256}, staged_board_sha256, declaration:{path,sha256}, check_report:
    {path,sha256,result}, drc:{severity_error:{path,exit,violations},
    severity_all:{...}}, kicad_cli_version}]——事实由编排侧实跑注入。
    """
    if not _HEX64_RE.search(toolchain_lock_sha256 or ""):
        raise ValueError("toolchain_lock_sha256 required (64 hex)")
    if not entries:
        raise ValueError("entries 不可空（fail-closed）")
    norm = []
    for e in entries:
        for key in ("declaration", "check_report", "reference_route"):
            _require_repo_relative(e[key]["path"], f"entries.{key}.path")
        norm.append({
            "profile_id": e["profile_id"], "board_id": e["board_id"],
            "dataset_role": e["dataset_role"],
            "reference_route": dict(e["reference_route"]),
            "staged_board_sha256": e["staged_board_sha256"],
            "staging_identical_to_reference":
                e["staged_board_sha256"] == e["reference_route"]["sha256"],
            "route_check_declaration": dict(e["declaration"]),
            "check_report": dict(e["check_report"]),
            "drc": e["drc"], "kicad_cli_version": e["kicad_cli_version"],
        })
    results: dict = {}
    for e in norm:
        results[e["check_report"]["result"]] = \
            results.get(e["check_report"]["result"], 0) + 1
    all_staged = all(e["staging_identical_to_reference"] for e in norm)
    return {
        "schema_version": "3.0",
        "artifact_kind": "tl5_route_check_execution_record",
        "track": TRACK, "record_date": CHECK_DATE,
        "route_scope": ROUTE_SCOPE,
        "route_scope_note": ROUTE_SCOPE_NOTE,
        "stage_semantics": "route/check executed=参考 routed 态验证执行"
                           "（连通性 kicad-cli authority+DRC 双 severity+"
                           "阈值对账）；布线生成未发生、无布线产物",
        "toolchain": {
            "kicad_cli_version": sorted({
                e["kicad_cli_version"] for e in norm}),
            "toolchain_lock": {"path": "toolchain_lock.json",
                               "sha256": toolchain_lock_sha256},
            "invocation": "编排侧 Bash（staging 拷贝+逐字节一致断言；"
                          "pcbflow .py 零子进程）",
        },
        "entries": norm,
        "summary": {
            "profile_count": len(norm),
            "results": dict(sorted(results.items())),
            "all_staging_identical": all_staged,
            "holdout_readonly": "holdout 板（bm11/t32-ref）只读验证、"
                                "零写回 datasets/",
        },
        "all_pass": (len(norm) > 0 and results.get("pass") == len(norm)
                     and all_staged),
        "producer": MODULE_NAME,
    }


def dumps_canonical(obj) -> str:
    """编排侧统一出口：canonical JSON 文本（零落盘由调用方保证）。"""
    return hashing.json_dumps(obj)
