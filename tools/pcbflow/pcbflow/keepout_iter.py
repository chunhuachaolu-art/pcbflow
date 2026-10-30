"""IT 会话：③ keepout-aware 布局重优化（KEEPOUT-EVIDENCE.md 立项，知情裁决）。

目标口径（可验证）：基线=冻结 fc3 route-plan（pin 08a3ed6b…，fd2 计划绑定）
的 ④ ramp keepout 控制违例 79；候选布局的违例度量=**同源精确复算**（④
solve_ramp + keepout 区随候选位姿重建，未动 refs 保留原浮点零漂移），基线
复算必须精确=79（度量自校；失配→blocked，不出优化结论）。推进阈值=违例
降幅 ≥10%（79→≤71；KEEPOUT-EVIDENCE §3 回退条款 <10% 的对偶）；护栏
（不回归）：③ 全部硬门逐门幅度 ≤ fd3 绑定基线、失败门不得新增；功率环路
(w,h) 逐维 ≤ 基线；去耦/就近（over_limit/target_rate/链半径/幅度）≤ 基线；
④ 物理可行性（ramp UNSAT 集 ⊆ 基线、未匹配数 ≤ 基线）。

确认点 #4 申报（随产物落库，转换不执行）：锚件集=structures.json 已批
10 只（J1–J5/U1/U2/U6/Y1/Y2），本优化永不生成锚件候选；it-layout.json 仅为
③ 提案，layout→placement.csv 转换与板应用须人工批准。

方法：确定性爬山。变量=非锚件 keepout 相关件（④ 违例 ramp 承载 ref ∪
protect_keepout 组员）；候选=coplace._candidate_moves 同 ③（±{0.5,1,2}mm×4
向 + 90° 旋转步进）；接受键=(违例数, ③硬违幅度和, 交叉, 拥塞, 过孔, 绕行,
对称偏差) 严格字典序改善且护栏全过；worst-first 稳定序（基线逐 ref 违例降
序，ref 字典序 tie-break）；无随机、wall-clock 只进 run_manifest。违例度量
每候选全量复算（量子位姿→mm 板重建→escape_check→solve_ramp；护栏先评、
便宜的 evaluate 拒绝在先）。

默认路径零扰动：本命令独立（keepout-iter）；③ co-place/④ route 默认产物
与历史 pin 不变（测试强制）。④ 官方对照=route --placement-from-layout
（opt-in；同 fd3 计划绑定，与 fc3 逐 run 可比）。
"""

from __future__ import annotations

import datetime
import json
import os
import socket
import sys

from . import audit_cmd, config, coplace_cmd, envelope, enum_cmd, ff_consume, \
    geo, hashing, route_cmd, route_view

IT_SCHEMA = "1.3"
IT_ARTIFACT_KIND = "keepout_iteration"
PROCEED_REDUCTION_MIN = 0.10   # 降幅 <10% → 回退存档（KEEPOUT-EVIDENCE §3）
GUARD_TOL = 1e-9               # 浮点护栏容差（mm/比率）
# W-G4（G2/G3 批 2026-09-25）：D 级 pin 消化——两计划缺省自 manifest
# out_dirs 派生（来源集中）。split+join 保平台分隔符形态=值不变门（G1+
# 留账「同 pin 异形」的消解：两平台派生值与原 os.path.join 字面量逐字节
# 相等；守卫=tests/test_manifest_g2.py 派生钉值族）。
_ki_od = config.load_project_manifest().out_dirs
FF_PLAN_DEFAULT = os.path.join(*_ki_od["kit_ff_plan"].split("/"))
FC3_PLAN_DEFAULT = os.path.join(*_ki_od["kit_route_plan"].split("/"))


