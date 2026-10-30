"""②→③ 前馈资源账本、比较与基线冻结（SPEC v1.3 §6/§7/§15 FF-0..FF-3）。

生成器模式：零落盘、零子进程；产物内存构建后由 CLI 打到 stdout，shell 重定向落盘。
只读输入：out/revc-a3、out/revc-b1 冻结产物 + p3 快照板/CSV + Rev-C 只读输入。
计划 authority=planning_advisory：不反向写 constraints/structures，不写板，
controls 未经 FF-4 consumer gate 不影响 ③ 候选接受（§18 红线）。
核心产物（plan/coverage/comparison/baseline-freeze）禁 wall-clock/主机路径；
run_manifest 单独收运行元数据（§14.3）。
"""

from __future__ import annotations

import datetime
import json
import math
import os
import socket
import sys

from . import audit_cmd, compile_cmd, config, coplace_cmd, envelope, enum_cmd
from . import feedforward_config as ffc
from . import geo, hashing

_PLAN_STATUS = "planning_advisory"
_PLAN_AUTHORITY = "planning_advisory"

# ---- FD2 级联重跑（2026-08-30 会话；SPEC v1.3 §15 adoption check） -----------------
# 批准/源输入（revc-fd1/approvals，FD1 会话落盘；本模块只读消费）
OVERRIDE_REL = "out/revc-fd1/approvals/structures.override.json"
SOURCES_DIR_REL = "out/revc-fd1/approvals/sources"
FAB_CAPABILITY_REL = SOURCES_DIR_REL + "/fabrication-capability-jlcpcb.json"
STACKUP_BASIS_REL = SOURCES_DIR_REL + "/stackup-basis.json"
INTERFACE_CURRENT_REL = SOURCES_DIR_REL + "/interface-current.json"
ADOPT_PLAN_ID = "FF-REVC-0002"
# ---- FF3 级联重跑（2026-08-30 会话；BOM 派生轨功耗表 derived 消费） ---------------
BOM_POWER_REL = "out/revc-fd3/approvals/sources/bom-power-derive.json"
FF3_PLAN_ID = "FF-REVC-0003"
# ---- CAS1 级联收口（2026-08-30 会话；确认点 #4 已批：IT 布局采纳） --------------
# placement 绑定切至采纳快照（§9.4 批准路径：layout.json 批准后确定性生成
# 新 placement.csv 并绑定）；fd3 口径沿留（--consume-bom），fd3 冻结零回写
CAS_PLAN_ID = "FF-REVC-0004"
# ---- FF5 资料级 rail 源复算（2026-08-30 会话；用户裁决「无实测；资料级即终态」） ----
# --bom-power-file 指向后续权威 rail 源（cas2 v2：EMMC_VSEL demand 落 sourced，
# VCAP1/2/VBAT/FB_NODE definitive 定性）；fd3 钉源为缺省，fd3 冻结零回写
FF5_PLAN_ID = "FF-REVC-0005"
RAIL_YELLOW_FRACTION = 0.10  # rail 供给落位后筛查线（与 via_budget 同口径）
IMPEDANCE_RERUN_SCHEMA = "1.3"
# via_budget 供给=能力表最小尺寸推导密度上界（derived，非实测）：
# 单元节距 = min_via_pad 0.25 + 2×min_trace_spacing 0.09 = 0.43mm
VIA_CELL_PAD_MM = 0.25
VIA_CELL_SPACING_MM = 0.09
VIA_BUDGET_YELLOW_FRACTION = 0.10  # 与 FF_LAYER_YELLOW_FRACTION 同口径（筛查）
# IPC-2221A 外层 1oz/10°C 拟合式（interface-current.json derived_policy 提案；
# I[A]=0.048·ΔT^0.44·A[mil²]^0.725；1oz 铜厚 1.37mil）
IPC2221_K_EXTERNAL = 0.048
IPC2221_DT_C = 10.0
IPC2221_OZ_THICKNESS_MIL = 1.37
USB_VBUS_BUDGET_A = 0.5  # sourced：USB 2.0 §7.2.1.1 高功率端口（无 CC 协商保守）


# ---- 基础工具 ---------------------------------------------------------------
def _abs(rel: str) -> str:
    return os.path.join(config.PCBFLOW_ROOT, *rel.split("/"))


def _read_json(rel: str, role: str, reads: list):
    """读冻结产物：返回 (obj, sha256)。登记真实读取（D7 actually_read 证据源）。"""
    with open(_abs(rel), "rb") as f:
        data = f.read()
    reads.append({"artifact": rel, "field": "<file>", "role": role})
    return json.loads(data.decode(config.ENCODING)), hashing.sha256_bytes(data)


def ff_config_snapshot() -> dict:
    return {k: v for k, v in vars(ffc).items() if k.isupper()}


def ff_config_sha256() -> str:
    return hashing.sha256_text(hashing.json_dumps(ff_config_snapshot()))


def classify_resource(margin, yellow_value: float, has_basis: bool) -> str:
    """四态分类（SPEC v1.3 §6.3）。缺 basis 一律 missing_basis，禁默认 green。"""
    if not has_basis or margin is None:
        return "missing_basis"
    if margin < 0:
        return "resource_deficit"
    if margin < yellow_value:
        return "low_margin"
    return "available"


def check_stale(plan_snapshot: dict, current_snapshot: dict) -> dict:
    """§7.4 六 hash 过期检查：任何不匹配 → stale_plan，不得静默消费。"""
    diffs = {}
    for k in ffc.STALE_CHECK_KEYS:
        if plan_snapshot.get(k) != current_snapshot.get(k):
            diffs[k] = {"plan": plan_snapshot.get(k),
                        "current": current_snapshot.get(k)}
    return {"stale_plan": bool(diffs), "diff_keys": sorted(diffs), "diffs": diffs}


def detect_control_conflicts(controls: list) -> list:
    """同 target 同 kind 且动作不一致 → 冲突登记（不静默覆盖，§6.5/§16.2-9）。"""
    by_target = {}
    for ctl in controls:
        by_target.setdefault(ctl["target"], []).append(ctl)
    conflicts = []
    for target in sorted(by_target):
        by_kind = {}
        for ctl in by_target[target]:
            by_kind.setdefault(ctl["kind"], []).append(ctl)
        for kind in sorted(by_kind):
            same = by_kind[kind]
            actions = {hashing.json_dumps(c["action"]) for c in same}
            if len(same) > 1 and len(actions) > 1:
                conflicts.append({
                    "conflict_id": "CFL-%04d" % (len(conflicts) + 1),
                    "target": target, "kind": kind,
                    "control_ids": sorted(c["control_id"] for c in same),
                    "actions": sorted(actions),
                    "resolution": "按 preemption_policy 排序（" + ffc.PREEMPTION_POLICY
                                  + "）；未裁决前双方均保持 planning_advisory，不静默择一",
                })
    return conflicts


# ---- FD2 批准/源消费（只读；显式 adopt 模式才启用，默认路径零影响） -------------
def load_override(reads):
    """① 权威批准件（structures.override.json）：返回 (obj, sha256)。
    base_draft.sha256 必须与盘上草案 hash 一致，否则 ValueError（不静默消费）。"""
    ov, ov_sha = _read_json(OVERRIDE_REL, "structures_override", reads)
    base = (ov.get("approved") or {}).get("base_draft") or {}
    draft_sha = hashing.sha256_file(_abs(ffc.A3_DIR_REL + "/structures.json"))
    if base.get("sha256") != draft_sha:
        raise ValueError(
            "structures.override base_draft sha256 不匹配盘上草案（%s vs %s）"
            % (base.get("sha256"), draft_sha))
    reads.append({"artifact": ffc.A3_DIR_REL + "/structures.json",
                  "field": "<file>（base_draft 一致性核对）",
                  "role": "structures_override_binding"})
    return ov, ov_sha


def approved_structures_view(draft: dict, override: dict) -> dict:
    """批准后 ① 权威视图 = 草案对读 override（不改草案文件本身，§override
    authority_note）：authority_status=approved + STR-1/STR-2 裁决落 status。"""
    st = json.loads(json.dumps(draft))  # 深拷贝，禁改冻结草案
    st["authority_status"] = "approved"
    st["authority_note"] = (
        "structures.override.json 转正（确认点 #1/#2 已批，2026-08-30 会话消费）；"
        "base_draft=%s；本视图=草案+STR-1/2 裁决的确定性对读，草案文件零修改"
        % ((override.get("approved") or {}).get("base_draft", {}).get("sha256",
                                                                      "")[:12]))
    verdict_to_status = {
        "adopt_proposal": "adopted（override STR-1，2026-08-30）",
        "adopt_with_structures": "adopted_with_structures（override STR-2）",
    }
    for f in st.get("findings") or []:
        for d in (override.get("approved") or {}).get("diff_vs_draft") or []:
            if f.get("id") == d.get("finding_id"):
                f["status"] = verdict_to_status.get(
                    d.get("verdict"), "adopted（override）")
    return st


def approved_structures_sha256(draft: dict, override: dict) -> str:
    return hashing.sha256_bytes(
        hashing.canonical_json_bytes(approved_structures_view(draft, override)))


def _load_fd2_sources(reads):
    """能力表/叠层基面/接口电流三源（FD1 会话查证落盘；本函数只读+hash 登记）。"""
    fab, fab_sha = _read_json(FAB_CAPABILITY_REL, "fab_capability", reads)
    stack, stack_sha = _read_json(STACKUP_BASIS_REL, "stackup_basis", reads)
    cur, cur_sha = _read_json(INTERFACE_CURRENT_REL, "interface_current", reads)
    return {"fab": fab, "fab_sha256": fab_sha,
            "stackup": stack, "stackup_sha256": stack_sha,
            "current": cur, "current_sha256": cur_sha}


def _load_bom_power(reads, rel=None):
    """BOM 派生轨功耗/供给表（FF3 会话钉源；derived 语义，只读+hash 登记）。

    rel=None 缺省 fd3 钉源；FF5 起 --bom-power-file 指向后续权威源，有效
    路径随 bom dict 的 rel 键下传（资源行 reads/basis 引用保持一致）。"""
    path = rel or BOM_POWER_REL
    bom, bom_sha = _read_json(path, "bom_power_derive", reads)
    return {"table": bom, "sha256": bom_sha, "rel": path}


def _trunk_width_mm(min_width_raw: str):
    """min_width_raw 首个数值=干路线宽（structures 已批口径；解析失败→None）。"""
    import re
    m = re.match(r"\s*(\d+(?:\.\d+)?)", min_width_raw or "")
    return float(m.group(1)) if m else None


def ipc2221_current_a(width_mm: float) -> float:
    """IPC-2221A 外层 1oz/10°C 拟合式（derived 政策；图表读数 3V3≈2.2A vs
    拟合 2.34A 差 ~6%，一致性核对随 basis 登记）。"""
    area_mil2 = (width_mm / 0.0254) * IPC2221_OZ_THICKNESS_MIL
    return (IPC2221_K_EXTERNAL * (IPC2221_DT_C ** 0.44)
            * (area_mil2 ** 0.725))


def via_budget_supply(supply_area_mm2_one_layer: float, fab: dict):
    """via_budget 供给=能力表最小尺寸推导密度上界（derived，非实测上界；
    逐单能力以下单页为准——caveat 随 basis）。"""
    v = fab.get("values") or {}
    pad = float(v.get("min_via_pad_mm") or VIA_CELL_PAD_MM)
    spacing = float(v.get("min_trace_width_spacing_1oz_multilayer_mm")
                    or VIA_CELL_SPACING_MM)
    cell_mm = pad + 2.0 * spacing
    cell_area = cell_mm * cell_mm
    return int(supply_area_mm2_one_layer / cell_area), {
        "cell_pitch_mm": round(cell_mm, 4), "cell_area_mm2": round(cell_area, 6),
        "min_via_pad_mm": pad, "min_trace_spacing_mm": spacing}


# ---- 阻抗一阶公式（IPC-2141 近似族；derived 预估，TBD-1 义务保留） --------------
def microstrip_z0(w_mm, h_mm, t_mm, er):
    return (87.0 / math.sqrt(er + 1.41)
            * math.log(5.98 * h_mm / (0.8 * w_mm + t_mm)))


def width_for_z0(z0_ohm, h_mm, t_mm, er):
    """闭式解：w = (5.98h·e^(−Z0·√(Er+1.41)/87) − t)/0.8。"""
    arg = math.exp(-z0_ohm * math.sqrt(er + 1.41) / 87.0)
    return (5.98 * h_mm * arg - t_mm) / 0.8


def zdiff_edge_coupled(w_mm, s_mm, h_mm, t_mm, er):
    """差分近似：Zdiff=2·Z0·(1−0.48·e^(−0.96·s/h))（IPC-2141 族一阶口径）。"""
    return 2.0 * microstrip_z0(w_mm, h_mm, t_mm, er) * (
        1.0 - 0.48 * math.exp(-0.96 * s_mm / h_mm))


