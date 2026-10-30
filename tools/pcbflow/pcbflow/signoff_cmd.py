"""⑥ 终检与签核（SPEC v1.3 §12/§15 FD1；HANDOFF FD1 行）。

四块交付：
1. 签核包（§12 清单 13 项逐项列账：path+sha256+status；缺项=not_available+原因，
   不伪造）。签核正文只由约束库终态、KiCad ERC/DRC authority、必要外部签核和
   人工批准决定（§12 正文条款）；feedforward 计划与 residuals=planning 附录，
   视觉 advisory 附录=空（视觉轨道未指派，HANDOFF §2）。
2. waiver 台账（§12.1）：approved=[]（人工逐条批准前恒空——确认点 #5，禁代办）；
   candidates=dry-run 已知开放项中可豁免对象的提案（constraint_id 无法映射时
   如实 null+unmapped 说明）。前馈资源赤字不生成 waiver（§12.1 红线）。
3. 重放验证（§12.2）：核心产物确定性重生成 vs 盘上 sha256 逐件对比（元数据
   run-manifest 不参与）；FC2 两靶为分钟级+adapter 依赖 → 双发基准 pin 记账
   （复跑命令随包，PHASE-REPORT-9 §5/PHASE-REPORT-10 实证）。
4. envelope：包完整性 gate 与生产签核 readiness 分列——dry-run 包 verdict 由
   已知未过项如实列账（HANDOFF §5），生产签核 blocked_on_human（确认点
   #1 structures 未批、#5 waivers 未批、外部签核未接入），不互相替代。

消费面：⑤ check 产物 + FC2 route 产物为输入（§9.1 同构消费证据随包）。
生成器模式：零落盘、零子进程；常量内聚本模块（config.py 零新增）。
"""

from __future__ import annotations

import json
import os

from . import check_cmd, config, hashing
from . import profile_loader

FD1_SCHEMA = "1.0"
# G0（REPAIR-P4 W-1）：Rev-C 目录 pin 自 profiles/revc-coreboard/profile.json 装载
_pf = profile_loader.load_profile(config.PCBFLOW_ROOT)
FD1_OUT_DEFAULT = profile_loader.require(_pf, "signoff_cmd", "fd1_out_default")
A3_DIR = profile_loader.require(_pf, "signoff_cmd", "a3_dir")
B1_DIR = profile_loader.require(_pf, "signoff_cmd", "b1_dir")
FF1_DIR = profile_loader.require(_pf, "signoff_cmd", "ff1_dir")
FF2_DIR = profile_loader.require(_pf, "signoff_cmd", "ff2_dir")
FC1_DIR = profile_loader.require(_pf, "signoff_cmd", "fc1_dir")
FC2_DIR = profile_loader.require(_pf, "signoff_cmd", "fc2_dir")
CHECK_DIR = FD1_OUT_DEFAULT
# FF3 BOM 派生轨功耗表（feedforward 常量镜像；常量内聚本模块，config.py 零新增）
FD3_BOM_POWER_REL = profile_loader.require(
    _pf, "signoff_cmd", "fd3_bom_power_rel")

# FC2 双发基准 pin（PHASE-REPORT-9 §4/§5 + PHASE-REPORT-10 段② 复核实证；
# 重生成分钟级+adapter 依赖 → 签核重放以 pin 记账，复跑命令随包）
FC2_DOUBLE_SEND_PINS = {
    "residual-certs.json": {
        "sha256": "289532b5ec40ea865fe1bdc54a3ceceb0489f0e90d051199431d7cd9263031cb",
        "rerun": "python -m pcbflow.cli residual --select residual "
                 "--out-dir out/revc-fc2",
        "evidence": "PHASE-REPORT-9 §5；PHASE-REPORT-10 §1（段② 独立复核）",
    },
    "replay-plan.json": {
        "sha256": "6b4687d80f939525bfa7da05d9207c1f6095f302b88c8bd33fb8df2dfcdaf546",
        "rerun": "python -m pcbflow.cli residual --select replay "
                 "--out-dir out/revc-fc2 --drc-dir out/revc-fc2/drc "
                 "--batches-dir",
        "evidence": "PHASE-REPORT-9 §5；PHASE-REPORT-10 §1（段② 独立复核）",
    },
}

# ④ 控制升级（FC3 会话）历史冻结 pin：fc1 route-plan=FF-REVC-0001 绑定口径的
# 冻结证据；升级后绑定路径字节如实改变（keepout=lex 语义+文本/字段升级），
# §12.2 重放集改指当前权威链 out/revc-fc3（bind FF-REVC-0002）；fc1 冻结件以
# sha pin 记账不重生成（rerun=None=只读核对 disk hash，禁改写历史产物）。
FC1_FROZEN_PINS = {
    "route-plan.json": {
        "sha256": "fd1da4e84477a3cb9e090d1addb6eb1c0cd1225e957c1ac4c39d02de71a7119d",
        "rerun": None,
        "evidence": "PHASE-REPORT-8（FC1 收官双发）；PHASE-REPORT-12 §2（④ "
                    "升级重放改指 fc3、fc1 转冻结 pin）；fc3 vs fc1 差异="
                    "control-attributed（plan 0001→0002+lex 语义）",
    },
}

# §12.2 重放集（秒级确定性重生成；command 口径=各阶段收官生成口径）
REPLAY_SET = (
    {"product": "out/revc-a3/constraints.json", "command": "compile",
     "select": "constraints", "out_dir": "out/revc-a3"},
    {"product": "out/revc-a3/net-registry.json", "command": "enum",
     "select": "net_registry", "out_dir": "out/revc-a3"},
    {"product": "out/revc-a3/audit.json", "command": "audit",
     "select": "audit", "out_dir": "out/revc-a3"},
    {"product": "out/revc-ff1/layout.json", "command": "co-place",
     "select": "layout", "out_dir": "out/revc-ff1"},
    {"product": "out/revc-ff1/feedforward-plan.json", "command": "feedforward",
     "select": "plan", "out_dir": "out/revc-ff1"},
    {"product": "out/revc-fc3/route-plan.json", "command": "route",
     "select": "route_plan", "out_dir": "out/revc-fc3",
     "feedforward_plan": "out/revc-fd2/feedforward-plan.json"},
)


