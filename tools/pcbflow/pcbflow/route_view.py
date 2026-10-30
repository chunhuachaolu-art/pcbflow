"""④ route view（registry-bound）+ FF 控制适配（④ 侧）（SPEC v1.3 §10.2/§15 FC1/§16.4）。

route view：逐网语义从 registry snapshot 读取（net_id/relation_id 稳定身份），
板事实（p3 快照）经 hash 绑定；禁止按网络名重新维护分类（§10.2）。
④ 控制适配：§10.2 七种可消费 kind；reserve_corridor/protect_power_loop 等
③ 侧 kind → ignored 带理由。consumer-gate-4 已批（ROUTE_CONSUMER_GATE）：
绑定有效时 controls 进入候选接受（keepout=lex 控制违例）；stale/conflict
→ planning_advisory 不应用；未绑计划=FC1 收官态零扰动（§7.2）。

FC1/FC2 输入钉死（NEXT.md #5 已批语义）：③ p3 基线 layout.json = FC2 靶 2
首个重放靶；live 板 hash 仅作零写见证，不作 dry-run 输入。

生成器模式：零落盘、零子进程。D7：actually_read 全部来自真实读取路径。
常量内聚本模块（config.py 零新增 → 历史 config_sha256 不漂移）。
"""

from __future__ import annotations

import json
import math
import os

from . import audit_cmd, config, enum_cmd, ff_consume, geo, hashing

ROUTE_SCHEMA = "1.3"          # ④ 新核心产物族（A3 版本策略）
ROUTE_VIEW_KIND = "route_view"

# §10.2 ④ 可消费控制 kind；§9.2 ③ 清单与本文互斥引用，两处清单外 → ignored
CONSUMABLE_ROUTE_KINDS = ("reserve_escape_slots", "assign_preferred_layer",
                          "reserve_via_budget", "reserve_lane",
                          "reserve_return_stitching", "set_route_order",
                          "protect_keepout")

# ④ 控制升级 consumer gate（consumer-gate-4，out/revc-fd1/approvals/ 批准件）。
# [G3 2026-09-25] 冻结证据叙述（consumer-gate-4 批准链+P4/G1+ 裁量链）已迁
# exec/REPAIR-G3-ROUTE-VIEW-FROZEN-EVIDENCE-2026-09-25.md；本 dict 活字符串值不动。
ROUTE_CONSUMER_GATE = {
    "approved": True,
    "approved_via": "out/revc-fd1/approvals/consumer-gate-4.json"
                    "（NEXT.md 待人工 #7 消费，批注=「全部通过查资料自行判断」，"
                    "2026-08-30；gate 批准与实现分离，实现=本会话）",
    "scope": "④ route 命令的 controls 消费从 planning_advisory 升级为可进入"
             "候选接受条件（keepout=lex 首位最小化控制违例；max-flow 先保证"
             "物理可行，控制违例≠物理不可布）；锚件/硬门阈值/Rev-C 冻结基线/"
             "历史 B 门不追改；UNSAT/UNKNOWN 语义与证书红线不变",
    "spec_ref": "SPEC v1.3 §9.2/§10.2/§15 FF-4 表（控制升级需独立批准）",
    "promotion_check": {
        "synthetic_replay": "tests/test_fc4.py::test_keepout_lex_prefers_clean_"
                            "channel（净通道存在→零控制违例）+ "
                            "test_keepout_violation_never_flips_sat_to_unsat"
                            "（违例≠物理不可布，flow/UNSAT 不变）+ "
                            "tests/test_fc1.py 合成板全量",
        "b_gate_zero_regression": "tests/test_fc4.py 默认路径 route_plan/"
                                  "envelope sha pin 零回归 + test_fc1 全量"
                                  "（SAT/UNSAT 集、77 未匹配、18+8 控制不变）+ "
                                  "test_ff4 默认 layout sha pin",
        "revc_frozen_sanity": "out/revc-fc3 envelope ok/pass+零写见证 8029f5ff…；"
                              "revc-fc1/fc2 冻结件逐件 hash 复核零改动（会话"
                              "开工/收尾双验）；fc3 vs fc1 差异全部 control-"
                              "attributed（plan FF-REVC-0001→0002+语义升级）",
        "verdict": "pass（2026-08-30 FC3 会话）",
    },
}