def width_for_zdiff(z0_target_ohm, s_mm, h_mm, t_mm, er, lo=0.05, hi=3.0,
                    iters=200):
    """给定间距求差分目标阻抗线宽（二分；固定迭代数=确定）。"""
    for _ in range(iters):
        mid = (lo + hi) / 2.0
        if zdiff_edge_coupled(mid, s_mm, h_mm, t_mm, er) > z0_target_ohm:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def build_impedance_targets(plan_id, sources, reads):
    """叠层基面重算（FD2 adoption 任务；一阶公式 derived 预估，正式定稿仍以
    板厂叠层表+实测为准——stackup-basis.json caveat 义务保留）。"""
    stack = sources["stackup"]
    layer0 = (stack.get("stackup") or [{}])[0]
    pp1 = next((l for l in stack.get("stackup") or []
                if str(l.get("material", "")).startswith("Prepreg")), {})
    h = float(pp1.get("thickness_mm"))
    er = float(pp1.get("er"))
    t = float(layer0.get("thickness_mm"))
    reads.append({"artifact": STACKUP_BASIS_REL,
                  "field": "stackup[Prepreg 7628].thickness_mm/er + stackup[Top]"
                           ".thickness_mm", "role": "stackup_basis"})
    w50 = width_for_z0(50.0, h, t, er)
    usb_w, usb_s = 0.2, 0.2  # adopted_width_mm/geom_spacing_mm（a3 基线口径）
    zd_adopted = zdiff_edge_coupled(usb_w, usb_s, h, t, er)
    w90 = width_for_zdiff(90.0, usb_s, h, t, er)
    base_rel = ffc.A3_DIR_REL + "/impedance_targets.json"
    base_obj, base_sha = _read_json(base_rel, "impedance_baseline", reads)
    targets = [
        {"net_class": "USB_DIFF", "impedance_ohm": 90, "layer": "F.Cu",
         "tolerance_pct": 15,
         "adopted_geometry_mm": {"width": usb_w, "spacing": usb_s},
         "est_zdiff_ohm_adopted_geometry": round(zd_adopted, 1),
         "est_width_mm_for_target": round(w90, 4),
         "est_geometry_basis": "s=%g（板现口径）下二分解 w；固定 200 迭代"
                               % usb_s,
         "within_tolerance": abs(zd_adopted - 90.0) <= 90.0 * 0.15,
         "revision_threshold_30pct_exceeded":
             abs(zd_adopted - 90.0) > 90.0 * 0.30,
         "status": "pending_TBD-1（一阶公式复核偏差；宽度修订建议留板厂"
                   "阻抗计算器定稿）",
         "note": "重算后 0.2/0.2 几何一阶预估偏离目标 %+.1f%%（±15%% 容差外、"
                 "<30%% 修订阈）；spec 已 deprioritize（<70mm，等长+参考连续"
                 "为主控）；正式值待板厂叠层定稿"
                 % ((zd_adopted - 90.0) / 90.0 * 100.0)},
        {"net_class": "single_ended_critical", "impedance_ohm": 50,
         "layer": "F.Cu", "tolerance_pct": 15,
         "adopted_width_mm": 0.2,
         "est_width_mm_for_target": round(w50, 4),
         "within_tolerance": True,
         "status": "deprioritized_by_spec（沿留）",
         "note": "50Ω 一阶解 w=%.4gmm（IPC-2141 闭式）；旧假设口径估 "
                 "0.35~0.40，方向一致；铜长 <70mm 等长为主控（§1 注沿留）"
                 % w50},
    ]
    return {
        "schema_version": IMPEDANCE_RERUN_SCHEMA,
        "artifact_kind": "impedance_targets_rerun",
        "spec_ref": "SPEC v1.3 §17.1/§15 adoption check；stackup-basis.json"
                    " caveat（impedance_targets 重算=FF 级联重跑会话任务）",
        "plan_id": plan_id,
        "estimate_class": "first_order_estimate（derived；非板厂权威）",
        "formulas": {
            "microstrip_z0": "Z0=87/√(Er+1.41)·ln(5.98h/(0.8w+t))（IPC-2141 "
                             "近似族）",
            "zdiff": "Zdiff=2·Z0·(1−0.48·e^(−0.96·s/h))",
            "width_for_z0": "闭式解 w=(5.98h·e^(−Z0·√(Er+1.41)/87)−t)/0.8",
        },
        "stackup_inputs": {"h_prepreg_mm": h, "er_prepreg": er,
                           "t_outer_mm": t,
                           "stackup_code": stack.get("stackup_code")},
        "baseline": {"path": base_rel, "sha256": base_sha,
                     "basis": base_obj.get("basis")},
        "targets": targets,
        "tbd1_note": "TBD-1 状态：无叠层可估→有基面可重算（本件）；正式阻抗"
                     "报告仍需板厂叠层定稿+实测（义务保留，不消除）",
    }


# ---- 冻结基线装载（FF-1 数据面） ---------------------------------------------
def _load_frozen_basis(override=None):
    """override=None：FF1 原口径（草案文件 hash 绑定）。
    override=批准件：structures_sha256 绑定=草案对读 override 的批准视图 hash
    （草案文件零修改；authority 转正=FD2 adoption，信息键随 snapshot 记录）。"""
    reads = []
    reg, reg_sha = _read_json(ffc.A3_DIR_REL + "/net-registry.json", "registry", reads)
    st, st_sha = _read_json(ffc.A3_DIR_REL + "/structures.json", "structures", reads)
    co, co_sha = _read_json(ffc.A3_DIR_REL + "/constraints.json", "constraints", reads)
    aud, aud_sha = _read_json(ffc.A3_DIR_REL + "/audit.json", "audit", reads)
    seed, seed_sha = _read_json(ffc.A3_DIR_REL + "/skeleton-seed.json", "skeleton_seed", reads)
    lay, lay_sha = _read_json(ffc.B1_DIR_REL + "/layout.json", "layout_baseline", reads)
    lp, lp_sha = _read_json(ffc.B1_DIR_REL + "/layer-plan.json", "layer_plan", reads)
    board_sha = hashing.sha256_file(config.AUDIT_P3_BOARD)
    placement_sha = hashing.sha256_file(config.AUDIT_P3_PLACEMENT_CSV)
    structures_sha = st_sha
    if override is not None:
        structures_sha = approved_structures_sha256(st, override)
    snapshot = {
        "registry_snapshot_hash": reg["registry_snapshot_hash"],
        "structures_sha256": structures_sha,
        "constraints_sha256": co_sha,
        "placement_snapshot_sha256": placement_sha,
        "board_snapshot_sha256": board_sha,
        "feedforward_config_sha256": ff_config_sha256(),
        "placement_basis_note": "D8：placement 绑定取 p3 板读数（③ 现行口径）；"
                                "placement.csv 仅作转换事实源，7 件差异列 diagnostics",
        "seed_sha256": seed_sha, "audit_sha256": aud_sha,
        "layout_sha256": lay_sha, "layer_plan_sha256": lp_sha,
    }
    if override is not None:
        snapshot["structures_authority"] = "approved（override 转正，草案冻结）"
        snapshot["structures_draft_sha256"] = st_sha
        snapshot["structures_override_sha256"] = \
            hashing.sha256_bytes(hashing.canonical_json_bytes(override))
    return {"registry": reg, "structures": st, "constraints": co, "audit": aud,
            "seed": seed, "layout": lay, "layer_plan": lp, "snapshot": snapshot,
            "reads": reads}


def _check_metric(aud, check_id, reads, artifact=ffc.A3_DIR_REL + "/audit.json"):
    for ch in aud["checks"]:
        if ch["check_id"] == check_id:
            reads.append({"artifact": artifact,
                          "field": "checks[%s].metrics" % check_id, "role": "audit"})
            return ch["metrics"]
    raise KeyError(check_id)


# ---- 六类资源构建 ------------------------------------------------------------
def _hashes_field(snapshot):
    return {"registry_snapshot_hash": snapshot["registry_snapshot_hash"],
            "structures_hash": snapshot["structures_sha256"],
            "constraints_hash": snapshot["constraints_sha256"]}


def _res(rid, kind, scope, supply, demand, reserve, yellow, basis, net_ids,
         relation_ids, blocking, snapshot, note=None, reason=None):
    has_basis = (supply["value"] is not None and demand["value"] is not None)
    margin = None
    if has_basis:
        margin = round(supply["value"] - demand["value"]
                       - (reserve["value"] or 0.0), 4)
    state = classify_resource(margin, yellow["value"] if yellow else 0.0, has_basis)
    row = {
        "resource_id": rid, "kind": kind, "scope": scope,
        "supply": supply, "demand": demand, "reserve": reserve,
        "margin": {"value": margin, "unit": supply["unit"]},
        "state": state,
        "yellow_margin": yellow,
        "basis": basis, "source_refs": [b for b in basis if b],
        "net_ids": sorted(set(net_ids)), "relation_ids": sorted(set(relation_ids)),
        "blocking_net_ids": sorted(set(blocking)) if state == "resource_deficit" else [],
        "demand_model": ffc.DEMAND_MODELS[kind],
    }
    row.update(_hashes_field(snapshot))
    if state == "resource_deficit":
        row["suggested_rollback_stage"] = ffc.SUGGESTED_ROLLBACK_STAGE[kind]
        row["deficit_magnitude"] = {"value": round(-margin, 4), "unit": supply["unit"]}
    if note:
        row["note"] = note
    if reason:
        row["reason"] = reason
    return row


def _zero_reserve(unit):
    return {"value": 0.0, "unit": unit, "basis": [ffc.RESERVE_DEFAULT_BASIS]}


def _escape_resources(basis, net_id_of, reads):
    """escape_slots：② C2 同源模型在 p3 板上重算（全字段；audit.json 证书仅含
    worst 12，故重算取全量，证书行用于交叉核对）。"""
    board = geo.parse_board(config.AUDIT_P3_BOARD)
    esc = audit_cmd.escape_check(board, compile_cmd._match_class)
    reads.append({"artifact": "design/coreboard/kicad/stm32h743-coreboard-revc/"
                             "snapshots/p3-placement-gates-pass/"
                             "stm32h743-coreboard-revc.kicad_pcb",
                  "field": "escape_check(board) 重算（C2 同源模型）", "role": "board"})
    snap = basis["snapshot"]
    yellow = ffc.YELLOW_MARGIN["escape_slots"]
    rows, unmapped = [], []
    fields = esc["fields"]
    for key in sorted(fields):
        f = fields[key]
        if not f["demand_transit_nets"]:
            continue  # 无逃逸需求不列账（总数进 coverage）
        nids = []
        for n in f["transit_nets"]:
            nid = net_id_of.get(n)
            if nid:
                nids.append(nid)
            else:
                unmapped.append(n)
        blocking = [net_id_of[n] for n in f["blocked_transit_nets"]
                    if n in net_id_of]
        rows.append(_res(
            rid="escape_slots:" + key, kind="escape_slots",
            scope={"ref": f["ref"], "side": f["side"]},
            supply={"value": f["supply_clear_channels"], "unit": "channels",
                    "basis": ["audit escape_check（C2 一阶扇出模型，p3 板重算）"]},
            demand={"value": f["demand_transit_nets"], "unit": "channels",
                    "basis": ["transit 网数（需离场网；C2 同源）"]},
            reserve=_zero_reserve("channels"), yellow=yellow,
            basis=["audit_cmd.escape_check", "C-0037 逃逸 ≤3mm"],
            net_ids=nids, relation_ids=[], blocking=blocking, snapshot=snap,
            note=("pads_total=%d，blocked_transit=%d"
                  % (f["pads_total"], len(f["blocked_transit_nets"])))
            if f["blocked_transit_nets"] else None))
    meta = {"fields_total": len(fields),
            "fields_with_demand": sum(
                1 for f in fields.values() if f["demand_transit_nets"]),
            "unmapped_escape_nets": sorted(set(unmapped))}
    return sorted(rows, key=lambda r: r["resource_id"]), meta