def _p(rel: str) -> str:
    return os.path.join(config.PCBFLOW_ROOT, rel)


def _rel(path: str) -> str:
    """产物内嵌路径一律仓相对（防绝对主机路径进核心产物；envelope 扫描强制）。"""
    return os.path.relpath(_p(path),
                           config.PCBFLOW_ROOT).replace("\\", "/")


def _fsha(rel: str) -> str | None:
    p = _p(rel)
    return hashing.sha256_file(p) if os.path.exists(p) else None


def _entry(rel: str, role: str, status="present"):
    sha = _fsha(rel)
    if sha is None:
        return {"path": rel, "role": role, "status": "missing",
                "sha256": None}
    return {"path": rel, "role": role, "status": status, "sha256": sha}


# ---- §12.1 waiver 台账 ---------------------------------------------------------
def _approvals_rel(out_dir_rel, approvals_dir=None):
    """批准输入目录：默认 out_dir/approvals（FD1 口径）；级联重跑（FD2）显式
    指向批准件实际所在目录（out/revc-fd1/approvals），路径隔离可重放。"""
    return (approvals_dir or (out_dir_rel + "/approvals"))


def _load_approvals(out_dir_rel, approvals_dir=None):
    """批准输入（确认点 #5 消费）：<approvals>/waiver-approvals.json；
    缺失=尚无批准（approved 恒空）。路径随 out_dir_rel/approvals_dir。"""
    rel = _approvals_rel(out_dir_rel, approvals_dir) + "/waiver-approvals.json"
    if not os.path.exists(_p(rel)):
        return None
    with open(_p(rel), encoding="utf-8") as f:
        return json.load(f)


def _dangling_candidates(replay: dict):
    """FC2 终检新增 warning（饰线类）→ waiver 候选（constraint_id 无映射→
    null+unmapped 说明；approver/created_at 留空=待人工，确认点 #5）。"""
    led = (replay or {}).get("execution_ledger") or {}
    fa = led.get("final_all") or {}
    out = []
    for w in fa.get("new_warning_detail") or []:
        kind = w.split(":", 1)[0] if ":" in w else w
        out.append({
            "waiver_id": None,
            "constraint_id": None,
            "constraint_basis": "unmapped:%s（约束库无对应条目；批准时由"
                                "人工决定是否补录约束）" % kind,
            "reason": "④ dry-run 新增 warning：%s（同网链合并饰线，"
                      "0 新增 error）" % w,
            "expiry": "下一 rev 强制复审（§12.1）",
            "approver": None,
            "status": "pending_approval（确认点 #5）",
            "evidence": {"path": FC2_DIR + "/drc/final-all.json",
                         "sha256": _fsha(FC2_DIR + "/drc/final-all.json")},
        })
    return out


def build_waiver_ledger(out_dir_rel=FD1_OUT_DEFAULT, fc2_dir=FC2_DIR,
                        approvals_dir=None):
    """approved 侧=确认点 #5 批准输入的消费结果（人工批准记录经
    approvals/waiver-approvals.json 读入，reason 与候选精确匹配防漂移）；
    candidates=当前未决提案。前馈资源赤字绝不入候选（§12.1：赤字≠violation，
    走 §17.2/§17.4-8 流程）。"""
    replay = None
    rel_path = fc2_dir + "/replay-plan.json"
    if os.path.exists(_p(rel_path)):
        with open(_p(rel_path), encoding="utf-8") as f:
            replay = json.load(f)
    candidates = _dangling_candidates(replay)
    # Rev-C 基线存量 warning（baseline 104 条，silk/courtyard 类）→ 1 条聚合候选
    base_rel = fc2_dir + "/drc/baseline-all.json"
    base = None
    if os.path.exists(_p(base_rel)):
        with open(_p(base_rel), encoding="utf-8") as f:
            base = json.load(f)
    if base is not None:
        counts = {}
        for v in base.get("violations", []):
            counts[v["type"]] = counts.get(v["type"], 0) + 1
        if counts:
            candidates.append({
                "waiver_id": None,
                "constraint_id": None,
                "constraint_basis": "unmapped:silk/courtyard 族（约束库无"
                                    "对应条目）",
                "reason": "Rev-C 基线存量 warning（回测板历史遗留，非本流水线"
                          "引入）：{%s}；dry-run 不阻断，制板前逐条裁决"
                          % ", ".join("%s×%d" % kv
                                      for kv in sorted(counts.items())),
                "expiry": "下一 rev 强制复审（§12.1）",
                "approver": None,
                "status": "pending_approval（确认点 #5）",
                "evidence": {"path": base_rel, "sha256": _fsha(base_rel)},
            })
    # —— 确认点 #5 批准消费：approved 侧（reason 精确匹配，漂移不静默合并） ------
    approved = []
    approval_drift = []
    approved_indexes = set()
    approvals = _load_approvals(out_dir_rel, approvals_dir)
    if approvals is not None:
        by_idx = {}
        for a in approvals.get("approvals") or []:
            if a.get("decision") == "approved":
                by_idx[a.get("candidate_index")] = a
        for i, cand in enumerate(candidates, start=1):
            a = by_idx.get(i)
            if a is None:
                continue
            if cand.get("reason") != a.get("reason"):
                approval_drift.append({
                    "candidate_index": i,
                    "reason": "批准记录 reason 与当前候选不一致（台账候选"
                              "内容漂移）；不合并，待人工复核后重记",
                })
                continue
            approved_indexes.add(i)
            approved.append({
                "waiver_id": "WV-%04d" % i,
                "constraint_id": cand.get("constraint_id"),
                "constraint_basis": cand.get("constraint_basis"),
                "reason": cand["reason"],
                "expiry": a.get("expiry") or cand.get("expiry"),
                "approver": a.get("approver"),
                "approved_via": a.get("approved_via"),
                "candidate_note": a.get("note"),
                "evidence": cand.get("evidence"),
            })
    pending = [c for i, c in enumerate(candidates, start=1)
               if i not in approved_indexes]
    return {
        "schema_version": FD1_SCHEMA,
        "artifact_kind": "waiver_ledger",
        "spec_ref": "SPEC v1.3 §12.1/§17.4-6",
        "approved": approved,
        "approved_note": "approved 条目按 §12.1 语义（constraint_id/reason/"
                         "expiry/approver）；created_at 以会话记录（PROGRESS/"
                         "NEXT.md）为准——核心产物禁 wall-clock 键；批准凭据"
                         "在 approved_via",
        "approvals_input": (
            None if approvals is None else
            {"path": _rel(_approvals_rel(out_dir_rel, approvals_dir)
                          + "/waiver-approvals.json"),
             "sha256": _fsha(_approvals_rel(out_dir_rel, approvals_dir)
                             + "/waiver-approvals.json")}),
        "approval_drift": approval_drift,
        "candidates": pending,
        "candidates_note": "候选=当前未决提案（已批条目转入 approved 侧）；"
                           "前馈资源赤字不生成 waiver（§12.1 红线），赤字走 "
                           "§17.2/§17.4-8",
        "confirmation_point": "确认点 #5（FD1 到点；批准经 approvals 输入消费）",
    }


