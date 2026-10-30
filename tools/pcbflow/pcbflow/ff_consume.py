"""FF-4 ③ 前馈计划消费器（SPEC v1.3 §9.1-§9.2/§15 FF-4）。

③ 消费 feedforward-plan.json：六 hash 绑定检查（§7.4，任何不匹配→stale_plan，
board/placement 不一致额外按 §9.4 报 conflict，不择一）、controls 分类解释
（§9.2 五种可消费 kind；清单外/未解析→ignored 带理由；同 target 冲突不静默）、
§9.1 消费证据（declared/actually_read/derived/ignored/stale_plan_reason 分列）。

consumer gate：NEXT.md 待人工输入 #6 已批（已批：全量 FF-4，2026-08-29）——
controls 允许进入 ③ 确定性候选接受条件；锚件/硬门阈值/Rev-C 冻结基线/历史 B 门
不追改。未绑计划（ff_plan_path=None）时本模块不被调用，③ 行为与 FF1 收官态
byte-exact 一致。

生成器模式：零落盘、零子进程。D7：actually_read 全部来自真实读取路径
（json 装载 + 字段访问点登记），禁止静态声明照抄。常量内聚本模块
（FF config 隔离先例，v1.3 §14.3 A3；config.py 零新增→历史 config_sha256 不漂移）。
"""

from __future__ import annotations

import json
import os

from . import compile_cmd, config, feedforward_config as ffc, hashing

FF4_SCHEMA = "1.3"          # 消费证据族（新核心产物族，A3 版本策略）
FF4_ARTIFACT_KIND = "ff_consumption"

# §9.2 可消费控制 kind（第一轮 advisory 清单；其余 kind ③ 无对应模型→ignored）
CONSUMABLE_KINDS = ("reserve_corridor", "reserve_escape_slots",
                    "assign_preferred_layer", "protect_keepout",
                    "protect_power_loop")

CONSUMER_GATE = {
    "approved": True,
    "approved_via": "NEXT.md 待人工输入 #6（已批：全量 FF-4，2026-08-29 会话消费；"
                    "批注=consumer gate 先行，过 gate 才生效、不过退回 advisory 并 BLOCKED；"
                    "26 条控制逐条消费证据，禁静默全量吞）",
    "scope": "controls 进入 ③ 确定性候选接受条件（控制派生检查计入硬违幅度→lex）；"
             "锚件/硬门阈值/Rev-C 冻结基线/历史 B 门不追改",
    "spec_ref": "SPEC v1.3 §9.2/§15 FF-4/§17.4-5",
    # 过 gate 才生效：三要素的证据指针（会话级门，2026-08-29 FF2 会话核验 pass；
    # 任何一要素失败=本会话 BLOCKED、controls 不发布——批注原文语义）
    "promotion_check": {
        "synthetic_replay": "tests/test_ff4.py::test_escape_reservation_gate_and_"
                            "optimizer_clears（escape 门红→绿）+ "
                            "tests/test_coplace_synthetic.py（FB1 合成板 5 用例）",
        "b_gate_zero_regression": "tests/test_ff4.py::test_default_layout_pinned_"
                                  "byte_exact（sha pin）+ FF-0 冻结 32 条目零漂移"
                                  "（PHASE-REPORT-7 §3）",
        "revc_frozen_sanity": "out/revc-ff2 envelope revc sanity=pass；位姿/"
                              "骨架与 revc-ff1 byte-exact；verdict=red=冻结证据",
        "verdict": "pass（2026-08-29 FF2 会话）",
    },
}

# escape 预留带横向裕量（audit C2 band_rect 同值：场带横向各加 0.1mm）
ESCAPE_BAND_LATERAL_MM = 0.1


def _read_field(reads, artifact, field, role):
    """D7 字段级实读登记（真实访问点调用；不预登记不读的字段）。"""
    reads.append({"artifact": artifact, "field": field, "role": role})


def load_plan(plan_path, reads):
    """装载计划文件（D7：文件级实读）。返回 (plan, sha256)。"""
    with open(plan_path, "rb") as f:
        data = f.read()
    rel = os.path.basename(plan_path)
    _read_field(reads, rel, "<file>", "feedforward_plan")
    plan = json.loads(data.decode(config.ENCODING))
    # 绑定字段实读（§7.4 六 hash 全部参与比较=全部真实访问）
    for k in ffc.STALE_CHECK_KEYS:
        _read_field(reads, rel, "snapshot." + k, "feedforward_plan")
    _read_field(reads, rel, "plan_id", "feedforward_plan")
    _read_field(reads, rel, "authority/status", "feedforward_plan")
    return plan, hashing.sha256_bytes(data)