def _corridor_resources(basis, net_id_of, rel_ids_of_net, reads, override=None):
    """corridor + bus_lane：D4 几何宽度口径（audit C4 corridor_budgets.required_mm）。

    override（FD2 adoption）：STR-1 已批 → 三条存储走廊 pending 注记解除；
    共走廊多总线追加合并通道行（19 网存储通道 4.1mm 需求，width_basis 复核）。"""
    c4 = _check_metric(basis["audit"], "C4_corridor_capacity", reads)
    reads.append({"artifact": ffc.A3_DIR_REL + "/audit.json",
                  "field": "checks[C4_corridor_capacity].metrics."
                           "corridor_budgets[].required_mm/gap_mm/member_count",
                  "role": "audit"})
    snap = basis["snapshot"]
    buses = {b["bus_id"]: b for b in basis["structures"]["buses"]}
    corr, lanes = [], []
    pending_corridors = {}
    for c in sorted(c4["corridor_budgets"], key=lambda x: x["bus_id"]):
        bus = c["bus_id"]
        members = buses.get(bus, {}).get("members", [])
        nids = [net_id_of[m] for m in members if m in net_id_of]
        rids = sorted({r for m in members for r in rel_ids_of_net.get(m, [])})
        pending = bus in ("BUS_QSPI", "BUS_SDMMC1", "BUS_SDMMC2")
        if pending and override is not None:
            note = ("STR-1 已批（override 2026-08-30）：存储走廊端点=U1↔J1；"
                    "audit C4 历史行 status=pending_STR-1 由本账本按批准裁决"
                    "解除（历史产物不回写）")
            pending_corridors.setdefault(c["corridor"], []).append(
                (bus, c, members))
        elif pending:
            note = ("STR-1 pending：存储走廊端点 U1↔J1 裁决待人工（NEXT 待人工 #2）；"
                    "照算不判 fatal（audit 保守口径）")
        else:
            note = None
        corr.append(_res(
            rid="corridor:" + c["corridor"], kind="corridor",
            scope={"bus_id": bus, "corridor": c["corridor"], "segment": "main"},
            supply={"value": c["gap_mm"], "unit": "mm",
                    "basis": ["audit C4：AABB 盒间净空（canonical G1 口径）"]},
            demand={"value": c["required_mm"], "unit": "mm",
                    "basis": ["audit C4 corridor_budgets.required_mm（C-0053："
                              "ceil(N/2)×0.35+0.6）"]},
            reserve=_zero_reserve("mm"), yellow=ffc.YELLOW_MARGIN["corridor"],
            basis=["out/revc-a3/audit.json#C4", "C-0053"],
            net_ids=nids, relation_ids=rids, blocking=nids, snapshot=snap,
            note=note))
        n = c["member_count"]
        lane_demand = round(math.ceil(n / 2) * 0.35, 2)
        lanes.append(_res(
            rid="bus_lane:" + bus, kind="bus_lane",
            scope={"bus_id": bus, "corridor": c["corridor"], "layer": "trunk"},
            supply={"value": c["gap_mm"], "unit": "mm",
                    "basis": ["audit C4 gap（走廊净空=可堆叠车道宽度上界）"]},
            demand={"value": lane_demand, "unit": "mm",
                    "basis": ["ceil(N/2)×0.35 车道堆叠宽（C-0053 车道项；"
                              "离散车道模型留 FC1）"]},
            reserve=_zero_reserve("mm"), yellow=ffc.YELLOW_MARGIN["bus_lane"],
            basis=["C-0053 车道项", "out/revc-a3/audit.json#C4(member_count)"],
            net_ids=nids, relation_ids=rids, blocking=nids, snapshot=snap))
    # —— STR-1 已批：共走廊存储总线合并通道行（per-bus 行低估共享通道占用） ------
    combined = []
    for corridor, rows in sorted(pending_corridors.items()):
        if len(rows) < 2:
            continue
        bus_ids = sorted(r[0] for r in rows)
        gap = rows[0][1]["gap_mm"]
        members = [m for _, _, mem in sorted(rows) for m in mem]
        n_all = len(members)
        demand = round(math.ceil(n_all / 2) * 0.35 + 0.6, 4)
        nids = [net_id_of[m] for m in members if m in net_id_of]
        rids = sorted({r for m in members
                       for r in rel_ids_of_net.get(m, [])})
        row = _res(
            rid="corridor:%s:storage_combined" % corridor, kind="corridor",
            scope={"corridor": corridor, "segment": "storage_combined",
                   "bus_ids": bus_ids},
            supply={"value": gap, "unit": "mm",
                    "basis": ["audit C4：AABB 盒间净空（同通道共享）"]},
            demand={"value": demand, "unit": "mm",
                    "basis": ["structures STR-1 finding 计算口径：%d 网存储"
                              "通道 ceil(N/2)×0.35+0.6（override width_basis）"
                              % n_all]},
            reserve=_zero_reserve("mm"), yellow=ffc.YELLOW_MARGIN["corridor"],
            basis=["structures STR-1（已批）", "C-0053",
                   "out/revc-a3/audit.json#C4"],
            net_ids=nids, relation_ids=rids, blocking=nids, snapshot=snap,
            note="共走廊 %d 总线合并需求（per-bus 行不叠加，本行为通道级复核）"
                 % len(bus_ids))
        row["width_basis_check"] = {
            "override_claim_mm": 4.1, "computed_mm": demand,
            "consistent": abs(demand - 4.1) <= 1e-6,
            "note": "override width_basis=19 网 4.1mm（NEXT #2 早稿括注 4.0mm "
                    "为草稿数；重算 demand_consistent 复核）"}
        combined.append(row)
    return (sorted(corr + combined, key=lambda r: r["resource_id"]),
            sorted(lanes, key=lambda r: r["resource_id"]))


def _bom_rail_resource(rail, info, nid, bom, snap, reads):
    """FF3 BOM 消费轨资源（derived 语义；SPEC §6.3/§17.1）。

    供给=源件额定（sourced）/链合成（derived）分列；需求=BOM consumption 口径
    （width-derived 上界降为铜宽载流复核项）；表内 value_a=null 时需求回退
    fd2 width-derived 政策口径、供给侧 missing_basis 保持——不虚构。"""
    entry = (bom["table"].get("rails") or {}).get(rail) or {}
    sup = entry.get("supply") or {}
    dem = entry.get("demand") or {}
    bom_rel = bom.get("rel") or BOM_POWER_REL
    reads.append({"artifact": bom_rel,
                  "field": "rails.%s（supply/demand 分列消费）" % rail,
                  "role": "bom_power_derive"})

    def _side(side, tag_class, lines):
        body = "；".join(lines) if lines else "（表内无注）"
        return ["%s：%s（bom-power-derive.json#rails.%s.%s）"
                % (tag_class, body, rail, side)]

    w = _trunk_width_mm(info.get("min_width_raw") or "")
    cap = ipc2221_current_a(w) if w is not None else None

    if sup.get("value_a") is not None:
        supply_val = float(sup["value_a"])
        supply = {"value": supply_val, "unit": "A",
                  "basis": _side("supply", sup.get("class") or "derived",
                                 sup.get("basis") or [])}
        yellow = {"value": round(RAIL_YELLOW_FRACTION * supply_val, 4),
                  "unit": "A",
                  "basis": ["supply 的 %.0f%%（筛查；rail 供给落位后生效）"
                            % (RAIL_YELLOW_FRACTION * 100)]}
    else:
        supply = {"value": None, "unit": "A",
                  "basis": ["missing_basis:supply（%s；bom-power-derive.json"
                            "#rails.%s.supply）"
                            % ("；".join(sup.get("basis") or ["无钉源"]), rail)]}
        yellow = None

    if dem.get("value_a") is not None:
        demand_val = float(dem["value_a"])
        demand_basis = _side("demand", dem.get("class") or "derived_consumption",
                             dem.get("basis") or [])
        if cap is not None:
            demand_basis.append(
                "宽度载流复核（信息性，不改需求口径）：干路 %gmm→IPC-2221 载流 "
                "%.3fA vs 需求 %gA→%s" % (w, cap, demand_val,
                                          "充足" if cap >= demand_val
                                          else "不足（登记）"))
    else:
        demand_val = None
        demand_basis = ["missing_basis:current（structures power_tree "
                        "current_budget_a=null）"]
        if w is not None:
            demand_val = round(ipc2221_current_a(w), 3)
            demand_basis = [
                "derived_policy：IPC-2221A 外层 1oz/10°C 拟合式 "
                "I=0.048·ΔT^0.44·A^0.725 @ 干路 %gmm（structures "
                "min_width_raw 已批）；BOM 表内无更好源（%s）→回退 width-derived "
                "上界（fd2 政策口径）"
                % (w, dem.get("class") or "no_basis")]

    reason = None
    if supply["value"] is None or demand_val is None:
        reason = ("missing_basis:supply_current_source（BOM 派生轨表已消费："
                  "供给/需求缺源侧 missing_basis 保持，不虚构）")
    note = info.get("budget_note")
    return _res(
        rid="power_return_space:rail:" + rail, kind="power_return_space",
        scope={"rail": rail},
        supply=supply, demand={"value": demand_val, "unit": "A",
                               "basis": demand_basis},
        reserve=_zero_reserve("A"), yellow=yellow,
        basis=["out/revc-a3/structures.json#power_tree.rails." + rail,
               "out/revc-fd1/approvals/sources/interface-current.json",
               bom_rel],
        net_ids=[nid] if nid else [], relation_ids=[], blocking=[],
        snapshot=snap, reason=reason, note=note)