# ---- §12.2 重放验证 -------------------------------------------------------------
def build_replay(out_dir_rel=FD1_OUT_DEFAULT, extra=()):
    from . import audit_cmd, compile_cmd, coplace_cmd, enum_cmd
    from . import feedforward as ff_mod
    from . import route_cmd
    rows = []
    for item in list(REPLAY_SET) + list(extra):
        disk_sha = _fsha(item["product"])
        try:
            if item["command"] == "compile":
                obj = compile_cmd.build_products(
                    out_dir_rel=item["out_dir"])[item["select"]]["obj"]
            elif item["command"] == "enum":
                obj = enum_cmd.build_products(
                    out_dir_rel=item["out_dir"])[item["select"]]["obj"]
            elif item["command"] == "audit":
                obj = audit_cmd.build_products(
                    out_dir_rel=item["out_dir"])[item["select"]]["obj"]
            elif item["command"] == "co-place":
                obj = coplace_cmd.build_products(
                    out_dir_rel=item["out_dir"])[item["select"]]["obj"]
            elif item["command"] == "feedforward":
                obj = ff_mod.build_products(
                    out_dir_rel=item["out_dir"],
                    adopt_override=item.get("adopt_override", False),
                    consume_bom=item.get("consume_bom", False),
                    placement_csv=item.get("placement_csv_path"),
                    placement_layout=item.get("placement_layout_path"),
                    bom_power_file=item.get("bom_power_file"),
                )[item["select"]]["obj"]
            elif item["command"] == "route":
                obj = route_cmd.build_products(
                    out_dir_rel=item["out_dir"],
                    ff_plan_path=item.get("feedforward_plan"),
                    placement_layout_path=item.get("placement_layout_path"),
                )[item["select"]]["obj"]
            else:
                raise ValueError(item["command"])
            regen = hashing.sha256_bytes(
                hashing.canonical_json_bytes(obj))
            ok = (disk_sha == regen)
            rows.append({"product": item["product"],
                         "command": item["command"],
                         "disk_sha256": disk_sha, "regen_sha256": regen,
                         "byte_exact": ok})
        except Exception as exc:  # 重放失败=如实记录，不静默
            rows.append({"product": item["product"],
                         "command": item["command"],
                         "disk_sha256": disk_sha, "regen_sha256": None,
                         "byte_exact": False, "error": str(exc)[:200]})
    pins = []
    for name, pin in sorted(FC2_DOUBLE_SEND_PINS.items()):
        disk = _fsha(FC2_DIR + "/" + name)
        pins.append({"product": FC2_DIR + "/" + name,
                     "pin_sha256": pin["sha256"], "disk_sha256": disk,
                     "matches_pin": disk == pin["sha256"],
                     "rerun": pin["rerun"], "evidence": pin["evidence"]})
    for name, pin in sorted(FC1_FROZEN_PINS.items()):
        disk = _fsha(FC1_DIR + "/" + name)
        pins.append({"product": FC1_DIR + "/" + name,
                     "pin_sha256": pin["sha256"], "disk_sha256": disk,
                     "matches_pin": disk == pin["sha256"],
                     "rerun": pin["rerun"], "evidence": pin["evidence"]})
    all_ok = (all(r.get("byte_exact") for r in rows)
              and all(p["matches_pin"] for p in pins))
    return {
        "schema_version": FD1_SCHEMA,
        "artifact_kind": "signoff_replay",
        "spec_ref": "SPEC v1.3 §12.2",
        "convention": "重放比较规范化核心产物 hash；run-manifest（wall-clock/"
                      "主机）属元数据不参与（§12.2/HANDOFF §4）",
        "regenerated": rows,
        "double_send_pins": pins,
        "all_byte_exact": all_ok,
    }


