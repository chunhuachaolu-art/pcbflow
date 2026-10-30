"""V4-EXEC-P09 复查发射管线（MASTER D-7；SUPERVISOR-PLAN §8 V4.0-C/E2 机制件）。

把三个既有断点接成正式管线步骤（全部纯函数；落盘由编排侧完成）：

1. 复查包生成器 ``build_review_package``：solver 终局候选 → 逐对象 diff
   （changed/added/removed + deep-equal 未变集留证）→ 带 state/source 标注的
   diff 视图 SVG + manifest + baseline/diff 双 PNG + 复查摘要（只高亮变更
   对象）。hash 链三绑 = board_snapshot + candidate_geometry + parent
   manifest payload（P0 合同 ``out/v4-comparative-experiment/p0/
   hash-contract-v1.json`` 具名 hash 的直接复用；禁用未限定
   manifest_sha256）。
2. critic 桥（advisory 恒定）：复用 ``pcbflow.critic_run`` 链形（渲染 →
   独立盲读子代理 → 旗标 → 人工队列），输入=复查包 diff 视图。复查专属
   旗标类别；fail-closed（hash 不匹配/stale/schema 非法 → invalid →
   人工队列）。critic 只能对 diff 区域加旗/排序，不能清旗、不能改门
   （L2 加旗律 + TD4 合同原文适用）。
3. disposition 挂钩（L6）：accept/reject/known_open 处置走 ledger 追加
   entry（authority=human / trust_level=untrusted）；只写处置，不写 gate、
   不改判、不升级 trust。

authority 链不变（V4 方案 §5.2）：复查疑点落位走 SVG data-* → manifest
取精确 mm 几何 → 几何 checker → DRC；像素/视觉判断永远只是定位提示。

红线映射：critic 恒 advisory（R6 扩展款）；复查包 append-only（R7，新版本
新文件，本模块零 IO 即零覆写）；对 v4cmp 冻结响应与产物只读引用；不修改
``critic_run.py`` 既有行为（桥接全部在本模块，复用 queue/ledger/disposition
内核）。

生成器模式：零 IO、零子进程、零网络、无 wall-clock、无主机路径；仅标准库
+ 包内 hashing/svg_route_package/ledger/disposition/queue。
"""

from __future__ import annotations

import json

from . import disposition as disposition_mod
from . import hashing, ledger, queue
from . import svg_route_package as srp

REVIEW_SCHEMA = "pcbflow.v4exec.review-package/1"
BUNDLE_KIND = "v4_review_input_bundle"
RECORD_SCHEMA = "v4_review_critic_record"

#: P0 hash 合同具名 hash（三绑；本模块产出的一切 hash 引用均为具名 hash）
BIND_BOARD_SNAPSHOT = "board_snapshot_sha256"
BIND_CANDIDATE_GEOMETRY = "candidate_geometry_sha256"
BIND_PARENT_MANIFEST_PAYLOAD = "parent_manifest_payload_sha256"
THREE_BIND_KEYS = (BIND_BOARD_SNAPSHOT, BIND_CANDIDATE_GEOMETRY,
                   BIND_PARENT_MANIFEST_PAYLOAD)

#: diff 视图逐对象 state/source 标注（srp.ROUTE_STATES/ROUTE_SOURCES 全集内）
STATE_UNCHANGED = ("baseline", "baseline")
STATE_CHANGED = ("candidate", "solver")
STATE_REMOVED = ("rejected", "baseline")

#: 复查旗标类别（advisory；复查专属，与 V3 视觉类别分立）
REVIEW_FLAG_CATEGORIES = ("detour_route", "redundant_via",
                          "suspected_conflict", "other_advisory")

#: 复查处置 kind（L6：accept/reject/known_open；waive/defer 不在复查管线）
REVIEW_DISPOSITION_KINDS = ("accept", "reject", "known_open")

ADVISORY_ONLY_NOTE = (
    "复查/critic 恒 advisory（R6 扩展款；L2 加旗律+TD4 合同）：旗标只能"
    "加旗/排序，不能清旗、不能改门、不能替代几何 checker/DRC authority。")

CALIBRATION_NOTE = (
    "当前无已校准置信域：confidence 仅作 advisory 排序参考，不进入任何 "
    "gate；不确定时用 abstain=true，不得压低 confidence 伪装确定。")

#: 读取者禁止事项（盲读纪律；G4 隔离清单的合同化）
PROHIBITIONS = (
    "不得形成 DRC/几何合法性/可制造性结论（advisory 只出旗标；几何以 "
    "checker/DRC 为唯一 authority）",
    "不得给出任何修改指令（改线、改 via、改布局等一律禁止）",
    "不得消旗/降级既有旗标（L2 加旗律：flags 单调增长）",
    "不得自封 critic_status/executed/valid——状态与合法性由管线赋值",
    "不确定就 abstain=true；宁缺勿造，禁止编造位置或现象",
    "只依据任务卡允许的输入盲读；如发现输入含参考答案/校验结果/处置"
    "历史等禁止材料，立即 abstain 并在 reading_notes 声明",
)

RAW_TOPLEVEL_KEYS = ("reader_id", "per_case", "reading_notes")
RAW_CASE_KEYS = ("case_id", "flags")
RAW_FLAG_KEYS = ("category", "confidence", "location_evidence",
                 "description", "abstain")
READER_ID_MAX = 128
LOCATION_MAX = 256
DESCRIPTION_MAX = 1024

SUMMARY_SCHEMA = "pcbflow.v4exec.review-summary/1"


# ---------------------------------------------------------------------------
# P0 合同 hash 口径（canonical json + strip_sha；与具名 hash 合同逐字对应）
# ---------------------------------------------------------------------------

def _canonical_json(obj) -> str:
    """铜族（紧凑）形态——登记=exec/CANONICAL-JSON-FORM-MAP-2026-09-25.md。"""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False)


def _strip_sha(obj):
    """递归剔除一切 *_sha256 结尾的键（P0 合同 strip_sha 规则）。"""
    if isinstance(obj, dict):
        return {k: _strip_sha(v) for k, v in obj.items()
                if not (isinstance(k, str) and k.endswith("_sha256"))}
    if isinstance(obj, list):
        return [_strip_sha(v) for v in obj]
    return obj


def object_sha256(obj) -> str:
    """P0 合同对象 hash：sha256(canonical_json(strip_sha(obj)).utf-8)。"""
    return hashing.sha256_bytes(_canonical_json(_strip_sha(obj)).encode(
        "utf-8"))


def candidate_geometry_sha256(geom) -> str:
    """候选几何 {routes,vias} 对象 hash（P0 合同 candidate_geometry_sha256）。

    与 v4cmp ``cmp_patch.candidate_geometry_sha256`` 同口径（canonical、
    strip_sha）；非法/非有限输入返回空串，不让异常穿越信任边界。
    """
    if not isinstance(geom, dict) or "routes" not in geom \
            or "vias" not in geom:
        return ""
    try:
        return object_sha256({"routes": geom["routes"],
                              "vias": geom["vias"]})
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# 复查包生成器
# ---------------------------------------------------------------------------