# ④ 匝道费用（整数；稳定 tie-break 由插边序保证）
RAMP_COST_STRAIGHT = 0
RAMP_COST_DOGLEG = 2
RAMP_COST_SIDE_MISMATCH = 1
RAMP_COST_KEEPOUT = 4
# ④ 车道费用：非首选干道层惩罚；道位序成本=index（鼓励低序紧凑堆叠）
LANE_COST_OTHER_LAYER = 2

# pcbagent 复用面（§15 FC1：可复用其 Grid/Occupancy/PathFinder、Region/A*、
# Legality、DRC adapter；不把 pcbagent prefix class 当 registry authority）。
# FC1 核心路径为零依赖（匝道/车道=精确组合流，无需网格启发式）；本锁钉内容
# hash + 文本符号探测，供 FC2（描线 A*/L1 终判/DRC adapter）按锁取用。
PCBAGENT_ADAPTER_MODULES = ("planner.py", "router.py", "legality.py",
                            "bridge.py", "geometry.py")
PCBAGENT_SYMBOL_PROBES = {
    "planner.py": ("class Grid", "class PathFinder", "class Occupancy"),
    "router.py": ("class Region", "def route_net", "def route_net_segmented"),
    "legality.py": ("def ",),
    "bridge.py": ("def ",),
}


def _read_json_file(path, reads, role):
    with open(path, "rb") as f:
        data = f.read()
    reads.append({"artifact": os.path.basename(path), "field": "<file>",
                  "role": role})
    return json.loads(data.decode(config.ENCODING))


def pcbagent_adapter_lock():
    """pcbagent 复用面锁定（内容 hash + 文本符号探测；零导入、零子进程）。"""
    base = os.path.join(config.WORKSPACE_ROOT, "tools", "pcbagent", "pcbagent")
    lock = {"available": os.path.isdir(base), "modules": {},
            "authority_note": "pcbagent prefix class ≠ pcbflow registry authority"
                              "（§15 FC1）；复用仅限几何/合法性/DRC adapter 层"}
    for name in PCBAGENT_ADAPTER_MODULES:
        p = os.path.join(base, name)
        if not os.path.exists(p):
            lock["modules"][name] = {"available": False}
            continue
        data = open(p, "rb").read()
        text = data.decode(config.ENCODING, errors="replace")
        probes = [s for s in PCBAGENT_SYMBOL_PROBES.get(name, ())
                  if s in text]
        lock["modules"][name] = {
            "available": True, "sha256": hashing.sha256_bytes(data),
            "symbols_text_probed": probes,
        }
    return lock


def _qpos(v_mm):
    """mm → ③ 量子（0.05mm）→ mm（board_with_layout 的 moved 判定键）。"""
    return round(round(v_mm / config.CPLACE_QUANT) * config.CPLACE_QUANT, 3)


def board_with_layout(board, placements):
    """③ 布局位姿 → 覆盖板（IT keepout 迭代；opt-in）。

    moved 判定键=placement 与原 footprint 的量化位姿（③ q/uq 同口径）；moved
    refs 的 pads=原绝对坐标反旋转→新位姿正变换（geo.transform 精确逆/正对），
    未动 refs 保留原浮点对象（零漂移——基线自校=79 依赖此性质）。返回
    (finalized board, moved_refs 升序)。
    """
    pos = {r["ref"]: r for r in placements}
    foot, moved = {}, []
    for ref, fp in board["footprints"].items():
        row = pos.get(ref)
        if row is None:
            foot[ref] = fp
            continue
        if (round(float(row["x"]), 3), round(float(row["y"]), 3),
                int(row["rot"]) % 360) == (_qpos(fp["x"]), _qpos(fp["y"]),
                                           int(fp["rot"]) % 360):
            foot[ref] = fp
            continue
        moved.append(ref)
        r0 = math.radians(fp["rot"])
        c0, s0 = math.cos(r0), math.sin(r0)
        r1 = math.radians(float(row["rot"]))
        c1, s1 = math.cos(r1), math.sin(r1)
        fx, fy = float(row["x"]), float(row["y"])
        pads = []
        for p in fp["pads"]:
            dx, dy = p["x"] - fp["x"], p["y"] - fp["y"]
            lx, ly = dx * c0 - dy * s0, dx * s0 + dy * c0
            pads.append({"ref": ref, "num": p["num"], "net": p["net"],
                         "x": fx + lx * c1 + ly * s1,
                         "y": fy + ly * c1 - lx * s1,
                         "w": p["w"], "h": p["h"]})
        foot[ref] = {"ref": ref, "x": fx, "y": fy,
                     "rot": float(row["rot"]), "pads": pads}
    return geo.finalize_board(foot), sorted(moved)


