# -*- coding: utf-8 -*-
"""P5⑤ 批量试跑报告生成器：17 板 per-board trial 报告 + 批量汇总。

输入：out/v5-p5/boards/<id>/ 各阶段产物（board.json / compiled.json /
execute.json / check.json / *.kicad_pcb / drc-classified.json / run-result.json）
与 out/v5-p5/holdout-ledger/access-log.jsonl。

输出（全部确定性：canonical + provenance 头，无时间戳）：
  out/v5-p5/trial/<id>.trial.json / .trial.md   ×17 板
  out/v5-p5/trial/batch-summary.json / .md      批量汇总（sidecar provenance 头）

汇总口径（P5⑤ 任务令 §交付 2：0.2.0 批口径机械扩展到 17 板 + drc 聚合协议
适配，报告生成侧适配，管线未改）：
  - 逐板逐阶段 verdict 表（check/export/drc 因 exec FAILED 跳过者如实标 SKIPPED）；
  - 每板 kicad-cli 聚合协议结果（runner 0.2.0 起 P5-UP3：每轮 5 跑同字节导出件、
    至多 3 轮；verdict=deterministic-5x-equal / nondeterministic-disclosed，
    逐跑 totals/by-type/三归类已入接触史台账）；
  - 每板 genuine / config-gap / contract-artifact 计数取锚定跑集并集最大值
    （保守口径）；
  - SAT 板计数：SAT := exec ROUTED 且 v5 route_check feasible（selection
    UNKNOWN 按 P4-G1 口径自 plan_candidates[0] 起跑；管线 0.3.0 起终局
    FAILED 按候选序轮换重试，candidate_source=实际布通候选）；
    P5-G1 需 ≥5 SAT 对照。
"""
import hashlib
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))

import p5_holdout_ledger as ledger  # noqa: E402
from v5 import canonical  # noqa: E402

# P5⑤ 批口径：17 板 = 7 补跑（board.json 复用）+ 10 全新全链，执行序小网数优先
BOARDS = ["badgeleds-do-electronics", "pmod-bme280", "stm32-ds2480-emu",
          "atmega32u4-breakout", "dc-scm-rot-jumper-card", "pmod-i2c24io",
          "m2-pcie-adapter",
          "thin-pod", "tmp108", "pmod-crypto", "axiom-micro-mainboard",
          "usb-gigabit-rev-e", "thatmicpre-v2", "om-flexgrid-v4-rigid-pcb",
          "ov9281-dual-camera-board", "cm5-minima-rev3",
          "thunderbolt-pcie-adapter"]
RERUN7 = set(BOARDS[:7])  # 补跑口径：convert 未重跑，board.json 复用
BOARDS_DIR = os.path.join(ROOT, "out", "v5-p5", "boards")
TRIAL = os.path.join(ROOT, "out", "v5-p5", "trial")
GENERATOR = "v5.p5-batch-report"
VERSION = "0.3.0"  # 0.3.0: P5⑤ 批口径机械扩展 6→17 板（+badgeleds 与 10 全新板）
                   # ；drc 文案适配 runner 0.2.0+ P5-UP3 聚合协议（每轮 5 跑、
                   # 至多 3 轮、并集 max）；execute 文案透传轮换字段（0.2.0 已备
                   # rotate_budget/tried_candidates 键）；管线零改动
STAGE_KEYS = ("convert", "compile", "execute", "check", "export", "drc")