def _relation_ids(board: dict, net_id: str) -> list:
    return sorted(str(r["relation_id"]) for r in board.get("relations", [])
                  if net_id in r.get("members", []))


def _line_type(board: dict, net_id: str) -> str:
    net = next((n for n in board["nets"]
                if str(n["net_id"]) == str(net_id)), None)
    if net is None:
        return "signal"
    cls = str(net.get("net_class", "default"))
    if cls == "clock":
        return "clock"
    if any(r.get("relation_type") == "bus" for r in board.get("relations", [])
           if net_id in r.get("members", [])):
        return "bus_member"
    return "signal"


def enrich_geometry(board: dict, geom: dict, *, state: str,
                    source: str) -> dict:
    """候选/baseline 几何 → srp.build 可消费的 ref（补齐身份字段，标注
    state/source；不改变几何事实）。state/source 必须在枚举内。"""
    if state not in srp.ROUTE_STATES:
        raise ValueError(f"enrich_geometry: state {state!r} 非法")
    if source not in srp.ROUTE_SOURCES:
        raise ValueError(f"enrich_geometry: source {source!r} 非法")
    if not isinstance(geom, dict) or not isinstance(geom.get("routes"), list) \
            or not isinstance(geom.get("vias"), list):
        raise ValueError("enrich_geometry: geom 需含 routes/vias 列表")
    routes = []
    for raw in geom["routes"]:
        r = dict(raw)
        nid = str(r["net_id"])
        r.setdefault("relation_ids", _relation_ids(board, nid))
        r.setdefault("line_type", _line_type(board, nid))
        r.setdefault("parent_id", None)
        r.setdefault("constraint_refs", [
            "C-clearance-%03d" % int(round(
                float(board["rules"]["clearance_mm"]) * 1000)),
            "C-width-%03d" % int(round(float(r["width_mm"]) * 1000)),
        ])
        r["state"] = state
        r["source"] = source
        routes.append(r)
    vias = [dict(v) for v in geom["vias"]]
    for v in vias:
        v["state"] = state
        v["source"] = source
    return {"scenario_id": str(board["scenario_id"]),
            "routes": routes, "vias": vias}


#: diff 比对时剥离的视图标注字段（state/source 是复查视图标注、svg_id 是
#: 派生 id——几何身份比对只看其余字段，未变对象逐字段 deep-equal 留证）
_ANNOTATION_KEYS = ("state", "source", "svg_id")


def _identity(obj: dict) -> dict:
    return {k: v for k, v in obj.items() if k not in _ANNOTATION_KEYS}


def _obj_key(obj: dict) -> str:
    return _canonical_json(_identity(obj))


def diff_geometries(baseline_norm: dict, candidate_norm: dict) -> dict:
    """逐对象 diff（未变对象逐字段 deep-equal 留证；P1 G5 内核复用）。

    输入两侧均为 srp 规范化后的 {routes,vias}（同板同身份：route_id/
    via_id 跨侧稳定）。返回按 id 索引的三态清单与未变集。
    """
    for name, side in (("baseline", baseline_norm),
                       ("candidate", candidate_norm)):
        if not isinstance(side, dict) \
                or not isinstance(side.get("routes"), list) \
                or not isinstance(side.get("vias"), list):
            raise ValueError(f"diff_geometries: {name} 需含 routes/vias 列表")
    out = {}
    for kind, keyf in (("route", "route_id"), ("via", "via_id")):
        base = {str(o[keyf]): o for o in baseline_norm[f"{kind}s"]}
        cand = {str(o[keyf]): o for o in candidate_norm[f"{kind}s"]}
        out[f"{kind}_changed"] = sorted(k for k in cand
                                        if k in base
                                        and _obj_key(base[k]) != _obj_key(cand[k]))
        out[f"{kind}_added"] = sorted(k for k in cand if k not in base)
        out[f"{kind}_removed"] = sorted(k for k in base if k not in cand)
        out[f"{kind}_unchanged"] = sorted(
            k for k in cand
            if k in base and _obj_key(base[k]) == _obj_key(cand[k]))
    return out


def _diff_view_ref(board: dict, baseline_norm: dict, candidate_norm: dict,
                   diff: dict) -> dict:
    """diff 视图 ref：未变=baseline/baseline；变更/新增=candidate/solver；
    移除=rejected/baseline（同图对照，route_id/via_id 恒为真实身份）。"""
    routes = []
    for o in candidate_norm["routes"]:
        rid = str(o["route_id"])
        if rid in diff["route_changed"] or rid in diff["route_added"]:
            r = dict(o)
            r["state"] = STATE_CHANGED[0]
            r["source"] = STATE_CHANGED[1]
        else:
            r = dict(o)
            r["state"] = STATE_UNCHANGED[0]
            r["source"] = STATE_UNCHANGED[1]
        routes.append(r)
    for rid in diff["route_removed"]:
        base = next(o for o in baseline_norm["routes"]
                    if str(o["route_id"]) == rid)
        r = dict(base)
        r["state"] = STATE_REMOVED[0]
        r["source"] = STATE_REMOVED[1]
        routes.append(r)
    vias = []
    for o in candidate_norm["vias"]:
        vid = str(o["via_id"])
        v = dict(o)
        if vid in diff["via_changed"] or vid in diff["via_added"]:
            v["state"] = STATE_CHANGED[0]
            v["source"] = STATE_CHANGED[1]
        else:
            v["state"] = STATE_UNCHANGED[0]
            v["source"] = STATE_UNCHANGED[1]
        vias.append(v)
    for vid in diff["via_removed"]:
        base = next(o for o in baseline_norm["vias"]
                    if str(o["via_id"]) == vid)
        v = dict(base)
        v["state"] = STATE_REMOVED[0]
        v["source"] = STATE_REMOVED[1]
        vias.append(v)
    return {"scenario_id": str(board["scenario_id"]),
            "routes": routes, "vias": vias}


def _require_valid_baseline_pkg(board: dict, baseline_pkg) -> None:
    if not isinstance(baseline_pkg, dict):
        raise ValueError("baseline_pkg: 不是对象")
    man = baseline_pkg.get("manifest")
    if not isinstance(man, dict):
        raise ValueError("baseline_pkg.manifest: 缺失")
    if man.get("scenario_id") != str(board["scenario_id"]):
        raise ValueError("baseline_pkg.manifest.scenario_id 与板不一致")
    for key in ("routes", "vias"):
        if not isinstance(man.get(key), list):
            raise ValueError(f"baseline_pkg.manifest.{key}: 必须是列表")
    if not isinstance(baseline_pkg.get("svg_text"), str):
        raise ValueError("baseline_pkg.svg_text: 缺失")


