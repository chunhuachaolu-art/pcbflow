"""⑤ 交错检查（SPEC v1.3 §11/§15 FD1；HANDOFF FD1 行）。

三块交付：
1. 检查器族+authority 注册表（§11.1 四档 authority，18 检查器；source=spec_built_in，
   非视觉候选 → §16.5 V1 晋升链不适用，视觉候选=0 如实记账）。
2. Rev-C dry-run 检查执行（消费 FC2 产物）：kicad_authoritative 档以 kicad-cli DRC
   报告为裁决（FC2 drc ledger=hash 输入；kicad-cli 由编排侧执行，pcbflow 零子进程，
   FC2-D3 口径）；deterministic_screening 在 ④ committed 路由上做确定性几何筛查
   （可对照 CLI，不覆盖 CLI）；screening_or_external/external 档如实
   not_executed（toolchain_lock 无外部工具登记→缺依赖不填默认值）。
3. 前馈残差（§11.2）：E(R)=actual(R)-predicted(R)；逐行绑定 plan_id/resource_id/
   net_ids/relation_ids/measurement_convention/actual_source/snapshot_hash；
   无可比实际=not_available+原因，禁伪 residual。

探针电池（HANDOFF FD1 门，仅 kicad_authoritative 子集）：5 检查器各配一块合成
探针板（单缺陷种子）+clean 对照板；kicad-cli 编排侧跑 DRC，JSON 以 hash 输入回填
probe-battery.json。板/工程文本由本模块 emit（--select probe_board/probe_project，
stdout 重定向落盘），复跑完全确定。

消费面（§9.1 同构，⑤ 版）：feedforward_plan_hash/五 snapshot 绑定/stale 检查/
declared≠actually_read≠derived≠ignored 分列；controls 全量 ignored（⑤ 只读
residual/账本，控制量属 ③/④ 消费面，升级=确认点流程）。

生成器模式：零落盘、零子进程。常量内聚本模块（config.py 零新增→历史
config_sha256 不漂移）。核心产物禁 wall-clock/主机路径（envelope 扫描强制）。
"""

from __future__ import annotations

import json
import os

from . import config, hashing
from . import profile_loader

FD1_SCHEMA = "1.0"
FD1_ARTIFACT_KIND = "check_family"
# G0（REPAIR-P4 W-1）：Rev-C 目录 pin 自 profiles/revc-coreboard/profile.json 装载
_pf = profile_loader.load_profile(config.PCBFLOW_ROOT)
FD1_OUT_DEFAULT = profile_loader.require(_pf, "check_cmd", "fd1_out_default")
A3_DIR = profile_loader.require(_pf, "check_cmd", "a3_dir")
FF1_DIR = profile_loader.require(_pf, "check_cmd", "ff1_dir")
FC2_DIR = profile_loader.require(_pf, "check_cmd", "fc2_dir")

AUTH_KICAD = "kicad_authoritative"
AUTH_DET = "deterministic_screening"
AUTH_SCREEN = "screening_or_external_required"
AUTH_EXT = "external_required"
AUTHORITIES = (AUTH_KICAD, AUTH_DET, AUTH_SCREEN, AUTH_EXT)

# ---- 检查器族（SPEC §11.1 权威表逐行；source=spec_built_in） ------------------
# mapping：KiCad DRC violation type → 检查器（kicad_authoritative 档裁决映射）
CHECKERS = (
    {"checker_id": "CHK-CONN", "name": "连通性", "authority": AUTH_KICAD,
     "spec_ref": "SPEC v1.3 §11.1", "params": {},
     "violation_types": [], "unconnected_items": True,
     "note": "裁决=kicad-cli DRC（--refill-zones --severity-all profile）；"
             "unconnected_items 计数"},
    {"checker_id": "CHK-SHORT", "name": "短路", "authority": AUTH_KICAD,
     "spec_ref": "SPEC v1.3 §11.1", "params": {},
     "violation_types": ["shorting_items", "tracks_crossing"],
     "unconnected_items": False, "note": ""},
    {"checker_id": "CHK-WIDTH", "name": "线宽", "authority": AUTH_KICAD,
     "spec_ref": "SPEC v1.3 §11.1", "params": {},
     "violation_types": ["track_width"], "unconnected_items": False,
     "note": ""},
    {"checker_id": "CHK-CLR", "name": "间距", "authority": AUTH_KICAD,
     "spec_ref": "SPEC v1.3 §11.1", "params": {},
     "violation_types": ["clearance", "copper_edge_clearance",
                         "hole_clearance"],
     "unconnected_items": False, "note": ""},
    {"checker_id": "CHK-ANNULAR", "name": "孔环", "authority": AUTH_KICAD,
     "spec_ref": "SPEC v1.3 §11.1", "params": {},
     "violation_types": ["annular_width"], "unconnected_items": False,
     "note": ""},
    {"checker_id": "CHK-CORNER", "name": "拐点", "authority": AUTH_DET,
     "spec_ref": "SPEC v1.3 §11.1", "params": {
         "min_segment_mm": 0.01,
         "basis": "零长/重复共线点=几何缺陷（口径内聚本模块；screening 不覆盖 CLI）"},
     "violation_types": [], "unconnected_items": False, "note": ""},
    {"checker_id": "CHK-LEN", "name": "长度", "authority": AUTH_DET,
     "spec_ref": "SPEC v1.3 §11.1", "params": {
         "max_detour_ratio": 1.5,
         "basis": "CPLACE_DETOUR_YELLOW（③ 同参，derived 标记；screening）"},
     "violation_types": [], "unconnected_items": False, "note": ""},
    {"checker_id": "CHK-SYMM", "name": "对称", "authority": AUTH_DET,
     "spec_ref": "SPEC v1.3 §11.1", "params": {
         "max_dev_mm": 0.5, "basis": "CPLACE_SYMM_DEV_YELLOW_MM（③ 同参）"},
     "violation_types": [], "unconnected_items": False,
     "note": "输入=已批 symmetry 结构声明；无声明→not_available"},
    {"checker_id": "CHK-DIFF", "name": "差分连续性", "authority": AUTH_DET,
     "spec_ref": "SPEC v1.3 §11.1", "params": {
         "max_len_mismatch_ratio": 0.1,
         "basis": "成员长度失配筛查阈值（口径内聚本模块；screening）"},
     "violation_types": [], "unconnected_items": False,
     "note": "输入=registry 差分 relation 成员路由"},
    {"checker_id": "CHK-IMP", "name": "阻抗",
     "authority": AUTH_SCREEN, "spec_ref": "SPEC v1.3 §11.1",
     "params": {}, "violation_types": [], "unconnected_items": False,
     "note": "一阶趋势或外部工具；本会话无外部工具登记"},
    {"checker_id": "CHK-XTALK", "name": "串扰",
     "authority": AUTH_SCREEN, "spec_ref": "SPEC v1.3 §11.1",
     "params": {}, "violation_types": [], "unconnected_items": False,
     "note": ""},
    {"checker_id": "CHK-RET", "name": "回流",
     "authority": AUTH_SCREEN, "spec_ref": "SPEC v1.3 §11.1",
     "params": {}, "violation_types": [], "unconnected_items": False,
     "note": ""},
    {"checker_id": "CHK-DECAP", "name": "去耦",
     "authority": AUTH_SCREEN, "spec_ref": "SPEC v1.3 §11.1",
     "params": {}, "violation_types": [], "unconnected_items": False,
     "note": ""},
    {"checker_id": "CHK-THERM", "name": "热",
     "authority": AUTH_SCREEN, "spec_ref": "SPEC v1.3 §11.1",
     "params": {}, "violation_types": [], "unconnected_items": False,
     "note": ""},
    {"checker_id": "CHK-DFM", "name": "DFM",
     "authority": AUTH_SCREEN, "spec_ref": "SPEC v1.3 §11.1",
     "params": {}, "violation_types": [], "unconnected_items": False,
     "note": ""},
    {"checker_id": "CHK-EMC", "name": "EMC", "authority": AUTH_EXT,
     "spec_ref": "SPEC v1.3 §11.1", "params": {},
     "violation_types": [], "unconnected_items": False,
     "note": "不由 kicad-cli 单独裁决"},
    {"checker_id": "CHK-EYE", "name": "眼图", "authority": AUTH_EXT,
     "spec_ref": "SPEC v1.3 §11.1", "params": {},
     "violation_types": [], "unconnected_items": False, "note": ""},
    {"checker_id": "CHK-PROT", "name": "协议裕量", "authority": AUTH_EXT,
     "spec_ref": "SPEC v1.3 §11.1", "params": {},
     "violation_types": [], "unconnected_items": False, "note": ""},
)