def _layer_via_power_resources(basis, net_id_of, reads, sources=None, bom=None):
    """layer_capacity / via_budget / power_return_space。

    sources（FD2 adoption）=能力表/叠层/接口电流三源：via_budget 供给按能力表
    derived 密度上界解锁；rail 电流按 sourced（5V_USB）/derived 政策（其余 11 轨）
    登记 demand（rail 供给侧仍缺→missing_basis 保持，不虚构）。

    bom（FF3）=BOM 派生轨功耗/供给表：rail 供给 sourced/derived 分列+需求
    consumption 口径（width-derived 降为铜宽载流复核项）；value_a=null 回退
    fd2 口径/供给侧 missing_basis 保持（不虚构）。"""
    c3 = _check_metric(basis["audit"], "C3_layer_budget", reads)
    c5 = _check_metric(basis["audit"], "C5_power_loop", reads)
    c6 = _check_metric(basis["audit"], "C6_return_continuity", reads)
    snap = basis["snapshot"]
    out = []

    supply_area = c3["supply_area_mm2"]
    demand_area = c3["demand_area_mm2"]
    yellow = None
    if supply_area is not None:
        yellow = {"value": round(ffc.FF_LAYER_YELLOW_FRACTION * supply_area, 3),
                  "unit": "mm2",
                  "basis": ["FF-config：supply 的 %.0f%%（筛查）"
                            % (ffc.FF_LAYER_YELLOW_FRACTION * 100)]}
    out.append(_res(
        rid="layer_capacity:board", kind="layer_capacity",
        scope={"board": "revc", "layers": config.AUDIT_SIGNAL_LAYERS},
        supply={"value": supply_area, "unit": "mm2",
                "basis": ["audit C3：2×(板面积−封装占用)（In1/B 为 GND 平面不供信号）"]},
        demand={"value": demand_area, "unit": "mm2",
                "basis": ["audit C3：链式直连长×0.35 pitch（2-4 端非电源网）"]},
        reserve=_zero_reserve("mm2"), yellow=yellow,
        basis=["out/revc-a3/audit.json#C3"],
        net_ids=[], relation_ids=[], blocking=[], snapshot=snap,
        note="聚合口径（全部信号网）；逐网归因仅赤字时给出（utilization=%s）"
             % c3.get("utilization")))

    via_supply = None
    via_supply_basis = ["missing_basis:fab_capability_table（缺失源待人工 #4："
                        "嘉立创能力表；不虚构供给）"]
    via_yellow = ffc.YELLOW_MARGIN["via_budget"]
    via_demand_basis = ["out/revc-b1/layer-plan.json via_count_total（③ 计划级）；"
                        "audit C3 planned_via_count=%s（另一口径，登记不改用）"
                        % c3.get("planned_via_count")]
    if sources is not None and supply_area is not None:
        supply_val, cell = via_budget_supply(supply_area / 2.0, sources["fab"])
        via_supply = supply_val
        via_supply_basis = [
            "derived：嘉立创能力表最小尺寸推导密度上界（单信号层可用面积 %g/2 ÷ "
            "孔位单元 %gmm 节距²）；derived 非实测，逐单能力以下单页为准"
            "（capability caveat 随行）"
            % (supply_area, cell["cell_pitch_mm"])]
        reads.append({"artifact": FAB_CAPABILITY_REL,
                      "field": "values.min_via_pad_mm/"
                               "min_trace_width_spacing_1oz_multilayer_mm",
                      "role": "fab_capability"})
        via_yellow = {"value": round(VIA_BUDGET_YELLOW_FRACTION * supply_val, 1),
                      "unit": "vias",
                      "basis": ["supply 的 %.0f%%（筛查；via 供给解锁后生效）"
                                % (VIA_BUDGET_YELLOW_FRACTION * 100)]}
        via_demand_basis.append("fab 单元口径=%s" % json.dumps(
            cell, sort_keys=True, ensure_ascii=False))
    out.append(_res(
        rid="via_budget:board", kind="via_budget",
        scope={"board": "revc"},
        supply={"value": via_supply, "unit": "vias",
                "basis": via_supply_basis},
        demand={"value": basis["layer_plan"]["via_count_total"], "unit": "vias",
                "basis": via_demand_basis},
        reserve=_zero_reserve("vias"), yellow=via_yellow,
        basis=["out/revc-b1/layer-plan.json"]
              + (["out/revc-fd1/approvals/sources/"
                  "fabrication-capability-jlcpcb.json"] if sources is not None
                 else ["缺失源：板厂能力表"]),
        net_ids=[], relation_ids=[], blocking=[], snapshot=snap,
        reason=(None if via_supply is not None
                else "missing_basis:fab_capability_table")))

    out.append(_res(
        rid="power_return_space:SW_loop_area", kind="power_return_space",
        scope={"loop": "buck Cin-SW_NODE-L1-3V3 Cout", "refs": c5["loop_refs"]},
        supply={"value": c5["limit_mm2"], "unit": "mm2",
                "basis": ["C-0046 上限 20×12"]},
        demand={"value": c5["loop_area_mm2"], "unit": "mm2",
                "basis": ["audit C5 实测外包络 %s×%s mm" % (c5["loop_w_mm"], c5["loop_h_mm"])]},
        reserve=_zero_reserve("mm2"),
        yellow=ffc.YELLOW_MARGIN_BY_RESOURCE["power_return_space:SW_loop_area"],
        basis=["out/revc-a3/audit.json#C5", "C-0046"],
        net_ids=[], relation_ids=[], blocking=[], snapshot=snap))

    worst = max(c5["decap_worst"], key=lambda d: d["nearest_cap_mm"]) \
        if c5.get("decap_worst") else None
    decap_demand = worst["nearest_cap_mm"] if worst else None
    decap_block = sorted({net_id_of[d["net"]] for d in c5["decap_worst"]
                          if d["net"] in net_id_of
                          and d["nearest_cap_mm"] > config.AUDIT_DECAP_LIMIT_MM}) \
        if c5.get("decap_worst") else []
    out.append(_res(
        rid="power_return_space:decap_radius", kind="power_return_space",
        scope={"rail": "3V3/5V", "limit_mm": config.AUDIT_DECAP_LIMIT_MM},
        supply={"value": config.AUDIT_DECAP_LIMIT_MM, "unit": "mm",
                "basis": ["C-0044 去耦上限 3.0（目标 2.0）"]},
        demand={"value": decap_demand, "unit": "mm",
                "basis": ["audit C5 decap_worst 最远去耦距离%s"
                          % ("（pin %s）" % worst["pin"] if worst else "")]},
        reserve=_zero_reserve("mm"),
        yellow=ffc.YELLOW_MARGIN_BY_RESOURCE["power_return_space:decap_radius"],
        basis=["out/revc-a3/audit.json#C5", "C-0044"],
        net_ids=[], relation_ids=[], blocking=decap_block, snapshot=snap,
        note="over_limit_pins=%d/%d" % (c5["decap_over_limit"],
                                        c5["decap_pins_checked"])))

    crossings = c6.get("digital_crossings_of_analog_zone") or []
    cross_nids = [net_id_of[n] for n in crossings if n in net_id_of]
    out.append(_res(
        rid="power_return_space:analog_zone_crossings", kind="power_return_space",
        scope={"zone": "analog_NW", "bbox_mm": c6.get("analog_zone_bbox")},
        supply={"value": 0, "unit": "crossings",
                "basis": ["placement §5 模拟角禁数字穿越（允许数=0）"]},
        demand={"value": len(crossings), "unit": "crossings",
                "basis": ["audit C6 digital_crossings_of_analog_zone（计划级口径）"]},
        reserve=_zero_reserve("crossings"),
        yellow=ffc.YELLOW_MARGIN_BY_RESOURCE[
            "power_return_space:analog_zone_crossings"],
        basis=["out/revc-a3/audit.json#C6", "placement §5"],
        net_ids=cross_nids, relation_ids=[], blocking=cross_nids, snapshot=snap,
        note="layer_plan_violations=%d（C6 另一口径，零违规）"
             % len(c6.get("layer_plan_violations") or [])))

    rails = basis["structures"]["power_tree"]["rails"]
    for rail in sorted(rails):
        info = rails[rail]
        nid = net_id_of.get(rail)
        if bom is not None:
            out.append(_bom_rail_resource(rail, info, nid, bom, snap, reads))
            continue
        demand_val = None
        demand_basis = ["missing_basis:current（structures power_tree "
                        "current_budget_a=null）"]
        reason = "missing_basis:current_budget_a"
        note = info.get("budget_note")
        if sources is not None:
            if rail == "5V_USB":
                demand_val = USB_VBUS_BUDGET_A
                demand_basis = ["sourced：USB 2.0 §7.2.1.1 高功率端口单元负载"
                                "上限 500mA（USB-C 无 CC 协商→保守口径；"
                                "interface-current.json#sourced_facts）"]
            else:
                w = _trunk_width_mm(info.get("min_width_raw") or "")
                if w is not None:
                    demand_val = round(ipc2221_current_a(w), 3)
                    demand_basis = [
                        "derived_policy：IPC-2221A 外层 1oz/10°C 拟合式 "
                        "I=0.048·ΔT^0.44·A^0.725 @ 干路 %gmm（structures "
                        "min_width_raw 已批）；图表读数 3V3≈2.2A 与拟合 2.382A "
                        "差约 8 个百分点（一致性核对）；非实测规划上界，精确值"
                        "待 BOM 功耗表"
                        "（interface-current.json#derived_policy_proposal）"
                        % w]
            reason = ("missing_basis:supply_current_source（demand 已按 "
                      "sourced/derived 登记；rail 供给侧电流待 BOM/器件规格，"
                      "不虚构）")
            note = (info.get("budget_note")
                    + "｜demand 已按 sourced/derived 登记（见 demand.basis）；"
                      "pending 语义沿留至供给侧落源")
            reads.append({"artifact": INTERFACE_CURRENT_REL,
                          "field": "sourced_facts/derived_policy_proposal"
                                   "（%s）" % rail, "role": "interface_current"})
        out.append(_res(
            rid="power_return_space:rail:" + rail, kind="power_return_space",
            scope={"rail": rail},
            supply={"value": None, "unit": "A",
                    "basis": ["missing_basis:current（电源树电流数据缺源，D5 不虚构）"]},
            demand={"value": demand_val, "unit": "A",
                    "basis": demand_basis},
            reserve=_zero_reserve("A"), yellow=None,
            basis=["out/revc-a3/structures.json#power_tree.rails." + rail]
                  + (["out/revc-fd1/approvals/sources/interface-current.json"]
                     if sources is not None else []),
            net_ids=[nid] if nid else [], relation_ids=[], blocking=[],
            snapshot=snap, reason=reason,
            note=note))
    return out


# ---- controls ----------------------------------------------------------------
def _build_controls(basis, escape_rows, net_id_of):
    st = basis["structures"]
    pri = st["priorities"]
    controls = []

    def add(kind, target, action, source_refs, consumer_stages, priority_scope):
        controls.append({
            "control_id": "CTL-%04d" % (len(controls) + 1),
            "kind": kind, "target": target, "action": action,
            "source_refs": source_refs, "consumer_stages": consumer_stages,
            "priority_scope": priority_scope,
            "preemption_policy": ffc.PREEMPTION_POLICY,
            "approval_state": "pending_FF4_consumer_gate（当前 authority="
                              "planning_advisory，不影响 ③ 候选接受）",
            "status": _PLAN_STATUS,
        })

    buses = {b["bus_id"]: b for b in st["buses"]}
    seed_buses = {b["bus_id"]: b for b in basis["seed"].get("buses", [])}
    for bus in sorted(buses):
        sb = seed_buses.get(bus, {})
        w = (sb.get("corridor") or {}).get("demand_width_mm")
        add("reserve_corridor", "bus:" + bus,
            {"reserve_width_mm": w, "note": "主走廊需求宽预留（C-0053）"},
            ["C-0053", "out/revc-a3/skeleton-seed.json"], [3, 4],
            "bus_order:" + bus)
    for r in escape_rows:
        if r["state"] == "resource_deficit":
            add("reserve_escape_slots", "field:" + r["scope"]["ref"] + "|"
                + r["scope"]["side"],
                {"reserve_channels": r["demand"]["value"],
                 "deficit_channels": r["deficit_magnitude"]["value"]},
                ["audit escape_check（C2）", "C-0037"], [3, 4],
                "escape:" + r["resource_id"])
    ranks = pri.get("layer_preference", {}).get("ranks") or []
    trunk = next((r.split("=")[0] for r in ranks
                  if isinstance(r, str) and r.startswith("In2.Cu")), "In2.Cu")
    for bus in sorted(buses):
        add("assign_preferred_layer", "bus:" + bus,
            {"preferred_layer": trunk,
             "escape_layer": "F.Cu<=3mm"},
            ["out/revc-a3/structures.json#priorities.layer_preference",
             "routing-spec §5"], [3, 4], "layer_preference:" + bus)
    bus_order = pri.get("bus_order", {})
    order = bus_order.get("ranks") if isinstance(bus_order, dict) else bus_order
    add("set_route_order", "board:revc",
        {"route_order": order or []},
        ["out/revc-a3/structures.json#priorities.bus_order"], [4],
        "bus_order")
    rt = st.get("return_tree", {})
    pl = rt.get("power_loop", {})
    add("protect_power_loop", "refs:" + ",".join(sorted(pl.get("refs") or [])),
        {"keep_refs_adjacent": True, "budget_mm2": pl.get("budget_mm2"),
         "limit_mm2": pl.get("limit_mm2")},
        ["C-0046", "out/revc-a3/structures.json#return_tree.power_loop"],
        [3, 4], "power_loop")
    stit = rt.get("stitching", {})
    add("reserve_return_stitching", "board:revc",
        {"grid_mm": stit.get("grid_mm"), "dense_mm": stit.get("dense_mm"),
         "dense_regions": stit.get("dense_regions")},
        ["C-0039", "out/revc-a3/structures.json#return_tree.stitching"],
        [3, 4], "return_stitching")
    for z in st.get("zones", []):
        if "XTAL" in (z.get("zone") or "") or "晶振" in (z.get("rule") or ""):
            add("protect_keepout", "zone:" + z["zone"],
                {"refs": z.get("refs"), "keepout_mm":
                 config.CPLACE_CRYSTAL_KEEPOUT_MM},
                ["placement §6.1", "structures zones"], [3, 4],
                "keepout:" + z["zone"])
    return sorted(controls, key=lambda c: (c["kind"], c["target"], c["control_id"]))