def _changed_object_records(baseline_norm: dict, candidate_norm: dict,
                            diff: dict) -> list:
    records = []
    for rid in diff["route_changed"]:
        old = next(o for o in baseline_norm["routes"]
                   if str(o["route_id"]) == rid)
        new = next(o for o in candidate_norm["routes"]
                   if str(o["route_id"]) == rid)
        records.append({
            "object_type": "route", "object_id": rid,
            "net_id": new["net_id"], "layer": new["layer"],
            "width_mm": new["width_mm"],
            "old_polyline_mm": old["polyline_mm"],
            "new_polyline_mm": new["polyline_mm"],
            "old_state": STATE_UNCHANGED[0], "new_state": STATE_CHANGED[0],
        })
    for rid in diff["route_added"]:
        new = next(o for o in candidate_norm["routes"]
                   if str(o["route_id"]) == rid)
        records.append({
            "object_type": "route", "object_id": rid,
            "net_id": new["net_id"], "layer": new["layer"],
            "width_mm": new["width_mm"],
            "old_polyline_mm": None,
            "new_polyline_mm": new["polyline_mm"],
            "old_state": None, "new_state": STATE_CHANGED[0],
        })
    for rid in diff["route_removed"]:
        old = next(o for o in baseline_norm["routes"]
                   if str(o["route_id"]) == rid)
        records.append({
            "object_type": "route", "object_id": rid,
            "net_id": old["net_id"], "layer": old["layer"],
            "width_mm": old["width_mm"],
            "old_polyline_mm": old["polyline_mm"],
            "new_polyline_mm": None,
            "old_state": STATE_UNCHANGED[0], "new_state": STATE_REMOVED[0],
        })
    return records


def _require_rejections(validator_rejections) -> list:
    if validator_rejections is None:
        return []
    if not isinstance(validator_rejections, list):
        raise ValueError("validator_rejections: 必须是列表或 None")
    out = []
    for r in validator_rejections:
        if not isinstance(r, dict):
            raise ValueError("validator_rejections[*]: 不是对象")
        for f in ("route_id", "reason_class", "reasons"):
            if f not in r:
                raise ValueError(f"validator_rejections[*]: 缺字段 {f}")
        if r["reason_class"] not in _REJECTION_CLASSES:
            raise ValueError(
                f"validator_rejections[*].reason_class {r['reason_class']!r}"
                f" 非法（合法集 {list(_REJECTION_CLASSES)}）")
        out.append({"route_id": str(r["route_id"]),
                    "reason_class": r["reason_class"],
                    "reasons": [str(x) for x in r["reasons"]]})
    return out


#: 已知 validator 拒绝原因类（G6 载体；与 cmp_patch 拒绝语义对应的稳定枚举）
_REJECTION_CLASSES = ("base_hash_mismatch", "endpoint_moved",
                      "keepout_or_collision", "off_grid_coord",
                      "width_mismatch", "layer_mismatch", "unknown_identity",
                      "undeclared_change", "illegal_geometry", "other")


def build_review_package(board: dict, baseline_pkg: dict, candidate_geom: dict,
                         *, case_id: str,
                         validator_rejections=None) -> dict:
    """candidate → diff 标注复查包（纯函数；落盘由编排侧完成）。

    baseline_pkg 为 baseline 视图包（srp.build 产物：svg_text + manifest），
    由调用方对 baseline 几何先行构建——本函数零覆写它，只读引用其
    manifest（parent 绑定）。返回 ReviewPackage canonical dict。
    """
    if not (isinstance(case_id, str) and case_id):
        raise ValueError("build_review_package: case_id 必须为非空字符串")
    _require_valid_baseline_pkg(board, baseline_pkg)
    if not isinstance(candidate_geom, dict) \
            or not isinstance(candidate_geom.get("routes"), list) \
            or not isinstance(candidate_geom.get("vias"), list):
        raise ValueError("candidate_geom: 需含 routes/vias 列表")
    rejections = _require_rejections(validator_rejections)

    # 两侧规范化（同一 srp 口径；身份字段同源补齐）
    base_ref = enrich_geometry(board, _manifest_geom(baseline_pkg["manifest"]),
                               state=STATE_UNCHANGED[0],
                               source=STATE_UNCHANGED[1])
    _, base_norm_man = srp.build(board, base_ref)
    cand_ref = enrich_geometry(board, candidate_geom, state=STATE_CHANGED[0],
                               source=STATE_CHANGED[1])
    _, cand_norm_man = srp.build(board, cand_ref)

    diff = diff_geometries(base_norm_man, cand_norm_man)
    diff_ref = _diff_view_ref(board, base_norm_man, cand_norm_man, diff)
    diff_svg, diff_man = srp.build(board, diff_ref)

    png_baseline = srp.render_png(board, baseline_pkg["manifest"])
    png_diff = srp.render_png(board, diff_man)

    bsha = baseline_pkg["manifest"]["board_snapshot_sha256"]
    if diff_man["board_snapshot_sha256"] != bsha \
            or cand_norm_man["board_snapshot_sha256"] != bsha:
        raise ValueError("board_snapshot_sha256 三视图不一致（fail-closed）")
    three_bind = {
        BIND_BOARD_SNAPSHOT: bsha,
        BIND_CANDIDATE_GEOMETRY: candidate_geometry_sha256(candidate_geom),
        BIND_PARENT_MANIFEST_PAYLOAD:
            baseline_pkg["manifest"]["manifest_payload_sha256"],
    }
    if not all(three_bind.values()):
        raise ValueError("three_bind 存在空 hash（fail-closed）")

    summary = {
        "schema": SUMMARY_SCHEMA,
        "case_id": case_id,
        "scenario_id": str(board["scenario_id"]),
        "three_bind": three_bind,
        "diff": {k: v for k, v in diff.items()},
        "changed_objects": _changed_object_records(
            base_norm_man, cand_norm_man, diff),
        "counts": {
            "route_changed": len(diff["route_changed"]),
            "route_added": len(diff["route_added"]),
            "route_removed": len(diff["route_removed"]),
            "route_unchanged": len(diff["route_unchanged"]),
            "via_changed": len(diff["via_changed"]),
            "via_added": len(diff["via_added"]),
            "via_removed": len(diff["via_removed"]),
            "via_unchanged": len(diff["via_unchanged"]),
        },
        "validator_rejections": rejections,
        "view_annotation": {
            "unchanged": list(STATE_UNCHANGED),
            "changed_added": list(STATE_CHANGED),
            "removed": list(STATE_REMOVED),
            "note": "diff 视图逐对象 state/source 标注；route_id/via_id 恒为"
                    "真实身份（跨视图可回查）",
        },
        "advisory_note": ADVISORY_ONLY_NOTE,
    }
    pkg = {
        "schema": REVIEW_SCHEMA,
        "package_id": "RP-%s" % case_id,
        "case_id": case_id,
        "scenario_id": str(board["scenario_id"]),
        "three_bind": three_bind,
        "baseline_view": {
            "svg_text": baseline_pkg["svg_text"],
            "manifest": baseline_pkg["manifest"],
            "png": _png_record(png_baseline),
        },
        "diff_view": {
            "svg_text": diff_svg,
            "manifest": diff_man,
            "png": _png_record(png_diff),
        },
        "summary": summary,
    }
    pkg["review_package_sha256"] = object_sha256(pkg)
    return pkg