# ---- 组装（一次性；候选期只做重建+求解） --------------------------------------
def setup(ff_plan_path, baseline_route_plan, out_dir_rel):
    """基线组装：③ ctx（fd3 绑定）+ ④ 度量底座 + 官方基线对照 + 候选集。"""
    enum_products = enum_cmd.build_products(out_dir_rel=out_dir_rel)
    structures = enum_products["structures"]["obj"]
    registry = enum_products["net_registry"]["obj"]
    registry_hash = registry["registry_snapshot_hash"]
    net_ids = {r["net_name"]: r["net_id"] for r in registry["nets"]}
    net_id_of = dict(net_ids)

    with open(config.SEED_PATH, encoding=config.ENCODING) as f:
        seed = json.load(f)

    board = geo.parse_board(config.AUDIT_P3_BOARD)
    baseline = coplace_cmd.import_placement_csv(config.AUDIT_P3_PLACEMENT_CSV)
    st0 = coplace_cmd.state_with_csv_zones(
        coplace_cmd.state_from_board(board), baseline)

    # ③ 侧：fd3 计划消费（§9.1；controls 进入候选接受=consumer gate 已批）
    ff = ff_consume.consume_plan(
        ff_plan_path, enum_products=enum_products,
        shape_refs=set(board["footprints"]),
        corridor_bus_ids=[b["bus_id"] for b in structures["buses"]],
        out_dir_rel=out_dir_rel)
    ctx = coplace_cmd.build_context(
        board, structures, seed, net_ids, registry_hash,
        zone_labels={r: b["zone"] for r, b in baseline.items()},
        registry_view={r["net_name"]: r for r in registry["nets"]},
        layer_preference_ranks=structures["priorities"]["layer_preference"]["ranks"],
        board_rect=coplace_cmd.edge_cuts_bbox(config.AUDIT_P3_BOARD),
        ff_controls=ff["extensions"] if ff["applied"] else None)
    base_ev = coplace_cmd.evaluate(ctx, st0)

    # ④ 侧：度量底座（registry/seed/placement 无关部分一次性；fd3 controls）
    vp = route_view.build_route_view(out_dir_rel)
    reads = []
    plan, plan_sha = ff_consume.load_plan(ff_plan_path, reads)
    current, st_basis = ff_consume.apply_plan_structures_basis(plan,
                                                               vp["view"]["snapshot"], reads)
    binding = ff_consume.snapshot_binding(plan, current,
                                          structures_basis=st_basis)
    ext_r, applied_r, ignored_r, _ = route_view.interpret_controls_route(
        plan, vp, reads)
    if not binding["all_match"]:
        ext_r, applied_r = {}, []

    official = _load_official(baseline_route_plan)
    per_ref_official = official["per_ref_viol"]

    group_refs = {r for g in ext_r.get("keepout_groups") or []
                  for r in g["refs"]}
    cand = sorted((set(per_ref_official) | group_refs)
                  - set(ctx["anchors"]))
    anchors = sorted(ctx["anchors"])

    m0 = viol_metric({"board": board, "net_id_of": net_id_of, "vp": vp,
                      "seed_sides": vp["seed_sides"], "ext_r": ext_r}, st0)
    return {
        "out_dir_rel": out_dir_rel, "ff_plan_path": ff_plan_path,
        "ff_plan_sha": plan_sha, "ff_binding": binding,
        "baseline_route_plan": baseline_route_plan,
        "registry_hash": registry_hash, "board": board, "st0": st0,
        "ctx": ctx, "base_ev": base_ev, "vp": vp, "ext_r": ext_r,
        "seed_sides": vp["seed_sides"], "net_id_of": net_id_of,
        "anchors": anchors, "candidate_refs": cand,
        "keepout_groups": ext_r.get("keepout_groups") or [],
        "official": official, "ff_applied": ff["applied"],
        "m0": m0,
        "controls_applied_3": None, "controls_applied_4": sorted(
            a["control_id"] for a in applied_r),
    }