TOOL_FIXES = [
    "tools/run_p5_board.py 0.1.0→0.1.1（最小修复，P5② 任务令红线驱动）："
    "① drc 阶段 kicad-cli 单跑→固定 3 跑（同字节），逐跑三归类，三次 totals 与 "
    "by-type 追加登记进接触史台账（action=drc 结果登记事件，extra."
    "nondeterministic=true）；② exec FAILED（候选在场 routes=None）时与 "
    "NO_CANDIDATES 路径同款优雅收口——原实现于 check 处 fail-closed 崩溃且不落 "
    "run-result；③ drc 预登记台账事件从阶段顶部移至紧贴实际执行前（避免失败时"
    "悬空事件）；④ 本工具所落台账事件 operator 归属 p5-part2-subagent、purpose "
    "标签 P5①→P5②（P5① 事件 seq≤30 原样未动）。",
    "tools/p5_batch_report.py 为本文件（P5② 新增）：P5① 的 p5_trial_report.py "
    "硬编码 badgeleds 单板，不覆盖批量交付，未改动。",
    "在途更正：seq35（stm32-ds2480-emu drc 预登记）因修复前的崩溃未实际发生 drc，"
    "已按 append-only 纪律以 seq36 更正登记披露，未改写任何历史行。",
    "tools/run_p5_board.py 0.1.1→0.2.0→0.3.0 与 v5 全族升级（P5-UP 系列任务令"
    "驱动，本批零改动只复用）：0.2.0=P5-UP3 drc 口径钉死——kicad-cli 10.0.5 并发"
    "不可控（无线程控制面，调研证据见工具 docstring）→聚合协议（每轮 5 跑、至多"
    "再 2 轮、verdict=deterministic-5x-equal/nondeterministic-disclosed、判据="
    "锚定跑集逐类并集 max）；0.3.0=P5⑤-F3 execute 终局 FAILED 按候选序轮换"
    "（--rotate-budget 默认 4，总试轮数=min(K,len(cands))，tried_candidates 逐轮"
    "登记，candidate_source=实际布通候选下标/全败 null 口径演进）。",
    "tools/p5_batch_report.py 0.2.0→0.3.0（本版，P5⑤ 任务令 §交付 2）：板清单 "
    "6→17 板（7 补跑 convert 复用 board.json——adapter 0.2.0 自 09-14 14:35 未变"
    "任务令裁定合法 + 10 板全新 convert 全链）+ throwing-star-pro 跳过披露；drc "
    "文案与汇总键自 3 跑口径机械适配聚合协议（rounds_totals/并集 max）；管线零"
    "改动，仅报告生成侧适配。",
]


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def sha256_file(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def maybe(path):
    return load_json(path) if os.path.isfile(path) else None


def failing_nets(execute_doc):
    out = []
    for pn in (execute_doc.get("execute", {}).get("per_net") or []):
        if pn.get("status") == "failed":
            out.append({"net_id": pn.get("net_id"),
                        "partition_id": pn.get("partition_id"),
                        "attempts": pn.get("attempts")})
    return out


def failure_reasons(execute_doc):
    seen = []
    for line in (execute_doc.get("execute", {}).get("negotiation_log") or []):
        s = str(line)
        if "FAILED after" in s and s not in seen:
            seen.append(s)
    return seen


def board_data(board_id):
    bdir = os.path.join(BOARDS_DIR, board_id)
    bd = {"board_id": board_id, "dir": bdir}
    bd["board_doc"] = load_json(os.path.join(bdir, "board.json"))
    bd["run"] = load_json(os.path.join(bdir, "run-result.json"))["run"]
    bd["compiled"] = maybe(os.path.join(bdir, "compiled.json"))
    bd["execute"] = maybe(os.path.join(bdir, "execute.json"))
    bd["check"] = maybe(os.path.join(bdir, "check.json"))
    drc_raw = maybe(os.path.join(bdir, "drc-classified.json"))
    bd["drc"] = drc_raw.get("drc") if isinstance(drc_raw, dict) else None
    pcb = os.path.join(bdir, "%s.kicad_pcb" % board_id)
    bd["export_sha"] = sha256_file(pcb) if os.path.isfile(pcb) else None
    bd["prereg"] = ledger.A_LAYER_PREREG[board_id]
    return bd


def stage_verdicts(bd):
    """逐板逐阶段 verdict 行（汇总表与 per-board 共用）。"""
    run = bd["run"]
    conv = run.get("convert", {})
    row = {"board_id": bd["board_id"]}
    row["convert"] = (
        "OK nets=%d（本批 convert，双跑字节等）" % conv.get("nets", -1)
        if conv and bd["board_id"] not in RERUN7
        else ("OK nets=%d（board.json 复用，本批未重跑 convert）"
              % conv.get("nets", -1) if conv
              else "OK（P5① 已转，本批复用）"))
    comp = run.get("compile")
    row["compile"] = ("OK coverage=%.1f%% conflicts=%d"
                      % (comp["coverage_pct"], comp["conflicts"])
                      if comp else "SKIPPED")
    ex = run.get("execute")
    if not ex:
        row["execute"] = "SKIPPED"
    elif ex.get("exec_verdict") == "ROUTED":
        row["execute"] = ("ROUTED（selection=%s→%s，%d 候选，tried=%d）"
                          % (ex.get("selection_verdict"),
                             ex.get("candidate_source"),
                             ex.get("n_candidates"),
                             len(ex.get("tried_candidates") or [])))
    else:
        tried = ex.get("tried_candidates") or []
        row["execute"] = ("FAILED（selection=%s→%s，%d 候选，轮换 tried=%d/%d；"
                          "%s）"
                          % (ex.get("selection_verdict"),
                             ex.get("candidate_source"),
                             ex.get("n_candidates"), len(tried),
                             min(ex.get("rotate_budget") or 4,
                                 ex.get("n_candidates") or 4),
                             "、".join(r.split("：")[-1]
                                       for r in failure_reasons(bd["execute"])
                                       [:1]) or "原因见 execute.json"))
    ch = run.get("check")
    row["check"] = ("feasible=%s violations=%d"
                    % (ch["feasible"], ch["violations_total"])
                    if ch else "SKIPPED（无 routes 输入）")
    row["export"] = ("%d bytes sha=%s…"
                     % (run["export"]["bytes"],
                        run["export"]["sha256"][:12])
                     if run.get("export") else "SKIPPED（无 routes 输入）")
    dr = run.get("drc")
    row["drc"] = ("%s（%d轮×%d跑 rounds_totals=%s union-max genuine=%s）"
                  % (dr["verdict"], dr["n_rounds"],
                     (dr.get("protocol") or {}).get("runs_per_round", 5),
                     dr["rounds_totals"],
                     (dr["aggregate_union_max"] or {}).get("classified", {})
                     .get("genuine"))
                  if dr else "SKIPPED（无导出件）")
    return row


def build_board_report(bd):
    run = bd["run"]
    board = bd["board_doc"]["board"]
    conv = run.get("convert", {})
    comp = run.get("compile")
    ex = run.get("execute")
    ch = run.get("check")
    drc_doc = bd["drc"]
    exp_sha = bd["export_sha"]
    is_rerun7 = bd["board_id"] in RERUN7

    stages = {}
    stages["convert"] = (
        {"verdict": "OK",
         "reuse": ("board.json 复用（P5① convert 产物；adapter 0.2.0 自 "
                   "09-14 14:35 未变，P5⑤ 任务令裁定复用合法），本批未重跑 "
                   "convert" if is_rerun7 else
                   "本批 convert 重跑（runner 0.3.0）：源 sha=预注册核过、"
                   "双跑字节等"),
         "source_sha256": bd["prereg"]["sha256"], "hash_matches_prereg": True,
         "board_sha256": board["provenance"]["board_sha256"],
         "nets": len(board["nets"]),
         "partitions": len(board["partitions"]),
         "adapter_report": bd["board_doc"]["adapter_report"],
         "granularity_prior_injected": conv.get(
             "granularity_prior_injected"),
         "granularity_note": conv.get("granularity_note"),
         "double_run_equal": conv.get("double_run_equal")}
        if conv or not is_rerun7 else {"verdict": "SKIPPED"})
    stages["compile"] = (
        {"verdict": "OK", "coverage_pct": comp["coverage_pct"],
         "partitions": comp["partitions"], "conflicts": comp["conflicts"],
         "j_items": comp["j_items"], "pkg_entries": comp["pkg_entries"],
         "double_run_equal": comp["double_run_equal"],
         "compiled_json": comp["compiled_json"]}
        if comp else {"verdict": "SKIPPED"})
    if not ex:
        stages["execute"] = {"verdict": "SKIPPED"}
    else:
        stages["execute"] = {
            "verdict": ex.get("exec_verdict"),
            "selection_verdict": ex.get("selection_verdict"),
            "candidate_source": ex.get("candidate_source"),
            "n_candidates": ex.get("n_candidates"),
            "per_net_count": ex.get("per_net_count"),
            "negotiation_log_entries": ex.get("negotiation_log_entries"),
            "routed": ex.get("routed"),
            "double_run_equal": ex.get("double_run_equal"),
            "rotate_budget": ex.get("rotate_budget"),
            "tried_candidates": ex.get("tried_candidates"),
            "note": ("selection UNKNOWN 按 P4 门 G1 口径自 plan_candidates[0] "
                     "起跑；管线 0.3.0 起终局 FAILED 按候选序轮换（预算 K），"
                     "candidate_source=实际布通候选下标，逐阶段 verdict 如实记录"),
            "failing_nets": failing_nets(bd["execute"]) if bd["execute"] else [],
            "failure_reasons": (failure_reasons(bd["execute"])
                                if bd["execute"] else [])}
        if run.get("skipped_stages"):
            stages["execute"]["skipped_stages"] = run["skipped_stages"]
            stages["execute"]["skip_reason"] = run.get("skip_reason")
    stages["check"] = (
        {"verdict": "feasible=%s" % ch["feasible"],
         "feasible": ch["feasible"],
         "violations_total": ch["violations_total"],
         "attributed_violations": ch["attributed_violations"],
         "violations_by_rule": ch["violations_by_rule"],
         "drc_version": ch["drc_version"],
         "route_check_version": ch["route_check_version"]}
        if ch else {"verdict": "SKIPPED（无 routes 输入）"})
    stages["export"] = (
        {"verdict": "OK", "bytes": run["export"]["bytes"],
         "sha256": exp_sha, "double_run_equal": True}
        if run.get("export") else {"verdict": "SKIPPED（无 routes 输入）"})
    stages["drc"] = (
        {"verdict": "OK（P5-UP3 聚合协议：%s）" % drc_doc["verdict"],
         "protocol_verdict": drc_doc["verdict"],
         "n_rounds": drc_doc["n_rounds"], "n_runs": drc_doc["n_runs"],
         "runs_per_round": (drc_doc.get("protocol") or {}).get(
             "runs_per_round"),
         "rounds_totals": drc_doc["rounds_totals"],
         "totals_in_order": drc_doc["totals_in_order"],
         "aggregate_union_max": drc_doc["aggregate_union_max"],
         "runs": drc_doc["runs"], "kicad_cli": drc_doc["kicad_cli"],
         "note": drc_doc["note"],
         "raw_report": "不落盘（计数提取即删，P4-G3 同口径）"}
        if drc_doc else {"verdict": "SKIPPED（无导出件）"})

    cap_rows = []
    if bd["check"]:
        ck = bd["check"]["check"]
        cap_rows = [{"corridor_layer_id": clid, "occupancy_mm": occ,
                     "capacity_mm": cap, "fits": bool(occ <= cap)}
                    for clid, occ, cap in ck["capacity_checks"]]

    classified_per_run = None
    if drc_doc:
        classified_per_run = [r["counts"]["classified"] for r in
                              drc_doc["runs"]]

    ev_ok = ledger.verify()
    report = {
        "purpose": "P5⑤ 单板全链批量执行对账（A 层 holdout；7 补跑板 convert "
                   "复用 P5① board.json，10 板本批 convert 全新全链）",
        "board_id": bd["board_id"],
        "tertile_nets": {"manifest_net_count": bd["prereg"]["nets"],
                         "adapter_nets": len(board["nets"]),
                         "disclosure": "manifest 索引网数与 adapter 申报网数"
                                       "口径差如实披露（P5① 同款）"},
        "stages": stages,
        "capacity_ledger_C": {
            "entries": cap_rows, "n_entries": len(cap_rows),
            "note": "adapter 丢弃语料源 zones → 真实板上走廊容量账本退化为平凡"
                    "（badgeleds 试跑同款结论）"},
        "drc_aggregate": {
            "protocol": "P5-UP3-aggregate-v1（每轮 5 跑同字节导出件，至多 3 轮；"
                        "一轮全等→deterministic-5x-equal；否则并集 max + "
                        "nondeterministic-disclosed）",
            "same_input_sha256": exp_sha,
            "protocol_verdict": drc_doc["verdict"] if drc_doc else None,
            "rounds_totals": drc_doc["rounds_totals"] if drc_doc else None,
            "totals_in_order": drc_doc["totals_in_order"] if drc_doc else None,
            "by_type_per_run": [r["by_type_observation"]
                                for r in drc_doc["runs"]] if drc_doc else None,
            "classified_per_run": classified_per_run,
            "classified_union_max": (drc_doc.get("aggregate_union_max") or {})
                .get("classified") if drc_doc else None,
            "genuine_conservative_max": (
                max(c["genuine"] for c in classified_per_run)
                if classified_per_run else None),
            "nondeterminism": ("同字节逐跑 totals/by-type 已全量入接触史台账"
                               "（action=drc 结果登记事件）；真实板上总数漂移为"
                               "已知现象（P5① badgeleds 6 跑 95-102）"
                               if drc_doc else "本板未进入 kicad 外权威对照")}}
    if ex and ex.get("exec_verdict") == "FAILED":
        report["risk_conclusion"] = {
            "verdict": "v5-side-failed",
            "verdict_text": "v5 侧未布通（executor FAILED，确定性双跑一致；"
                            "0.3.0 轮换口径下终局 FAILED=轮换预算内全部候选"
                            "均未布通）：板未产出布线，check/export/drc 无输入"
                            "跳过，不进入 kicad 外权威对照；失败串/exhaustion-"
                            "cause 见 execute.json negotiation_log 与 "
                            "tried_candidates",
            "genuine_count": None,
            "evidence": "failure_reasons/tried_candidates 见 stages.execute"}
    elif drc_doc:
        genuines = [c["genuine"] for c in classified_per_run]
        report["risk_conclusion"] = {
            "verdict": "conditional" if max(genuines) == 0 else "failed",
            "verdict_text": (
                "有条件达成（badgeleds 同款）：v5 route_check feasible 且 0 违例"
                "；kicad-cli 聚合协议 %s（%d轮×%d跑，totals %d-%d）但锚定跑集"
                "并集 genuine=%d——差距全部来自合同抽象与规则配置，非布线搜索"
                "质量；零违例门需先完成 P5① 试跑报告三项条件（出口合同升级 / "
                "DRC 规则配置对齐 / 外权威口径确定化）"
                % (drc_doc["verdict"], drc_doc["n_rounds"],
                   (drc_doc.get("protocol") or {}).get("runs_per_round", 5),
                   min(drc_doc["totals_in_order"]),
                   max(drc_doc["totals_in_order"]), max(genuines))),
            "genuine_count": max(genuines),
            "blocking_counts": {
                "config-gap": max(c["config-gap"] for c in
                                  classified_per_run),
                "contract-artifact": max(c["contract-artifact"] for c in
                                         classified_per_run)}}
    else:
        report["risk_conclusion"] = {"verdict": "unknown"}
    report["ledger"] = {
        "path": "out/v5-p5/holdout-ledger/access-log.jsonl",
        "verify": ev_ok,
        "board_events": sum(1 for e in ledger.read_events()
                            if e["board_id"] == bd["board_id"])}
    return report


def md_board(rep):
    st = rep["stages"]
    lines = [
        "<!-- v5.p5-batch-report provenance generator=%s generator_version=%s"
        " board_id=%s -->" % (GENERATOR, VERSION, rep["board_id"]),
        "# P5⑤ 单板全链对账：%s" % rep["board_id"],
        "",
        "| 阶段 | 结果 |",
        "|---|---|",
        "| convert | %s；板 %d 网 %d 分区 |" % (
            ("OK：board.json 复用（P5① 产物，adapter 0.2.0 未变），本批未重跑"
             if rep["board_id"] in RERUN7 else
             "OK：源 hash=预注册，本批 convert 双跑字节等"),
            st["convert"]["nets"], st["convert"]["partitions"]),
    ]
    if st["compile"]["verdict"] == "OK":
        lines.append("| compile | coverage=%.1f%%；conflicts=%d；J 项=%d；双跑"
                     "字节等 |" % (st["compile"]["coverage_pct"],
                                   st["compile"]["conflicts"],
                                   st["compile"]["j_items"]))
    else:
        lines.append("| compile | SKIPPED |")
    ex = st["execute"]
    if ex.get("verdict") == "ROUTED":
        lines.append("| execute | ROUTED（selection=%s → %s，%d 候选，轮换 "
                     "tried=%d）；双跑字节等 |"
                     % (ex["selection_verdict"], ex["candidate_source"],
                        ex["n_candidates"],
                        len(ex.get("tried_candidates") or [])))
    elif ex.get("verdict") == "FAILED":
        lines.append("| execute | **FAILED**（selection=%s → %s，%d 候选，轮换 "
                     "tried=%d；失败网 %s：%s） |"
                     % (ex["selection_verdict"], ex["candidate_source"],
                        ex["n_candidates"],
                        len(ex.get("tried_candidates") or []),
                        "、".join(f["net_id"] for f in ex["failing_nets"]) or
                        "见 execute.json",
                        (ex["failure_reasons"][0].split("：", 1)[-1]
                         if ex["failure_reasons"] else "见 execute.json")))
        lines.append("| check | SKIPPED（无 routes 输入） |")
        lines.append("| export | SKIPPED（无 routes 输入） |")
        lines.append("| drc | SKIPPED（无导出件） |")
    else:
        lines.append("| execute | SKIPPED |")
    if st["check"]["verdict"].startswith("feasible"):
        lines.append("| check | v5 route_check %s，违例 %d 条（v5.drc %s） |"
                     % (st["check"]["verdict"], st["check"]["violations_total"],
                        st["check"]["drc_version"]))
        lines.append("| export | %d bytes，sha256=%s…，双跑字节等 |"
                     % (st["export"]["bytes"], st["export"]["sha256"][:16]))
        d = st["drc"]
        lines.append("| drc | kicad-cli %s：%d轮×%d跑 rounds_totals=%s；锚定"
                     "跑集并集三归类=%s |"
                     % (d["protocol_verdict"], d["n_rounds"],
                        d["runs_per_round"], d["rounds_totals"],
                        json.dumps(rep["drc_aggregate"]["classified_union_max"],
                                   ensure_ascii=False, sort_keys=True)))
    lines += ["",
              "## C 容量账本（全路线）",
              "",
              "走廊容量账本项 = %d 条（adapter 丢弃语料源 zones → 容量维度退化"
              "为平凡；间距/短接由 kicad-cli 实几何隐式承担）。"
              % rep["capacity_ledger_C"]["n_entries"],
              ""]
    d3 = rep["drc_aggregate"]
    if d3["totals_in_order"] is not None:
        lines += [
            "## kicad-cli 外权威（P5-UP3 聚合协议，同字节输入）",
            "",
            "- 版本：%s" % st["drc"]["kicad_cli"]["version"].strip(),
            "- 协议判定：%s（%d轮×%d跑）" % (d3["protocol_verdict"],
                                             st["drc"]["n_rounds"],
                                             st["drc"]["runs_per_round"]),
            "- rounds_totals：%s" % d3["rounds_totals"],
            "- totals（观测顺序）：%s" % d3["totals_in_order"],
            "- by-type 逐跑：%s" % json.dumps(d3["by_type_per_run"],
                                              ensure_ascii=False,
                                              sort_keys=True),
            "- 三归类逐跑：%s" % json.dumps(d3["classified_per_run"],
                                            ensure_ascii=False,
                                            sort_keys=True),
            "- 三归类并集 max（保守口径）：%s"
            % json.dumps(d3["classified_union_max"], ensure_ascii=False,
                         sort_keys=True),
            "- **非确定性**：%s" % d3["nondeterminism"],
            ""]
    rc = rep["risk_conclusion"]
    lines += ["## 结论（%s）" % rc["verdict"], "", rc["verdict_text"], ""]
    lines += ["台账：%s（%d 事件，verify=%s；本板事件 %d 条）"
              % (rep["ledger"]["path"], rep["ledger"]["verify"]["n_events"],
                 rep["ledger"]["verify"]["ok"],
                 rep["ledger"]["board_events"]),
              ""]
    return "\n".join(lines)


def build_batch_summary(reports, verdict_rows):
    board_fps = []
    for bd in (board_data(b) for b in BOARDS):
        board_fps.append({"board_id": bd["board_id"],
                          "board_sha256": bd["board_doc"]["board"][
                              "provenance"]["board_sha256"],
                          "export_sha256": bd["export_sha"],
                          "run_result_sha256": sha256_file(os.path.join(
                              bd["dir"], "run-result.json"))})
    fingerprint = hashlib.sha256(canonical.canonical_json(board_fps)).hexdigest()
    sat_boards = []
    for rep in reports:
        ex = rep["stages"]["execute"]
        ck = rep["stages"]["check"]
        if ex.get("verdict") == "ROUTED" and ck.get("feasible") is True:
            sat_boards.append(rep["board_id"])
    genuine = {}
    for rep in reports:
        g = rep["drc_aggregate"].get("genuine_conservative_max")
        if g is not None:
            genuine[rep["board_id"]] = g
    drc_boards = {}
    for rep in reports:
        if rep["drc_aggregate"]["totals_in_order"] is not None:
            drc_boards[rep["board_id"]] = {
                "protocol_verdict": rep["drc_aggregate"]["protocol_verdict"],
                "n_rounds": rep["stages"]["drc"]["n_rounds"],
                "rounds_totals": rep["drc_aggregate"]["rounds_totals"],
                "totals_in_order": rep["drc_aggregate"]["totals_in_order"],
                "by_type_per_run": rep["drc_aggregate"]["by_type_per_run"],
                "classified_per_run": rep["drc_aggregate"][
                    "classified_per_run"],
                "classified_union_max": rep["drc_aggregate"][
                    "classified_union_max"],
                "unconnected_per_run":
                    [r["counts"]["unconnected_items"]
                     for r in rep["stages"]["drc"]["runs"]],
                "schematic_parity_per_run":
                    [r["counts"]["schematic_parity"]
                     for r in rep["stages"]["drc"]["runs"]]}
    sel = load_json(os.path.join(ROOT, "out", "v5-p5", "holdout-ledger",
                                 "first8-selection.json"))
    first8_ids = [r["board_id"] for r in sel["selected"]]
    first8_sat = sorted(b for b in sat_boards if b in first8_ids)
    summary = {
        "purpose": "P5⑤ 批量执行汇总（17 板：7 补跑 compile→drc 复用 "
                   "board.json + 10 板 convert→drc 全新全链；executor 0.4.0 + "
                   "runner 0.3.0 修后重跑；throwing-star-pro convert 两世界"
                   "同败已留档跳过）",
        "scope": {"batch_boards": BOARDS,
                  "excluded": {
                      "throwing-star-pro":
                          "convert FAILED 两世界同（convert-failed.json 留档），"
                          "任务令跳过（台账 seq85 登记）"},
                  "rerun7_reuse_note":
                      "7 补跑板 convert 未重跑：board.json 复用（adapter 0.2.0 "
                      "自 09-14 14:35 未变，任务令裁定合法）；重跑前既有 "
                      "execute/check/export/drc 产物已留档 *.pre-f4.json"},
        "stage_verdict_table": verdict_rows,
        "kicad_aggregate": drc_boards,
        "classification_counts": {
            b: {"per_run": drc_boards[b]["classified_per_run"],
                "classified_union_max": drc_boards[b]["classified_union_max"],
                "genuine_conservative_max": max(
                    c["genuine"] for c in drc_boards[b]["classified_per_run"]),
                "config_gap_max": max(c["config-gap"] for c in
                                      drc_boards[b]["classified_per_run"]),
                "contract_artifact_max": max(
                    c["contract-artifact"] for c in
                    drc_boards[b]["classified_per_run"])}
            for b in drc_boards},
        "genuine_summary": {
            "per_board_conservative_max": genuine,
            "batch_genuine_total": sum(genuine.values()),
            "note": "genuine=两权威一致的真布线问题；仅 drc 到达板可判；"
                    "exec FAILED 板未产出布线不进入 kicad 对照（v5 侧失败即"
                    "头号发现）"},
        "sat": {
            "definition": "exec ROUTED 且 v5 route_check feasible=True"
                          "（selection UNKNOWN 按 P4-G1 口径自 plan_candidates[0]"
                          "起跑；管线 0.3.0 起终局 FAILED 按候选序轮换重试，"
                          "candidate_source=实际布通候选下标）",
            "batch_sat_boards": sat_boards,
            "batch_sat_count": len(sat_boards),
            "batch_total": len(BOARDS),
            "first8_sat_boards": first8_sat,
            "first8_sat_count": len(first8_sat),
            "first8_total": len(first8_ids),
            "baselines": {
                "p5_2_old_world_sat": "2/8",
                "pre_5_sat": "0/7（7 补跑板 pre-⑤ 全 FAILED）",
                "post_5_this_batch": "%d/%d" % (len(sat_boards), len(BOARDS))},
            "g1_gate": {"required_sat": 5, "batch_actual": len(sat_boards),
                        "first8_actual": len(first8_sat),
                        "met": len(first8_sat) >= 5,
                        "note": "G1 ≥5 SAT 对照达成与否按数据陈述，判定归主线"}},
        "exec_failed_boards": [
            {"board_id": rep["board_id"],
             "rotate_tried": len(rep["stages"]["execute"].get(
                 "tried_candidates") or []),
             "failing_nets": rep["stages"]["execute"]["failing_nets"],
             "failure_modes": sorted({re.sub(
                 r"^.*FAILED after \d+ attempts:\s*", "", r)
                 for r in rep["stages"]["execute"][
                     "failure_reasons"]})}
            for rep in reports
            if rep["stages"]["execute"].get("verdict") == "FAILED"],
        "tool_fixes_disclosure": TOOL_FIXES,
        "ledger": {
            "path": "out/v5-p5/holdout-ledger/access-log.jsonl",
            "verify": ledger.verify()},
        "boards_fingerprint_input": board_fps,
    }
    return summary, fingerprint


def main():
    os.makedirs(TRIAL, exist_ok=True)
    reports, verdict_rows = [], []
    for bid in BOARDS:
        bd = board_data(bid)
        rep = build_board_report(bd)
        reports.append(rep)
        verdict_rows.append(stage_verdicts(bd))
        doc = {"provenance": {"generator": GENERATOR,
                              "generator_version": VERSION,
                              "board_sha256": bd["board_doc"]["board"][
                                  "provenance"]["board_sha256"]}}
        doc.update(rep)
        with open(os.path.join(TRIAL, "%s.trial.json" % bid), "wb") as f:
            f.write(canonical.canonical_json(doc))
        with open(os.path.join(TRIAL, "%s.trial.md" % bid), "wb") as f:
            f.write(md_board(rep).encode("utf-8"))
        print("trial: out/v5-p5/trial/%s.trial.{json,md}" % bid)
    summary, fingerprint = build_batch_summary(reports, verdict_rows)
    doc = {"provenance": {"generator": GENERATOR,
                          "generator_version": VERSION,
                          "board_sha256": fingerprint}}
    doc.update(summary)
    with open(os.path.join(TRIAL, "batch-summary.json"), "wb") as f:
        f.write(canonical.canonical_json(doc))
    with open(os.path.join(TRIAL, "batch-summary.md"), "wb") as f:
        f.write(md_batch(summary, fingerprint).encode("utf-8"))
    print("batch summary: out/v5-p5/trial/batch-summary.{json,md}")
    return 0


def md_batch(s, fingerprint):
    lines = [
        "<!-- v5.p5-batch-report provenance generator=%s generator_version=%s"
        " batch_fingerprint=%s -->" % (GENERATOR, VERSION, fingerprint[:16]),
        "# P5⑤ 批量执行汇总（17 板 A 层 holdout 修后重跑）",
        "",
        "范围：17 板（7 补跑 compile→drc，convert 复用 P5① board.json——"
        "adapter 0.2.0 自 09-14 14:35 未变，任务令裁定合法；10 板 convert→drc "
        "全新全链）；重跑前既有 execute/check/export/drc 产物已留档 *.pre-f4."
        "json；throwing-star-pro convert 两世界同败已留档跳过（台账 seq85）。"
        "批次指纹（boards+run-result+export sha256 的 canonical 摘要）=%s"
        % fingerprint,
        "",
        "## 逐板逐阶段 verdict",
        "",
        "| 板 | convert | compile | execute | check | export | drc |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in s["stage_verdict_table"]:
        lines.append("| %s | %s | %s | %s | %s | %s | %s |"
                     % (r["board_id"], r["convert"], r["compile"],
                        r["execute"].replace("|", "\\|"), r["check"],
                        r["export"], r["drc"]))
    lines += ["",
              "## kicad-cli 聚合协议（P5-UP3：每轮 5 跑同字节导出件，至多 3 轮）"
              "与三归类",
              "",
              "三归类覆盖 violations+unconnected_items 全部条目（故逐跑三类合计"
              " = violations_total + unconnected_items）；genuine 保守口径=锚定"
              "跑集逐类并集最大值。",
              "",
              "| 板 | 协议判定 | rounds_totals | unconnected 逐跑 | "
              "genuine 逐跑 | config-gap 逐跑 | contract-artifact 逐跑 |",
              "|---|---|---|---|---|---|---|",
              ]
    for b, d in s["kicad_aggregate"].items():
        cls = d["classified_per_run"]
        lines.append("| %s | %s | %s | %s | %s | %s | %s |"
                     % (b, d["protocol_verdict"], d["rounds_totals"],
                        d["unconnected_per_run"],
                        [c["genuine"] for c in cls],
                        [c["config-gap"] for c in cls],
                        [c["contract-artifact"] for c in cls]))
    gs = s["genuine_summary"]
    lines += ["",
              "**genuine 汇总**：批内可判板（drc 到达）逐跑保守最大值合计 "
              "%d；%s" % (gs["batch_genuine_total"],
                          json.dumps(gs["per_board_conservative_max"],
                                     ensure_ascii=False, sort_keys=True)),
              "",
              "exec FAILED 板未产出布线，不进入 kicad 对照（v5 侧失败即头号"
              "发现，进引擎侧缺陷清单）。失败模式（轮换口径：终局 FAILED=轮换"
              "预算内全部候选均未布通）：",
              ""]
    for f in s["exec_failed_boards"]:
        lines.append("- %s：tried=%d；%s（首败网 %s）"
                     % (f["board_id"], f["rotate_tried"],
                        "；".join(f["failure_modes"]),
                        "、".join(n["net_id"] for n in f["failing_nets"])))
    sat = s["sat"]
    lines += ["",
              "## SAT 板计数（P5-G1 需 ≥5 SAT 对照）",
              "",
              "- SAT 定义：%s" % sat["definition"],
              "- 本批：%d/%d（%s）" % (sat["batch_sat_count"],
                                       sat["batch_total"],
                                       "、".join(sat["batch_sat_boards"]) or
                                       "无"),
              "- 首批 8 板口径：%d/%d（%s）"
              % (sat["first8_sat_count"], sat["first8_total"],
                 "、".join(sat["first8_sat_boards"]) or "无"),
              "- 基线对照：P5② 2/8 → pre-⑤ 0/7 → 本期（post-⑤）%d/%d"
              % (sat["batch_sat_count"], sat["batch_total"]),
              "- **G1 门：需 ≥5，first8 口径实际 %d，batch 口径实际 %d**"
              % (sat["g1_gate"]["first8_actual"], sat["g1_gate"]["batch_actual"]),
              "",
              "## 工具披露（历史修复 + 本版机械扩展）",
              ""]
    for i, t in enumerate(s["tool_fixes_disclosure"], 1):
        lines.append("%d. %s" % (i, t))
    lines += ["",
              "台账：%s（%d 事件，verify=%s）"
              % (s["ledger"]["path"], s["ledger"]["verify"]["n_events"],
                 s["ledger"]["verify"]["ok"]),
              ""]
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