def _manifest_geom(manifest: dict) -> dict:
    """manifest 的规范化 routes/vias → 几何（回填 state/source 供再入 enrich）。"""
    routes = []
    for o in manifest["routes"]:
        r = dict(o)
        r.setdefault("state", STATE_UNCHANGED[0])
        r.setdefault("source", STATE_UNCHANGED[1])
        routes.append(r)
    vias = [dict(o) for o in manifest["vias"]]
    return {"routes": routes, "vias": vias}


def _png_record(rendered: dict) -> dict:
    """PNG 证据记录：包内以具名 hash 绑定（png_sha256），字节不入包——
    canonical 复查包保持纯 JSON 可序列化；字节经
    ``render_review_package_pngs`` 确定性重渲染取得（同输入逐字节一致）。"""
    if not rendered.get("available"):
        return {"available": False, "status": rendered.get("status"),
                "reason": rendered.get("reason")}
    return {"available": True,
            "width": rendered["width"], "height": rendered["height"],
            "png_sha256": hashing.sha256_bytes(rendered["png_bytes"])}


def render_review_package_pngs(board: dict, pkg: dict) -> dict:
    """复查包双通道 PNG 字节（确定性重渲染；hash 须与包内 png_sha256 一致，
    漂移即 ValueError fail-closed）。纯函数；落盘由编排侧完成。"""
    out = {}
    for view in ("baseline_view", "diff_view"):
        rec = pkg[view]["png"]
        if not rec.get("available"):
            out[view] = None
            continue
        rendered = srp.render_png(board, pkg[view]["manifest"],
                                  width=rec["width"], height=rec["height"])
        data = rendered.get("png_bytes")
        if not rendered.get("available") or data is None:
            raise ValueError(f"render_review_package_pngs: {view} 重渲染失败"
                             "（fail-closed）")
        if hashing.sha256_bytes(data) != rec["png_sha256"]:
            raise ValueError(f"render_review_package_pngs: {view} 重渲染"
                             " hash 与包内绑定不符（fail-closed）")
        out[view] = data
    return out


def review_package_sha256(pkg: dict) -> str:
    """复查包 canonical hash（strip_sha 自引键后计算）。"""
    return object_sha256(pkg)


def verify_review_package(pkg, *, expected_three_bind=None) -> list:
    """复查包完整性校验（编排侧读回后调用；返回错误列表，[]=合法）。"""
    errs = []
    if not isinstance(pkg, dict) or pkg.get("schema") != REVIEW_SCHEMA:
        return ["review package: schema 非法"]
    tb = pkg.get("three_bind")
    if not isinstance(tb, dict) or sorted(tb) != sorted(THREE_BIND_KEYS):
        errs.append("three_bind: 键集不符（须为三个具名 hash）")
        return errs
    for k, v in tb.items():
        if not (isinstance(v, str) and len(v) == 64
                and all(ch in "0123456789abcdef" for ch in v)):
            errs.append(f"three_bind.{k}: 非法 hash 形状")
    recomputed = object_sha256(pkg)
    if pkg.get("review_package_sha256") != recomputed:
        errs.append("review_package_sha256 重算不一致（内容被篡改或口径漂移）")
    if expected_three_bind is not None:
        for k in THREE_BIND_KEYS:
            if expected_three_bind.get(k) != tb.get(k):
                errs.append(f"three_bind.{k}: 与期望不符（stale）")
    for view in ("baseline_view", "diff_view"):
        v = pkg.get(view)
        if not isinstance(v, dict) or not isinstance(v.get("svg_text"), str) \
                or not isinstance(v.get("manifest"), dict):
            errs.append(f"{view}: 结构缺失")
    if not isinstance(pkg.get("summary"), dict):
        errs.append("summary: 缺失")
    return errs


# ---------------------------------------------------------------------------
# critic 桥（advisory 恒定；链形复用 critic_run，桥接全在本模块）
# ---------------------------------------------------------------------------

def review_reader_task_card(*, cases: list) -> dict:
    """读取者任务卡（bundle 内字段；主审按此派发盲读子代理）。"""
    return {
        "mission": (
            "以 advisory 身份对复查包 diff 视图做盲读：对照 baseline 视图，"
            "只对变更/新增/移除对象所在区域输出旗标（类别/置信度/位置证据/"
            "说明）。允许类别以 bundle.allowed_categories 为准；本任务不"
            "裁决任何质量结论。"),
        "untrusted_note": (
            "读取者输出恒为 untrusted 模型输出：critic_status/valid、"
            "flags=[] 是否表示「无旗」均由管线（pcbflow.v4_review_dispatch."
            "ingest_review_run）赋值，读者不得自封任何状态或合法性。"),
        "inputs": {
            "per_case": ["diff_view SVG 源码", "diff_view PNG",
                         "baseline_view PNG", "summary.diff 对象清单"
                         "（仅 diff 三态 id 列表与标注说明）"],
            "bundle_fields": ("allowed_categories", "confidence_scale",
                              "prohibitions", "cases"),
        },
        "output_contract": {
            "format": ("单个 JSON 对象以文本返回（主审原样字节落盘 "
                       "raw-flags.json；不得改写读者文本）"),
            "shape": {
                "reader_id": "非空字符串（≤128 字符）",
                "per_case": [{
                    "case_id": "必须与 bundle.cases[].case_id 一一对应",
                    "flags": [{
                        "category": "allowed_categories 枚举之一",
                        "confidence": "0.0–1.0 数值（不含布尔）",
                        "location_evidence": (
                            "非空位置证据（≤256 字符）；必须含所指对象的"
                            " route_id 或 via_id（diff manifest 内可回查）"),
                        "description": "非空说明（≤1024 字符）",
                        "abstain": "布尔；不确定=true，禁止编造",
                    }],
                }],
                "reading_notes": "字符串；每例 flags=[] 时必须在此说明依据",
            },
            "requirements": (
                "每例必须出现且仅出现一次（case_id 精确匹配）；每例给出 "
                "flags 数组（可为空数组+reading_notes 说明）；只对变更/"
                "新增/移除对象区域加旗；不确定就 abstain=true；只输出观察"
                "不输出结论或指令。"),
        },
    }