# ---- FF-1 plan ----------------------------------------------------------------
def build_plan(adopt_override=False, consume_bom=False, placement_csv=None,
               placement_layout=None, bom_power_file=None):
    """adopt_override=False：FF1 收官口径（byte-exact 与 revc-ff1 一致）。
    True：FD2 级联重跑——① override 转正消费+能力/叠层/电流三源消费
    （adoption check：FF 六 hash 中 structures 按设计变化，其余五 hash 不变）。
    consume_bom=True（需 adopt_override）：FF3——BOM 派生轨功耗表 derived
    消费（rail 供给 sourced/derived 分列+需求 consumption 口径）。
    placement_csv=采纳快照路径（需 adopt_override）：CAS1——确认点 #4 已批，
    placement 六 hash 绑定切至 it-layout 确定性转换的 placement.csv（§9.4
    批准路径）；基线 p3 绑定沿留 baseline_placement_sha256（fd3 冻结口径）；
    placement_layout=采纳布局提案路径（provenance 登记，不参与六 hash）。
    bom_power_file=rail 源覆盖路径（需 consume_bom）：FF5——用户裁决「无实测；
    资料级即终态」（2026-08-30）后指向后续权威源（cas2 v2）；缺省 fd3 钉源
    逐字节不变。"""
    if consume_bom and not adopt_override:
        raise ValueError("consume_bom 需 adopt_override（BOM 消费建立在 "
                         "FD2 adoption 基准上）")
    if placement_csv is not None and not adopt_override:
        raise ValueError("placement_csv 需 adopt_override（采纳绑定建立在 "
                         "FD2 adoption 基准上）")
    if bom_power_file is not None and not consume_bom:
        raise ValueError("bom_power_file 需 consume_bom（FF5 rail 源覆盖建立"
                         "在 BOM 消费口径上）")
    reads = []
    override = None
    sources = None
    bom = None
    if adopt_override:
        override, _ov_sha = load_override(reads)
        sources = _load_fd2_sources(reads)
        if consume_bom:
            bom = _load_bom_power(reads, rel=bom_power_file)
    basis = _load_frozen_basis(override=override)
    if placement_csv is not None:
        if not os.path.exists(_abs(placement_csv)):
            raise FileNotFoundError(placement_csv)
        if placement_layout is not None:
            reads.append({"artifact": placement_layout, "field": "<file hash>",
                          "role": "binding"})
        reads.append({"artifact": placement_csv, "field": "<file hash>",
                      "role": "binding"})
        snap = basis["snapshot"]
        snap["baseline_placement_sha256"] = snap["placement_snapshot_sha256"]
        snap["placement_snapshot_sha256"] = \
            hashing.sha256_file(_abs(placement_csv))
        snap["placement_basis"] = "it_adopted_cascade"
        snap["adopted_placement_path"] = placement_csv
        snap["placement_basis_note"] = (
            "CAS1：placement 绑定=确认点 #4 已批采纳的 placement.csv 快照"
            "（it-layout 确定性转换，转换证明=conversion.json）；基线 p3 "
            "CSV 绑定沿留 baseline_placement_sha256（fd3 口径冻结）；board "
            "快照仍绑 p3 冻结板（回测数据源，零写板）")
        if placement_layout is not None:
            if not os.path.exists(_abs(placement_layout)):
                raise FileNotFoundError(placement_layout)
            snap["adopted_layout_path"] = placement_layout
            snap["adopted_layout_sha256"] = \
                hashing.sha256_file(_abs(placement_layout))
    reads.extend(basis["reads"])  # D7：文件级真实读取并入 actually_read
    reg = basis["registry"]
    net_id_of = {n["net_name"]: n["net_id"] for n in reg["nets"]}
    rel_ids_of_net = {}
    for rid, rel in (reg.get("relations") or {}).items():
        for m in rel.get("members", []):
            rel_ids_of_net.setdefault(m, []).append(rid)

    escape_rows, esc_meta = _escape_resources(basis, net_id_of, reads)
    corr_rows, lane_rows = _corridor_resources(basis, net_id_of, rel_ids_of_net,
                                               reads, override=override)
    lvp_rows = _layer_via_power_resources(basis, net_id_of, reads,
                                          sources=sources, bom=bom)
    resources = sorted(escape_rows + corr_rows + lane_rows + lvp_rows,
                       key=lambda r: r["resource_id"])
    controls = _build_controls(basis, escape_rows, net_id_of)
    conflicts = detect_control_conflicts(controls)

    lay = basis["layout"]
    diagnostics = [
        {"id": "ff3_empty_comparison_historical",
         "severity": "defect_registered_not_backfilled",
         "title": "FB1 §2.5 七走廊 demand_consistent=true 为空比较（已实证缺陷）",
         "evidence": ["pcbflow/coplace_cmd.py:1264-1273（修复前：读不存在的 "
                      "demand_width_mm → None→true）",
                      "out/revc-b1/layout.json sanity_vs_audit.rows（audit_demand_mm "
                      "全 null 而 consistent=true）"],
         "resolution": "FF-3 修复：改读 canonical required_mm 三态；历史产物不回写"},
        {"id": "placement_csv_deltas",
         "severity": "snapshot_hygiene",
         "title": "p3 快照板 vs placement.csv 7 件位置不一致（D8）",
         "evidence": ["out/revc-b1/layout.json baseline_deltas.rows"],
         "resolution": "以 p3 板读数为准（③ 现行口径）；CSV 仅作转换事实源；"
                       "差异登记留档不作为 conflict 择一"},
        {"id": "missing_sources",
         "severity": "missing_basis",
         "title": "缺失源 3 项（沿留，阻签核不阻建造）：嘉立创能力表 / 叠层 TBD-1 / 接口规范",
         "evidence": ["NEXT.md 待人工 #4"],
         "resolution": "via_budget 供给与 rail 电流需求因此 missing_basis；不虚构"},
        {"id": "mcu_af_table_missing",
         "severity": "missing_basis",
         "title": "MCU AF 表供源缺失：② pin-swap 零候选（沿留）",
         "evidence": ["out/revc-a3/audit.json C1"],
         "resolution": "不生成 propose_pin_swap 控制（无来源不提案）"},
        {"id": "str1_pending_corridors",
         "severity": "pending_human",
         "title": "STR-1：QSPI/SDMMC1/SDMMC2 走廊对象改 U1↔J1 裁决待人工（沿留）",
         "evidence": ["NEXT.md 待人工 #2"],
         "resolution": "相关 corridor 资源照算并标注 pending；不参与 fatal"},
    ]
    if esc_meta["unmapped_escape_nets"]:
        diagnostics.append({
            "id": "escape_unmapped_nets", "severity": "coverage_gap",
            "title": "escape transit 网未映射到 registry net_id",
            "evidence": esc_meta["unmapped_escape_nets"],
            "resolution": "保留网名于 scope；列账待查"})
    if adopt_override:
        diagnostics = [d for d in diagnostics if d["id"] not in
                       ("missing_sources", "str1_pending_corridors")]
        diagnostics.append({
            "id": "str1_adopted_corridors", "severity": "adopted",
            "title": "STR-1 已批（override 2026-08-30）：QSPI/SDMMC1/SDMMC2 "
                     "存储走廊=U1↔J1；合并通道行 19 网需求复核入账",
            "evidence": ["out/revc-fd1/approvals/structures.override.json"
                         "#diff_vs_draft",
                         "corridor:U1-J1:storage_combined.width_basis_check"],
            "resolution": "per-bus 行 pending 注记解除；audit C4 历史行不回写；"
                          "STR-2（bus_order）连带生效"})
        diagnostics.append({
            "id": "missing_sources_partial_resolved", "severity":
                "missing_basis_partial",
            "title": "缺失源 adoption（2026-08-30）：已入=嘉立创能力表（via 供给"
                     "derived 上界）/叠层基面 JLC04161H-7628（阻抗重算=独立产物）"
                     "/接口电流（5V_USB sourced+11 轨 IPC-2221 derived 政策）；"
                     "仍缺=rail 供给侧电流（BOM 功耗表）/板厂叠层定稿（TBD-1 "
                     "义务保留）",
            "evidence": ["out/revc-fd1/approvals/sources/（3 件，双源核验记录随"
                         "文件）"],
            "resolution": "消费分类 sourced/derived 随 demand/supply.basis 登记；"
                          "rail 供给侧 missing_basis 保持，不虚构"})
        if consume_bom:
            diagnostics = [d for d in diagnostics
                           if d["id"] != "missing_sources_partial_resolved"]
            rails_all = [r for r in resources
                         if r["resource_id"].startswith(
                             "power_return_space:rail:")]
            landed = [r for r in rails_all if r["supply"]["value"] is not None]
            diagnostics.append({
                "id": "missing_sources_partial_resolved",
                "severity": "missing_basis_partial",
                "title": "缺失源 adoption（FF3，2026-08-30）：已入=嘉立创能力表"
                         "（via 供给 derived 上界）/叠层基面 JLC04161H-7628"
                         "（阻抗重算=独立产物）/接口电流（sourced 0.5A+IPC-2221 "
                         "政策）/板上 BOM 派生轨功耗表（derived：rail 供给 "
                         "sourced/derived 分列 %d/%d 轨落位+需求 consumption "
                         "口径）；仍缺=板厂叠层定稿（TBD-1 义务保留）/VBAT 超级"
                         "电容放电额定/VCAP1/2 内核 LDO 独立额定/EMMC_VSEL 载板"
                         "定义源" % (len(landed), len(rails_all)),
                "evidence": ["out/revc-fd3/approvals/sources/"
                             "bom-power-derive.json（inputs 四件 hash 随文件）",
                             "out/revc-fd1/approvals/sources/（3 件，双源核验"
                             "记录随文件）"],
                "resolution": "消费分类 sourced/derived 随 supply/demand.basis "
                              "登记；仍缺轨 missing_basis 保持，不虚构"
                              "（5V_HDR 赤字=载板负载无界×width 上界口径的登记，"
                              "非板载违规）"})

    if placement_csv is not None:
        diagnostics.append({
            "id": "cas1_placement_adoption",
            "severity": "snapshot_binding_update",
            "title": "确认点 #4 已批（2026-08-30）：placement 六 hash 绑定切至"
                     "采纳快照（it-layout→placement.csv 确定性转换）；fd3 "
                     "口径沿留，fd3 冻结零回写",
            "evidence": [placement_layout or "（采纳布局路径未登记）",
                         placement_csv,
                         "out/revc-it/keepout-iteration.json（IT 实验账）"],
            "resolution": "§9.4 批准路径：转换证明=conversion.json；基线 p3 "
                          "绑定沿留 baseline_placement_sha256；board 快照仍绑"
                          " p3 冻结板（回测数据源，零写板）"})

    declared = [
        "net-registry.json:registry_snapshot_hash",
        "net-registry.json:nets[].net_id/net_name/routing_class/allowed_layers",
        "net-registry.json:excluded_nets",
        "net-registry.json:relations[].members",
        "structures.json:buses[].members/member_count/endpoint_refs",
        "structures.json:power_tree.rails[].current_budget_a",
        "structures.json:return_tree.power_loop/stitching",
        "structures.json:priorities.layer_preference/bus_order",
        "structures.json:zones[]",
        "constraints.json:<file sha256 binding>",
        "audit.json:checks[C2/C3/C4/C5/C6].metrics",
        "skeleton-seed.json:buses[].corridor.demand_width_mm",
        "layout.json:baseline_deltas/optimization/evidence.verdict/registry_consumption",
        "layer-plan.json:via_count_total",
        "board(p3):escape_check 重算",
        "placement(p3):sha256 binding",
    ]
    derived = [
        "resources[].margin/state/yellow_margin/deficit_magnitude",
        "controls[]（由资源与 structures 派生的 planning_advisory 控制合同）",
        "diagnostics[]（交叉核对与缺陷登记）",
    ]
    if consume_bom:
        derived += [
            "rail 需求 consumption 口径（BOM 派生表 derived 语义）与铜宽载流"
            "复核行（IPC-2221 上界为信息性，非需求）",
        ]
    ignored = [
        "net-registry.json:aliases/planner_class_view/width_mm（本轮账本未消费）",
        "audit.json:checks[C1/C7]（pin-swap 零候选；连接器方向不进六类资源）",
        "skeleton-seed.json:buses[].endpoints[].side_votes（控制只用 demand_width_mm）",
        "layout.json:placements[]/skeletons[]（③ 优化输出，FF-1 只读证据字段）",
    ]
    if adopt_override:
        declared += [
            "structures.override.json:approved.diff_vs_draft（STR-1/STR-2 裁决）"
            "+base_draft.sha256（草案一致性核对）",
            "sources/fabrication-capability-jlcpcb.json:values.min_via_pad_mm/"
            "min_trace_width_spacing（via 供给 derived 上界）",
            "sources/interface-current.json:sourced_facts（5V_USB=0.5A）/"
            "derived_policy_proposal（11 轨 IPC-2221）",
            "sources/stackup-basis.json:stackup（阻抗重算=独立产物 "
            "impedance-targets.json 输入）",
        ]
    if consume_bom:
        declared += [
            "sources/bom-power-derive.json:rails[].supply（sourced/derived "
            "分列）/rails[].demand（consumption 口径）/assumptions（A1-A5）/"
            "board_totals/vendor_verifications",
        ]
    if placement_csv is not None:
        declared += [
            "placement.csv(adopted):sha256 binding（it-layout 确定性转换）",
            "it-layout.json:placements[]（确认点 #4 已批采纳布局；provenance）",
        ]
    plan = {
        "schema_version": ffc.SCHEMA_FF_PLAN,
        "plan_id": (FF5_PLAN_ID if bom_power_file is not None else
                    CAS_PLAN_ID if placement_csv is not None else
                    FF3_PLAN_ID if consume_bom else
                    ADOPT_PLAN_ID if adopt_override else ffc.PLAN_ID),
        "status": _PLAN_STATUS,
        "authority": _PLAN_AUTHORITY,
        "note": ("FF5 资料级 rail 源复算（--bom-power-file：用户裁决「无实测；"
                 "资料级即终态」2026-08-30——EMMC_VSEL demand 落 sourced，"
                 "VCAP1/2/VBAT/FB_NODE definitive 定性；SPEC v1.3 §17.1）："
                 if bom_power_file is not None else
                 "CAS1 级联收口（IT 布局采纳=确认点 #4 已批：placement 绑定"
                 "切至采纳快照，fd3 BOM 口径沿留；SPEC §9.4/§15）："
                 if placement_csv is not None else
                 "FF3 级联重跑（BOM 派生轨功耗表 derived 消费：rail 供给 "
                 "sourced/derived 分列+需求 consumption 口径；SPEC v1.3 §15）："
                 if consume_bom else
                 "FD2 adoption 级联重跑（① override 转正+能力/叠层/电流源消费；"
                 "SPEC v1.3 §15）："
                 if adopt_override else
                 "FF-1 纯内存资源账本（SPEC v1.3 §7）；")
                + "margin=supply−demand−reserve；"
                "缺 basis→missing_basis 禁默认 green；赤字归因 net/relation/resource",
        "snapshot": {**{k: basis["snapshot"][k] for k in ffc.STALE_CHECK_KEYS},
                     **({k: basis["snapshot"][k]
                         for k in ("structures_authority",
                                   "structures_draft_sha256",
                                   "structures_override_sha256")}
                        if adopt_override else {}),
                     **({k: basis["snapshot"][k]
                         for k in ("placement_basis", "adopted_placement_path",
                                   "baseline_placement_sha256",
                                   "adopted_layout_path",
                                   "adopted_layout_sha256")}
                        if placement_csv is not None else {}),
                     **({"bom_power_source_path": bom["rel"],
                         "bom_power_source_sha256": bom["sha256"]}
                        if bom_power_file is not None else {})},
        "snapshot_basis_note": basis["snapshot"]["placement_basis_note"],
        "resources": resources,
        "controls": controls,
        "control_conflicts": conflicts,
        "diagnostics": sorted(diagnostics, key=lambda d: d["id"]),
        "residuals": [],
        "residuals_note": "无可比实际结果（④ route 未实现）→ 不生成伪 residual，"
                          "仅记录 not_available（SPEC §11.2）",
        "consumption_contract": {
            "declared_consumed": declared,
            "actually_read": reads,
            "derived": derived,
            "ignored": ignored,
            "fallback": None,
            "fidelity": "full（FF-1 账本口径：六类资源一阶模型；escape 全字段为 "
                        "C2 同函数于 p3 板重算，audit.json 证书仅含 worst 12 作交叉核对）",
        },
        "escape_fields_meta": esc_meta,
        "determinism": {"claim": "byte_exact",
                        "note": "双跑 byte-exact 由测试强制；无 wall-clock/主机路径"},
    }
    basis["override"] = override
    basis["sources"] = sources
    basis["bom"] = bom
    return plan, basis