# 探针电池：expected_class ↔ 探针板；clean=阴性对照（HANDOFF FD1 门：仅
# kicad_authoritative 子集；100%=5/5 detected + clean 零 error 级违规）
PROBES = (
    {"probe": "probe-connectivity", "checker_id": "CHK-CONN",
     "seed": "同网双焊盘无走线", "expected_types": ["@unconnected_items"]},
    {"probe": "probe-shorting", "checker_id": "CHK-SHORT",
     "seed": "异网十字交叉叠铜", "expected_types": ["tracks_crossing",
                                                    "shorting_items"]},
    {"probe": "probe-width", "checker_id": "CHK-WIDTH",
     "seed": "0.1mm 走线（规则下限 0.2）", "expected_types": ["track_width"]},
    {"probe": "probe-clearance", "checker_id": "CHK-CLR",
     "seed": "异网平行走线 0.1mm 间距（规则 0.2）",
     "expected_types": ["clearance"]},
    {"probe": "probe-annular", "checker_id": "CHK-ANNULAR",
     "seed": "过孔环宽 0.1mm（规则下限 0.25）",
     "expected_types": ["annular_width"]},
)
PROBE_CLEAN = "probe-clean"


# ---- 读盘与绑定（actually_read=真实读取点） ----------------------------------
def _p(rel: str) -> str:
    return os.path.join(config.PCBFLOW_ROOT, rel)


def _rel(path: str) -> str:
    """产物内嵌路径一律仓相对（防绝对主机路径进核心产物；envelope 扫描强制）。"""
    return os.path.relpath(_p(path),
                           config.PCBFLOW_ROOT).replace("\\", "/")


def _fsha(rel: str) -> str | None:
    p = _p(rel)
    return hashing.sha256_file(p) if os.path.exists(p) else None


def _read(reads: list, rel: str, field: str, role: str):
    reads.append({"artifact": _rel(rel), "field": field, "role": role})
    return reads[-1]


def _load_json(rel: str, reads: list | None = None, role: str = "input",
               field: str = "<file>"):
    """只读装载；登记 actually_read。文件缺失返回 None（上层如实 not_available）。"""
    p = _p(rel)
    if not os.path.exists(p):
        return None
    if reads is not None:
        _read(reads, rel, field, role)
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def _structures_current(plan, reads):
    """plan.snapshot 声明的 structures 基准 → 当前值：
    无 override 键=草案文件 hash（FF1 口径）；有=草案对读 override 的批准视图
    hash（FD2 adoption 口径）。返回 (current, basis_tag)。"""
    snap = plan.get("snapshot") or {}
    if not snap.get("structures_override_sha256"):
        return _fsha(A3_DIR + "/structures.json"), "draft_file"
    from . import feedforward as _ff
    ov_rel = _ff.OVERRIDE_REL
    if not os.path.exists(_p(ov_rel)):
        return None, "approved_override（override 文件缺失）"
    draft = _load_json(A3_DIR + "/structures.json", reads, role="binding",
                       field="<file>（approved 视图重建基准）")
    ov = _load_json(ov_rel, reads, role="binding",
                    field="approved.base_draft/diff_vs_draft")
    if draft is None or ov is None:
        return None, "approved_override（草案/override 缺失）"
    try:
        return _ff.approved_structures_sha256(draft, ov), "approved_override"
    except ValueError as exc:
        reads.append({"artifact": ov_rel,
                      "field": "base_draft.sha256 一致性核对失败",
                      "role": "binding"})
        return None, "approved_override（%s）" % str(exc)[:80]


def _binding(plan: dict, reads: list) -> dict:
    """§7.4 计划绑定检查（五 snapshot；任一失配→stale_plan，残差降级 not_available
    不删除——绑定基准=各字段声明的 basis 口径，与 FF-1 计划侧同源）。
    CAS1：计划声明 it_adopted_cascade 时，placement 现值经 §9.4 转换证明
    闭环回算（采纳布局→to_placement_csv→hash 与计划绑定逐字节核对）；
    失配→保持 p3 现值→stale 如实（不静默消费）。"""
    snap = plan.get("snapshot") or {}
    place_current = _fsha(os.path.relpath(config.AUDIT_P3_PLACEMENT_CSV,
                                          config.PCBFLOW_ROOT).replace("\\", "/"))
    place_basis = {"artifact": "design/coreboard/.../p3-placement-gates-pass/"
                               "placement.csv", "field": "<file>"}
    cas1_closure = None
    if snap.get("placement_basis") == "it_adopted_cascade":
        lay_rel = snap.get("adopted_layout_path")
        csv_rel = snap.get("adopted_placement_path")
        ok_conv = False
        if lay_rel and csv_rel:
            _read(reads, lay_rel, "<file>（adopted_layout，转换闭环基准）",
                  "binding")
            _read(reads, csv_rel, "<file>（adopted placement 绑定现值）",
                  "binding")
            try:
                from . import coplace_cmd
                lay_p = _p(lay_rel)
                if os.path.exists(lay_p):
                    with open(lay_p, encoding="utf-8") as f:
                        lay_obj = json.load(f)
                    conv_sha = hashing.sha256_bytes(
                        coplace_cmd.to_placement_csv(lay_obj))
                    ok_conv = (conv_sha
                               == snap.get("placement_snapshot_sha256")
                               and _fsha(lay_rel)
                               == snap.get("adopted_layout_sha256"))
                    if ok_conv:
                        place_current = conv_sha
            except Exception:
                ok_conv = False
        cas1_closure = {"status": ("matched" if ok_conv else "mismatch"),
                        "adopted_placement_path": csv_rel,
                        "adopted_layout_path": lay_rel,
                        "note": "§9.4 转换证明闭环：to_placement_csv 回算与"
                                "计划 placement 绑定核对（确认点 #4 已批）"}
        place_basis = {"artifact": csv_rel or "placement.csv(adopted)",
                       "field": "<file>（basis=it_adopted_cascade 转换闭环）"}

    def _match(key, actual, basis):
        ok = (actual is not None and snap.get(key) == actual)
        if not ok:
            _read(reads, basis["artifact"], basis["field"], "binding")
        return {"field": key, "planned": snap.get(key), "current": actual,
                "match": ok}

    reg = _load_json(A3_DIR + "/net-registry.json", reads,
                     role="binding", field="registry_snapshot_hash")
    st_current, st_basis = _structures_current(plan, reads)
    checks = [
        _match("registry_snapshot_hash",
               (reg or {}).get("registry_snapshot_hash"),
               {"artifact": A3_DIR + "/net-registry.json",
                "field": "registry_snapshot_hash"}),
        _match("constraints_sha256", _fsha(A3_DIR + "/constraints.json"),
               {"artifact": A3_DIR + "/constraints.json", "field": "<file>"}),
        _match("structures_sha256", st_current,
               {"artifact": A3_DIR + "/structures.json",
                "field": "<file>（basis=%s）" % st_basis}),
        _match("placement_snapshot_sha256", place_current, place_basis),
        _match("board_snapshot_sha256",
               _fsha(os.path.relpath(config.AUDIT_P3_BOARD,
                                     config.PCBFLOW_ROOT).replace("\\", "/")),
               {"artifact": "design/coreboard/.../p3-placement-gates-pass/"
                            "stm32h743-coreboard-revc.kicad_pcb",
                "field": "<file>"}),
    ]
    stale = [c["field"] for c in checks if not c["match"]]
    out = {"checks": checks, "all_match": not stale,
           "stale_plan_reason": (None if not stale else
                                 "snapshot_mismatch:" + ",".join(stale))}
    if cas1_closure is not None:  # CAS1 口径才落键（默认路径字节稳定）
        out["placement_basis_closure"] = cas1_closure
    if st_basis != "draft_file":  # FD2 adoption 口径才落键（FF1 字节稳定）
        out["structures_basis"] = st_basis
    return out