def build_review_bundle(*, run_id: str, cases: list, approval_sha256: str,
                        calibration_domain_established: bool = False,
                        viewer_files_by_case=None) -> dict:
    """构建 critic 输入 bundle（canonical dict；byte-exact 由调用方复验）。

    cases 每项：{case_id, review_package_sha256,
                 three_bind: {board_snapshot_sha256,
                              candidate_geometry_sha256,
                              parent_manifest_payload_sha256},
                 files: {diff_svg/diff_png/baseline_png/summary:
                         {file_rel, sha256}}}。
    非法输入 ValueError（fail-closed；bundle 是管线可信侧输入）。

    V4-EXEC-P10 桥接（追加式，向后兼容）：可选 ``viewer_files_by_case``
    = {case_id: {baseline_viewer_html / diff_viewer_html:
    {file_rel, sha256}}}（由 :func:`review_viewer_files` 产出后落盘的
    附件记录）。**不传（默认 None）时输出与历史逐字节一致**；传入时
    每个规范化 case 附加 ``viewer_files`` 键（新产物新文件，R7；不回写
    任何既有 bundle/复查包文件）。
    """
    if not (isinstance(run_id, str) and run_id):
        raise ValueError("build_review_bundle: run_id 必须为非空字符串")
    if not (isinstance(approval_sha256, str) and len(approval_sha256) == 64
            and all(ch in "0123456789abcdef" for ch in approval_sha256)):
        raise ValueError("build_review_bundle: approval_sha256 必须为 64-hex")
    if not isinstance(calibration_domain_established, bool):
        raise ValueError("build_review_bundle: calibration_domain_established"
                         " 必须为布尔")
    norm_cases = []
    seen = set()
    for c in cases:
        nc = _norm_bundle_case(c, seen)
        if viewer_files_by_case is not None:
            vf = viewer_files_by_case.get(nc["case_id"])
            if vf is not None:
                nc["viewer_files"] = _norm_viewer_files(nc["case_id"], vf)
        norm_cases.append(nc)
    norm_cases.sort(key=lambda c: c["case_id"])
    return {
        "schema_version": 3,
        "kind": BUNDLE_KIND,
        "run_id": run_id,
        "selection_rule": (
            "发展域复查发射验证样本（protocol-r4-review-v1 冻结清单）；"
            "holdout 冻结集零接触（R8）"),
        "cases": norm_cases,
        "td4_inputs_absent": (
            "TD4 critic 输入=板渲染、前后 diff、提议摘要、确定性 artifact "
            "refs。本桥输入=复查包 diff 视图（前后 diff 已内建于视图）；"
            "提议摘要以 diff 对象清单承载；validator 拒绝记录、处置历史、"
            "GT 与门结果一律不在盲读上下文（G4 隔离），缺席如实声明。"),
        "allowed_categories": list(REVIEW_FLAG_CATEGORIES),
        "confidence_scale": {
            "range": "0.0–1.0",
            "abstain_rule": "不确定就 abstain=true，禁止编造",
            "calibration_note": CALIBRATION_NOTE,
        },
        "prohibitions": list(PROHIBITIONS),
        "calibration": {
            "domain_established": calibration_domain_established,
            "note": CALIBRATION_NOTE,
        },
        "approval": {
            "disposition_id": "APR-0005",
            "duty_level": "advisory_only",
            "path_rel": ("out/v3-approvals/"
                         "disposition-APR-0005-critic-duty-level.json"),
            "sha256": approval_sha256,
            "note": ("model.approved 的唯一依据指针（人工批准：advisory_only"
                     " 最小上岗等级）；编排侧实测该文件 sha256 后绑定。"),
        },
        "reader_task_card": review_reader_task_card(cases=norm_cases),
        "pipeline": {
            "record_schema": RECORD_SCHEMA,
            "status_assigned_by": "pcbflow.v4_review_dispatch.ingest_review_run",
            "queue_events": "pcbflow.queue（queue-event-ledger 内核）",
            "advisory_only": True,
            "authority_note": ADVISORY_ONLY_NOTE,
        },
    }


_BUNDLE_FILE_ROLES = ("diff_svg", "diff_png", "baseline_png", "summary")

#: V4-EXEC-P10：viewer 附件角色（可选；新产物新文件，R7）
VIEWER_FILE_ROLES = ("baseline_viewer_html", "diff_viewer_html")


def _norm_viewer_files(case_id: str, vf) -> dict:
    """viewer 附件记录规范化（fail-closed；结构与 files 同款）。"""
    if not isinstance(vf, dict) or sorted(vf) != sorted(VIEWER_FILE_ROLES):
        raise ValueError(f"bundle case {case_id}: viewer_files 键集不符"
                         f"（须为 {VIEWER_FILE_ROLES}）")
    norm = {}
    for role in VIEWER_FILE_ROLES:
        f = vf[role]
        if not isinstance(f, dict) or not f.get("file_rel") \
                or not (isinstance(f.get("sha256"), str)
                        and len(f["sha256"]) == 64
                        and all(ch in "0123456789abcdef"
                                for ch in f["sha256"])):
            raise ValueError(f"bundle case {case_id}: viewer_files.{role}"
                             " 非法（file_rel + 64-hex sha256）")
        norm[role] = {"file_rel": str(f["file_rel"]),
                      "sha256": f["sha256"]}
    return norm


def review_viewer_files(board: dict, pkg: dict) -> dict:
    """V4-EXEC-P10 桥接：复查包 → viewer HTML 附件（纯函数，零 IO）。

    对 pkg 的 baseline_view / diff_view 各生成一份自包含 route-viewer
    HTML（``pcbflow.v4_route_viewer.build_route_viewer``；交互过滤/高亮
    /计数/view-spec 导出），返回 {view: {"html_text": str,
    "html_sha256": str}}。生成器自身 fail-closed（board/manifest/SVG
    三方 hash 不一致即 ValueError）。**只读 pkg，不写任何既有文件**
    （新产物由编排侧落盘到新路径；out/v4-exec/r4-review/ 冻结件零回写）。

    注意：viewer 是表现层皮肤——不改变复查包任何 authority 字段，
    bundle 是否携带附件由编排侧显式选择（``build_review_bundle`` 的
    viewer_files_by_case）。
    """
    from . import v4_route_viewer as vrv  # 惰性：P09 既有路径零新依赖
    out = {}
    for view in ("baseline_view", "diff_view"):
        v = pkg.get(view) if isinstance(pkg, dict) else None
        if not isinstance(v, dict) or not isinstance(
                v.get("manifest"), dict) \
                or not isinstance(v.get("svg_text"), str):
            raise ValueError(f"review_viewer_files: pkg.{view} 缺 "
                             "svg_text/manifest（fail-closed）")
        title = "%s %s" % (pkg.get("case_id", ""), view)
        html = vrv.build_route_viewer(board, v["manifest"], v["svg_text"],
                                      title=title)
        out[view] = {"html_text": html,
                     "html_sha256": hashing.sha256_bytes(
                         html.encode("utf-8"))}
    return out