def build_coverage(plan, basis):
    reg = basis["registry"]
    by_kind = {}
    for r in plan["resources"]:
        d = by_kind.setdefault(r["kind"], {"total": 0, "available": 0,
                                           "low_margin": 0, "resource_deficit": 0,
                                           "missing_basis": 0})
        d["total"] += 1
        d[r["state"]] += 1
    nets_with_bus = {m for b in basis["structures"]["buses"] for m in b["members"]}
    in_rel = set()
    for rel in (reg.get("relations") or {}).values():
        in_rel.update(rel.get("members", []))
    net_names = {n["net_name"] for n in reg["nets"]}
    deficits = [r for r in plan["resources"] if r["state"] == "resource_deficit"]
    return {
        "schema_version": ffc.SCHEMA_FF_COVERAGE,
        "plan_id": plan["plan_id"],
        "snapshot": plan["snapshot"],
        "nets": {
            "named_total": len(reg["nets"]),
            "nc_excluded_total": len(reg["excluded_nets"]),
            "nc_listed_explicitly": True,
            "nc_sample_first3": sorted(
                n["net_name"] for n in reg["excluded_nets"])[:3],
            "net_id_stable": all(n.get("net_id") for n in reg["nets"]),
            "with_bus_membership": len(nets_with_bus & net_names),
            "in_relations": len(in_rel & net_names),
        },
        "relations": {"total": len(reg.get("relations") or {})},
        "resources": {
            "kinds_declared": list(ffc.RESOURCE_KINDS),
            "by_kind": {k: by_kind[k] for k in sorted(by_kind)},
            "kinds_missing": [k for k in ffc.RESOURCE_KINDS if k not in by_kind],
            "total": len(plan["resources"]),
            "deficit_total": len(deficits),
            "all_deficits_attributed": all(
                r["blocking_net_ids"] or r["net_ids"] for r in deficits),
            "all_resources_have_basis": all(r["basis"] for r in plan["resources"]),
        },
        "controls": {"total": len(plan["controls"]),
                     "conflicts": len(plan["control_conflicts"]),
                     "unresolved_conflicts": [c["conflict_id"] for c in
                                              plan["control_conflicts"]]},
        "escape_fields": plan["escape_fields_meta"],
        "consumers": {
            "declared_stages": [3, 4],
            "gate": "FF-4 consumer gate 未批 → controls 均为 planning_advisory，"
                    "不影响 ③ 候选接受（§9.2）",
        },
    }


# ---- FF-0 基线冻结 ------------------------------------------------------------
def _revc_readonly_inputs() -> list:
    return [
        ("design/coreboard/reports/routing-spec-v1.md", config.ROUTING_SPEC),
        ("design/coreboard/reports/placement-spec-v1.md", config.PLACEMENT_SPEC),
        ("design/coreboard/kicad/stm32h743-coreboard-revc/revc.netlist",
         config.REVC_NETLIST),
        ("design/coreboard/kicad/stm32h743-coreboard-revc/snapshots/"
         "p3-placement-gates-pass/stm32h743-coreboard-revc.kicad_pcb",
         config.AUDIT_P3_BOARD),
        ("design/coreboard/kicad/stm32h743-coreboard-revc/snapshots/"
         "p3-placement-gates-pass/placement.csv", config.AUDIT_P3_PLACEMENT_CSV),
        ("design/coreboard/kicad/stm32h743-coreboard-revc/snapshots/"
         "p3-placement-gates-pass/gates-p3.json", coplace_cmd.P3_GATES_JSON),
        ("design/coreboard/kicad/stm32h743-coreboard-revc/opens.csv",
         config.AUDIT_OPENS_CSV),
        ("design/coreboard/kicad/stm32h743-coreboard-revc/length-report.py",
         config.LENGTH_REPORT_PY),
        ("tools/pcbflow/toolchain_lock.json",
         os.path.join(config.PCBFLOW_ROOT, "toolchain_lock.json")),
    ]


def build_baseline_freeze():
    """FF-0：hash 锁定历史产物与只读输入；登记历史状态与已实证缺陷；零回写。"""
    frozen_products = {
        ffc.A3_DIR_REL: {n: hashing.sha256_file(_abs(ffc.A3_DIR_REL + "/" + n))
                         for n in ffc.A3_FROZEN_PRODUCTS},
        ffc.B1_DIR_REL: {n: hashing.sha256_file(_abs(ffc.B1_DIR_REL + "/" + n))
                         for n in ffc.B1_FROZEN_PRODUCTS},
    }
    revc_inputs = {rel: hashing.sha256_file(path)
                   for rel, path in _revc_readonly_inputs()}
    reads = []
    aud, _ = _read_json(ffc.A3_DIR_REL + "/audit.json", "audit", reads)
    st, _ = _read_json(ffc.A3_DIR_REL + "/structures.json", "structures", reads)
    lay, _ = _read_json(ffc.B1_DIR_REL + "/layout.json", "layout_baseline", reads)
    conv, _ = _read_json(ffc.B1_DIR_REL + "/conversion.json", "conversion", reads)
    data = {
        "schema_version": ffc.SCHEMA_FF_BASELINE_FREEZE,
        "freeze_id": ffc.FREEZE_ID,
        "role": "FF-0 基线冻结（SPEC v1.3 §15 FF-0/§16.1）：历史产物与输入 hash 锁定；"
                "只登记不回写",
        "frozen_products": frozen_products,
        "revc_readonly_inputs": revc_inputs,
        "historical_registration": {
            "registry": {
                "a3_registry_snapshot_hash": None,  # filled below
                "a3_registry_consumed": None,
                "b1_layout_registry_consumed": lay["registry_consumption"],
            },
            "coplace_optimization": lay["optimization"],
            "layout_evidence_verdict": lay["evidence"]["verdict"],
            "gate_verdicts": {
                "A_0_constraints": {"status_ref": "out/revc-a3/constraints.json"},
                "A_1_structures": {"authority_status": st.get("authority_status"),
                                   "note": "确认点 #1 待批（沿留）"},
                "A_2_audit_gates": {k: {"pass": v["pass"], "rate": v.get("rate"),
                                        "denominator": v.get("denominator")}
                                    for k, v in sorted(aud["gates"].items())},
                "B_coplace": {
                    "synthetic_red_to_green":
                        "由测试执行（tests/test_coplace_synthetic.py；FB1 冻结证据）",
                    "converter_replay":
                        conv["roundtrip_proof"]["byte_exact_vs_source"],
                    "revc_sanity": "pass（差异已解释，PHASE-REPORT-4 §3）",
                },
            },
        },
        "registered_defects": [
            {"id": "FF3-1", "title": "FB1 §2.5 七走廊 demand_consistent=true 为空比较",
             "evidence": ["pcbflow/coplace_cmd.py:1264-1273（修复前：sanity 交叉核对读 "
                          "不存在的 demand_width_mm，audit_demand 全 null → 空比较判 true）",
                          "out/revc-b1/layout.json#sanity_vs_audit.rows"],
             "policy": "只登记不回写；FF-3 修复后新证据进 out/revc-ff1"},
        ],
        "policy": "历史产物/报告零回写；Rev-C 零写板；FF 产物仅落 out/revc-ff1",
    }
    data["historical_registration"]["registry"]["a3_registry_snapshot_hash"] = \
        aud["registry_consumption"].get("registry_snapshot_hash")
    data["historical_registration"]["registry"]["a3_registry_consumed"] = \
        {"registry_consumed": aud["registry_consumption"].get("registry_consumed"),
         "fields_consumed": aud["registry_consumption"].get("fields_consumed"),
         "note": "②=registry 首消费者（FA3 v1.2 adoption）"}
    env = envelope.build_envelope(
        command="feedforward", status="ok", verdict="pass",
        command_kind="core", schema_version=ffc.SCHEMA_FF_ENVELOPE,
        inputs=[{"path": rel, "sha256": sha, "role": "frozen_input"}
                for rel, sha in sorted(revc_inputs.items())],
        artifacts=[],
        config_sha256=None,
        spec_refs=["tools/pcbflow/SPEC.md#§15-FF-0"],
        determinism_claim="byte_exact",
        metrics={"frozen_a3_files": len(frozen_products[ffc.A3_DIR_REL]),
                 "frozen_b1_files": len(frozen_products[ffc.B1_DIR_REL]),
                 "revc_readonly_inputs": len(revc_inputs),
                 "defects_registered": len(data["registered_defects"])},
        diagnostics=[{"id": "ff0_freeze",
                      "title": "FF-0 基线冻结：历史 registry_consumed / "
                               "optimization.applied=false / A/B 门 verdict 如实登记"}],
        data=data)
    return env


# ---- FF-2 comparison ----------------------------------------------------------
def _canon_key_diff(new_obj, frozen_obj):
    """逐顶层键比较 canonical bytes：返回 (差异键列表, 是否全部一致)。"""
    keys = sorted(set(new_obj) | set(frozen_obj))
    changed = [k for k in keys
               if hashing.json_dumps(new_obj.get(k)) != hashing.json_dumps(frozen_obj.get(k))]
    return changed