def _load_official(path):
    """冻结 fc3 route-plan → 官方违例账（逐 ref、UNSAT 集、未匹配数）。"""
    with open(path, encoding=config.ENCODING) as f:
        rp = json.load(f)
    runs = [r for r in rp["solver_runs"] if r["kind"] == "ramp"]
    per_ref = {r["scope"]["ref"]: r["keepout_control_violations"]
               for r in runs if r["keepout_control_violations"]}
    return {
        "path": path.replace("\\", "/"),
        "viol": sum(r["keepout_control_violations"] for r in runs),
        "per_ref_viol": per_ref,
        "unsat_refs": sorted(r["scope"]["ref"] for r in runs
                             if r["status"] == "UNSAT"),
        "unmatched": sum(len(r["unmatched"]) for r in rp["ramps"]),
        "plan_id": (rp.get("plan_binding") or {}).get("plan_id"),
        "route_plan_sha256": hashing.sha256_file(path),
    }


# ---- 违例度量（④ 同源复算；自校=基线 79） ------------------------------------
def viol_metric(base, st):
    """候选位姿 → ④ ramp keepout 控制违例账（精确同源；moved refs 重建板，
    未动 refs 原浮点零漂移）。"""
    rows = [{"ref": r, "x": coplace_cmd.uq(st[r]["x"]),
             "y": coplace_cmd.uq(st[r]["y"]), "rot": st[r]["rot"]}
            for r in sorted(st)]
    board2, moved = route_view.board_with_layout(base["board"], rows)
    esc2 = audit_cmd.escape_check(board2, route_view._cls_identity)
    fields_out, transit_refs, unmapped = route_view.escape_fields_of(
        esc2, base["net_id_of"])
    view2 = dict(base["vp"]["view"])
    view2.update({"escape_fields": fields_out,
                  "escape_fields_total": len(esc2["fields"]),
                  "escape_fields_with_demand": len(fields_out),
                  "transit_refs": sorted(transit_refs)})
    vctx = {"view": view2, "board": board2, "esc": esc2,
            "seed_sides": base["seed_sides"]}
    ramp_rows, _, runs = route_cmd.solve_ramp(vctx, base["ext_r"])
    return {
        "viol": sum(r["keepout_control_violations"] for r in runs),
        "per_ref": {r["scope"]["ref"]: r["keepout_control_violations"]
                    for r in runs if r["keepout_control_violations"]},
        "unsat_refs": sorted(r["scope"]["ref"] for r in runs
                             if r["status"] == "UNSAT"),
        "unmatched": sum(len(r["unmatched"]) for r in ramp_rows),
        "moved_refs": moved,
    }


def _key(m, ev):
    """接受键：违例数 → ③ lex 尾部（硬违幅度和/交叉/拥塞/过孔/绕行/对称）。"""
    return (m["viol"], ev["hard_magnitude_mm"], ev["soft"]["crossings"],
            ev["soft"]["congestion_max"], ev["soft"]["vias"],
            ev["soft"]["detour_max"], ev["soft"]["symmetry_dev_max_mm"])