def build_current_snapshot(enum_products, out_dir_rel):
    """③ 现行装载链的六 hash 现值（registry/structures=enum 内存重建；
    constraints=compile 内存重建；board/placement=只读文件 hash；FF-config=代码常量）。
    """
    compile_products = compile_cmd.build_products(out_dir_rel)
    from . import feedforward as _ff  # 延迟导入避免 coplace→ff_consume→feedforward 环
    return {
        "registry_snapshot_hash":
            enum_products["net_registry"]["obj"]["registry_snapshot_hash"],
        "structures_sha256": enum_products["structures"]["sha256"],
        "constraints_sha256": compile_products["constraints"]["sha256"],
        "placement_snapshot_sha256":
            hashing.sha256_file(config.AUDIT_P3_PLACEMENT_CSV),
        "board_snapshot_sha256": hashing.sha256_file(config.AUDIT_P3_BOARD),
        "feedforward_config_sha256": _ff.ff_config_sha256(),
    }


def snapshot_binding(plan, current_snapshot, structures_basis=None):
    """六 hash 绑定（§7.4/§9.4）：逐键 match；任何不匹配→stale_plan；
    board/placement 不一致额外列 conflict（§9.4 前馈计划必须绑定板与布局快照）。
    structures_basis≠draft_file 时落键（FD2 adoption 口径；FF1 字节稳定）。fc3-D3。
    """
    checks = []
    for k in ffc.STALE_CHECK_KEYS:
        pv = (plan.get("snapshot") or {}).get(k)
        cv = current_snapshot.get(k)
        checks.append({"key": k, "plan": pv, "current": cv, "match": pv == cv})
    diff_keys = sorted(c["key"] for c in checks if not c["match"])
    conflict_keys = sorted(k for k in diff_keys
                           if k in ("board_snapshot_sha256",
                                    "placement_snapshot_sha256"))
    out = {
        "checks": checks,
        "all_match": not diff_keys,
        "stale_plan": bool(diff_keys),
        "stale_plan_reason": (["snapshot_hash_mismatch:" + k for k in diff_keys]
                              if diff_keys else None),
        "conflict_keys": conflict_keys,
        "conflict": ({"keys": conflict_keys,
                      "resolution": "报告不择一（§9.4）；controls 不应用，"
                                    "authority 保持 planning_advisory"}
                     if conflict_keys else None),
        "note": "六 hash=registry/structures/constraints/placement/board/FF-config"
                "（v1.3 §7.4）；③ 侧现值来自与产物同一装载链的内存重建+只读文件 hash",
    }
    if structures_basis not in (None, "draft_file"):
        out["structures_basis"] = structures_basis
    return out


A3_DIR_REL = "out/revc-a3"


def plan_structures_current(plan, reads=None):
    """按计划 snapshot 声明选择 structures 绑定基准（fc3-D3；⑤ _structures_current
    同构）：无 override 声明键=草案文件 hash（FF1 口径，原值返回零字节扰动）；
    有=草案对读 override 的批准视图 hash（FD2 adoption 口径；base_draft.sha256
    与盘上草案核对，失配→None=如实 stale）。返回 (structures_current, basis_tag)。
    """
    snap = plan.get("snapshot") or {}
    if not snap.get("structures_override_sha256"):
        return None, "draft_file"
    from . import feedforward as _ff  # 延迟导入避免环
    ov_rel = _ff.OVERRIDE_REL
    draft_rel = A3_DIR_REL + "/structures.json"
    p_root = config.PCBFLOW_ROOT
    draft_p = os.path.join(p_root, draft_rel)
    ov_p = os.path.join(p_root, ov_rel)
    if not os.path.exists(ov_p):
        return None, "approved_override（override 文件缺失）"
    if reads is not None:
        reads.append({"artifact": draft_rel,
                      "field": "<file>（approved 视图重建基准）",
                      "role": "binding"})
        reads.append({"artifact": ov_rel,
                      "field": "approved.base_draft/diff_vs_draft",
                      "role": "binding"})
    try:
        with open(draft_p, "rb") as f:
            draft = json.loads(f.read().decode(config.ENCODING))
        with open(ov_p, "rb") as f:
            ov = json.loads(f.read().decode(config.ENCODING))
    except (OSError, ValueError) as exc:
        return None, "approved_override（%s）" % str(exc)[:80]
    try:
        return _ff.approved_structures_sha256(draft, ov), "approved_override"
    except ValueError as exc:
        reads_append = reads.append if reads is not None else (lambda _r: None)
        reads_append({"artifact": ov_rel,
                      "field": "base_draft.sha256 一致性核对失败",
                      "role": "binding"})
        return None, "approved_override（%s）" % str(exc)[:80]