# ---- §12 签核包 -----------------------------------------------------------------
def _drc_ledger_entries(fc2_dir=FC2_DIR):
    files = ["baseline-all.json", "batch-1.json", "batch-2.json",
             "batch-3.json", "batch-4.json", "batch-5.json",
             "batch-6.json", "final-all.json"]
    out = []
    for n in files:
        e = _entry(fc2_dir + "/drc/" + n, "erc_drc_raw")
        if e["status"] == "present":
            e["status"] = "present"
        out.append(e)
    return out


def build_package(out_dir_rel=FD1_OUT_DEFAULT, fc2_dir=FC2_DIR,
                  ff_plan_dir=None, check_dir=None,
                  approvals_dir=None):
    """FD1 签核包 §12 清单逐项；缺项 not_available+原因。known-open 由
    ⑤/FC2 产物如实带入。

    FD2 adoption（计划 snapshot 带 structures_override_sha256）：① 转正后
    structures 段=已批权威（override 对读），known_open 去除 structures 条目；
    阻抗重算产物随 constraints 段列账（TBD-1 义务保留）。节级状态由
    entries 逐条推导（REPAIR-P2 W-3 / SEC-A-01+02：任一 entry 缺失 ⇒
    "missing"，杜绝恒真）。"""
    ff_plan_dir = ff_plan_dir or FF1_DIR
    check_dir = check_dir or CHECK_DIR
    items = []
    plan = None
    plan_rel = ff_plan_dir + "/feedforward-plan.json"
    if os.path.exists(_p(plan_rel)):
        with open(_p(plan_rel), encoding="utf-8") as f:
            plan = json.load(f)
    structures_approved = bool(
        (plan or {}).get("snapshot", {}).get("structures_override_sha256"))

    def add(item, entries, note=None, status=None):
        # 节级状态由 entries 逐条推导（REPAIR-P2 W-3 / SEC-A-01+02）：
        # - entries 非空：全部 present 才可取声明状态（或缺省 present）；
        #   任一 entry 缺失（部分或全部）⇒ "missing"（任一文件在场即
        #   present 的旧行为会掩盖缺件，且词表里 "missing" 从不出现、
        #   build_envelope 的 missing 判定成死条件 ⇒ package_complete 恒真）。
        # - entries 为空：设计内声明节（SI/PI 外部未接入 not_available、
        #   advisory empty_by_design），保留声明状态。
        row = {"item": item, "entries": entries}
        if entries:
            if all(e.get("status") == "present" for e in entries):
                row["status"] = (status or "present")
            else:
                row["status"] = "missing"
        else:
            row["status"] = (status or "not_available")
        if note:
            row["note"] = note
        items.append(row)

    imp_rerun_rel = out_dir_rel + "/impedance-targets.json"
    imp_entries = [_entry(A3_DIR + "/impedance_targets.json", "authority")]
    if structures_approved:
        imp_entries.append(_entry(imp_rerun_rel, "authority_rerun_basis"))
    add("constraints final snapshot",
        [_entry(A3_DIR + "/constraints.json", "authority"),
         _entry(A3_DIR + "/coverage.json", "authority"),
         *imp_entries],
        note="约束库终态（60 条；⓪ 门 pass；A 期权威）"
             + ("；叠层基面重算（JLC04161H-7628，一阶预估；TBD-1 定稿义务"
                "保留）已列账" if structures_approved else ""))
    if structures_approved:
        add("structures snapshot",
            [_entry(A3_DIR + "/structures.json", "authority"),
             {"path": "out/revc-fd1/approvals/structures.override.json",
              "role": "authority_approval",
              "status": ("present" if os.path.exists(
                  _p("out/revc-fd1/approvals/structures.override.json"))
                  else "missing"),
              "sha256": _fsha("out/revc-fd1/approvals/"
                              "structures.override.json")}],
            note="已批（override 转正，2026-08-30 会话消费）：草案+STR-1/2 "
                 "对读为权威；草案文件冻结零修改（确认点 #1/#2 关闭）",
            status="present")
    else:
        add("structures snapshot",
            [_entry(A3_DIR + "/structures.json", "authority_pending")],
            note="authority_status=draft：确认点 #1 未批 → ① 类结论不得进签核正文"
                 "（确认点 #1 沿留）",
            status="present_unapproved")
    add("net-registry snapshot",
        [_entry(A3_DIR + "/net-registry.json", "authority"),
         _entry(A3_DIR + "/net-identity-map.json", "authority")],
        note="逐网只读编译视图（registry_snapshot_hash 绑定随 FF 计划/⑤⑥ 产物）")
    add("coverage",
        [_entry(A3_DIR + "/coverage-structures.json", "authority")],
        note="① 全量覆盖账本")
    add("feedforward-plan",
        [_entry(ff_plan_dir + "/feedforward-plan.json", "planning_appendix")],
        note="planning_advisory：只进附录，不进签核正文（§12 正文条款）")
    add("feedforward residuals",
        [_entry(check_dir + "/ff-residuals.json", "planning_appendix"),
         _entry(check_dir + "/check-report.json", "check_stage")],
        note="⑤ §11.2 残差（not_available 项如实随包）")
    cons_entries = [_entry(A3_DIR + "/audit.json", "consumer_2_first"),
                    _entry(FF2_DIR + "/ff-consumption.json", "consumer_3_ff4"),
                    _entry(FC1_DIR + "/route-consumption.json",
                           "consumer_4_route")]
    cons_cas1 = ((plan or {}).get("snapshot", {}).get("placement_basis")
                 == "it_adopted_cascade")
    if cons_cas1:
        cons_entries.append(_entry(ff_plan_dir + "/route-consumption.json",
                                   "consumer_4_route_cas1"))
    add("consumer evidence", cons_entries,
        note=("② 首消费者 + ③ FF-4（NEXT #6 已批）+ ④ route 消费（planning_"
              "advisory）；④ 控制升级 gate 已批（consumer-gate-4.json），"
              "实现排建造会话（未实现前 controls 保持 planning_advisory）；"
              "CAS1 级联 ④ 消费随包（route-consumption.json，consumer_4_"
              "route_cas1，绑定 FF-REVC-0004）"
              + ("；确认点 #4 已批（placement 绑定=采纳快照）"
                 if cons_cas1 else "")
              if structures_approved else
              "② 首消费者 + ③ FF-4（NEXT #6 已批）+ ④ route 消费（planning_"
              "advisory）；④ 控制升级 consumer gate 未消费（NEXT #7 沿留）"))
    add("ERC/DRC raw reports and diffs", _drc_ledger_entries(fc2_dir),
        note="kicad-cli authority 报告（hash 输入；batch severity-error / "
             "终检 severity-all 分列）")
    add("SI/PI/thermal/DFM/external reports", [],
        note=("not_available：外部签核工具未接入（toolchain_lock 仅 kicad 工具族）；"
              "能力/叠层/电流三源已由 FD2 级联重跑消费（via 供给 derived 上界/"
              "5V_USB sourced+11 轨 derived 政策/阻抗基面重算）；正式阻抗/电流"
              "定稿仍需板厂叠层表+BOM 功耗数据→生产签核前置条件未满足"
              if structures_approved else
              "not_available：外部签核工具未接入（toolchain_lock 仅 kicad 工具族）；"
              "嘉立创能力表/叠层/接口电流源已登记（out/revc-fd1/approvals/sources/，"
              "规划基面）待 FF 级联重跑消费；正式阻抗/电流定稿仍需板厂叠层表+BOM "
              "功耗数据→生产签核前置条件未满足"),
        status="not_available")
    add("waiver ledger", [_entry(out_dir_rel + "/waiver-ledger.json",
                                 "ledger")],
        note=("approved/candidates 见 waiver-ledger.json（批准输入="
              "approvals/waiver-approvals.json；确认点 #5；WV-0004 附带制板前 "
              "81 条 silk 逐条复审义务）" if structures_approved else
              "approved=[]；candidates 待人工逐条批准（确认点 #5）"))
    add("replay result", [_entry(out_dir_rel + "/signoff-replay.json",
                                 "replay")],
        note="§12.2 规范化核心产物 hash 重放（FC2=双发基准 pin；fc1 "
             "route-plan=④ 升级后冻结 pin，重放改指 fc3）")
    add("advisory appendix", [],
        note="视觉 advisory=空（视觉轨道未指派，HANDOFF §2；advisory_only "
             "不进正文）",
        status="empty_by_design")
    add("toolchain lock and hashes",
        [_entry("toolchain_lock.json", "authority")],
        note="kicad-cli 10.0.5 锁定；实现 hash 随 run-manifest（元数据）")

    # 已知未过项（HANDOFF §5：如实列出）
    known_open = []
    check_report = None
    cr_rel = check_dir + "/check-report.json"
    if os.path.exists(_p(cr_rel)):
        with open(_p(cr_rel), encoding="utf-8") as f:
            check_report = json.load(f)
    if check_report:
        for r in check_report["results"]:
            if r.get("verdict") == "fail":
                known_open.append({
                    "source": "⑤ check-report",
                    "checker_id": r["checker_id"],
                    "detail": {"unconnected_items":
                               r.get("unconnected_items"),
                               "new_vs_baseline":
                               r.get("unconnected_new_vs_baseline")},
                    "note": "dry-run 已知开放项（④ 55/61 committed）"})
    certs_rel = fc2_dir + "/residual-certs.json"
    if os.path.exists(_p(certs_rel)):
        with open(_p(certs_rel), encoding="utf-8") as f:
            certs = json.load(f)
        c = certs.get("counts") or {}
        known_open.append({
            "source": "④ FC2 靶 1",
            "detail": {"UNSAT": c.get("UNSAT"), "UNKNOWN": c.get("UNKNOWN"),
                       "unsat_without_certificate":
                           certs.get("unsat_without_certificate")},
            "note": "UNSAT 全证书 verified；UNKNOWN=region_over_window 如实"
                    "（无 proof 不写 UNSAT）"})
    replay_rel = fc2_dir + "/replay-plan.json"
    if os.path.exists(_p(replay_rel)):
        with open(_p(replay_rel), encoding="utf-8") as f:
            replay = json.load(f)
        d = replay.get("definition") or {}
        if d.get("committed") != d.get("denominator"):
            known_open.append({
                "source": "④ FC2 靶 2",
                "detail": {"committed": d.get("committed"),
                           "denominator": d.get("denominator"),
                           "planned_sat": d.get("planned_sat")},
                "note": "未落板网=已知开放项；2 网顺序规划失败=UNKNOWN"
                        "（no_witness_no_certificate）"})
    structures = None
    st_rel = A3_DIR + "/structures.json"
    if os.path.exists(_p(st_rel)):
        with open(_p(st_rel), encoding="utf-8") as f:
            structures = json.load(f)
    if not structures_approved and \
            (structures or {}).get("authority_status") != "approved":
        known_open.append({
            "source": "① structures",
            "detail": {"authority_status":
                       (structures or {}).get("authority_status")},
            "note": "确认点 #1 未批 → ① 类结论不进签核正文"})

    # 正文四要素（§12 正文条款）
    body = {
        "constraints_final": True,
        "kicad_erc_drc_authority": True,
        "external_signoff": False,
        "human_approval": False,
        "statement": "正文=约束库终态 + KiCad ERC/DRC authority（dry-run 口径）；"
                     "外部签核与人工批准未到位 → 本包为 dry-run 签核包，"
                     "非生产签核（§12）",
    }
    return {
        "schema_version": FD1_SCHEMA,
        "artifact_kind": "signoff_package",
        "spec_ref": "SPEC v1.3 §12/§15-FD1",
        "project": "stm32h743-coreboard-revc（回测板；全程只读快照/副本）",
        "mode": "dry_run（Rev-C 快照副本演练；live 板零写）",
        "sections": items,
        "signoff_body": body,
        "known_open": known_open,
        "known_open_note": "已知未过项如实列出（HANDOFF §5）；UNKNOWN 不写 "
                           "UNSAT；前馈赤字不自动 waiver",
    }