# ---- 护栏（不回归；NEXT.md IT 护栏条款的实现） --------------------------------
def guards_3(base, ev):
    """③ 侧护栏：逐门不回归 + 功率环路 (w,h) 逐维 + 去耦/就近分项。"""
    checks = []
    ok = True
    bg = base["base_ev"]["hard"]
    for gname in sorted(bg):
        b, g = bg[gname], ev["hard"][gname]
        if b["pass"] and not g["pass"]:
            ok = False
            checks.append({"gate": gname, "kind": "new_fail"})
        elif g["magnitude_mm"] > b["magnitude_mm"] + GUARD_TOL:
            ok = False
            checks.append({"gate": gname, "kind": "magnitude_regression",
                           "baseline": b["magnitude_mm"],
                           "trial": g["magnitude_mm"]})
    bl, gl = bg["buck_loop"], ev["hard"]["buck_loop"]      # 功率环路逐维
    if bl.get("w_mm") is not None and gl.get("w_mm") is not None:
        if gl["w_mm"] > bl["w_mm"] + GUARD_TOL or \
                gl["h_mm"] > bl["h_mm"] + GUARD_TOL:
            ok = False
            checks.append({"gate": "buck_loop", "kind": "wh_regression",
                           "baseline": [bl["w_mm"], bl["h_mm"]],
                           "trial": [gl["w_mm"], gl["h_mm"]]})
    bp, gp = bg["proximity"], ev["hard"]["proximity"]      # 去耦半径/就近分项
    if gp["decap_over_limit"] > bp["decap_over_limit"]:
        ok = False
        checks.append({"gate": "proximity", "kind": "decap_over_limit_up",
                       "baseline": bp["decap_over_limit"],
                       "trial": gp["decap_over_limit"]})
    if gp["decap_target_rate"] < bp["decap_target_rate"] - GUARD_TOL:
        ok = False
        checks.append({"gate": "proximity", "kind": "target_rate_down",
                       "baseline": bp["decap_target_rate"],
                       "trial": gp["decap_target_rate"]})
    bx = max((r["excess_mm"] for r in bp["chain_radius_rows"]), default=0.0)
    gx = max((r["excess_mm"] for r in gp["chain_radius_rows"]), default=0.0)
    if gx > bx + GUARD_TOL:
        ok = False
        checks.append({"gate": "proximity", "kind": "chain_radius_up",
                       "baseline": bx, "trial": gx})
    return ok, checks


def guards_physical(base, m):
    """④ 物理可行性护栏：UNSAT 集 ⊆ 基线、未匹配数 ≤ 基线。"""
    base_u = set(base["official"]["unsat_refs"])
    if not set(m["unsat_refs"]) <= base_u:
        return False, [{"gate": "ramp_physical", "kind": "new_unsat",
                        "baseline": base["official"]["unsat_refs"],
                        "trial": m["unsat_refs"]}]
    if m["unmatched"] > base["official"]["unmatched"]:
        return False, [{"gate": "ramp_physical", "kind": "unmatched_up",
                        "baseline": base["official"]["unmatched"],
                        "trial": m["unmatched"]}]
    return True, []


def guards_of(base, ev, m):
    """全护栏（③ 侧 + ④ 物理）；最终布局复核与测试用。"""
    ok, checks = guards_3(base, ev)
    ok2, checks2 = guards_physical(base, m)
    return ok and ok2, checks + checks2


# ---- 确定性爬山（锚件永不入候选；无随机；严格改善） ---------------------------
def optimize(base, max_sweeps=None, refs=None):
    """返回 (final_st, result dict)。接受键严格字典序改善 + 护栏全过。"""
    max_sweeps = max_sweeps or config.CPLACE_MAX_SWEEPS
    st0 = base["st0"]
    cur_st = {r: dict(v) for r, v in st0.items()}
    cur_ev = base["base_ev"]
    cur_m = base["m0"]
    cur_key = _key(cur_m, cur_ev)
    order = sorted(refs or base["candidate_refs"],
                   key=lambda r: (-base["official"]["per_ref_viol"].get(r, 0),
                                  r))
    trace = []
    accepted = 0
    converged = False
    sweeps = 0
    guard_rejects = 0
    for _ in range(max_sweeps):
        sweeps += 1
        improved = False
        for ref in order:
            for kind, _, dx, dy, rot in coplace_cmd._candidate_moves(ref):
                trial = {r: dict(v) for r, v in cur_st.items()}
                t = trial[ref]
                if kind == "move":
                    t["x"] += dx
                    t["y"] += dy
                else:
                    t["rot"] = (t["rot"] + rot) % 360
                ev = coplace_cmd.evaluate(base["ctx"], trial)
                ok, _ = guards_3(base, ev)
                if not ok:
                    guard_rejects += 1
                    continue
                m = viol_metric(base, trial)
                ok2, _ = guards_physical(base, m)
                if not ok2:
                    guard_rejects += 1
                    continue
                key = _key(m, ev)
                if key < cur_key:
                    trace.append({
                        "sweep": sweeps, "ref": ref,
                        "move": {"kind": kind, "dx": coplace_cmd.uq(dx),
                                 "dy": coplace_cmd.uq(dy), "rot": rot},
                        "viol_before": cur_m["viol"],
                        "viol_after": m["viol"],
                        "key_before": list(cur_key), "key_after": list(key)})
                    cur_st, cur_ev, cur_m, cur_key = trial, ev, m, key
                    accepted += 1
                    improved = True
        if not improved:
            converged = True
            break
    for a in base["anchors"]:  # 红线断言：锚件位姿冻结
        assert (cur_st[a]["x"], cur_st[a]["y"], cur_st[a]["rot"]) == \
            (st0[a]["x"], st0[a]["y"], st0[a]["rot"]), a
    result = {
        "final_st": cur_st, "final_ev": cur_ev, "final_m": cur_m,
        "trace": trace, "accepted": accepted, "sweeps": sweeps,
        "converged": converged, "max_sweeps_reached":
            not converged and sweeps >= max_sweeps,
        "guard_rejects": guard_rejects,
        "order": order, "refs": refs,
    }
    return cur_st, result