def _consumption_evidence(plan, plan_sha, binding, reads, derived_rows):
    """§9.1 同构消费证据（⑤ 版）：declared≠actually_read≠derived≠ignored 分列。"""
    ignored_kinds = sorted({c.get("kind") for c in plan.get("controls") or []})
    return {
        "schema_version": FD1_SCHEMA,
        "artifact_kind": "check_consumption",
        "plan_id": plan.get("plan_id"),
        "feedforward_plan_hash": plan_sha,
        "feedforward_registry_snapshot_hash":
            (plan.get("snapshot") or {}).get("registry_snapshot_hash"),
        "plan_authority": plan.get("authority"),
        "snapshot_check": binding,
        "stale_plan_reason": binding["stale_plan_reason"],
        "declared_consumed": [
            "feedforward-plan.json:plan_id",
            "feedforward-plan.json:snapshot.*（五绑定）",
            "feedforward-plan.json:resources[].{resource_id,kind,demand,supply,"
            "reserve,margin,state,net_ids,relation_ids,reason}",
            "feedforward-plan.json:residuals_note",
        ],
        "controls_declared_consumed": [],
        "controls_actually_read": [],
        "controls_ignored": [
            {"kind": k,
             "reason": "⑤ 不消费控制量（controls 属 ③/④ 消费面；升级=确认点"
                       "流程 §17.4）；⑤ 只读资源账本与 residual"}
            for k in ignored_kinds],
        "derived": derived_rows,
        "consumption_contract": {
            "actually_read": reads,
            "fallback": None,
            "fidelity": "full（⑤ 只读：DRC ledger=hash 输入；路由几何来自 "
                        "executed_routes；declared≠actually_read 分列）",
        },
    }


# ---- 检查执行 ------------------------------------------------------------------
def _plan_with_binding(reads, ff_plan_dir=None):
    ff_plan_dir = ff_plan_dir or FF1_DIR  # 调用时解析（测试 monkeypatch 可生效）
    plan = _load_json(ff_plan_dir + "/feedforward-plan.json", reads,
                      role="ff_plan", field="<file>")
    if plan is None:
        return None, None, {"checks": [], "all_match": False,
                            "structures_basis": "draft_file",
                            "stale_plan_reason": "plan_missing"}
    _read(reads, ff_plan_dir + "/feedforward-plan.json", "plan_id", "residual")
    plan_sha = _fsha(ff_plan_dir + "/feedforward-plan.json")
    binding = _binding(plan, reads)
    return plan, plan_sha, binding


def run_kicad_authoritative(reads: list, out_dir_rel=FC2_DIR):
    """kicad_authoritative 5 检查器：消费 FC2 DRC ledger（baseline/final，
    hash 输入）。ledger 缺失→checker_status=not_executed+原因（不伪造）。"""
    base_rel = out_dir_rel + "/drc/baseline-all.json"
    final_rel = out_dir_rel + "/drc/final-all.json"
    base = _load_json(base_rel, reads, role="authority_report",
                      field="violations[].type/severity")
    final = _load_json(final_rel, reads, role="authority_report",
                       field="violations[].type/severity")
    if final is None:
        return [{"checker_id": c["checker_id"], "name": c["name"],
                 "authority": c["authority"],
                 "checker_status": "not_executed",
                 "verdict": None,
                 "reason": "FC2 drc ledger 缺失（kicad-cli 编排侧未跑或未回填）"}
                for c in CHECKERS if c["authority"] == AUTH_KICAD]
    # 形状门（REPAIR-P2 W-3 / SEC-A-04）：ledger 在但形状漂移（合法 JSON
    # 却缺/非法 violations、unconnected_items——kicad-cli 版本升级改字段名/
    # 文件被裁剪即触发）= 证据不可信 ⇒ 全部 kicad 检查器 not_executed，
    # 不得 executed+pass。hash 绑定不校验形状，此门是形状侧的 fail-closed
    # 兜底；口径对照 check_stage.summarize_drc（缺键 ValueError 拒算）。
    # baseline 在场时同受形状门约束（缺键=比对基准失真；baseline 允许
    # 整体缺席（base is None），在场即须形状合法）。
    _SHAPE_KEYS = ("violations", "unconnected_items")
    shape_bad = ["final:" + k for k in _SHAPE_KEYS
                 if not isinstance(final.get(k), list)]
    if base is not None:
        shape_bad += ["baseline:" + k for k in _SHAPE_KEYS
                      if not isinstance(base.get(k), list)]
    if shape_bad:
        return [{"checker_id": c["checker_id"], "name": c["name"],
                 "authority": c["authority"],
                 "checker_status": "not_executed",
                 "verdict": None,
                 "reason": "FC2 drc ledger 形状漂移：%s 缺/非法（hash 绑定"
                           "不校验形状；缺证据即 not_executed，不伪造 "
                           "executed+pass）" % "、".join(shape_bad)}
                for c in CHECKERS if c["authority"] == AUTH_KICAD]
    final_types = {}
    for v in final.get("violations", []):
        final_types[v["type"]] = final_types.get(v["type"], 0) + 1
    base_types = {}
    for v in (base or {}).get("violations", []):
        base_types[v["type"]] = base_types.get(v["type"], 0) + 1
    rows = []
    mapped = set()
    for c in CHECKERS:
        if c["authority"] != AUTH_KICAD:
            continue
        hits = {t: final_types.get(t, 0) for t in c["violation_types"]}
        n_unconn = (len(final.get("unconnected_items", []))
                    if c.get("unconnected_items") else None)
        new_unconn = None
        if c.get("unconnected_items") and base is not None:
            new_unconn = (n_unconn - len(base.get("unconnected_items", [])))
        mapped.update(hits)
        err_count = sum(hits.values())
        fail = err_count > 0 or (n_unconn and n_unconn > 0)
        rows.append({
            "checker_id": c["checker_id"], "name": c["name"],
            "authority": AUTH_KICAD, "checker_status": "executed",
            "verdict": "fail" if fail else "pass",
            "violation_counts": hits,
            "unconnected_items": n_unconn,
            "unconnected_new_vs_baseline": new_unconn,
            "evidence": {
                "report": os.path.basename(final_rel),
                "sha256": _fsha(final_rel),
                "baseline": os.path.basename(base_rel),
                "baseline_sha256": _fsha(base_rel),
                "profile": "kicad-cli DRC（FC2 编排侧；--refill-zones "
                           "--severity-all；severity 分列不互替）",
            },
        })
    unmapped = {t: n for t, n in sorted(final_types.items())
                if t not in mapped}
    if unmapped:
        rows.append({
            "checker_id": "CHK-LEDGER-UNMAPPED", "name": "台账未映射类型列账",
            "authority": AUTH_KICAD, "checker_status": "executed",
            "verdict": None,
            "violation_counts": unmapped,
            "reason": "观测到但 §11.1 五检查器不映射的 DRC 类型；列账不静默"
                      "丢弃（severity 分列随台账）",
            "evidence": {"report": os.path.basename(final_rel),
                         "sha256": _fsha(final_rel)},
        })
    return rows