def _plan_snapshot(ff_dir_rel):
    """读 FF 计划文件 snapshot（无文件→空 dict；重放/envelope 输入派生用）。"""
    plan_rel = _p(ff_dir_rel + "/feedforward-plan.json")
    if not os.path.exists(plan_rel):
        return {}
    with open(plan_rel, encoding="utf-8") as f:
        return (json.load(f).get("snapshot") or {})


def _adopt_replay_extras(ff_dir_rel, consume_bom=False):
    """FD2 adoption 重放附加项：adopt 口径核心 FF 产物（重生成对比）。
    基准=FF 计划所在目录（fc3-D5）：fd2 场景 out_dir==ff_dir 字节不变；
    ⑥ 重发到其他目录（fc3）时 FF 行仍指 adoption 权威目录，不复制产物。
    consume_bom=True（FF3）：重放也按 BOM 消费口径重生成。
    CAS1（计划 snapshot.placement_basis=it_adopted_cascade）：FF 重放携带
    placement 绑定参数；route 重放绑级联计划+采纳布局（§9.4 转换证明闭环）。
    FF5（计划 snapshot.bom_power_source_path）：FF 重放携带 rail 源覆盖路径
    （计划=单一事实源，signoff 侧不设独立旗标）。"""
    items = [{"product": ff_dir_rel + "/" + name, "command": "feedforward",
              "select": sel, "out_dir": ff_dir_rel, "adopt_override": True,
              "consume_bom": bool(consume_bom)}
             for name, sel in (("feedforward-plan.json", "plan"),
                               ("feedforward-coverage.json", "coverage"),
                               ("feedforward-comparison.json", "comparison"),
                               ("impedance-targets.json", "impedance_targets"))]
    snap = _plan_snapshot(ff_dir_rel)
    if snap.get("bom_power_source_path"):
        for it in items:
            it["bom_power_file"] = snap["bom_power_source_path"]
    if snap.get("placement_basis") == "it_adopted_cascade":
        for it in items:
            it["placement_csv_path"] = snap.get("adopted_placement_path")
            it["placement_layout_path"] = snap.get("adopted_layout_path")
        items += [
            {"product": ff_dir_rel + "/route-plan.json", "command": "route",
             "select": "route_plan", "out_dir": ff_dir_rel,
             "feedforward_plan": ff_dir_rel + "/feedforward-plan.json",
             "placement_layout_path": snap.get("adopted_layout_path")},
            {"product": ff_dir_rel + "/route-consumption.json",
             "command": "route", "select": "consumption",
             "out_dir": ff_dir_rel,
             "feedforward_plan": ff_dir_rel + "/feedforward-plan.json",
             "placement_layout_path": snap.get("adopted_layout_path")},
        ]
    return tuple(items)