def _norm_bundle_case(c, seen: set) -> dict:
    if not isinstance(c, dict):
        raise ValueError("bundle case: 不是对象")
    cid = c.get("case_id")
    if not (isinstance(cid, str) and cid) or cid in seen:
        raise ValueError(f"bundle case: case_id 缺失或重复 {cid!r}")
    seen.add(cid)
    rsha = c.get("review_package_sha256")
    if not (isinstance(rsha, str) and len(rsha) == 64
            and all(ch in "0123456789abcdef" for ch in rsha)):
        raise ValueError(f"bundle case {cid}: review_package_sha256 非法")
    tb = c.get("three_bind")
    if not isinstance(tb, dict) or sorted(tb) != sorted(THREE_BIND_KEYS):
        raise ValueError(f"bundle case {cid}: three_bind 键集不符")
    for k, v in tb.items():
        if not (isinstance(v, str) and len(v) == 64
                and all(ch in "0123456789abcdef" for ch in v)):
            raise ValueError(f"bundle case {cid}: three_bind.{k} 非法")
    files = c.get("files")
    if not isinstance(files, dict) or sorted(files) != sorted(
            _BUNDLE_FILE_ROLES):
        raise ValueError(f"bundle case {cid}: files 键集不符")
    norm_files = {}
    for role in _BUNDLE_FILE_ROLES:
        f = files[role]
        if not isinstance(f, dict) or not f.get("file_rel") \
                or not (isinstance(f.get("sha256"), str)
                        and len(f["sha256"]) == 64):
            raise ValueError(f"bundle case {cid}: files.{role} 非法")
        norm_files[role] = {"file_rel": str(f["file_rel"]),
                            "sha256": f["sha256"]}
    return {"case_id": cid, "review_package_sha256": rsha,
            "three_bind": dict(tb), "files": norm_files}


def review_bundle_sha256(bundle: dict) -> str:
    """bundle 的 canonical 字节 sha256（sidecar 值；bundle 内不嵌自引）。"""
    return hashing.sha256_bytes(hashing.canonical_json_bytes(bundle))


def validate_review_bundle(bundle) -> None:
    """bundle 结构校验（管线可信侧；非法 ValueError）。"""
    if not isinstance(bundle, dict):
        raise ValueError("validate_review_bundle: bundle 必须为 dict")
    if bundle.get("kind") != BUNDLE_KIND:
        raise ValueError(f"validate_review_bundle: kind 应为 {BUNDLE_KIND!r}")
    if not (isinstance(bundle.get("run_id"), str) and bundle["run_id"]):
        raise ValueError("validate_review_bundle: run_id 缺失")
    if bundle.get("allowed_categories") != list(REVIEW_FLAG_CATEGORIES):
        raise ValueError("validate_review_bundle: allowed_categories 与复查"
                         "类别集不一致")
    cal = bundle.get("calibration")
    if not (isinstance(cal, dict)
            and isinstance(cal.get("domain_established"), bool)):
        raise ValueError("validate_review_bundle: calibration.domain_"
                         "established 必须为布尔")
    ap = bundle.get("approval")
    if not (isinstance(ap, dict) and ap.get("disposition_id") == "APR-0005"
            and ap.get("duty_level") == "advisory_only"
            and isinstance(ap.get("sha256"), str)):
        raise ValueError("validate_review_bundle: approval 块缺失或非法")
    if not isinstance(bundle.get("reader_task_card"), dict):
        raise ValueError("validate_review_bundle: reader_task_card 缺失")
    if not isinstance(bundle.get("cases"), list) or not bundle["cases"]:
        raise ValueError("validate_review_bundle: cases 必须为非空列表")
    seen = set()
    for c in bundle["cases"]:
        _norm_bundle_case(c, seen)


def validate_review_raw_flags(raw, *, expected_case_ids) -> list:
    """raw flags（untrusted 读取者输出）结构+语义校验；[]=合法。

    顶层键固定 reader_id/per_case/reading_notes（多余键=invalid——读者
    自封 status/valid 等字段由此挡下）；per_case 与 expected_case_ids
    一一对应；flag 字段固定、category 枚举、location 非空。
    """
    errs = []
    expected = [str(x) for x in expected_case_ids]
    if not isinstance(raw, dict):
        return ["raw_flags: 不是 JSON 对象"]
    unknown = sorted(set(raw) - set(RAW_TOPLEVEL_KEYS))
    if unknown:
        errs.append(f"raw_flags: 未知顶层键 {unknown}（白名单外一律 invalid）")
    for k in RAW_TOPLEVEL_KEYS:
        if k not in raw:
            errs.append(f"raw_flags: 缺顶层键 {k}")
    if errs:
        return errs
    if not (isinstance(raw["reader_id"], str) and raw["reader_id"]
            and len(raw["reader_id"]) <= READER_ID_MAX):
        errs.append("raw_flags.reader_id: 非空且 ≤128 字符")
    if not isinstance(raw["reading_notes"], str):
        errs.append("raw_flags.reading_notes: 必须是字符串")
    cases = raw["per_case"]
    if not isinstance(cases, list):
        errs.append("raw_flags.per_case: 必须是列表")
        return errs
    seen = []
    for i, c in enumerate(cases):
        if not isinstance(c, dict):
            errs.append(f"per_case[{i}]: 不是对象")
            continue
        unknown_c = sorted(set(c) - set(RAW_CASE_KEYS))
        if unknown_c:
            errs.append(f"per_case[{i}]: 未知键 {unknown_c}")
        cid = c.get("case_id")
        if not isinstance(cid, str) or not cid:
            errs.append(f"per_case[{i}].case_id: 缺失")
            continue
        seen.append(cid)
        if cid not in expected:
            errs.append(f"per_case[{i}].case_id {cid!r} 不在期望集")
        flags = c.get("flags")
        if not isinstance(flags, list):
            errs.append(f"per_case[{i}].flags: 必须是列表")
            continue
        for j, f in enumerate(flags):
            errs.extend(_flag_errors(f, f"per_case[{i}].flags[{j}]"))
    dup = sorted({x for x in seen if seen.count(x) > 1})
    if dup:
        errs.append(f"per_case: case_id 重复 {dup}")
    missing = [x for x in expected if x not in seen]
    if missing:
        errs.append(f"per_case: 缺例 {missing}")
    return errs