def run_deterministic_screening(routes: list, sym_classes=None,
                                diff_relations=None, reads=None,
                                structures_approved=False):
    """deterministic_screening 4 检查器（纯函数；routes=④ committed 路由
    [{net_id,segments,vias}]，segments=[layer,x1,y1,x2,y2]）。

    sym_classes：已批对称声明 [{class_id,members:[[ref,pad],...]}]（Rev-C 无
    已批声明→not_available）。diff_relations：registry 差分 relation
    [{relation_id,members,segments:{side:[net_id]}}]。"""
    del reads  # 纯函数：数据由调用方装载并登记
    rows = []

    # CHK-CORNER：零长段/相邻重复点
    corner_viol = []
    for r in routes:
        segs = r.get("segments") or []
        for i, s in enumerate(segs):
            if abs(s[1] - s[3]) < 1e-9 and abs(s[2] - s[4]) < 1e-9:
                corner_viol.append({"net_id": r.get("net_id"),
                                    "kind": "zero_length_segment",
                                    "index": i})
            if i and s[1:5] == segs[i - 1][1:5]:
                corner_viol.append({"net_id": r.get("net_id"),
                                    "kind": "duplicate_consecutive_segment",
                                    "index": i})
    rows.append({"checker_id": "CHK-CORNER", "name": "拐点",
                 "authority": AUTH_DET, "checker_status": "executed",
                 "verdict": "fail" if corner_viol else "pass",
                 "violations": corner_viol,
                 "measured": {"routes": len(routes)},
                 "params": CHECKERS[5]["params"]})

    # CHK-LEN：绕行比筛查（routed/manhattan）
    len_viol = []
    ratios = []
    for r in routes:
        segs = r.get("segments") or []
        if not segs:
            continue
        routed = sum(((s[3] - s[1]) ** 2 + (s[4] - s[2]) ** 2) ** 0.5
                     for s in segs)
        manh = (abs(segs[-1][3] - segs[0][1])
                + abs(segs[-1][4] - segs[0][2]))
        ratio = (routed / manh) if manh > 1e-9 else None
        if ratio is None:
            len_viol.append({"net_id": r.get("net_id"),
                             "kind": "degenerate_manhattan_zero"})
            continue
        ratios.append(round(ratio, 4))
        if ratio > CHECKERS[6]["params"]["max_detour_ratio"] + 1e-6:
            len_viol.append({"net_id": r.get("net_id"),
                             "kind": "detour_ratio_over",
                             "ratio": round(ratio, 4)})
    rows.append({"checker_id": "CHK-LEN", "name": "长度",
                 "authority": AUTH_DET, "checker_status": "executed",
                 "verdict": "fail" if len_viol else "pass",
                 "violations": sorted(len_viol,
                                      key=lambda v: (str(v["net_id"]),
                                                     v["kind"])),
                 "measured": {"max_ratio": max(ratios) if ratios else None,
                              "routes": len(routes)},
                 "params": CHECKERS[6]["params"]})

    # CHK-SYMM：需要已批对称声明；无→not_available（不伪造）
    if not sym_classes:
        sym_reason = ("无已批 symmetry 结构声明（① 已批视图/override 2026-08-30 "
                      "未声明 symmetry_class）→无可检查输入"
                      if structures_approved else
                      "无已批 symmetry 结构声明（structures=draft，"
                      "确认点 #1 沿留）→无可检查输入")
        rows.append({"checker_id": "CHK-SYMM", "name": "对称",
                     "authority": AUTH_DET, "checker_status": "not_executed",
                     "verdict": None,
                     "not_available_reason": sym_reason})
    else:
        sym_viol = []
        for sc in sym_classes:
            mem = sc.get("members") or []
            pos = {}
            for r in routes:
                key = r.get("ref_pad") or r.get("net_id")
                pos[key] = r
            xs = [pos.get(tuple(m)) or pos.get(str(m)) for m in mem]
            pts = [x for x in xs if x]
            if len(pts) < 2:
                sym_viol.append({"class_id": sc.get("class_id"),
                                 "kind": "members_missing",
                                 "found": len(pts), "declared": len(mem)})
                continue
            dev = _sym_deviation(pts)
            if dev > CHECKERS[7]["params"]["max_dev_mm"] + 1e-6:
                sym_viol.append({"class_id": sc.get("class_id"),
                                 "kind": "symmetry_deviation_over",
                                 "dev_mm": round(dev, 4)})
        rows.append({"checker_id": "CHK-SYMM", "name": "对称",
                     "authority": AUTH_DET, "checker_status": "executed",
                     "verdict": "fail" if sym_viol else "pass",
                     "violations": sym_viol,
                     "params": CHECKERS[7]["params"]})

    # CHK-DIFF：registry 差分 relation 成员路由连续性
    diff_viol = []
    diff_unavail = []
    executed = False
    for rel in diff_relations or []:
        sides = (rel.get("segments") or {})
        member_routes = {}
        for side, ids in sorted(sides.items()):
            for nid in ids:
                for r in routes:
                    if r.get("net_id") == nid:
                        member_routes[nid] = r
        if not member_routes:
            diff_unavail.append({"relation_id": rel.get("relation_id"),
                                 "kind": "members_not_in_dataset",
                                 "declared_members": sorted(
                                     nid for ids in sides.values()
                                     for nid in ids)})
            continue
        executed = True
        lens = {}
        for nid, r in member_routes.items():
            lens[nid] = sum(((s[3] - s[1]) ** 2 + (s[4] - s[2]) ** 2) ** 0.5
                            for s in (r.get("segments") or []))
        by_side = {side: [lens[nid] for nid in ids if nid in lens]
                   for side, ids in sides.items()}
        sides_present = {k: v for k, v in by_side.items() if v}
        if len(sides_present) < 2:
            diff_viol.append({"relation_id": rel.get("relation_id"),
                              "kind": "side_incomplete",
                              "sides_present": sorted(sides_present)})
            continue
        all_lens = [x for v in sides_present.values() for x in v]
        lo, hi = min(all_lens), max(all_lens)
        ratio = ((hi - lo) / lo) if lo > 1e-9 else None
        if ratio is None or ratio > (CHECKERS[8]["params"]
                                     ["max_len_mismatch_ratio"] + 1e-6):
            diff_viol.append({"relation_id": rel.get("relation_id"),
                              "kind": "length_mismatch_over",
                              "ratio": (round(ratio, 4) if ratio is not None
                                        else None)})
    rows.append({"checker_id": "CHK-DIFF", "name": "差分连续性",
                 "authority": AUTH_DET,
                 "checker_status": "executed" if executed else "not_executed",
                 "verdict": (("fail" if diff_viol else "pass")
                             if executed else None),
                 "violations": diff_viol,
                 "not_available": (diff_unavail or None),
                 "not_available_reason": (None if executed else
                                          "差分 relation 成员不在 ④ 数据集"
                                          "（无实际走线可比）"),
                 "params": CHECKERS[8]["params"]})
    return rows