def escape_fields_of(esc, net_id_of):
    """escape_check 结果 → ④ 匝道需求侧视图（C2 同口径；registry 缺档列账）。

    因子化自 build_route_view（输出同构；keepout-iter 每候选复算复用）。
    返回 (fields_out, transit_refs, unmapped_transit)。
    """
    fields_out, transit_refs = [], {}
    unmapped_transit = set()
    for key in sorted(esc["fields"]):
        f = esc["fields"][key]
        if not f["demand_transit_nets"]:
            continue
        nids = []
        for nm in f["transit_nets"]:
            if nm in net_id_of:
                nids.append(net_id_of[nm])
            else:
                unmapped_transit.add(nm)
        transit_refs.setdefault(f["ref"], set()).update(nids)
        fields_out.append({
            "field": key, "ref": f["ref"], "side": f["side"],
            "supply_clear_channels": f["supply_clear_channels"],
            "demand_transit_nets": f["demand_transit_nets"],
            "blocked_transit_nets": len(f["blocked_transit_nets"]),
            "net_ids": sorted(nids),
        })
    return fields_out, transit_refs, unmapped_transit


def build_route_view(out_dir_rel, placement_layout_path=None):
    """route view：registry 绑定逐网语义 + 板事实 hash 绑定 + FC1/FC2 钉死。

    placement_layout_path（opt-in，IT 会话）：③ 布局提案覆盖板几何（moved
    refs 重建、未动 refs 原浮点零漂移）；registry/计划绑定仍对 p3 基线快照，
    覆盖变量单列 placement_override（缺省=None=默认路径零扰动）。
    """
    reads = []
    enum_products = enum_cmd.build_products(out_dir_rel=out_dir_rel)
    registry = enum_products["net_registry"]["obj"]
    structures = enum_products["structures"]["obj"]
    reads.append({"artifact": "enum 内存重建链", "field":
                  "net_registry/structures（registry_snapshot_hash 绑定）",
                  "role": "registry"})

    current = ff_consume.build_current_snapshot(enum_products, out_dir_rel)
    for k in ("AUDIT_P3_BOARD", "AUDIT_P3_PLACEMENT_CSV"):
        reads.append({"artifact": k, "field": "<file hash>", "role": "binding"})

    board = geo.parse_board(config.AUDIT_P3_BOARD)
    reads.append({"artifact": "p3 board 快照", "field":
                  "parse_board（C2 同源重算输入）", "role": "board"})
    placement_override = None
    if placement_layout_path:
        layout = _read_json_file(placement_layout_path, reads,
                                 "placement_override")
        board, moved = board_with_layout(board, layout["placements"])
        placement_override = {
            "layout_path": placement_layout_path.replace("\\", "/"),
            "layout_sha256": hashing.sha256_file(placement_layout_path),
            "moved_refs": moved, "moved_count": len(moved),
            "mode": "keepout_iteration_dry_run",
            "binding_note": "IT 实验变量=布局几何；registry/structures/"
                            "constraints/placement(CSV) 快照绑定仍对 p3 基线"
                            "（六 hash 口径不变，SPEC §7.4：adopt 须按新 "
                            "placement 重生成计划=级联路径）；keepout 控制"
                            "语义（refs/keepout_mm）与位姿无关→与冻结基线"
                            "逐 run 可比",
        }
    esc = audit_cmd.escape_check(board, _cls_identity)
    seed = _read_json_file(config.SEED_PATH, reads, "skeleton_seed")
    seed_sides = {b["bus_id"]: {e["ref"]: e.get("dominant_exit_side")
                                for e in b.get("endpoints", [])}
                  for b in seed.get("buses", [])}

    net_id_of = {n["net_name"]: n["net_id"] for n in registry["nets"]}
    bus_of = {}
    for b in structures["buses"]:
        for m in b["members"]:
            bus_of[m] = b["bus_id"]

    nets_out = []
    for n in sorted(registry["nets"], key=lambda x: x["net_id"]):
        nets_out.append({
            "net_id": n["net_id"], "net_name": n["net_name"],
            "bus_id": bus_of.get(n["net_name"]),
            "routing_class": (n.get("routing_class") or {}).get("value"),
            "allowed_layers": n.get("allowed_layers"),
            "preferred_layer": n.get("preferred_layer"),
            "via_policy": n.get("via_policy"),
            "relation_ids": n.get("relation_ids") or [],
            "endpoints": sorted(n.get("endpoints") or []),
        })

    # 板上存在但 registry 未建档的网 → missing_basis 列账（不静默丢弃）
    board_nets = sorted({p["net"] for p in board["pads"] if p["net"]})
    registry_names = set(net_id_of)
    board_only = [x for x in board_nets
                  if x not in registry_names
                  and x != "GND" and not x.startswith("unconnected-")]

    # 逃逸场（C2 同源重算；与 FF-1 账本同口径）——匝道需求侧
    fields_out, transit_refs, unmapped_transit = escape_fields_of(esc,
                                                                  net_id_of)

    corridors = audit_cmd.corridor_budget_check(board, structures)["corridors"]
    reads.append({"artifact": "audit_cmd.corridor_budget_check", "field":
                  "bus_id/corridor/gap_mm/required_mm/member_count",
                  "role": "audit"})

    buses_out = []
    ranks = (structures.get("priorities", {}).get("bus_order") or {})
    order = ranks.get("ranks") if isinstance(ranks, dict) else ranks
    order = order or []
    for b in sorted(structures["buses"], key=lambda x: x["bus_id"]):
        members = b.get("members") or []
        buses_out.append({
            "bus_id": b["bus_id"],
            "member_net_ids": sorted(net_id_of[m] for m in members
                                     if m in net_id_of),
            "member_count": b.get("member_count", len(members)),
            "endpoint_refs": b.get("endpoint_refs") or [],
            "route_order_rank": order.index(b["bus_id"])
            if b["bus_id"] in order else len(order),
            "seed_exit_sides": seed_sides.get(b["bus_id"], {}),
        })

    view = {
        "schema_version": ROUTE_SCHEMA,
        "artifact_kind": ROUTE_VIEW_KIND,
        "mode": "fc1_dry_run_planning",
        "snapshot": dict(current),
        "registry_snapshot_hash": registry["registry_snapshot_hash"],
        "registry_policy_version": registry.get("policy_version"),
        "nets": nets_out,
        "buses": buses_out,
        "escape_fields": fields_out,
        "escape_fields_total": len(esc["fields"]),
        "escape_fields_with_demand": len(fields_out),
        "transit_refs": sorted(transit_refs),
        "unmapped_transit_nets": sorted(unmapped_transit),
        "board_only_nets": board_only,
        "excluded_nets_count": len(registry.get("excluded_nets") or []),
        "corridors": corridors,
        "signal_layers": list(config.AUDIT_SIGNAL_LAYERS),
        "lane_pitch_mm": config.AUDIT_TRACK_PITCH_MM,
        "lane_margin_mm": 0.6,
        "pins": {
            # [G3 2026-09-25] pins 三节冻结证据叙述已迁
            # exec/REPAIR-G3-ROUTE-VIEW-FROZEN-EVIDENCE-2026-09-25.md；节值不动。
            "fc2_replay_target": {
                "path": "out/revc-b1/layout.json",
                "sha256": hashing.sha256_file(
                    os.path.join(config.OUT_DIR, "revc-b1", "layout.json")),
                "approved": "NEXT.md #5（2026-08-29 已批：首个重放靶=当前 "
                            "layout.json p3 基线，供 FC2 靶 2）",
            },
            "live_board_zero_write_witness": {
                "path": "design/coreboard/kicad/stm32h743-coreboard-revc/"
                        "stm32h743-coreboard-revc.kicad_pcb",
                "sha256": hashing.sha256_file(config.REVC_BOARD),
            },
            "snapshot_copy_protocol":
                "FC2 开工后从本 pins 的 source hash 建快照副本再演练；"
                "FC1 零写板（内存 dry-run），不预建副本（HANDOFF §2 跨项目单写者）",
        },
        "note": "§10.2：route target/失败/冲突一律用 net_id/relation_id；"
                "board/placement 事实经 snapshot hash 绑定，不在本视图复制坐标",
    }
    if placement_override:
        view["mode"] = placement_override["mode"]
        view["placement_override"] = placement_override
    return {"view": view, "reads": reads,
            "board": board, "esc": esc, "registry": registry,
            "structures": structures, "enum_products": enum_products,
            "seed_sides": seed_sides,
            "placement_override": placement_override}