def apply_plan_structures_basis(plan, current_snapshot, reads=None):
    """计划声明基准 → 调整后的六 hash 现值（draft_file 路径原对象返回）。"""
    cur, basis = plan_structures_current(plan, reads)
    if basis == "draft_file":
        return current_snapshot, basis
    adjusted = dict(current_snapshot)
    adjusted["structures_sha256"] = cur
    return adjusted, basis


def interpret_controls(plan, shape_refs, corridor_bus_ids, reads):
    """把计划 controls 解释为 ③ ctx 扩展（§9.2 五 kind）；清单外/未解析/未裁决
    冲突→ignored（带理由，不静默）。reads=字段级实读登记。

    返回 (extensions, ignored, conflicts)：
      extensions = {reserve_corridor_buses, escape_fields, preferred_layers,
                    keepout_groups, power_loop}
    """
    rel = "feedforward-plan.json"
    controls = plan.get("controls") or []
    _read_field(reads, rel, "controls[]", "feedforward_plan")
    conflicted = set()
    from . import feedforward as _ff  # 同上：延迟导入
    conflicts = _ff.detect_control_conflicts(controls)
    for c in conflicts:
        conflicted.update(c["control_ids"])
        _read_field(reads, rel,
                    "controls[conflict:%s]" % ",".join(c["control_ids"]),
                    "feedforward_plan")

    ext = {"reserve_corridor_buses": [], "escape_fields": [],
           "preferred_layers": {}, "keepout_groups": [], "power_loop": None}
    applied = []  # 逐条生效证据（批注：禁静默全量吞）
    ignored = []
    signal_layers = set(config.AUDIT_SIGNAL_LAYERS) | {"B.Cu"}
    for ctl in controls:
        cid, kind = ctl.get("control_id"), ctl.get("kind")
        target = ctl.get("target")
        action = ctl.get("action") or {}
        for fld in ("control_id", "kind", "target", "action", "consumer_stages",
                    "status"):
            if fld in ctl:
                _read_field(reads, rel, "controls[%s].%s" % (cid, fld),
                            "feedforward_plan")
        reason = None
        if kind not in CONSUMABLE_KINDS:
            reason = ("kind 不在 §9.2 可消费清单（③ 无对应模型；%s 属 ④/⑥ 侧）"
                      % kind)
        elif cid in conflicted:
            reason = "control conflict 未裁决（不静默择一/覆盖）"
        elif kind == "reserve_corridor":
            bus = target.split(":", 1)[-1]
            if bus not in corridor_bus_ids:
                reason = "target bus 未解析（③ 走廊集无此总线）"
            else:
                _read_field(reads, rel, "controls[%s].action.reserve_width_mm"
                            % cid, "feedforward_plan")
                ext["reserve_corridor_buses"].append(bus)
                applied.append({"control_id": cid, "kind": kind,
                                "target": target,
                                "applied_as": "channel_keepouts 启用"
                                              "（第三方 0 侵入→硬违幅度）"})
        elif kind == "reserve_escape_slots":
            t = target.split(":", 1)[-1]
            ref, _, side = t.partition("|")
            if ref not in shape_refs or side not in ("N", "S", "E", "W"):
                reason = "target field 未解析（ref/side 不在 ③ 板）"
            else:
                for fld in ("reserve_channels", "deficit_channels"):
                    _read_field(reads, rel, "controls[%s].action.%s"
                                % (cid, fld), "feedforward_plan")
                ext["escape_fields"].append({
                    "control_id": cid, "ref": ref, "side": side,
                    "reserve_channels": action.get("reserve_channels"),
                    "deficit_channels": action.get("deficit_channels")})
                applied.append({"control_id": cid, "kind": kind,
                                "target": target,
                                "applied_as": "escape_slot_reservation 硬门"
                                              "（%s|%s 带，电气邻件豁免）"
                                              % (ref, side)})
        elif kind == "assign_preferred_layer":
            bus = target.split(":", 1)[-1]
            layer = action.get("preferred_layer")
            if bus not in corridor_bus_ids:
                reason = "target bus 未解析（③ 走廊集无此总线）"
            elif layer not in signal_layers:
                reason = "preferred_layer 非信号层（%s）" % layer
            else:
                for fld in ("preferred_layer", "escape_layer"):
                    if fld in action:
                        _read_field(reads, rel, "controls[%s].action.%s"
                                    % (cid, fld), "feedforward_plan")
                ext["preferred_layers"][bus] = layer
                applied.append({"control_id": cid, "kind": kind,
                                "target": target,
                                "applied_as": "layer_plan 首选层前置→%s"
                                              "（allowed_layers 仍为硬权限）"
                                              % layer})
        elif kind == "protect_keepout":
            refs = [r for r in (action.get("refs") or []) if r in shape_refs]
            mm = action.get("keepout_mm")
            if not refs:
                reason = "action.refs 为空或均不在 ③ 板"
            elif not mm or mm <= 0:
                reason = "action.keepout_mm 缺失/非正"
            else:
                for fld in ("refs", "keepout_mm"):
                    _read_field(reads, rel, "controls[%s].action.%s"
                                % (cid, fld), "feedforward_plan")
                ext["keepout_groups"].append({
                    "control_id": cid, "scope": target.split(":", 1)[-1],
                    "refs": sorted(refs), "keepout_mm": mm})
                applied.append({"control_id": cid, "kind": kind,
                                "target": target,
                                "applied_as": "keepout 控制组净空 %gmm"
                              "（组员+电气邻件豁免）" % mm})
        elif kind == "protect_power_loop":
            refs = [r for r in target.split(":", 1)[-1].split(",") if r]
            if not refs or not all(r in shape_refs for r in refs):
                reason = "target refs 未解析"
            else:
                for fld in ("budget_mm2", "limit_mm2", "keep_refs_adjacent"):
                    if fld in action:
                        _read_field(reads, rel, "controls[%s].action.%s"
                                    % (cid, fld), "feedforward_plan")
                ext["power_loop"] = {
                    "control_id": cid, "refs": sorted(refs),
                    "budget_mm": list(action.get("budget_mm2") or []),
                    "limit_mm": list(action.get("limit_mm2") or []),
                    "keep_refs_adjacent": bool(
                        action.get("keep_refs_adjacent"))}
                applied.append({"control_id": cid, "kind": kind,
                                "target": target,
                                "applied_as": "buck 环路预算对账"
                                              "（硬限仍=config，不静默覆盖）"})
        if reason:
            ignored.append({"control_id": cid, "kind": kind, "target": target,
                            "reason": reason})
    ext["reserve_corridor_buses"] = sorted(set(ext["reserve_corridor_buses"]))
    return ext, applied, ignored, conflicts