def _sym_deviation(pts):
    """对称偏差：成员到成员中位线的最大距离（一阶筛查口径，内聚本模块）。"""
    n = len(pts)

    def _pt(r):
        s = (r.get("segments") or [[0, 0, 0, 0, 0]])[0]
        return (s[1], s[2])

    coords = [_pt(r) for r in pts]
    if n == 2:
        (x1, y1), (x2, y2) = coords
        return ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5 / 2.0
    cx = sorted(c[0] for c in coords)[n // 2]
    cy = sorted(c[1] for c in coords)[n // 2]
    return max(abs(c[0] - cx) + abs(c[1] - cy) for c in coords)


def run_not_executed():
    """screening_or_external + external 档：如实 not_executed（toolchain_lock
    只登记 kicad 工具族；缺依赖不填默认值，§17.1）。"""
    rows = []
    for c in CHECKERS:
        if c["authority"] not in (AUTH_SCREEN, AUTH_EXT):
            continue
        reason = ("无外部工具登记（toolchain_lock 仅 kicad 工具族）；一阶筛查"
                  "未实现，如实 not_executed"
                  if c["authority"] == AUTH_SCREEN else
                  "external_required：不由 kicad-cli 单独裁决（§11.1）；"
                  "外部签核工具未接入")
        rows.append({"checker_id": c["checker_id"], "name": c["name"],
                     "authority": c["authority"],
                     "checker_status": "not_executed", "verdict": None,
                     "reason": reason})
    return rows


# ---- 前馈残差（§11.2） ---------------------------------------------------------
LANE_PITCH_MM = 0.35  # 与 ②/FF 计划同口径（audit C3：len×0.35 pitch）
# KiCad 10 层常量（HANDOFF §4：F=0/B=2/In1=4/In2=6）
LAYER_NAMES = {0: "F.Cu", 2: "B.Cu", 4: "In1.Cu", 6: "In2.Cu"}


def build_ff_residuals(out_dir_rel=FC2_DIR, ff_plan_dir=None):
    """E(R)=actual-predicted；无可比实际→not_available+原因（§11.2）。

    actual_source 固定为 FC2 产物（hash 输入）；分母/口径逐行写明，不混读。"""
    reads: list = []
    plan, plan_sha, binding = _plan_with_binding(reads, ff_plan_dir)
    out = {
        "schema_version": FD1_SCHEMA,
        "artifact_kind": "ff_residuals",
        "spec_ref": "SPEC v1.3 §11.2/§15-FD1",
        "plan_id": (plan or {}).get("plan_id"),
        "feedforward_plan_hash": plan_sha,
        "snapshot_check": binding,
        "stale_plan_reason": binding["stale_plan_reason"],
        "residual_definition": "E(R) = actual(R) - predicted(R)",
        "rows": [],
        "not_available": [],
    }
    if plan is None:
        out["not_available"].append(
            {"dimension": "*", "reason": "feedforward-plan.json 缺失"})
        out["consumption"] = _consumption_evidence({}, None, binding, reads, [])
        return out
    if not binding["all_match"]:
        out["not_available"].append(
            {"dimension": "*", "reason": "stale_plan：" +
                                         binding["stale_plan_reason"]})
    res_index = {}
    for r in plan.get("resources") or []:
        res_index.setdefault(r["kind"], []).append(r)

    rows = out["rows"]
    na = out["not_available"]

    # —— layer_capacity：demand vs 实际铜消耗（同口径 len×0.35） ----------------
    lc = (res_index.get("layer_capacity") or [None])[0]
    replay = _load_json(out_dir_rel + "/replay-plan.json", reads,
                        role="actual_source", field="executed_routes")
    if lc and replay and binding["all_match"]:
        executed = replay.get("executed_routes") or []
        consumed_mm2 = 0.0
        layer_mm = {}
        for r in executed:
            for s in r.get("segments") or []:
                ln = ((s[3] - s[1]) ** 2 + (s[4] - s[2]) ** 2) ** 0.5
                consumed_mm2 += ln * LANE_PITCH_MM
                layer_mm[s[0]] = layer_mm.get(s[0], 0.0) + ln * LANE_PITCH_MM
        pred = (lc.get("demand") or {}).get("value")
        supply = (lc.get("supply") or {}).get("value")
        plan_margin = (lc.get("margin") or {}).get("value")
        final_margin = (supply - consumed_mm2) if supply is not None else None
        rows.append({
            "residual_id": "RES-LC-1", "plan_id": plan.get("plan_id"),
            "resource_id": lc["resource_id"], "dimension": "demand_vs_consumption",
            "predicted": {"value": pred, "unit": "mm2",
                          "basis": (lc.get("demand") or {}).get("basis")},
            "actual": {"value": round(consumed_mm2, 3), "unit": "mm2",
                       "source": {"path": _rel(out_dir_rel +
                                               "/replay-plan.json"),
                                  "field": "executed_routes",
                                  "sha256": _fsha(out_dir_rel +
                                                  "/replay-plan.json")}},
            "E": {"value": (round(consumed_mm2 - pred, 3)
                            if pred is not None else None), "unit": "mm2"},
            "measurement_convention":
                "预测=audit C3 链式直连长×0.35 pitch（全信号网聚合）；"
                "实际=④ committed 路由折线长×%g pitch（55/61 网子集）——"
                "分母差异如实记账，不混读" % LANE_PITCH_MM,
            "net_ids": [], "relation_ids": [],
            "snapshot_hash": (plan.get("snapshot") or {})
            .get("registry_snapshot_hash"),
            "note": "聚合口径（resource 级 note 引 utilization=0.340288）",
        })
        rows.append({
            "residual_id": "RES-LC-2", "plan_id": plan.get("plan_id"),
            "resource_id": lc["resource_id"], "dimension": "margin_final",
            "predicted": {"value": plan_margin, "unit": "mm2",
                          "basis": "plan margin=supply-demand-reserve"},
            "actual": {"value": (round(final_margin, 3)
                                 if final_margin is not None else None),
                       "unit": "mm2",
                       "source": {"path": _rel(out_dir_rel +
                                               "/replay-plan.json"),
                                  "field": "executed_routes",
                                  "sha256": _fsha(out_dir_rel +
                                                  "/replay-plan.json")}},
            "E": {"value": (round(final_margin - plan_margin, 3)
                            if None not in (final_margin, plan_margin)
                            else None), "unit": "mm2"},
            "measurement_convention": "final margin=supply−实际消耗（同 "
                                      "RES-LC-1 实际口径）",
            "net_ids": [], "relation_ids": [],
            "snapshot_hash": (plan.get("snapshot") or {})
            .get("registry_snapshot_hash"),
            "layer_split_mm2": {(LAYER_NAMES.get(k, "L%d" % k)):
                                round(v, 3)
                                for k, v in sorted(layer_mm.items())},
        })
    else:
        na.append({"dimension": "demand_vs_consumption",
                   "resource_id": (lc or {}).get("resource_id"),
                   "reason": "layer_capacity/replay-plan 缺失或 plan stale"
                             "→无可比实际"})

    # —— unresolved：预测赤字资源数 vs FC2 三态/重放未落板（口径分列） ----------
    n_deficit = sum(1 for r in plan.get("resources") or []
                    if r.get("state") == "resource_deficit")
    certs = _load_json(out_dir_rel + "/residual-certs.json", reads,
                       role="actual_source", field="counts")
    if certs and binding["all_match"]:
        c = certs.get("counts") or {}
        unresolved_dry = (c.get("UNSAT", 0) + c.get("UNKNOWN", 0))
        rows.append({
            "residual_id": "RES-UNRES-1", "plan_id": plan.get("plan_id"),
            "resource_id": "*", "dimension": "unresolved",
            "predicted": {"value": n_deficit, "unit": "resources",
                          "basis": "plan resources state=resource_deficit 计数"},
            "actual": {"value": unresolved_dry, "unit": "nets",
                       "source": {"path": _rel(out_dir_rel +
                                               "/residual-certs.json"),
                                  "field": "counts",
                                  "sha256": _fsha(out_dir_rel +
                                                  "/residual-certs.json")}},
            "E": None,
            "measurement_convention":
                "口径不同分列：预测=资源级赤字数；实际=残网行级 UNSAT+UNKNOWN"
                "（frozen 布局 dry-run）——量纲不同，只并列不相减",
            "net_ids": [], "relation_ids": [],
            "snapshot_hash": (plan.get("snapshot") or {})
            .get("registry_snapshot_hash"),
        })
    if replay and binding["all_match"]:
        d = replay.get("definition") or {}
        unplaced = (d.get("denominator") - d.get("committed")
                    if d.get("denominator") and
                    d.get("committed") is not None else None)
        rows.append({
            "residual_id": "RES-UNRES-2", "plan_id": plan.get("plan_id"),
            "resource_id": "*", "dimension": "unresolved",
            "predicted": {"value": n_deficit, "unit": "resources",
                          "basis": "plan resources state=resource_deficit 计数"},
            "actual": {"value": unplaced, "unit": "nets",
                       "source": {"path": _rel(out_dir_rel +
                                               "/replay-plan.json"),
                                  "field": "definition.committed",
                                  "sha256": _fsha(out_dir_rel +
                                                  "/replay-plan.json")}},
            "E": None,
            "measurement_convention": "③ 重放板未落板网数（61 分母；"
                                      "committed 由 DRC 台账导出=derived）",
            "net_ids": [], "relation_ids": [],
            "snapshot_hash": (plan.get("snapshot") or {})
            .get("registry_snapshot_hash"),
        })

    # —— via_budget：demand 可比则成 residual；供给解锁后 0=退化预测（非缺数据） -
    vb = (res_index.get("via_budget") or [None])[0]
    via_obs = None
    if replay:
        via_obs = sum(len(r.get("vias") or [])
                      for r in (replay.get("executed_routes") or []))
    vb_demand = ((vb or {}).get("demand") or {}).get("value") if vb else None
    vb_supply = ((vb or {}).get("supply") or {}).get("value") if vb else None
    entry = {
        "residual_id": "RES-VIA-1", "plan_id": plan.get("plan_id"),
        "resource_id": (vb or {}).get("resource_id", "via_budget:board"),
        "dimension": "demand_vs_consumption",
        "actual_observed": {"value": via_obs, "unit": "vias",
                            "source": {"path": _rel(out_dir_rel +
                                                    "/replay-plan.json"),
                                       "field": "executed_routes",
                                       "sha256": (_fsha(out_dir_rel +
                                                  "/replay-plan.json")
                                                  if replay else None)}},
    }
    if vb is None or vb_demand is None or (vb_demand == 0 and vb_supply is None):
        entry.update({
            "status": "not_available",
            "reason": "via_budget demand=missing_basis（fab_capability_table "
                      "缺失，NEXT 待人工 #4）→无可比预测；实际观测 %s vias 仅"
                      "列账不成 residual" % via_obs,
        })
        na.append(entry)
    else:
        entry.update({
            "predicted": {"value": vb_demand, "unit": "vias",
                          "basis": (vb.get("demand") or {}).get("basis")},
            "E": {"value": (via_obs - vb_demand)
                  if via_obs is not None else None, "unit": "vias"},
            "measurement_convention": "count(vias in executed_routes)",
            "snapshot_hash": (plan.get("snapshot") or {})
            .get("registry_snapshot_hash"),
        })
        if vb_demand == 0:
            entry["measurement_convention"] = (
                "count(vias in executed_routes)；预测=③ 计划级 "
                "via_count_total=0（退化口径：③ 层计划未计 via，非真实零预测）"
                "——E=+%s 指向 demand 模型缺口，作 §17.3 离线校准输入" % via_obs)
            entry["model_gap"] = "layer_plan via_count_total=0（计划级未计）"
        rows.append(entry)

    # —— 其余资源族：无可比实际（符号 scope，无几何 join）→ not_available -------
    for kind, reason in (
        ("corridor", "计划资源 scope=符号引用（bus_id/corridor 名）；route 产物"
                     "无走廊成员归因→无可比实际（不伪造）"),
        ("bus_lane", "同 corridor：无几何 scope join；车道占用的走廊级实测未建"),
        ("escape_slots", "槽位实际占用需板级 escape 带几何重放；FC2 产物无该"
                         "实测→not_available"),
        ("power_return_space", "环路面积需电源网络实测布局；committed 集不含"
                               "电源网→not_available"),
    ):
        rs = res_index.get(kind) or []
        na.append({"dimension": "demand_vs_consumption",
                   "resource_id": (rs[0]["resource_id"] if rs else kind),
                   "reason": reason})
    na.append({"dimension": "reserve_vs_actual_reserve",
               "resource_id": "*",
               "reason": "实际 reserve 未在本 dry-run 重测（reserve 为计划量；"
                         "无可比实际→不生成伪 residual）"})

    rows.sort(key=lambda r: r["residual_id"])
    derived_rows = [
        {"derived": "actual 消耗 mm2=Σ(len×%g)@executed_routes" % LANE_PITCH_MM,
         "target": "layer_capacity:board"},
        {"derived": "unresolved 实际=counts.UNSAT+UNKNOWN / "
                    "denominator-committed", "target": "*"},
        {"derived": "max_detour_ratio 阈值=CPLACE_DETOUR_YELLOW（③ 同参）",
         "target": "CHK-LEN"},
    ]
    out["consumption"] = _consumption_evidence(plan, plan_sha, binding,
                                               reads, derived_rows)
    return out


# ---- 探针板/工程（kicad-cli 编排侧跑；本模块只 emit 文本） ---------------------
_PROBE_HEADER = (
    '(kicad_pcb\n'
    '\t(version 20260206)\n'
    '\t(generator "pcbflow-fd1-probe")\n'
    '\t(general\n\t\t(thickness 1.6)\n\t)\n'
    '\t(paper "A4")\n'
    '\t(layers\n'
    '\t\t(0 "F.Cu" signal)\n'
    '\t\t(2 "B.Cu" signal)\n'
    '\t\t(25 "Edge.Cuts" user)\n'
    '\t)\n'
)


def _pad(ref, num, net_code, net_name, x, y, w=1.0, h=1.0):
    return ('\t(footprint "T:T"\n\t\t(layer "F.Cu")\n\t\t(at %g %g)\n'
            '\t\t(property "Reference" "%s")\n'
            '\t\t(pad "%s" smd rect (at 0 0) (size %g %g) '
            '(layers "F.Cu" "F.Mask") (net "%s") (uuid "p-%s-%s"))\n'
            '\t)\n' % (x, y, ref, num, w, h, net_name, ref, num))


def _seg(net_code, net_name, x1, y1, x2, y2, w, uuid):
    return ('\t(segment\n\t\t(start %g %g)\n\t\t(end %g %g)\n'
            '\t\t(width %g)\n\t\t(layer "F.Cu")\n\t\t(net "%s")\n'
            '\t\t(uuid "%s")\n\t)\n'
            % (x1, y1, x2, y2, w, net_name, uuid))


def _via(net_code, net_name, x, y, size, drill, uuid):
    return ('\t(via\n\t\t(at %g %g)\n\t\t(size %g)\n\t\t(drill %g)\n'
            '\t\t(layers "F.Cu" "B.Cu")\n\t\t(net "%s")\n'
            '\t\t(uuid "%s")\n\t)\n' % (x, y, size, drill, net_name, uuid))


def build_probe_board(name: str) -> str:
    """合成探针板文本（单缺陷种子/clean 对照；固定 uuid=确定）。"""
    body = _PROBE_HEADER
    end = ('\t(gr_rect\n\t\t(start 0 0)\n\t\t(end 60 40)\n'
           '\t\t(stroke\n\t\t\t(width 0.05)\n\t\t\t(type default)\n\t\t)\n'
           '\t\t(layer "Edge.Cuts")\n\t\t(uuid "edge-probe")\n\t)\n)\n')

    def foot(pads):
        return "".join(_pad(*p) for p in pads)

    if name == PROBE_CLEAN:
        # 阴性对照：0.25 走线连通 + 合规过孔（环宽 0.3 ≥0.25）
        body += foot([("A", "1", 1, "N1", 10.0, 20.0),
                      ("B", "1", 1, "N1", 30.0, 20.0)])
        body += _seg(1, "N1", 10.0, 20.0, 30.0, 20.0, 0.25, "u-clean-1")
        body += _via(1, "N1", 20.0, 20.0, 1.0, 0.4, "u-clean-via")
    elif name == "probe-connectivity":
        body += foot([("A", "1", 1, "N1", 10.0, 20.0),
                      ("B", "1", 1, "N1", 30.0, 20.0)])
    elif name == "probe-shorting":
        body += foot([("A", "1", 1, "N1", 10.0, 20.0),
                      ("B", "1", 1, "N1", 30.0, 20.0),
                      ("C", "1", 2, "N2", 20.0, 5.0),
                      ("D", "1", 2, "N2", 20.0, 35.0)])
        body += _seg(1, "N1", 10.0, 20.0, 30.0, 20.0, 0.25, "u-short-1")
        body += _seg(2, "N2", 20.0, 5.0, 20.0, 35.0, 0.25, "u-short-2")
    elif name == "probe-width":
        body += foot([("A", "1", 1, "N1", 10.0, 20.0),
                      ("B", "1", 1, "N1", 30.0, 20.0)])
        body += _seg(1, "N1", 10.0, 20.0, 30.0, 20.0, 0.1, "u-width-1")
    elif name == "probe-clearance":
        body += foot([("A", "1", 1, "N1", 10.0, 20.0, 0.3, 0.3),
                      ("B", "1", 1, "N1", 30.0, 20.0, 0.3, 0.3),
                      ("C", "1", 2, "N2", 10.0, 20.4, 0.3, 0.3),
                      ("D", "1", 2, "N2", 30.0, 20.4, 0.3, 0.3)])
        body += _seg(1, "N1", 10.0, 20.0, 30.0, 20.0, 0.2, "u-clr-1")
        body += _seg(2, "N2", 10.0, 20.4, 30.0, 20.4, 0.2, "u-clr-2")
    elif name == "probe-annular":
        body += foot([("A", "1", 1, "N1", 10.0, 20.0),
                      ("B", "1", 1, "N1", 30.0, 20.0)])
        body += _seg(1, "N1", 10.0, 20.0, 20.0, 20.0, 0.25, "u-ann-1")
        body += _via(1, "N1", 20.0, 20.0, 0.6, 0.4, "u-ann-via")
        body += _seg(1, "N1", 20.0, 20.0, 30.0, 20.0, 0.25, "u-ann-2")
    else:
        raise ValueError("unknown probe: %s" % name)
    return body + end


def build_probe_project(_name: str) -> str:
    """探针工程 .kicad_pro 文本（显式规则=确定口径；rule_severities 全 error）。"""
    return json.dumps({
        "board": {
            "design_settings": {
                "rules": {
                    "min_clearance": 0.2,
                    "min_track_width": 0.2,
                    "min_annular_width": 0.25,
                    "min_hole_to_hole": 0.25,
                    "min_through_hole_diameter": 0.3,
                    "min_via_annular_width": 0.25,
                    "min_via_diameter": 0.6,
                },
            },
        },
        "meta": {"filename": "probe.kicad_pro", "version": "1"},
        "net_settings": {"excluded_layers": []},
        "text_variables": {},
    }, indent=2, sort_keys=True) + "\n"


def build_probe_battery(probe_drc_dir: str, out_dir_rel=FD1_OUT_DEFAULT):
    """探针电池判定：kicad-cli DRC JSON（hash 输入）→ 每探针 expected class
    detected？clean 对照零 error 级违规？门=5/5+clean（HANDOFF FD1）。"""
    del out_dir_rel
    drc_rel = probe_drc_dir
    results = []
    for p in PROBES:
        rel = "%s/%s/drc/probe-drc.json" % (drc_rel, p["probe"])
        d = _load_json(rel)
        if d is None:
            results.append({"probe": p["probe"], "checker_id": p["checker_id"],
                            "detected": None,
                            "reason": "DRC JSON 缺失（编排侧未跑）"})
            continue
        types = {v["type"] for v in d.get("violations", [])}
        unconn = bool(d.get("unconnected_items"))
        hit = bool(types & set(p["expected_types"])) or \
            (p["checker_id"] == "CHK-CONN" and unconn)
        results.append({
            "probe": p["probe"], "checker_id": p["checker_id"],
            "seed": p["seed"], "expected_types": p["expected_types"],
            "observed_types": sorted(types),
            "unconnected_items": len(d.get("unconnected_items", [])),
            "detected": hit,
            "evidence": {"report": _rel(rel), "sha256": _fsha(rel)},
        })
    clean_rel = "%s/%s/drc/probe-drc.json" % (drc_rel, PROBE_CLEAN)
    clean = _load_json(clean_rel)
    if clean is None:
        clean_row = {"probe": PROBE_CLEAN, "clean": None,
                     "reason": "DRC JSON 缺失（编排侧未跑）"}
        clean_ok = None
    else:
        errs = [v for v in clean.get("violations", [])
                if v.get("severity") == "error"]
        clean_row = {"probe": PROBE_CLEAN, "clean": not errs,
                     "error_violations": len(errs),
                     "observed_types": sorted({v["type"] for v in
                                               clean.get("violations", [])}),
                     "unconnected_items": len(clean.get("unconnected_items",
                                                        [])),
                     "evidence": {"report": clean_rel,
                                  "sha256": _fsha(clean_rel)}}
        clean_ok = not errs and not clean.get("unconnected_items")
    detected = [r for r in results if r.get("detected") is True]
    missing = [r for r in results if r.get("detected") is not True]
    total = len(PROBES)
    passed = len(detected)
    battery_100 = (passed == total and clean_ok is True)
    return {
        "schema_version": FD1_SCHEMA,
        "artifact_kind": "probe_battery",
        "spec_ref": "SPEC v1.3 §11.1（kicad_authoritative 子集）；"
                    "HANDOFF FD1 门",
        "authority_scope": AUTH_KICAD,
        "gate": {"expected": total, "detected": passed,
                 "clean_control_ok": clean_ok,
                 "battery_100": battery_100},
        "results": results + [clean_row],
        "drc_runner": "kicad-cli（编排侧执行；pcbflow 零子进程，FC2-D3 口径）",
    }


# ---- envelope/report/组装 ------------------------------------------------------
def _checker_registry(out_dir_rel=FD1_OUT_DEFAULT, ff_plan_dir=None):
    del out_dir_rel
    reads: list = []
    plan, plan_sha, binding = _plan_with_binding(reads, ff_plan_dir)
    vision = 0  # 视觉候选=0（视觉轨道未被指派；HANDOFF §2 adoption 规则）
    return {
        "schema_version": FD1_SCHEMA,
        "artifact_kind": "checker_registry",
        "spec_ref": "SPEC v1.3 §11.1/§16.5",
        "authority_classes": list(AUTHORITIES),
        "checkers": [
            {"checker_id": c["checker_id"], "name": c["name"],
             "authority": c["authority"], "spec_ref": c["spec_ref"],
             "params": c["params"], "violation_types": c["violation_types"],
             "note": c["note"], "source": "spec_built_in",
             "promotion": {"path": "spec_built_in（§11.1 权威表逐行）",
                           "v1_vision_promotion": "not_applicable",
                           "mutation_battery": (
                               "tests/test_fd1.py 正向/负向变异"
                               if c["authority"] == AUTH_DET else None)}}
            for c in CHECKERS],
        "vision_candidates": vision,
        "vision_candidates_note": "视觉轨道未被指派（HANDOFF §2：advisory 轨道"
                                  "不进核心会话任务面）→候选 0，如实记账",
        "consumption": _consumption_evidence(plan, plan_sha, binding, reads, []),
    }


def build_check_report(out_dir_rel=FD1_OUT_DEFAULT, fc2_dir=FC2_DIR,
                       ff_plan_dir=None):
    ff_plan_dir = ff_plan_dir or FF1_DIR
    reads: list = []
    plan, plan_sha, binding = _plan_with_binding(reads, ff_plan_dir)
    kicad_rows = run_kicad_authoritative(reads, fc2_dir)
    replay = _load_json(fc2_dir + "/replay-plan.json", reads,
                        role="input", field="executed_routes")
    routes = (replay or {}).get("executed_routes") or []
    registry = _load_json(A3_DIR + "/net-registry.json", reads,
                          role="input", field="relations")
    diff_rels = [r for r in ((registry or {}).get("relations") or {}).values()
                 if r.get("kind") == "differential_pair"]
    det_rows = run_deterministic_screening(
        routes,
        sym_classes=None,
        diff_relations=diff_rels,
        reads=reads,
        structures_approved=bool(
            (plan or {}).get("snapshot", {}).get(
                "structures_override_sha256")))
    ext_rows = run_not_executed()
    all_rows = kicad_rows + det_rows + ext_rows
    failed = [r["checker_id"] for r in all_rows if r.get("verdict") == "fail"]
    executed_n = sum(1 for r in all_rows
                     if r.get("checker_status") == "executed")
    return {
        "schema_version": FD1_SCHEMA,
        "artifact_kind": "check_report",
        "spec_ref": "SPEC v1.3 §11/§11.4",
        "dataset": "Rev-C FC2 dry-run（④ committed 55/61 路由 + DRC ledger）",
        "registry_snapshot_hash":
            (plan.get("snapshot") or {}).get("registry_snapshot_hash")
            if plan else None,
        "plan_id": (plan or {}).get("plan_id"),
        "snapshot_check": binding,
        "stale_plan_reason": binding["stale_plan_reason"],
        "checker_status_note": "checker_status（executed/not_executed）与 "
                               "verdict 分列不互替（SPEC §0.1）",
        "results": all_rows,
        "summary": {"checkers": len(all_rows),
                    "executed": executed_n,
                    "not_executed": len(all_rows) - executed_n,
                    "failed": sorted(failed)},
        "run_strategy": "④ 期间逐总线增量检查未启用（dry-run 终局全量一次；"
                        "§11.4）；同一 registry snapshot+计划 hash 绑定",
        "consumption": _consumption_evidence(plan, plan_sha, binding, reads, [
            {"derived": "CHK-LEN 绕行比；CHK-CORNER 零长/重复段",
             "target": "executed_routes"}]),
    }


def build_envelope(out_dir_rel=FD1_OUT_DEFAULT, probe_drc_dir=None,
                   fc2_dir=FC2_DIR, ff_plan_dir=None):
    """⑤ 门（HANDOFF FD1）= 检查器族验证：探针电池 100%（kicad_authoritative
    子集）+ authority 检查执行完整 + 变异电池（pytest）。

    board_quality 单列（dry-run 已知开放项如实带入 ⑥，不与检查器验证混读）：
    检查器在 dry-run 板上的 fail（如 CHK-CONN 303 unconnected）是检查结论，
    不是检查器验证失败——口径同 FC2（55/61 verdict=pass + 已知未过项分列）。
    """
    ff_plan_dir = ff_plan_dir or FF1_DIR
    battery = None
    bpath = _p(out_dir_rel + "/probe-battery.json")
    if os.path.exists(bpath):
        with open(bpath, encoding="utf-8") as f:
            battery = json.load(f)
    report = build_check_report(out_dir_rel, fc2_dir, ff_plan_dir)
    conn_row = next((r for r in report["results"]
                     if r["checker_id"] == "CHK-CONN"), {})
    kicad_rows = [r for r in report["results"]
                  if r["authority"] == AUTH_KICAD
                  and r["checker_id"] != "CHK-LEDGER-UNMAPPED"]
    det_rows = [r for r in report["results"]
                if r["authority"] == AUTH_DET]
    validation = {
        "probe_battery_100": (battery or {}).get("gate", {}).get(
            "battery_100"),
        "probe_battery": (battery or {}).get("gate"),
        "kicad_authoritative_executed": all(
            r.get("checker_status") == "executed" for r in kicad_rows),
        "deterministic_available_executed": all(
            r.get("checker_status") == "executed" for r in det_rows
            if r.get("checker_status") is not None
            and r.get("verdict") is not None),
        "mutation_battery": "tests/test_fd1.py（deterministic_screening "
                            "正向/负向变异；pytest 门）",
    }
    validation["validation_ok"] = (validation["probe_battery_100"] is True
                                   and validation[
                                       "kicad_authoritative_executed"]
                                   and validation[
                                       "deterministic_available_executed"])
    gate = {
        "spec_ref": "HANDOFF FD1/SPEC §11/§15-FD1",
        "checker_validation": validation,
        "board_quality": {
            "failed_checkers": report["summary"]["failed"],
            "connectivity_unconnected": conn_row.get("unconnected_items"),
            "connectivity_new_vs_baseline":
                conn_row.get("unconnected_new_vs_baseline"),
            "note": "dry-run 已知开放项（④ 55/61 committed；非本集网络未连）"
                    "如实列账并带入 ⑥ 签核包，不与检查器验证混读",
        },
        "external_not_executed_honest": all(
            r.get("checker_status") == "not_executed"
            for r in report["results"]
            if r["authority"] in (AUTH_SCREEN, AUTH_EXT)),
        "stale_plan": report["stale_plan_reason"],
    }
    diagnostics = []
    if validation["probe_battery_100"] is None:
        diagnostics.append({
            "id": "probe_battery_missing",
            "title": "probe-battery.json 缺失：先编排侧跑 kicad-cli 探针 DRC，"
                     "再 --select probe_battery 回填（HANDOFF FD1 门）"})
    if gate["board_quality"]["failed_checkers"]:
        diagnostics.append({
            "id": "board_quality_known_open",
            "title": "板级检查结论含 fail（dry-run 已知开放项）：%s"
                     % ",".join(gate["board_quality"]["failed_checkers"])})
    status = ("ok" if validation["validation_ok"] else
              "unknown" if validation["probe_battery_100"] is None
              else "failed")
    verdict = ("pass" if status == "ok" else
               "yellow" if status == "unknown" else "fail")
    inputs = []
    for rel, role in (
            (out_dir_rel + "/probe-battery.json", "probe_battery"),
            (fc2_dir + "/drc/final-all.json", "authority_report"),
            (fc2_dir + "/drc/baseline-all.json", "authority_baseline"),
            (fc2_dir + "/replay-plan.json", "route_actual"),
            (ff_plan_dir + "/feedforward-plan.json", "ff_plan")):
        sha = _fsha(rel)
        if sha:
            inputs.append({"path": rel, "sha256": sha, "role": role})
    return {
        "schema_version": FD1_SCHEMA,
        "tool": "pcbflow", "tool_version": config.TOOL_VERSION,
        "command": "check", "command_kind": "core",
        "status": status, "verdict": verdict,
        "deterministic": True, "determinism_claim": "byte_exact",
        "inputs": inputs, "config_sha256": None,
        "spec_refs": ["tools/pcbflow/SPEC.md#§11",
                      "tools/pcbflow/SPEC.md#§15-FD1",
                      "tools/pcbflow/SPEC.md#§16.5"],
        "artifacts": [
            {"path": _rel(out_dir_rel + "/checker-registry.json"),
             "role": "core"},
            {"path": _rel(out_dir_rel + "/check-report.json"), "role": "core"},
            {"path": _rel(out_dir_rel + "/ff-residuals.json"), "role": "core"},
            {"path": _rel(out_dir_rel + "/probe-battery.json"),
             "role": "core"},
            {"path": _rel(out_dir_rel + "/check-report.md"),
             "role": "human_report"},
        ],
        "metrics": {
            "checkers": report["summary"]["checkers"],
            "executed": report["summary"]["executed"],
            "probe_battery": (battery or {}).get("gate"),
            "board_quality_failed": gate["board_quality"]["failed_checkers"],
        },
        "diagnostics": diagnostics + [
            {"id": "external_not_executed",
             "title": "screening_or_external/external 档如实 not_executed"
                      "（toolchain_lock 无外部工具；§11.1 authority 设计）"},
        ],
        "waivers": [],
        "solver": {},
        "run_metadata": {},
        "data": {"gate": gate},
    }


def build_report_md(env, report, residuals, battery):
    g = env["data"]["gate"]
    lines = ["# PCBFlow ⑤ 交错检查报告（FD1）", "",
             "- 门 verdict：%s；status：%s" % (env["verdict"], env["status"]),
             "- dataset：%s" % report["dataset"], ""]
    lines += ["## 探针电池（kicad_authoritative 子集）", ""]
    if battery:
        bg = battery["gate"]
        lines.append("- %d/%d detected；clean 对照=%s；battery_100=%s"
                     % (bg["detected"], bg["expected"],
                        bg.get("clean_control_ok"), bg["battery_100"]))
        for r in battery["results"]:
            if "checker_id" in r:
                lines.append("- %s → %s：%s" % (
                    r["probe"], r["checker_id"],
                    ("detected（%s）" % ",".join(r.get("observed_types", [])))
                    if r.get("detected") else
                    (r.get("reason") or "未检出")))
            else:
                lines.append("- %s：clean=%s（error 违规 %s）" % (
                    r["probe"], r.get("clean"),
                    r.get("error_violations")))
    else:
        lines.append("- 未回填（编排侧 kicad-cli 未跑）")
    lines += ["", "## 检查器（authority 分档）", "",
              "| 检查器 | authority | status | verdict | 说明 |",
              "|---|---|---|---|---|"]
    for r in report["results"]:
        note = r.get("reason") or r.get("not_available_reason") or ""
        if r.get("violation_counts"):
            note = json.dumps(r["violation_counts"], ensure_ascii=False)
        if r.get("unconnected_items") is not None:
            note = ("unconnected=%s（vs baseline %+d）"
                    % (r["unconnected_items"],
                       r.get("unconnected_new_vs_baseline") or 0))
        lines.append("| %s %s | %s | %s | %s | %s |" % (
            r["checker_id"], r["name"], r["authority"],
            r["checker_status"], r.get("verdict") or "-", note[:60]))
    lines += ["", "## 前馈残差（§11.2）", ""]
    for r in residuals["rows"]:
        lines.append("- %s %s（%s）：E=%s；口径=%s"
                     % (r["residual_id"], r["resource_id"], r["dimension"],
                        json.dumps(r["E"], ensure_ascii=False)
                        if r.get("E") is not None else "n/a",
                        r["measurement_convention"][:70]))
    for r in residuals["not_available"]:
        lines.append("- not_available %s（%s）：%s"
                     % (r.get("residual_id", r.get("dimension")),
                        r.get("resource_id", "*"), r["reason"][:80]))
    lines += ["", "## 门", ""]
    for k, v in sorted(g.items()):
        lines.append("- %s：`%s`" % (k, v))
    lines += ["", "人读视图非事实源；核心产物见 checker-registry/check-report/"
              "ff-residuals/probe-battery。", ""]
    return "\n".join(lines)


def build_products(select="summary", out_dir_rel=FD1_OUT_DEFAULT,
                   probe=None, probe_drc_dir=None, fc2_dir=FC2_DIR,
                   ff_plan_dir=None):
    ff_plan_dir = ff_plan_dir or FF1_DIR
    import datetime

    t0 = datetime.datetime.now(datetime.timezone.utc)
    if select == "checker_registry":
        obj = _checker_registry(out_dir_rel, ff_plan_dir)
        return {"payload": {"obj": obj}, "kind": "json"}
    if select == "check_report":
        obj = build_check_report(out_dir_rel, fc2_dir, ff_plan_dir)
        return {"payload": {"obj": obj}, "kind": "json"}
    if select == "ff_residuals":
        obj = build_ff_residuals(fc2_dir, ff_plan_dir)
        return {"payload": {"obj": obj}, "kind": "json"}
    if select == "probe_board":
        return {"payload": build_probe_board(probe).encode(config.ENCODING),
                "kind": "bytes"}
    if select == "probe_project":
        return {"payload": build_probe_project(probe).encode(config.ENCODING),
                "kind": "bytes"}
    if select == "probe_battery":
        obj = build_probe_battery(probe_drc_dir, out_dir_rel)
        return {"payload": {"obj": obj}, "kind": "json"}
    if select == "envelope":
        env = build_envelope(out_dir_rel, probe_drc_dir, fc2_dir, ff_plan_dir)
        return {"payload": {"obj": env}, "kind": "json"}
    if select == "run_manifest":
        t1 = datetime.datetime.now(datetime.timezone.utc)
        manifest = {
            "started_at": t0.isoformat(), "finished_at": t1.isoformat(),
            "elapsed_s": round((t1 - t0).total_seconds(), 3),
            "python_version": __import__("sys").version.split()[0],
            "tool_version": config.TOOL_VERSION,
            "command": "check", "out_dir": out_dir_rel,
            "spec_sha256": hashing.sha256_file(
                os.path.join(config.PCBFLOW_ROOT, "SPEC.md")),
        }
        return {"payload": {"obj": manifest}, "kind": "json"}
    if select == "report":
        env = build_envelope(out_dir_rel, probe_drc_dir, fc2_dir, ff_plan_dir)
        report = build_check_report(out_dir_rel, fc2_dir, ff_plan_dir)
        residuals = build_ff_residuals(fc2_dir, ff_plan_dir)
        bpath = _p(out_dir_rel + "/probe-battery.json")
        battery = None
        if os.path.exists(bpath):
            with open(bpath, encoding="utf-8") as f:
                battery = json.load(f)
        return {"payload": build_report_md(env, report, residuals,
                                           battery).encode("utf-8"),
                "kind": "bytes"}
    # summary
    env = build_envelope(out_dir_rel, probe_drc_dir, fc2_dir, ff_plan_dir)
    return {"payload": {"obj": {
        "command": "check", "status": env["status"],
        "verdict": env["verdict"], "metrics": env["metrics"],
        "gate": env["data"]["gate"], "diagnostics": env["diagnostics"],
        "note": "人读视图非事实源；核心产物见 checker-registry/check-report/"
                "ff-residuals/probe-battery",
    }}, "kind": "json"}