# ---- 产物（keepout-iteration.json + it-layout.json；核心禁 wall-clock） -------
def build_products(out_dir_rel=config.load_project_manifest().out_dirs["keepout_iter"],
                   ff_plan_path=FF_PLAN_DEFAULT,
                   baseline_route_plan=FC3_PLAN_DEFAULT, max_sweeps=None,
                   refs=None):
    """⑤-keepout 迭代布局主构建：基线对账 → 守门迭代优化 → 级联裁决。

    流程与裁决序：
    1. setup 装载（FF 计划+FC3 基线路由计划+M0 critic 复算）；M0 与官方
       viol 不一致即整批 blocked/red（不进入优化——基线漂移先挡）；
    2. optimize 逐器件迭代（max_sweeps/refs 透传），final 状态+评估经
       guards_of 复核（锚定器件不动+守门全绿才可信）；
    3. 裁减率 reduction=(official-final)/official，达 PROCEED_REDUCTION_
       MIN 且 guards 全绿 → cascade_candidate（verdict=pass），否则
       rollback_archive（verdict=yellow）；
    4. placements 按器件三分类记账（anchor_locked / it_optimized /
       baseline_unchanged），产物=keepout-iteration.json（optimization/
       violations/guards/双消费登记/target_caliber/metric_self_check/
       baseline_evidence/result 全节）+ it-layout.json + run_manifest。
    """
    t0 = datetime.datetime.now(datetime.timezone.utc)
    base = setup(ff_plan_path, baseline_route_plan, out_dir_rel)

    match = base["m0"]["viol"] == base["official"]["viol"]
    status, verdict = "ok", None
    opt = None
    if not match:
        status, verdict = "blocked", "red"
        final_st, m_final, ev_final = base["st0"], None, base["base_ev"]
    else:
        final_st, opt = optimize(base, max_sweeps=max_sweeps, refs=refs)
        m_final, ev_final = opt["final_m"], opt["final_ev"]

    official_v = base["official"]["viol"]
    final_v = m_final["viol"] if m_final else None
    reduction = (round((official_v - final_v) / official_v, 4)
                 if final_v is not None and official_v else 0.0)
    target_met = bool(final_v is not None and official_v
                      and reduction >= PROCEED_REDUCTION_MIN - 1e-12)
    guards_final_ok = True
    guard_checks = []
    if opt is not None:
        guards_final_ok, guard_checks = guards_of(base, ev_final, m_final)
    decision = ("cascade_candidate" if target_met and guards_final_ok
                else "rollback_archive")
    if verdict is None:
        verdict = "pass" if decision == "cascade_candidate" else "yellow"

    st0 = base["st0"]
    placements = []
    for ref in sorted(final_st):
        moved = (final_st[ref]["x"], final_st[ref]["y"],
                 final_st[ref]["rot"]) != (st0[ref]["x"], st0[ref]["y"],
                                           st0[ref]["rot"])
        role = ("anchor_locked" if ref in base["ctx"]["anchors"]
                else ("it_optimized" if moved else "baseline_unchanged"))
        placements.append({
            "ref": ref, "x": coplace_cmd.uq(final_st[ref]["x"]),
            "y": coplace_cmd.uq(final_st[ref]["y"]),
            "rot": final_st[ref]["rot"],
            "side": final_st[ref].get("side") or "F",
            "zone": final_st[ref].get("zone") or "",
            "role": role, "moved": moved})

    baseline_gates = {k: {"pass": v["pass"],
                          "magnitude_mm": v["magnitude_mm"]}
                      for k, v in base["base_ev"]["hard"].items()}
    final_gates = {k: {"pass": v["pass"], "magnitude_mm": v["magnitude_mm"]}
                   for k, v in ev_final["hard"].items()}
    it_layout = {
        "schema_version": config.SCHEMA_COPLACE,
        "artifact_kind": "it_layout",
        "project": "stm32h743-coreboard-revc", "stage": 3,
        "role": "IT keepout 迭代布局提案（非权威；转换执行=确认点 #4 待批）",
        "baseline": "p3 冻结基线（板读数量化）；锚件位姿冻结",
        "optimization": {
            "applied": opt is not None, "mode":
                "keepout_aware_hill_climb(违例=④ solve_ramp 同源复算)",
            "sweeps": opt["sweeps"] if opt else 0,
            "accepted_moves": opt["accepted"] if opt else 0,
            "converged": opt["converged"] if opt else None,
            "max_sweeps_reached":
                opt["max_sweeps_reached"] if opt else None,
            "candidate_refs": base["candidate_refs"],
            "order_basis": "worst-first（基线逐 ref 违例降序，ref 序 tie）",
            "reason": "KEEPOUT-EVIDENCE.md 立项（2026-08-30 人工裁决：驱动 ③"
                      " 迭代）；fd3 计划绑定；锚件/硬门阈值/历史 B 门不追改",
        },
        "placements": placements,
        "violations": {"baseline": official_v, "final": final_v},
        "guards": {"baseline_gates": baseline_gates,
                   "final_gates": final_gates,
                   "non_regression": guards_final_ok,
                   "final_checks": guard_checks},
        "registry_consumption": {
            "registry_snapshot_hash": base["registry_hash"],
            "registry_consumed": True,
            "fields_consumed": ["net_id", "allowed_layers", "via_policy",
                                "skeleton_seed(corridor demand/exit sides)"],
            "fallback": None, "fidelity": "full（同 ③ coplace 口径）"},
        "feedforward_consumption": {
            "plan_path": base["ff_plan_path"].replace("\\", "/"),
            "feedforward_plan_hash": base["ff_plan_sha"],
            "binding_all_match": base["ff_binding"]["all_match"],
            "applied_3": base["ff_applied"],
            "controls_applied_4": base["controls_applied_4"],
        },
    }

    iteration = {
        "schema_version": IT_SCHEMA,
        "artifact_kind": IT_ARTIFACT_KIND,
        "purpose": "IT keepout ③ 迭代（KEEPOUT-EVIDENCE.md 立项，知情裁决）",
        "target_caliber": {
            "metric": "④ ramp keepout 控制违例（route_cmd.solve_ramp 同源"
                      "复算；lex 最小化口径与 fc3 一致）",
            "baseline": official_v,
            "baseline_source": base["official"],
            "proceed_threshold": "降幅 ≥%g%%（%d→≤%d）；<%g%% → 回退存档"
                                 % (PROCEED_REDUCTION_MIN * 100, official_v,
                                    official_v - int(
                                        official_v * PROCEED_REDUCTION_MIN),
                                    PROCEED_REDUCTION_MIN * 100),
            "non_regression": ["③ 全部硬门逐门幅度 ≤ 基线且失败门不新增",
                               "功率环路 (w,h) 逐维 ≤ 基线",
                               "去耦半径/就近（over_limit/target_rate/链半径/"
                               "幅度）≤ 基线",
                               "④ ramp UNSAT 集 ⊆ 基线、未匹配数 ≤ 基线",
                               "断点预测门：② a3 冻结输入零变更（IT 不触 ②）"],
            "metric_self_check": {
                "recomputed_baseline": base["m0"]["viol"],
                "equals_official": match,
                "note": "未动 refs 原浮点零漂移 ⇒ 基线复算必须精确=官方值",
            },
        },
        "confirmation_point_4_declaration": {
            "anchors": base["anchors"],
            "anchor_source": "out/revc-a2/structures.json 已批锚件（fd1 "
                             "override 未改 anchors；KEEPOUT-EVIDENCE §0）",
            "anchor_candidates_generated": 0,
            "conversion_executed": False,
            "note": "it-layout.json 仅为 ③ 提案；layout→placement.csv 转换"
                    "与板应用须人工批准（HANDOFF §3 #4）",
        },
        "baseline_evidence": {
            "verdict_bound": "fd3（FF-REVC-0003）；controls 与 fd2 逐字节"
                             "一致（1661a9b8…）→ 与 fc3 官方 79 可比",
            "gates_fd3_bound": baseline_gates,
            "note": "护栏基线=fd3 绑定评估（与优化自洽）；b1 默认证据差异"
                    "仅 ff 派生门（escape 预留带/ff_keepout 体级行）",
        },
        "optimization": None if opt is None else {
            "method": "deterministic_hill_climb（接受键=违例→③ lex 尾部；"
                      "护栏前置拒绝；无随机）",
            "sweeps": opt["sweeps"], "accepted_moves": opt["accepted"],
            "converged": opt["converged"],
            "max_sweeps_reached": opt["max_sweeps_reached"],
            "guard_rejects": opt["guard_rejects"],
            "order": opt["order"], "refs_filter": opt["refs"],
            "trace": opt["trace"],
            "per_ref_viol_final": opt["final_m"]["per_ref"],
            "moved_refs": [p["ref"] for p in placements if p["moved"]],
        },
        "result": {
            "violations_baseline": official_v,
            "violations_final": final_v,
            "reduction_pct": reduction * 100.0,
            "target_met": target_met,
            "guards_non_regression": guards_final_ok,
            "guard_final_checks": guard_checks,
            "decision": decision,
            "decision_note": (
                "≥10% 降幅且护栏全过 → 级联候选（级联执行仍须确认点 #4 批准"
                "后另会话收口；fd3 口径沿留 --consume-bom、新 out 目录、"
                "fd3 冻结）" if decision == "cascade_candidate" else
                "收益不足（<10%）或护栏回归 → 回退存档：fc3/fd3 权威链"
                "不变，本产物作为 KEEPOUT-EVIDENCE §3 存档路径证据"),
        },
    }

    core_scan = envelope.scan_forbidden_core_fields(iteration) + \
        envelope.scan_forbidden_core_fields(it_layout)
    assert not core_scan, core_scan

    products = {}
    for name, obj in (("keepout_iteration", iteration), ("it_layout",
                                                         it_layout)):
        data = hashing.canonical_json_bytes(obj)
        products[name] = {"obj": obj, "bytes": data,
                          "sha256": hashing.sha256_bytes(data)}

    inputs = [
        {"path": "design/coreboard/kicad/stm32h743-coreboard-revc/snapshots/"
                 "p3-placement-gates-pass/stm32h743-coreboard-revc.kicad_pcb",
         "sha256": hashing.sha256_file(config.AUDIT_P3_BOARD), "role": "board"},
        {"path": "design/coreboard/kicad/stm32h743-coreboard-revc/snapshots/"
                 "p3-placement-gates-pass/placement.csv",
         "sha256": hashing.sha256_file(config.AUDIT_P3_PLACEMENT_CSV),
         "role": "board"},
        {"path": "out/revc-a3/skeleton-seed.json",
         "sha256": hashing.sha256_file(config.SEED_PATH),
         "role": "skeleton_seed"},
        {"path": "out/revc-a3/net-registry.json",
         "sha256": base["registry_hash"], "role": "registry"},
        {"path": base["ff_plan_path"].replace("\\", "/"),
         "sha256": base["ff_plan_sha"], "role": "feedforward_plan"},
        {"path": base["official"]["path"],
         "sha256": base["official"]["route_plan_sha256"],
         "role": "baseline_route_plan"},
    ]
    artifacts = [
        {"path": f"{out_dir_rel}/keepout-iteration.json",
         "sha256": products["keepout_iteration"]["sha256"], "role": "core"},
        {"path": f"{out_dir_rel}/it-layout.json",
         "sha256": products["it_layout"]["sha256"], "role": "core"},
    ]
    env = envelope.build_envelope(
        command="keepout-iter", status=status, verdict=verdict,
        command_kind="core", schema_version=config.SCHEMA_ENVELOPE,
        inputs=inputs, artifacts=artifacts,
        config_sha256=hashing.sha256_text(hashing.json_dumps(
            {k: v for k, v in vars(config).items() if k.isupper()})),
        spec_refs=["tools/pcbflow/SPEC.md#§9", "tools/pcbflow/SPEC.md#§10",
                   "tools/pcbflow/KEEPOUT-EVIDENCE.md"],
        metrics={
            "baseline_violations_official": official_v,
            "baseline_violations_recomputed": base["m0"]["viol"],
            "metric_self_check_pass": match,
            "final_violations": final_v,
            "reduction_pct": reduction * 100.0,
            "proceed_threshold_pct": PROCEED_REDUCTION_MIN * 100.0,
            "target_met": target_met,
            "guards_non_regression": guards_final_ok,
            "moved_refs": len([p for p in placements if p["moved"]]),
            "candidate_refs": len(base["candidate_refs"]),
            "anchors_frozen": len(base["anchors"]),
            "sweeps": opt["sweeps"] if opt else 0,
            "converged": opt["converged"] if opt else None,
            "decision": decision,
            "board_write": False,
        },
        diagnostics=[
            {"id": "it_target_caliber",
             "title": "目标口径：违例 79→≤71（≥10% 降幅）+功率环路/去耦半径/"
                      "断点预测门不回归；<10% → 回退存档（KEEPOUT-EVIDENCE "
                      "§3 条款）"},
            {"id": "it_confirmation_point_4",
             "title": "锚件申报：structures 已批 10 只（J1–J5/U1/U2/U6/Y1/Y2）"
                      "永不移动；it-layout 仅为提案，转换执行待批"},
            {"id": "it_metric_self_check",
             "title": "度量自校：基线复算=官方 79（同源精确；失配=blocked）"},
        ],
        data={"gate": {
            "metric_self_check": match,
            "anchors_never_moved": True,
            "conversion_pending_approval": True,
            "note": "算法实验门≠项目交付门；fc3/fd3 权威链在本会话保持冻结",
        }},
    )
    products["envelope"] = {"obj": env}

    t1 = datetime.datetime.now(datetime.timezone.utc)
    products["run_manifest"] = {"obj": {
        "started_at": t0.isoformat(), "finished_at": t1.isoformat(),
        "elapsed_s": round((t1 - t0).total_seconds(), 3),
        "host": socket.gethostname(), "python_version": sys.version.split()[0],
        "tool_version": config.TOOL_VERSION,
        "command": "keepout-iter", "out_dir": out_dir_rel,
        "input_sha256": {i["path"]: i["sha256"] for i in inputs},
        "config_sha256": hashing.sha256_text(hashing.json_dumps(
            {k: v for k, v in vars(config).items() if k.isupper()})),
        "spec_sha256": hashing.sha256_file(os.path.join(config.PCBFLOW_ROOT,
                                                        "SPEC.md")),
        "registry_snapshot_sha256": base["registry_hash"],
        "feedforward_plan_sha256": base["ff_plan_sha"],
        "schema_version": IT_SCHEMA,
    }}
    return products