def consume_plan(plan_path, enum_products, shape_refs, corridor_bus_ids,
                 out_dir_rel):
    """FF-4 消费入口：装载→绑定→解释→§9.1 证据。stale/conflict 时 applied=False
    （controls 不进入 ③；authority 保持 planning_advisory，状态交由 envelope 报）。
    """
    reads = []
    plan, plan_sha = load_plan(plan_path, reads)
    current = build_current_snapshot(enum_products, out_dir_rel)
    for k in ("AUDIT_P3_BOARD", "AUDIT_P3_PLACEMENT_CSV"):
        _read_field(reads, k, "<file hash>", "binding")
    current, st_basis = apply_plan_structures_basis(plan, current, reads)
    binding = snapshot_binding(plan, current, structures_basis=st_basis)
    ext, applied, ignored, conflicts = interpret_controls(
        plan, shape_refs, corridor_bus_ids, reads)
    applied = applied if binding["all_match"] else []  # stale→不生效（批注语义）
    declared = sorted(a["control_id"] for a in applied)
    actually_read = sorted({tok for r in reads
                            if r["field"].startswith("controls[")
                            for tok in (r["field"].split("]")[0].split("[")[-1],)
                            if tok and not tok.startswith("conflict")})
    derived = _derived_rows(ext)
    evidence = {
        "schema_version": FF4_SCHEMA,
        "artifact_kind": FF4_ARTIFACT_KIND,
        "plan_id": plan.get("plan_id"),
        "feedforward_plan_hash": plan_sha,
        "feedforward_registry_snapshot_hash":
            (plan.get("snapshot") or {}).get("registry_snapshot_hash"),
        "plan_authority": plan.get("authority"),
        "consumer_gate": CONSUMER_GATE,
        "authority_effective": ("upgraded_for_candidate_acceptance"
                                if binding["all_match"] else
                                "planning_advisory（stale/conflict 未应用）"),
        "snapshot_check": binding,
        "stale_plan_reason": binding["stale_plan_reason"],
        "conflict": binding["conflict"],
        "controls_declared_consumed": declared,
        "controls_applied": sorted(applied,
                                   key=lambda a: a["control_id"]),
        "controls_actually_read": actually_read,
        "controls_derived": derived,
        "controls_ignored": sorted(ignored, key=lambda i: i["control_id"]),
        "control_conflicts": conflicts,
        "application": {
            "applied": binding["all_match"],
            "reserve_corridor": {
                "channel_keepouts_enabled": ext["reserve_corridor_buses"],
                "effect": "channel_check 第三方 0 侵入启用（侵入幅度计入硬违）"},
            "reserve_escape_slots": {
                "reserved_fields": [f["ref"] + "|" + f["side"]
                                    for f in ext["escape_fields"]],
                "effect": "escape_slot_reservation 硬门（带内非电气邻件体侵入=幅度）"},
            "assign_preferred_layer": {
                "per_bus": dict(sorted(ext["preferred_layers"].items())),
                "effect": "layer_plan 该总线首选层前置（via 软指标随之）"},
            "protect_keepout": {
                "groups": [{"scope": g["scope"], "refs": g["refs"],
                            "keepout_mm": g["keepout_mm"]}
                           for g in ext["keepout_groups"]],
                "effect": "keepout_check 控制组净空（组员+电气邻件豁免）"},
            "protect_power_loop": ext["power_loop"] or {"applied": False},
        },
        "consumption_contract": {
            "actually_read": reads,
            "derived": [d["derived"] for d in derived],
            "ignored": [i["control_id"] for i in ignored],
            "fallback": None,
            "fidelity": "full（③ 一阶模型：体级净空/通道/层计划；⑥ DRC=精确权威；"
                        "actually_read=真实字段访问点，declared≠actually_read 分列）",
        },
        "note": "§9.1 消费证据；controls 升级依据=NEXT.md #6 已批（consumer gate）；"
                "锚件/硬门阈值/Rev-C 冻结基线/历史 B 门不追改",
    }
    return {"plan": plan, "plan_sha": plan_sha, "reads": reads,
            "binding": binding, "extensions": ext if binding["all_match"]
            else None,
            "ignored": ignored, "conflicts": conflicts,
            "evidence": evidence, "applied": binding["all_match"]}