def build_envelope(out_dir_rel=FD1_OUT_DEFAULT, fc2_dir=FC2_DIR,
                   ff_plan_dir=None, check_dir=None,
                   approvals_dir=None, adopt_override=False,
                   consume_bom=False):
    """FD1 签核 envelope 总装：package+wavier 台账+重放三源 → gate 判定。

    编排=build_package（§12 节清单）+build_waiver_ledger（豁免台账）+
    build_replay（重放证据；adopt_override/consume_bom 追加对应 extra）；
    gate.package_complete 由 missing 节推导（恒真缺陷已修，SEC-A-01），
    production_signoff_ready 维持设计恒 False（外部证据未接，P5 成文）。
    rail 源路径自计划 snapshot 派生（FF5；无键→fd3 钉源缺省）。
    """
    ff_plan_dir = ff_plan_dir or FF1_DIR
    check_dir = check_dir or CHECK_DIR
    # FF5：rail 源路径从计划 snapshot 派生（fd3/cas1 计划无此键→缺省 fd3 钉源，
    # 历史目录 envelope 字节不变）
    bom_src = (_plan_snapshot(ff_plan_dir or out_dir_rel)
               .get("bom_power_source_path")) if consume_bom else None
    pkg = build_package(out_dir_rel, fc2_dir, ff_plan_dir, check_dir,
                        approvals_dir)
    ledger = build_waiver_ledger(out_dir_rel, fc2_dir, approvals_dir)
    extra_replay = (_adopt_replay_extras(ff_plan_dir or out_dir_rel,
                                         consume_bom=consume_bom)
                    if adopt_override else ())
    replay = build_replay(out_dir_rel, extra_replay)
    missing = [s["item"] for s in pkg["sections"]
               if s["status"] == "missing"]
    gate = {
        "spec_ref": "HANDOFF FD1/SPEC §12/§15-FD1",
        "package_complete": not missing,
        "missing_sections": missing,
        "replay_all_byte_exact": replay["all_byte_exact"],
        "waiver_approved_count": len(ledger["approved"]),
        "waiver_candidates_pending": len(ledger["candidates"]),
        "structures_approved": any(
            s["item"] == "structures snapshot"
            and s["status"] == "present"
            for s in pkg["sections"]) and not any(
            k.get("source") == "① structures" for k in pkg["known_open"]),
        "external_signoff_available": any(
            s["item"] == "SI/PI/thermal/DFM/external reports"
            and s["status"] == "present" for s in pkg["sections"]),
        "dry_run_package_ok": None,   # 下面赋值
        "production_signoff_ready": False,
    }
    gate["dry_run_package_ok"] = (gate["package_complete"]
                                  and gate["replay_all_byte_exact"])
    diagnostics = []
    if not gate["package_complete"]:
        diagnostics.append({"id": "package_missing_sections",
                            "title": "签核包缺项：%s"
                                     % ",".join(gate["missing_sections"])})
    if not gate["replay_all_byte_exact"]:
        diagnostics.append({"id": "replay_mismatch",
                            "title": "§12.2 重放存在 byte_exact=false 项"})
    if gate["structures_approved"]:
        diagnostics += [
            {"id": "production_blocked_on_human",
             "title": "生产签核 readiness=false：外部签核未接入 + 生产正文人工"
                      "批准未发生（§12 正文条款）；WV-0004 附带制板前 81 条 "
                      "silk_over_copper 逐条复审义务；确认点 #1/#5 已批关闭"},
            {"id": "known_open_listed",
             "title": "已知未过项如实列入 known_open（CHK-CONN 303 unconnected/"
                      "UNSAT 40 证书化/UNKNOWN 13 超窗/未落板 6）"},
            {"id": "fd2_adoption",
             "title": "FD2 级联重跑包：structures.override 权威生效 + FF/⑤⑥ "
                      "受影响阶段重跑；②③④ 冻结件零改动（adoption check）"},
        ] + ([{"id": "fd3_bom_consumption",
               "title": "FF3 级联重跑包：BOM 派生轨功耗表 derived 消费（rail "
                        "供给 sourced/derived 分列）；重放/包输入按 consume_bom "
                        "口径"}] if consume_bom else [])
    else:
        diagnostics += [
            {"id": "production_blocked_on_human",
             "title": "生产签核 readiness=false：确认点 #1（structures）/#5"
                      "（waivers 逐条）待人工 + 外部签核未接入（§12 正文条款；"
                      "不代办的确认点 HANDOFF §3）"},
            {"id": "known_open_listed",
             "title": "已知未过项如实列入 known_open（CHK-CONN 303 unconnected/"
                      "UNSAT 40 证书化/UNKNOWN 13 超窗/未落板 6/structures "
                      "draft）"},
        ]
    status = "ok" if gate["dry_run_package_ok"] else (
        "unknown" if not gate["package_complete"] else "failed")
    verdict = ("pass" if status == "ok" else
               "yellow" if status == "unknown" else "fail")
    inputs = []
    for rel, role in (
            (check_dir + "/check-report.json", "check_stage"),
            (check_dir + "/ff-residuals.json", "ff_residuals"),
            (check_dir + "/waiver-ledger.json", "waiver_ledger"),
            (check_dir + "/signoff-replay.json", "replay"),
            (fc2_dir + "/residual-certs.json", "fc2_target1"),
            (fc2_dir + "/replay-plan.json", "fc2_target2"),
            (ff_plan_dir + "/feedforward-plan.json", "ff_plan_appendix")):
        sha = _fsha(rel)
        if sha:
            inputs.append({"path": rel, "sha256": sha, "role": role})
    if adopt_override:
        for rel, role in (
                ("out/revc-fd1/approvals/structures.override.json",
                 "structures_override"),
                ("out/revc-fd1/approvals/waiver-approvals.json",
                 "waiver_approvals"),
                (out_dir_rel + "/impedance-targets.json",
                 "impedance_rerun")):
            sha = _fsha(rel)
            if sha:
                inputs.append({"path": rel, "sha256": sha, "role": role})
    if consume_bom:
        eff_rel = bom_src or FD3_BOM_POWER_REL
        sha = _fsha(eff_rel)
        if sha:
            inputs.append({"path": eff_rel, "sha256": sha,
                           "role": "bom_power_derive"})
    return {
        "schema_version": FD1_SCHEMA,
        "tool": "pcbflow", "tool_version": config.TOOL_VERSION,
        "command": "signoff", "command_kind": "core",
        "status": status, "verdict": verdict,
        "deterministic": True, "determinism_claim": "byte_exact",
        "inputs": inputs, "config_sha256": None,
        "spec_refs": ["tools/pcbflow/SPEC.md#§12",
                      "tools/pcbflow/SPEC.md#§15-FD1",
                      "tools/pcbflow/SPEC.md#§17.4"],
        "artifacts": [
            {"path": out_dir_rel + "/signoff-package.json", "role": "core"},
            {"path": out_dir_rel + "/waiver-ledger.json", "role": "core"},
            {"path": out_dir_rel + "/signoff-replay.json", "role": "core"},
            {"path": out_dir_rel + "/signoff-report.md",
             "role": "human_report"},
        ],
        "metrics": {
            "sections": len(pkg["sections"]),
            "known_open": len(pkg["known_open"]),
            "waiver_candidates": len(ledger["candidates"]),
            "replay": ({"regenerated": len(replay["regenerated"]),
                        "double_send_pins": len(replay["double_send_pins"]),
                        "all_byte_exact": replay["all_byte_exact"]}),
            "production_signoff_ready": gate["production_signoff_ready"],
            **({} if not gate["structures_approved"] else
               {"adoption": ("FD3（structures_override 权威生效+BOM 派生轨表"
                             "消费；FF/⑤⑥ 重跑）" if consume_bom else
                             "FD2（structures_override 权威生效；FF/⑤⑥ 重跑）")}),
        },
        "diagnostics": diagnostics,
        "waivers": ledger["approved"],
        "solver": {},
        "run_metadata": {},
        "data": {"gate": gate},
    }