def _cls_identity(_net):
    """C2 escape_check 的 cls_of 参数：route view 不做类过滤（全量逃逸场）。"""
    return None


def interpret_controls_route(plan, view_ctx, reads):
    """§10.2 控制适配（④ 侧）：七 kind 可消费；③ 侧 kind → ignored 带理由。

    返回 (ext, applied, ignored, conflicts)。authority=planning_advisory。
    """
    rel = "feedforward-plan.json"
    controls = plan.get("controls") or []
    reads.append({"artifact": rel, "field": "controls[]", "role":
                  "feedforward_plan"})
    from . import feedforward as _ff
    conflicts = _ff.detect_control_conflicts(controls)
    conflicted = set()
    for c in conflicts:
        conflicted.update(c["control_ids"])
        reads.append({"artifact": rel, "field":
                      "controls[conflict:%s]" % ",".join(c["control_ids"]),
                      "role": "feedforward_plan"})

    registry_buses = {b["bus_id"] for b in view_ctx["view"]["buses"]}
    bus_allowed = {}
    for n in view_ctx["view"]["nets"]:
        if n["bus_id"]:
            bus_allowed.setdefault(n["bus_id"], set())
            if n["allowed_layers"]:
                bus_allowed[n["bus_id"]] |= set(n["allowed_layers"])

    ext = {"escape_reserved_fields": [], "preferred_layers": {},
           "preferred_layer_notes": [], "keepout_groups": [],
           "route_order": None, "stitching": None,
           "via_budget_reserve": [], "reserve_lane": []}
    applied, ignored = [], []
    signal_layers = set(config.AUDIT_SIGNAL_LAYERS) | {"B.Cu"}
    present_kinds = set()
    for ctl in controls:
        cid, kind, target = (ctl.get("control_id"), ctl.get("kind"),
                             ctl.get("target"))
        action = ctl.get("action") or {}
        present_kinds.add(kind)
        for fld in ("control_id", "kind", "target", "action",
                    "consumer_stages", "status"):
            if fld in ctl:
                reads.append({"artifact": rel, "field":
                              "controls[%s].%s" % (cid, fld),
                              "role": "feedforward_plan"})
        reason = None
        if kind not in CONSUMABLE_ROUTE_KINDS:
            if kind == "reserve_corridor":
                reason = ("③ 侧走廊预留（§9.2 清单）；④ 走廊容量经 C4/"
                          "corridor 资源进入，不重复预留")
            elif kind == "protect_power_loop":
                reason = "③/⑥ 侧功率环路语义（§9.2）；④ 无对应模型"
            else:
                reason = "kind 不在 §10.2 ④ 可消费清单"
        elif cid in conflicted:
            reason = "control conflict 未裁决（不静默择一/覆盖）"
        elif kind == "reserve_escape_slots":
            fkey = target.split(":", 1)[-1]
            if fkey not in {f["field"] for f in
                            view_ctx["view"]["escape_fields"]}:
                reason = "target field 未解析（④ 逃逸场集无此项）"
            else:
                for fld in ("reserve_channels", "deficit_channels"):
                    reads.append({"artifact": rel, "field":
                                  "controls[%s].action.%s" % (cid, fld),
                                  "role": "feedforward_plan"})
                ext["escape_reserved_fields"].append({
                    "control_id": cid, "field": fkey,
                    "reserve_channels": action.get("reserve_channels"),
                    "deficit_channels": action.get("deficit_channels")})
                applied.append({
                    "control_id": cid, "kind": kind, "target": target,
                    "applied_as": "匝道场预留登记：demand 预订（C2 口径），"
                                  "缺额进 resource_conflicts；场内通道"
                                  "不向他网开放"})
        elif kind == "assign_preferred_layer":
            bus = target.split(":", 1)[-1]
            layer = action.get("preferred_layer")
            if bus not in registry_buses:
                reason = "target bus 未解析（route view 无此总线）"
            else:
                reads.append({"artifact": rel, "field":
                              "controls[%s].action.preferred_layer" % cid,
                              "role": "feedforward_plan"})
                allowed = {x for x in (bus_allowed.get(bus) or set())
                           if x in signal_layers}
                if layer in allowed:
                    ext["preferred_layers"][bus] = layer
                else:
                    # FF4-D3 同语义：registry allowed_layers 为硬权限，
                    # 控制偏好越权 → 记 note，不生效不报错
                    ext["preferred_layer_notes"].append({
                        "control_id": cid, "bus": bus, "requested": layer,
                        "allowed": sorted(allowed),
                        "note": "preferred_layer 不在 registry allowed_layers"
                                "（硬权限）→ 偏好不生效"})
                applied.append({
                    "control_id": cid, "kind": kind, "target": target,
                    "applied_as": "车道干道层偏好（allowed_layers 硬权限内"
                                  "生效；越权记录不生效）"})
        elif kind == "protect_keepout":
            refs = [r for r in (action.get("refs") or [])]
            mm = action.get("keepout_mm")
            if not refs:
                reason = "action.refs 为空"
            elif not mm or mm <= 0:
                reason = "action.keepout_mm 缺失/非正"
            else:
                for fld in ("refs", "keepout_mm"):
                    reads.append({"artifact": rel, "field":
                                  "controls[%s].action.%s" % (cid, fld),
                                  "role": "feedforward_plan"})
                ext["keepout_groups"].append({
                    "control_id": cid, "scope": target.split(":", 1)[-1],
                    "refs": sorted(refs), "keepout_mm": mm})
                applied.append({
                    "control_id": cid, "kind": kind, "target": target,
                    "applied_as": "匝道通道 keepout 进入候选接受（lex 首位="
                                  "控制违例数，M 系数前置；组员/电气邻件豁免；"
                                  "max-flow 物理可行性与三态红线不变）"})
        elif kind == "set_route_order":
            order = action.get("route_order") or []
            reads.append({"artifact": rel, "field":
                          "controls[%s].action.route_order" % cid,
                          "role": "feedforward_plan"})
            known = [b for b in order if b in registry_buses]
            ext["route_order"] = {"control_id": cid, "order": known,
                                  "dropped_unknown":
                                      [b for b in order
                                       if b not in registry_buses]}
            applied.append({
                "control_id": cid, "kind": kind, "target": target,
                "applied_as": "总线处理序（车道分配插边序；确定性）"})
        elif kind == "reserve_return_stitching":
            reads.append({"artifact": rel, "field":
                          "controls[%s].action.grid_mm" % cid,
                          "role": "feedforward_plan"})
            ext["stitching"] = {
                "control_id": cid, "grid_mm": action.get("grid_mm"),
                "dense_mm": action.get("dense_mm"),
                "dense_regions": action.get("dense_regions"),
                "status": "acknowledged（④ dry-run 无缝合求解器；"
                          "供给模型 missing_basis，不编造资源数）"}
            applied.append({
                "control_id": cid, "kind": kind, "target": target,
                "applied_as": "缝合预留登记（无求解，缺供给→missing_basis）"})
        elif kind == "reserve_via_budget":
            reads.append({"artifact": rel, "field":
                          "controls[%s].action" % cid, "role":
                          "feedforward_plan"})
            ext["via_budget_reserve"].append({"control_id": cid,
                                              "action": action})
            applied.append({
                "control_id": cid, "kind": kind, "target": target,
                "applied_as": "过孔预算预留登记（供给 missing_basis）"})
        elif kind == "reserve_lane":
            bus = target.split(":", 1)[-1]
            ext["reserve_lane"].append({"control_id": cid, "bus": bus,
                                        "action": action})
            applied.append({
                "control_id": cid, "kind": kind, "target": target,
                "applied_as": "车道预留（池容量预扣）"})
        if reason:
            ignored.append({"control_id": cid, "kind": kind, "target":
                            target, "reason": reason})
    ext["zero_present_kinds"] = sorted(
        k for k in CONSUMABLE_ROUTE_KINDS if k not in present_kinds)
    return ext, applied, ignored, conflicts