def _flag_errors(f, where: str) -> list:
    if not isinstance(f, dict):
        return [f"{where}: 不是对象"]
    errs = []
    unknown = sorted(set(f) - set(RAW_FLAG_KEYS))
    if unknown:
        errs.append(f"{where}: 未知键 {unknown}")
    for k in RAW_FLAG_KEYS:
        if k not in f:
            errs.append(f"{where}: 缺字段 {k}")
    if errs:
        return errs
    if f["category"] not in REVIEW_FLAG_CATEGORIES:
        errs.append(f"{where}.category {f['category']!r} 非法"
                    f"（合法集 {list(REVIEW_FLAG_CATEGORIES)}）")
    conf = f["confidence"]
    if isinstance(conf, bool) or not isinstance(conf, (int, float)) \
            or not 0.0 <= float(conf) <= 1.0:
        errs.append(f"{where}.confidence: 须为 0.0–1.0 数值")
    loc = f["location_evidence"]
    if not (isinstance(loc, str) and loc and len(loc) <= LOCATION_MAX):
        errs.append(f"{where}.location_evidence: 非空且 ≤{LOCATION_MAX} 字符")
    desc = f["description"]
    if not (isinstance(desc, str) and desc and len(desc) <= DESCRIPTION_MAX):
        errs.append(f"{where}.description: 非空且 ≤{DESCRIPTION_MAX} 字符")
    if not isinstance(f["abstain"], bool):
        errs.append(f"{where}.abstain: 必须为布尔")
    return errs


def flags_object_traceability(raw, *, object_ids_by_case: dict) -> list:
    """G3：每条旗标 location_evidence 须指认 diff manifest 内对象 id。

    object_ids_by_case: {case_id: set(route_id/via_id 字符串)}。
    返回错误列表（[]=全部可回查）。
    """
    errs = []
    for c in raw.get("per_case", []):
        cid = c.get("case_id")
        known = object_ids_by_case.get(cid)
        if known is None:
            errs.append(f"traceability: {cid!r} 无对象 id 集")
            continue
        for f in c.get("flags", []):
            loc = str(f.get("location_evidence", ""))
            hit = sorted(o for o in known if o in loc)
            if not hit:
                errs.append(f"traceability[{cid}]: 旗标位置证据不含任何可回查"
                            f"对象 id（{loc[:60]!r}…）")
    return errs


def ingest_review_run(*, run_id: str, bundle: dict, raw_flags_text: str,
                      expected_bundle_sha256: str, actual_hashes: dict,
                      approval_ok: bool, ledger_events=None,
                      provenance_hashes=None) -> dict:
    """raw flags → 复查 critic 记录 + fail-closed 路由 + 队列事件。

    与 ``critic_run.ingest_run`` 同链形（本模块桥接实现，不改其行为）：
    - expected_bundle_sha256 与内存 bundle canonical hash 不符 = 可信侧
      漂移 → ValueError；
    - actual_hashes：编排侧对盘上实测 sha256，键约定 {"bundle" 可选,
      "raw_flags" 可选, "<case_id>:<file_role>"}；任一声明键缺失或不符 →
      invalid（fail-closed）；
    - approval_ok=False → invalid（模型未获批不得执行）；
    - flags=[] 且无已校准置信域 → 按人工队列路由（CALIBRATION_NOTE
      承诺的 fail-closed：无校准域时「无旗」不可信）；
    - provenance_hashes：纯结构性修复（如从 as-returned 文本提取 JSON
      对象）的原文留证绑定，键 ``provenance:<名>`` 并入 input_hashes；
    - record 为合同级投影（category/confidence/location），读者完整原文
      以 raw 字节 sha256 进入 evidence_refs；状态由本管线赋值，读者自封
      一律无效。
    返回 {record, record_sha256, critic_status, queue_events,
          invalid_reasons, abstain_count, raw_flags_sha256}。
    """
    validate_review_bundle(bundle)
    if bundle["run_id"] != run_id:
        raise ValueError(f"ingest_review_run: bundle.run_id={bundle['run_id']!r}"
                         f" ≠ run_id={run_id!r}")
    if review_bundle_sha256(bundle) != expected_bundle_sha256:
        raise ValueError("ingest_review_run: bundle canonical hash 与 sidecar"
                         " 声明不符（可信侧漂移，拒绝产出 record）")
    expected_cases = [c["case_id"] for c in bundle["cases"]]

    invalid_reasons = []
    try:
        raw = json.loads(raw_flags_text)
    except Exception as exc:
        raw = None
        invalid_reasons.append(f"raw_flags: 不是合法 JSON（{exc}）")
    raw_valid = raw is not None
    if raw is not None:
        raw_errs = validate_review_raw_flags(raw,
                                             expected_case_ids=expected_cases)
        invalid_reasons.extend(raw_errs)
        raw_valid = not raw_errs

    raw_bytes = raw_flags_text.encode("utf-8")
    raw_sha = hashing.sha256_bytes(raw_bytes)
    actual = actual_hashes if isinstance(actual_hashes, dict) else {}
    hash_reasons, declared = _hash_check(bundle, actual)
    if "raw_flags" in actual and actual["raw_flags"] != raw_sha:
        hash_reasons.append("hash: raw_flags 盘上实测 sha256 与传入文本不一致"
                            "（落盘须为原样字节）")
    invalid_reasons.extend(hash_reasons)
    hashes_ok = not hash_reasons

    executed = raw_valid and hashes_ok and approval_ok is True
    critic_status = "executed" if executed else "invalid"
    if approval_ok is not True:
        invalid_reasons.append("approval: APR-0005 锚校验未通过"
                               "（model.approved=False，fail-closed）")

    flags = []
    abstain_count = 0
    reader_id = None
    if raw is not None and raw_valid:
        reader_id = raw.get("reader_id")
        for c in raw.get("per_case", []):
            for f in c.get("flags", []):
                if f.get("abstain") is True:
                    abstain_count += 1
                flags.append({"case_id": c["case_id"],
                              "category": f["category"],
                              "confidence": float(f["confidence"]),
                              "location": f["location_evidence"]})
    input_hashes = {"raw_flags": raw_sha,
                    "approval:APR-0005": bundle["approval"]["sha256"]}
    for key in sorted(declared):
        input_hashes[key] = declared[key]
    if "bundle" in actual:
        input_hashes["bundle"] = actual["bundle"]
    evidence = [raw_sha]
    prov = dict(provenance_hashes) if provenance_hashes else {}
    bad_prov = sorted(k for k, v in prov.items()
                      if not (isinstance(k, str) and k and ":" not in k
                              and len(str(v)) == 64))
    if bad_prov:
        raise ValueError(f"ingest_review_run: provenance_hashes 键值非法: "
                         f"{bad_prov}")
    for k in sorted(prov):
        pkey = f"provenance:{k}"
        if pkey in input_hashes:
            raise ValueError(f"ingest_review_run: provenance 键冲突 {pkey!r}")
        input_hashes[pkey] = prov[k]
        evidence.append(prov[k])
    record = {
        "schema": RECORD_SCHEMA,
        "critic_run_id": "RCR-%s" % run_id,
        "critic_status": critic_status,
        "advisory_only": True,
        "model": {"provider": "subagent_critic_reader", "version": reader_id,
                  "approved": approval_ok is True},
        "input_hashes": input_hashes,
        "input_hashes_match": hashes_ok,
        "flags": flags,
        "calibration": {"in_calibrated_range":
                        bundle["calibration"]["domain_established"]},
        "evidence_refs": evidence,
        "schema_validation": {"valid": raw_valid,
                              "record_schema": RECORD_SCHEMA},
        "authority_note": ADVISORY_ONLY_NOTE,
    }
    record_sha256 = hashing.sha256_bytes(
        hashing.canonical_json_bytes(record))

    events = list(ledger_events) if ledger_events is not None else []
    queue_events = []
    if critic_status != "executed":
        ev = queue.make_event(
            events, event="enqueue", item_id=f"ITEM-{run_id}",
            actor="pcbflow-v4-review-pipeline", actor_role="critic_model",
            reason_code=critic_status, refs={"critic_ref": record_sha256})
        events, ev = queue.append(events, ev)
        queue_events.append(ev)
    elif not flags and not bundle["calibration"]["domain_established"]:
        # CALIBRATION_NOTE 承诺的 fail-closed：无校准域时「无旗」不可信，
        # executed 也按人工队列路由（宁人工复核，不自动视为干净）。
        ev = queue.make_event(
            events, event="enqueue", item_id=f"ITEM-{run_id}",
            actor="pcbflow-v4-review-pipeline", actor_role="critic_model",
            reason_code="no_flags_uncalibrated",
            refs={"critic_ref": record_sha256})
        events, ev = queue.append(events, ev)
        queue_events.append(ev)
    return {
        "record": record,
        "record_sha256": record_sha256,
        "critic_status": critic_status,
        "queue_events": queue_events,
        "ledger_events": events,
        "invalid_reasons": invalid_reasons,
        "abstain_count": abstain_count,
        "raw_flags_sha256": raw_sha,
    }