def build_report_md(env, pkg, ledger, replay, session_tag="FD1"):
    g = env["data"]["gate"]
    lines = ["# PCBFlow ⑥ 终检与签核报告（%s，dry-run）" % session_tag, "",
             "- 门 verdict：%s；status：%s（dry-run 包；生产签核 readiness=%s）"
             % (env["verdict"], env["status"],
                env["metrics"]["production_signoff_ready"]),
             "- mode：%s" % pkg["mode"], "",
             "## 签核包清单（§12）", "",
             "| 条目 | status | 说明 |", "|---|---|---|"]
    for s in pkg["sections"]:
        lines.append("| %s | %s | %s |"
                     % (s["item"], s["status"],
                        (s.get("note") or "")[:70]))
    lines += ["", "## 签核正文（§12 正文条款）", ""]
    for k, v in sorted(pkg["signoff_body"].items()):
        lines.append("- %s：`%s`" % (k, v))
    lines += ["", "## 已知未过项（如实列出）", ""]
    for k in pkg["known_open"]:
        lines.append("- %s：%s（%s）"
                     % (k["source"], json.dumps(k["detail"],
                                                ensure_ascii=False),
                        k["note"]))
    lines += ["", "## waiver 台账（§12.1；批准=确认点 #5 消费）", "",
              "- approved：%d 条（批准输入=%s）"
              % (len(ledger["approved"]),
                 (ledger.get("approvals_input") or {}).get("path")
                 or "无（批准前恒空）")]
    for a in ledger["approved"]:
        lines.append("- %s：%s（approver=%s；expiry=%s）"
                     % (a["waiver_id"], a["reason"][:60],
                        a.get("approver"), a.get("expiry")))
    for d in ledger.get("approval_drift") or []:
        lines.append("- 漂移（未合并）：候选 %s：%s"
                     % (d["candidate_index"], d["reason"]))
    lines.append("- 未决候选 %d 条（赤字不入候选）" % len(ledger["candidates"]))
    lines += ["", "## 重放（§12.2）", ""]
    for r in replay["regenerated"]:
        lines.append("- %s：byte_exact=%s" % (r["product"],
                                              r.get("byte_exact")))
    for p in replay["double_send_pins"]:
        lines.append("- %s：matches_pin=%s（双发基准）"
                     % (p["product"], p["matches_pin"]))
    lines += ["", "## 门", ""]
    for k, v in sorted(g.items()):
        lines.append("- %s：`%s`" % (k, v))
    lines += ["", "人读视图非事实源；核心产物见 signoff-package/waiver-ledger/"
              "signoff-replay。", ""]
    return "\n".join(lines)