def build_comparison(plan, basis, adopt_override=False, override=None,
                     placement_csv=None):
    """④ 一致性对比：当前上游重建 vs 计划快照锚（byte-exact 新鲜度检查）。

    三个 match 轴（reads 台账逐项登记 artifact/field/role）：
    1. registry/structures：重建 enum 产物 sha 与 A3 落盘件+plan 快照双对；
    2. adopt_override 分叉口径：批准视图 hash 绑定+草案文件冻结另核
       （draft_frozen_match，FD2：采纳=批准视图、草案零修改）；
       缺省口径=草案 sha 直比 basis 快照；
    3. constraints/place：compile 重建 sha 对快照；place 用采纳 CSV 口径
       （CAS1：与 stale 现值同用采纳 CSV，缺省=p3 基线）。
    返回 (comparison_obj, invariants_ok)。
    """
    reads = []
    # 当前上游快照（真实重建，byte-exact 确定性的新鲜度检查）
    enum_products = enum_cmd.build_products(ffc.A3_DIR_REL)
    compile_products = compile_cmd.build_products(ffc.A3_DIR_REL)
    coplace_products = coplace_cmd.build_products(ffc.FF_OUT_DIR_REL)
    reads.append({"artifact": "<rebuild>enum_cmd.build_products",
                  "field": "net_registry/structures（registry+structures match）",
                  "role": "rebuild"})
    reads.append({"artifact": "<rebuild>compile_cmd.build_products",
                  "field": "constraints（constraints match）", "role": "rebuild"})
    reads.append({"artifact": "<rebuild>coplace_cmd.build_products(FF-3 修复后)",
                  "field": "layout/placement_csv/geojson/layer_plan（rerun diff）",
                  "role": "rebuild"})

    snapshot = plan["snapshot"]
    reg_match = (enum_products["net_registry"]["sha256"]
                 == hashing.sha256_file(_abs(ffc.A3_DIR_REL + "/net-registry.json"))
                 and enum_products["net_registry"]["obj"]["registry_snapshot_hash"]
                 == snapshot["registry_snapshot_hash"])
    draft_match = (enum_products["structures"]["sha256"]
                   == hashing.sha256_file(_abs(ffc.A3_DIR_REL
                                               + "/structures.json")))
    draft_frozen_match = None
    if adopt_override:
        # FD2：计划绑定=批准视图 hash；草案文件零修改（frozen）另核
        current_structures_sha = approved_structures_sha256(
            enum_products["structures"]["obj"], override)
        base = ((override.get("approved") or {}).get("base_draft") or {})
        draft_frozen_match = bool(
            base.get("sha256")
            == hashing.sha256_file(_abs(ffc.A3_DIR_REL + "/structures.json")))
        st_match = draft_match and draft_frozen_match and (
            current_structures_sha == snapshot["structures_sha256"])
    else:
        current_structures_sha = enum_products["structures"]["sha256"]
        st_match = draft_match and (
            enum_products["structures"]["sha256"]
            == basis["snapshot"]["structures_sha256"])
    co_match = (compile_products["constraints"]["sha256"]
                == basis["snapshot"]["constraints_sha256"])
    # CAS1：采纳快照口径——place 比较与 stale 现值同用采纳 CSV（缺省=p3 基线）
    place_current_sha = (hashing.sha256_file(_abs(placement_csv))
                         if placement_csv is not None else
                         hashing.sha256_file(config.AUDIT_P3_PLACEMENT_CSV))
    place_match = (
        place_current_sha == snapshot["placement_snapshot_sha256"]
        and hashing.sha256_file(config.AUDIT_P3_BOARD)
        == snapshot["board_snapshot_sha256"])
    stale = check_stale(snapshot, {
        "registry_snapshot_hash":
            enum_products["net_registry"]["obj"]["registry_snapshot_hash"],
        "structures_sha256": current_structures_sha,
        "constraints_sha256": compile_products["constraints"]["sha256"],
        "placement_snapshot_sha256": place_current_sha,
        "board_snapshot_sha256": hashing.sha256_file(config.AUDIT_P3_BOARD),
        "feedforward_config_sha256": ff_config_sha256(),
    })

    # 历史文件与 FF-0 冻结记录比对（gate/verdict 未被本会话改动）
    freeze_obj, freeze_sha = ({}, None)
    freeze_path = _abs(ffc.FF_OUT_DIR_REL + "/baseline-freeze.json")
    if os.path.exists(freeze_path):
        freeze_obj, freeze_sha = _read_json(
            ffc.FF_OUT_DIR_REL + "/baseline-freeze.json", "ff0_freeze", reads)
    frozen_now_a3 = {n: hashing.sha256_file(_abs(ffc.A3_DIR_REL + "/" + n))
                     for n in ffc.A3_FROZEN_PRODUCTS}
    frozen_now_b1 = {n: hashing.sha256_file(_abs(ffc.B1_DIR_REL + "/" + n))
                     for n in ffc.B1_FROZEN_PRODUCTS}
    frozen_unchanged = bool(freeze_obj) and (
        freeze_obj.get("data", {}).get("frozen_products", {})
        .get(ffc.A3_DIR_REL) == frozen_now_a3
        and freeze_obj.get("data", {}).get("frozen_products", {})
        .get(ffc.B1_DIR_REL) == frozen_now_b1)
    gate_unchanged = frozen_unchanged
    aud_gates = {k: v["pass"] for k, v in basis["audit"]["gates"].items()}
    lay = basis["layout"]

    # FF-3：修复后重跑 ③ 与冻结 b1 的差异必须只落在 sanity_vs_audit（证据字段）
    new_lay = coplace_products["layout"]["obj"]
    changed_keys = _canon_key_diff(new_lay, lay)
    layout_core_unchanged = [k for k in changed_keys
                             if k not in ("sanity_vs_audit",)] == []
    placement_csv_equal = (coplace_products["placement_csv"]["bytes"]
                           == open(_abs(ffc.B1_DIR_REL + "/placement.csv"), "rb").read())
    geojson_equal = (coplace_products["geojson"]["sha256"]
                     == hashing.sha256_file(_abs(ffc.B1_DIR_REL + "/skeletons.geojson")))
    layer_plan_equal = (coplace_products["layer_plan"]["sha256"]
                        == hashing.sha256_file(_abs(ffc.B1_DIR_REL + "/layer-plan.json")))

    invariants_ok = all([reg_match, st_match, co_match, place_match, gate_unchanged,
                         not stale["stale_plan"], layout_core_unchanged,
                         placement_csv_equal, geojson_equal, layer_plan_equal])
    cc = plan["consumption_contract"]
    comparison = {
        "schema_version": ffc.SCHEMA_FF_COMPARISON,
        "plan_id": plan["plan_id"],
        "role": "FF-2 comparison（SPEC v1.3 §16.3）：FF 会话不改变基线门/verdict/板",
        "registry_snapshot_match": reg_match,
        "structures_snapshot_match": st_match,
        "constraints_snapshot_match": co_match,
        "placement_snapshot_match": place_match,
        "placement_basis_note": plan["snapshot_basis_note"]
                                + "（差异为快照卫生问题、显式登记，非 conflict 择一）",
        "gate_unchanged": gate_unchanged,
        "gate_verdicts_registered": {"audit": aud_gates,
                                     "layout_evidence": lay["evidence"]["verdict"],
                                     "structures_authority_status":
                                         basis["structures"].get("authority_status")},
        "baseline_verdict_unchanged": frozen_unchanged,
        "baseline_freeze_sha256": freeze_sha,
        "frozen_products_unchanged_since_ff0": frozen_unchanged,
        "optimization_applied_unchanged": False,
        "optimization_applied": lay["optimization"]["applied"],
        "optimization_note": "SPEC §16.3 契约值：optimization.applied 保持 false"
                             "（FF 轨不执行优化；layout.optimization.mode="
                             + str(lay["optimization"]["mode"]) + "）",
        "board_write": False,
        "board_write_evidence": "feedforward 生成器模式：零落盘/零子进程/无 --save-board "
                                "路径；板文件 hash 与 FF-0 冻结一致",
        "declared_consumed": cc["declared_consumed"],
        "actually_read": [dict(r) for r in cc["actually_read"]] + reads,
        "derived": cc["derived"],
        "ignored": cc["ignored"],
        "fallback": cc["fallback"],
        "fidelity": cc["fidelity"],
        "stale_plan_check": stale,
        "structures_adoption": (None if not adopt_override else {
            "structures_basis": "approved_override（草案+STR-1/2 对读视图）",
            "structures_draft_frozen_match": draft_frozen_match,
            "structures_draft_unchanged_policy":
                "历史草案文件零修改（a3 冻结）；authority 转正经 override "
                "登记（SPEC §15 adoption check：FF/⑤⑥ 受影响阶段重跑，"
                "②③④ 语义输入=草案内容未变不重跑）",
            "override_ref": OVERRIDE_REL,
        }),
        **({"placement_adoption": {
            "placement_basis": snapshot.get("placement_basis"),
            "adopted_placement_path": snapshot.get("adopted_placement_path"),
            "baseline_placement_sha256":
                snapshot.get("baseline_placement_sha256"),
            "adopted_layout_sha256": snapshot.get("adopted_layout_sha256"),
            "confirmation": "确认点 #4 已批（2026-08-30；IT 布局采纳级联收口"
                            "CAS1；§9.4 批准路径，转换证明=conversion.json）",
        }} if placement_csv is not None else {}),
        "ff3_fix": {
            "applied": True,
            "canonical_field": ffc.SANITY_CANONICAL_FIELD,
            "rerun_out_dir": ffc.FF_OUT_DIR_REL,
            "layout_changed_top_level_keys": changed_keys,
            "layout_core_unchanged_outside_sanity_vs_audit": layout_core_unchanged,
            "placement_csv_byte_equal": placement_csv_equal,
            "geojson_byte_equal": geojson_equal,
            "layer_plan_byte_equal": layer_plan_equal,
            "sanity_rows_now": [
                {"bus_id": r["bus_id"], "audit_demand_mm": r["audit_demand_mm"],
                 "demand_consistent": r["demand_consistent"]}
                for r in new_lay["sanity_vs_audit"]["rows"]],
            "historical_limitation": "out/revc-b1/layout.json 的 demand_consistent=true "
                                     "为空比较产物（audit_demand_mm 全 null）；历史不回写，"
                                     "以本 comparison 的 sanity_rows_now 为修复后证据",
        },
    }
    return comparison, invariants_ok


# ---- 产品组装（CLI 入口） ------------------------------------------------------
def _state_counts(resources):
    out = {}
    for r in resources:
        out[r["state"]] = out.get(r["state"], 0) + 1
    return {k: out[k] for k in sorted(out)}