def _hash_check(bundle: dict, actual: dict) -> tuple:
    """bundle 声明 file hash vs 盘上实测对账（缺/不符都 fail-closed）。"""
    reasons = []
    declared = {}
    for c in bundle["cases"]:
        cid = c["case_id"]
        rkey = f"{cid}:review_package_sha256"
        if rkey not in actual:
            reasons.append(f"hash: 缺实测 {rkey}")
        elif actual[rkey] != c["review_package_sha256"]:
            reasons.append(f"hash: {rkey} 实测与 bundle 声明不符（stale）")
        else:
            declared[rkey] = actual[rkey]
        for role in _BUNDLE_FILE_ROLES:
            key = f"{cid}:{role}"
            if key not in actual:
                reasons.append(f"hash: 缺实测 {key}")
            elif actual[key] != c["files"][role]["sha256"]:
                reasons.append(f"hash: {key} 实测与 bundle 声明不符")
            else:
                declared[key] = actual[key]
    return reasons, declared


# ---------------------------------------------------------------------------
# disposition 挂钩（L6：只写处置，不写 gate、不改判、不升级 trust）
# ---------------------------------------------------------------------------

def build_review_disposition(*, disposition_id: str, case_id: str,
                             review_package_sha256: str, kind: str,
                             rationale_code: str, approver: str,
                             approver_role: str, rationale_text: str = None,
                             flag_refs=None) -> dict:
    """复查处置记录（accept/reject/known_open；scope=candidate）。

    fact_refs 绑定 case 与复查包具名 hash 引用 + 旗标 refs；经
    validate_no_gate_write 扫描（处置无门写权）。非 waive 类，不受
    waiver policy 约束。
    """
    if kind not in REVIEW_DISPOSITION_KINDS:
        raise ValueError(f"build_review_disposition: kind {kind!r} 非法"
                         f"（合法集 {list(REVIEW_DISPOSITION_KINDS)}）")
    if not (isinstance(review_package_sha256, str)
            and len(review_package_sha256) == 64):
        raise ValueError("build_review_disposition: review_package_sha256"
                         " 必须为 64-hex")
    refs = [str(case_id), "review-package:%s" % review_package_sha256]
    for r in (flag_refs or []):
        refs.append(str(r))
    record = disposition_mod.build_disposition(
        disposition_id=disposition_id, fact_refs=refs, kind=kind,
        scope="candidate", rationale_code=rationale_code, approver=approver,
        approver_role=approver_role,
        **({"rationale_text": rationale_text} if rationale_text else {}))
    errs = disposition_mod.validate_no_gate_write(record)
    if errs:
        raise ValueError(f"disposition 含门写禁区（fail-closed）: {errs}")
    return record


def append_review_disposition(entries, *, disposition: dict, case_id: str,
                              three_bind: dict,
                              critic_record_sha256=None) -> tuple:
    """处置 → ledger 追加 entry（authority=human / trust_level=untrusted）。

    entry 以 artifact_hashes 绑定三绑具名 hash、disposition_refs 指向处置
    记录 id；human authority 仅允许 disposition 类 entry（ledger.
    TRUST_POLICY / HUMAN_AUTHORITY_ENTRY_KINDS 强制，不可手写升级）。
    返回 (new_entries, entry)；原列表不被修改。
    """
    if not isinstance(disposition, dict):
        raise ValueError("append_review_disposition: disposition 必须为 dict")
    did = disposition.get("disposition_id")
    if not (isinstance(did, str) and did):
        raise ValueError("append_review_disposition: disposition_id 缺失")
    if disposition.get("kind") not in REVIEW_DISPOSITION_KINDS:
        raise ValueError("append_review_disposition: kind 非法")
    if not isinstance(three_bind, dict) \
            or sorted(three_bind) != sorted(THREE_BIND_KEYS):
        raise ValueError("append_review_disposition: three_bind 键集不符")
    errs = disposition_mod.validate_no_gate_write(disposition)
    if errs:
        raise ValueError(f"disposition 含门写禁区（fail-closed）: {errs}")
    body = dict(
        entry_kind="disposition",
        entry_id=did,
        schema_validation=ledger.make_schema_validation("disposition_record",
                                                        valid=True),
        authority="human",
        trust_level="untrusted",
        candidate_id=str(case_id),
        disposition_refs=[did],
        artifact_hashes={k: three_bind[k] for k in THREE_BIND_KEYS},
    )
    if critic_record_sha256 is not None:
        if not (isinstance(critic_record_sha256, str)
                and len(critic_record_sha256) == 64):
            raise ValueError("critic_record_sha256 必须为 64-hex")
        body["critic_run_hash"] = critic_record_sha256
    return ledger.append(entries, body)