def _derived_rows(ext):
    """controls_derived：控制→③ 侧派生量（几何/口径随位姿运行时计算，此处登记口径）。"""
    rows = []
    for bus in ext["reserve_corridor_buses"]:
        rows.append({"target": "bus:" + bus,
                     "derived": "channel_keepouts 带宽=主端点 pad-bbox 面向边带"
                                "（运行时随位姿）"})
    for f in ext["escape_fields"]:
        rows.append({"target": "field:%s|%s" % (f["ref"], f["side"]),
                     "derived": "escape 带=%s pad-bbox %s 侧外延 %gmm+%.1fmm 横向"
                                "（audit C2 同深；运行时随位姿）"
                     % (f["ref"], f["side"], config.AUDIT_ESCAPE_DEPTH_MM,
                        ESCAPE_BAND_LATERAL_MM)})
    for bus, layer in sorted(ext["preferred_layers"].items()):
        rows.append({"target": "bus:" + bus,
                     "derived": "layer_plan 首选层前置 → %s（via 计数随之）" % layer})
    for g in ext["keepout_groups"]:
        rows.append({"target": g["scope"],
                     "derived": "keepout=组员 body 外扩 %gmm（电气邻件豁免）"
                                % g["keepout_mm"]})
    if ext["power_loop"]:
        rows.append({"target": "refs:" + ",".join(ext["power_loop"]["refs"]),
                     "derived": "buck 环路包络预算/上限对账（硬限仍=config CPLACE_*）"})
    return sorted(rows, key=lambda r: r["target"])