def build_products(out_dir_rel=config.load_project_manifest().out_dirs["feedforward"],
                   adopt_override=False,
                   consume_bom=False, placement_csv=None,
                   placement_layout=None, bom_power_file=None):
    """④ 前馈主构建：计划 → 覆盖 → 一致性对比三件核心产物（SPEC ④）。

    编排：build_plan（含 adopt_override/consume_bom/placement/bom_power
    全部 opt-in 开关）→ build_coverage（资源覆盖统计）→ build_comparison
    （上游新鲜度对账，见其 docstring）。产物族=feedforward-plan /
    coverage / comparison 三件（canonical bytes+sha256，role=core）；
    adopt_override 时追加 impedance-targets（FD2 阻抗目标件）。artifacts
    清单+human_report（feedforward-report.md）与落盘在函数尾部统一装配。
    """
    t0 = datetime.datetime.now(datetime.timezone.utc)
    plan, basis = build_plan(adopt_override, consume_bom=consume_bom,
                             placement_csv=placement_csv,
                             placement_layout=placement_layout,
                             bom_power_file=bom_power_file)
    coverage = build_coverage(plan, basis)
    comparison, invariants_ok = build_comparison(
        plan, basis, adopt_override=adopt_override,
        override=basis.get("override"), placement_csv=placement_csv)

    products = {}
    for name, obj in (("plan", plan), ("coverage", coverage),
                      ("comparison", comparison)):
        data = hashing.canonical_json_bytes(obj)
        products[name] = {"obj": obj, "bytes": data,
                          "sha256": hashing.sha256_bytes(data)}
    if adopt_override:
        imp_reads = []
        imp = build_impedance_targets(plan["plan_id"], basis["sources"],
                                      imp_reads)
        data = hashing.canonical_json_bytes(imp)
        products["impedance_targets"] = {
            "obj": imp, "bytes": data, "sha256": hashing.sha256_bytes(data)}

    artifacts = [
        {"path": out_dir_rel + "/feedforward-plan.json",
         "sha256": products["plan"]["sha256"], "role": "core"},
        {"path": out_dir_rel + "/feedforward-coverage.json",
         "sha256": products["coverage"]["sha256"], "role": "core"},
        {"path": out_dir_rel + "/feedforward-comparison.json",
         "sha256": products["comparison"]["sha256"], "role": "core"},
        {"path": out_dir_rel + "/feedforward-report.md", "role": "human_report"},
    ]
    if adopt_override:
        artifacts.insert(3, {
            "path": out_dir_rel + "/impedance-targets.json",
            "sha256": products["impedance_targets"]["sha256"],
            "role": "core"})
    inputs = [
        {"path": ffc.A3_DIR_REL + "/net-registry.json",
         "sha256": hashing.sha256_file(_abs(ffc.A3_DIR_REL + "/net-registry.json")),
         "role": "registry"},
        {"path": ffc.A3_DIR_REL + "/structures.json",
         "sha256": basis["snapshot"]["structures_sha256"], "role": "structures"},
        {"path": ffc.A3_DIR_REL + "/constraints.json",
         "sha256": basis["snapshot"]["constraints_sha256"], "role": "constraints"},
        {"path": ffc.A3_DIR_REL + "/audit.json",
         "sha256": basis["snapshot"]["audit_sha256"], "role": "audit"},
        {"path": ffc.B1_DIR_REL + "/layout.json",
         "sha256": basis["snapshot"]["layout_sha256"], "role": "layout_baseline"},
        {"path": "design/coreboard/kicad/stm32h743-coreboard-revc/snapshots/"
                 "p3-placement-gates-pass/stm32h743-coreboard-revc.kicad_pcb",
         "sha256": basis["snapshot"]["board_snapshot_sha256"], "role": "board"},
    ]
    if adopt_override:
        inputs += [
            {"path": OVERRIDE_REL, "role": "structures_override",
             "sha256": hashing.sha256_file(_abs(OVERRIDE_REL))},
            {"path": FAB_CAPABILITY_REL, "role": "fab_capability",
             "sha256": hashing.sha256_file(_abs(FAB_CAPABILITY_REL))},
            {"path": STACKUP_BASIS_REL, "role": "stackup_basis",
             "sha256": hashing.sha256_file(_abs(STACKUP_BASIS_REL))},
            {"path": INTERFACE_CURRENT_REL, "role": "interface_current",
             "sha256": hashing.sha256_file(_abs(INTERFACE_CURRENT_REL))},
        ]
    if consume_bom:
        inputs += [
            {"path": (bom_power_file or BOM_POWER_REL),
             "role": "bom_power_derive",
             "sha256": hashing.sha256_file(
                 _abs(bom_power_file or BOM_POWER_REL))},
        ]
    if placement_csv is not None:
        inputs += [
            {"path": placement_csv, "role": "placement_adopted",
             "sha256": hashing.sha256_file(_abs(placement_csv))},
        ]
        if placement_layout is not None:
            inputs += [
                {"path": placement_layout, "role": "placement_layout_adopted",
                 "sha256": hashing.sha256_file(_abs(placement_layout))},
            ]
    env = envelope.build_envelope(
        command="feedforward",
        status="ok" if invariants_ok else "blocked",
        verdict="pass" if invariants_ok else "yellow",
        command_kind="core", schema_version=ffc.SCHEMA_FF_ENVELOPE,
        inputs=inputs, artifacts=artifacts,
        config_sha256=ff_config_sha256(),
        spec_refs=["tools/pcbflow/SPEC.md#§6", "tools/pcbflow/SPEC.md#§7",
                   "tools/pcbflow/SPEC.md#§15-FF1", "tools/pcbflow/SPEC.md#§16.3"],
        determinism_claim="byte_exact",
        metrics={
            "plan_id": plan["plan_id"],
            "resources_total": len(plan["resources"]),
            "resources_by_state": _state_counts(plan["resources"]),
            "controls_total": len(plan["controls"]),
            "control_conflicts": len(plan["control_conflicts"]),
            "registry_snapshot_match": comparison["registry_snapshot_match"],
            "structures_snapshot_match": comparison["structures_snapshot_match"],
            "placement_snapshot_match": comparison["placement_snapshot_match"],
            "gate_unchanged": comparison["gate_unchanged"],
            "baseline_verdict_unchanged": comparison["baseline_verdict_unchanged"],
            "optimization_applied_unchanged": False,
            "board_write": False,
            "ff3_layout_core_unchanged":
                comparison["ff3_fix"]["layout_core_unchanged_outside_sanity_vs_audit"],
            **({} if not adopt_override else {
                "adoption": ("structures_override+sources+BOM 派生轨表"
                             "（FF3 级联重跑）" if consume_bom else
                             "structures_override+sources（FD2 级联重跑）"),
                "structures_authority": "approved",
                "impedance_targets_rerun": True,
                "sources_consumed": (4 if consume_bom else 3),
            }),
            **({} if placement_csv is None else {
                "placement_adoption": "it_adopted_cascade（确认点 #4 已批）",
                "baseline_placement_sha256":
                    plan["snapshot"]["baseline_placement_sha256"][:12] + "…",
            }),
        },
        diagnostics=[{"id": "ff1_planning_advisory",
                      "title": "FF 计划 authority=planning_advisory；资源 red 不等价"
                               "架构致命（§8.5）；controls 待 FF-4 consumer gate"},
                     {"id": "ff3_fix_note",
                      "title": "②→③ required_mm 空比较已修复；历史 b1 证据局限见 "
                               "comparison.ff3_fix.historical_limitation"}]
                     + ([{"id": "fd2_adoption",
                         "title": "FD2 级联重跑：structures.override 转正消费 + "
                                  "能力/叠层/电流三源消费 + 阻抗基面重算"
                                  "（impedance-targets.json）；STR-1 合并通道行入账"}]
                       if adopt_override else [])
                     + ([{"id": "fd3_bom_consumption",
                         "title": "FF3 级联重跑：BOM 派生轨功耗表 derived 消费——"
                                  "rail 供给 sourced/derived 分列+需求 consumption "
                                  "口径；FB_NODE/VBAT/VCAP1/2/EMMC_VSEL 缺源侧 "
                                  "missing_basis 保持"}]
                       if consume_bom and bom_power_file is None else [])
                     + ([{"id": "ff5_source_refined",
                         "title": "FF5 资料级 rail 源复算：用户裁决「无实测；资料级"
                                  "即终态」（2026-08-30）——EMMC_VSEL demand 落 "
                                  "sourced（PDR_ON FT_xx Ilkg ±250nA），VCAP1/2="
                                  "内部稳压器储能端、VBAT=查证性缺源、FB_NODE="
                                  "控制传感节点（definitive 定性）"}]
                       if bom_power_file is not None else [])
                     + ([{"id": "cas1_it_adoption",
                         "title": "CAS1 级联收口：确认点 #4 已批——placement "
                                  "绑定切至采纳快照（it-layout→placement.csv，"
                                  "转换证明=conversion.json）；fd3 口径沿留，"
                                  "fd3/fc3 冻结零回写"}]
                       if placement_csv is not None else []),
        data={"gate": {"ff1": {"ledger_built": True,
                               "six_kinds_present":
                                   not coverage["resources"]["kinds_missing"],
                               "double_run_byte_exact": "由测试强制"},
                       "ff2": {"invariants_all_hold": invariants_ok},
                       **({} if not adopt_override else
                          {"fd2_adoption": {
                              "override_consumed": True,
                              "structures_authority": "approved",
                              "impedance_rerun": True,
                              "sources_consumed": 3}}),
                       **({} if not consume_bom else
                          {"fd3_bom_consumption": {
                              "bom_power_table": True,
                              "rails_total": len([r for r in plan["resources"]
                                                  if r["resource_id"].startswith(
                                                      "power_return_space:"
                                                      "rail:")]),
                              "rails_supply_landed": len(
                                  [r for r in plan["resources"]
                                   if r["resource_id"].startswith(
                                       "power_return_space:rail:")
                                   and r["supply"]["value"] is not None]),
                              "rails_still_missing_basis": sorted(
                                  r["resource_id"].split(":")[-1]
                                  for r in plan["resources"]
                                  if r["resource_id"].startswith(
                                      "power_return_space:rail:")
                                  and r["state"] == "missing_basis")}}),
                       **({} if placement_csv is None else
                          {"cas1_placement_adoption": {
                              "confirmation_4": "approved（2026-08-30）",
                              "placement_basis": "it_adopted_cascade",
                              "adopted_placement":
                                  plan["snapshot"]["adopted_placement_path"],
                              "adopted_layout_sha256":
                                  plan["snapshot"]["adopted_layout_sha256"],
                              "fd3_frozen": True}}),
                       "note": "FF 门=独立 planning/consumer promotion gate，"
                               "不改核心阶段门（§15）"},
              "comparison_keys": sorted(comparison)})
    products["envelope"] = {"obj": env}

    report = _build_report_md(plan, coverage, comparison, env)
    products["report"] = {"obj": None,
                          "bytes": report.encode(config.ENCODING),
                          "sha256": hashing.sha256_bytes(
                              report.encode(config.ENCODING))}
    for art in env["artifacts"]:
        if art["path"].endswith("feedforward-report.md"):
            art["sha256"] = products["report"]["sha256"]

    t1 = datetime.datetime.now(datetime.timezone.utc)
    products["run_manifest"] = {"obj": {
        "started_at": t0.isoformat(), "finished_at": t1.isoformat(),
        "elapsed_s": round((t1 - t0).total_seconds(), 3),
        "host": socket.gethostname(), "python_version": sys.version.split()[0],
        "tool_version": config.TOOL_VERSION,
        "ff_config_version": ffc.FF_CONFIG_VERSION,
        "input_sha256": {i["path"]: i["sha256"] for i in inputs},
        "feedforward_config_sha256": ff_config_sha256(),
        "spec_sha256": hashing.sha256_file(os.path.join(config.PCBFLOW_ROOT,
                                                        "SPEC.md")),
        "schema_version": ffc.SCHEMA_FF_ENVELOPE,
        "registry_snapshot_sha256": basis["snapshot"]["registry_snapshot_hash"],
        "command": "feedforward", "out_dir": out_dir_rel,
        "adopt_override": adopt_override,
        "consume_bom": consume_bom,
        "placement_csv": placement_csv,
    }}
    return products


def _build_report_md(plan, coverage, comparison, env):
    """人读视图（确定性；SPEC §6 工程约定：Markdown 是视图不是事实源）。"""
    lines = []
    a = lines.append
    a("# feedforward-report — %s（FF-1/FF-2 人读视图）" % plan["plan_id"])
    a("")
    a("- authority：`planning_advisory`（资源 red ≠ 架构致命；controls 待 FF-4 "
      "consumer gate，不影响 ③ 候选接受）")
    a("- 快照绑定：registry `%s…` / structures `%s…` / constraints `%s…`"
      % (plan["snapshot"]["registry_snapshot_hash"][:12],
         plan["snapshot"]["structures_sha256"][:12],
         plan["snapshot"]["constraints_sha256"][:12]))
    a("")
    a("## 资源账本（margin = supply − demand − reserve）")
    a("")
    a("| 状态 | 数量 |")
    a("|---|---|")
    for state, n in _state_counts(plan["resources"]).items():
        a("| %s | %d |" % (state, n))
    a("")
    a("按类别：")
    a("")
    a("| kind | total | available | low_margin | resource_deficit | missing_basis |")
    a("|---|---|---|---|---|---|")
    for kind, d in sorted(coverage["resources"]["by_kind"].items()):
        a("| %s | %d | %d | %d | %d | %d |"
          % (kind, d["total"], d["available"], d["low_margin"],
             d["resource_deficit"], d["missing_basis"]))
    a("")
    a("### 赤字资源（blocking 归因）")
    a("")
    deficits = [r for r in plan["resources"] if r["state"] == "resource_deficit"]
    if deficits:
        a("| resource_id | 缺量 | blocking net_ids | 建议回退级 |")
        a("|---|---|---|---|")
        for r in sorted(deficits, key=lambda x: x["resource_id"]):
            a("| %s | %s %s | %s | %s |"
              % (r["resource_id"].replace("|", "/"),
                 r["deficit_magnitude"]["value"],
                 r["deficit_magnitude"]["unit"],
                 ", ".join(r["blocking_net_ids"][:6]) or "（聚合口径见 net_ids）",
                 "第 %s 级（%s）"
                 % (r["suggested_rollback_stage"],
                    {2: "②架构重审", 3: "③局部修"}[r["suggested_rollback_stage"]])))
    else:
        a("（无 resource_deficit）")
    a("")
    a("## 控制（planning_advisory）")
    a("")
    a("共 %d 条；冲突 %d 条（不静默覆盖）。动作种类：%s"
      % (len(plan["controls"]), len(plan["control_conflicts"]),
         ", ".join(sorted({c["kind"] for c in plan["controls"]})) or "无"))
    a("")
    a("## comparison（§16.3）")
    a("")
    a("| 字段 | 值 |")
    a("|---|---|")
    for k in ("registry_snapshot_match", "structures_snapshot_match",
              "constraints_snapshot_match", "placement_snapshot_match",
              "gate_unchanged", "baseline_verdict_unchanged",
              "optimization_applied_unchanged", "optimization_applied",
              "board_write"):
        a("| %s | %s |" % (k, comparison[k]))
    a("")
    a("FF-3 修复证据：layout 差异键=%s（须仅 sanity_vs_audit）；"
      "placement.csv/geojson/layer-plan byte-equal=%s/%s/%s"
      % (comparison["ff3_fix"]["layout_changed_top_level_keys"],
         comparison["ff3_fix"]["placement_csv_byte_equal"],
         comparison["ff3_fix"]["geojson_byte_equal"],
         comparison["ff3_fix"]["layer_plan_byte_equal"]))
    a("")
    a("历史局限：out/revc-b1 的 demand_consistent=true 为空比较产物（不回写）；"
      "修复后三态见 comparison.ff3_fix.sanity_rows_now。")
    a("")
    if comparison.get("structures_adoption"):
        ad = comparison["structures_adoption"]
        a("## adoption（%s，2026-08-30）"
          % ("FF5 资料级 rail 源复算" if plan["plan_id"] == FF5_PLAN_ID else
             "CAS1 级联收口" if plan["plan_id"] == CAS_PLAN_ID else
             "FF3 级联重跑" if plan["plan_id"] == FF3_PLAN_ID
             else "FD2 级联重跑"))
        pa = comparison.get("placement_adoption")
        if pa:
            a("")
            a("- placement 基准：%s（确认点 #4 已批采纳快照；转换证明="
              "conversion.json）；基线 p3 绑定沿留 `%s…`"
              % (pa["placement_basis"],
                 str(pa["baseline_placement_sha256"])[:12]))
        a("")
        a("- structures 基准：%s；草案冻结核对（draft_frozen_match）=%s"
          % (ad["structures_basis"], ad["structures_draft_frozen_match"]))
        a("- 源消费：嘉立创能力表（via 供给 derived 上界）/叠层基面 "
          "JLC04161H-7628（阻抗重算=独立产物 impedance-targets.json）/"
          "接口电流（5V_USB sourced 0.5A + 11 轨 IPC-2221 derived 政策）")
        a("- STR-1 已批：合并通道行 corridor:U1-J1:storage_combined 入账"
          "（19 网需求 4.1mm，width_basis_check 复核随 plan）；STR-2 连带生效")
        a("- adoption check：FF/⑤⑥ 受影响阶段重跑至 %s；②③④ 语义输入=草案"
          "内容未变不重跑（冻结件零改动）" % ad["override_ref"].split("/")[1])
        if plan["plan_id"] in (FF3_PLAN_ID, CAS_PLAN_ID):
            rails_all = [r for r in plan["resources"]
                         if r["resource_id"].startswith("power_return_space:rail:")]
            landed = [r for r in rails_all if r["supply"]["value"] is not None]
            still = sorted(r["resource_id"].split(":")[-1] for r in rails_all
                           if r["state"] == "missing_basis")
            a("- BOM 派生轨表消费（FF3，derived 语义）：rail 供给 sourced/derived "
              "分列 %d/%d 轨落位；需求切 consumption 口径（width 上界降为铜宽"
              "载流复核项）" % (len(landed), len(rails_all)))
            if still:
                a("- 仍缺供给源（missing_basis 保持，不虚构）：%s"
                  % "、".join(still))
            hdr = next((r for r in rails_all
                        if r["resource_id"] == "power_return_space:rail:5V_HDR"),
                       None)
            if hdr and hdr["state"] == "resource_deficit":
                a("- 5V_HDR 赤字 %.4gA=载板负载无界（width 上界口径）×输入预算 "
                  "余量的登记，非板载违规；载板供电预算列设计输入评审项"
                  % hdr["deficit_magnitude"]["value"])
        a("")
    a("## 诊断登记")
    a("")
    for d in plan["diagnostics"]:
        a("- **%s**（%s）：%s" % (d["id"], d["severity"], d["title"]))
    a("")
    a("（事实源=feedforward-plan/coverage/comparison JSON；本报告为视图）")
    a("")
    return "\n".join(lines)