def build_products(select="summary", out_dir_rel=FD1_OUT_DEFAULT,
                   fc2_dir=FC2_DIR, ff_plan_dir=None, check_dir=None,
                   approvals_dir=None, adopt_override=False,
                   consume_bom=False, session_tag="FD1"):
    ff_plan_dir = ff_plan_dir or FF1_DIR
    check_dir = check_dir or CHECK_DIR
    import datetime

    t0 = datetime.datetime.now(datetime.timezone.utc)
    if select == "package":
        return {"payload": {"obj": build_package(out_dir_rel, fc2_dir,
                                                 ff_plan_dir, check_dir,
                                                 approvals_dir)},
                "kind": "json"}
    if select == "waiver_ledger":
        return {"payload": {"obj": build_waiver_ledger(out_dir_rel, fc2_dir,
                                                       approvals_dir)},
                "kind": "json"}
    if select == "replay":
        extra = (_adopt_replay_extras(ff_plan_dir or out_dir_rel,
                                      consume_bom=consume_bom)
                 if adopt_override else ())
        return {"payload": {"obj": build_replay(out_dir_rel, extra)},
                "kind": "json"}
    if select == "envelope":
        env = build_envelope(out_dir_rel, fc2_dir, ff_plan_dir, check_dir,
                             approvals_dir, adopt_override,
                             consume_bom=consume_bom)
        return {"payload": {"obj": env}, "kind": "json"}
    if select == "run_manifest":
        t1 = datetime.datetime.now(datetime.timezone.utc)
        manifest = {
            "started_at": t0.isoformat(), "finished_at": t1.isoformat(),
            "elapsed_s": round((t1 - t0).total_seconds(), 3),
            "python_version": __import__("sys").version.split()[0],
            "tool_version": config.TOOL_VERSION,
            "command": "signoff", "out_dir": out_dir_rel,
            "spec_sha256": hashing.sha256_file(
                os.path.join(config.PCBFLOW_ROOT, "SPEC.md")),
        }
        return {"payload": {"obj": manifest}, "kind": "json"}
    if select == "report":
        env = build_envelope(out_dir_rel, fc2_dir, ff_plan_dir, check_dir,
                             approvals_dir, adopt_override,
                             consume_bom=consume_bom)
        pkg = build_package(out_dir_rel, fc2_dir, ff_plan_dir, check_dir,
                            approvals_dir)
        ledger = build_waiver_ledger(out_dir_rel, fc2_dir, approvals_dir)
        extra = (_adopt_replay_extras(ff_plan_dir or out_dir_rel,
                                      consume_bom=consume_bom)
                 if adopt_override else ())
        replay = build_replay(out_dir_rel, extra)
        return {"payload": build_report_md(env, pkg, ledger, replay,
                                           session_tag).encode("utf-8"),
                "kind": "bytes"}
    # summary
    env = build_envelope(out_dir_rel, fc2_dir, ff_plan_dir, check_dir,
                         approvals_dir, adopt_override,
                         consume_bom=consume_bom)
    return {"payload": {"obj": {
        "command": "signoff", "status": env["status"],
        "verdict": env["verdict"], "metrics": env["metrics"],
        "gate": env["data"]["gate"], "diagnostics": env["diagnostics"],
        "note": "人读视图非事实源；核心产物见 signoff-package/waiver-ledger/"
                "signoff-replay；waiver 批准=确认点 #5（禁代办）",
    }}, "kind": "json"}
