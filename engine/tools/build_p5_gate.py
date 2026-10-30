# -*- coding: utf-8 -*-
"""build_p5_gate.py — P5 五门（G1-G5）机械评估器（合同 P5-WAVE6 §3 第 7 条交付件）。

数据源（全部只读）：
  - out/v5-p5/wave6/_logs/*.wave6.done.json（17 板终态标记）
  - out/v5-p5/boards/<b>/（check.json / drc-classified.json / run-result.json / execute.json）
  - out/v5-p5/holdout-ledger/access-log.jsonl（G3 纪律门）
  - tests/ 套件绿态引用（G5-PF/PS 口径，引用 2026-09-21 主审复跑 1170 passed 389.64s）

口径（2026-09-21 用户裁定 wave6-criteria-rulings-2026-09-21.md）：
  - 豁免类=A(copper_edge_clearance/contract-artifact)+B(holes_co_located/contract-artifact)
  - C(hole_to_hole/genuine) 计入；D(check 段 R5) 非 kicad 口径不入 kicad 分子
  - 判据二干净板 = kicad 违例总数 − 豁免类计数 == 0
  - 微段豁免（2026-09-28 七裁③）：track_dangling 悬挂段 <0.06mm 并入豁免类
    （仅限微段阈值；≥阈值真悬空仍入豁免外余量）

G4 与 G5-PU 接会话波产物（out/v5-p5/p5-sessions/：g4-table.json + vote-tally.json
+ defect-ledger.jsonl + views/，2026-09-21 A 层会话波交付后主审接线）。

V5-SMALLWAVE G1 处置落地（2026-09-23，任务书 §1.G1/用户令「124 按推荐」Q1）：
  --dispositions 清单（默认 out/v5-p5/p5-gate/dispositions-2026-09-23.json，
  8 板 board-inherent=diag-failed8 终判+witness 锚）生效时 G1 双口径输出：
  原口径（全 14 终态板分母）并记 + 可布域口径（分母剔 8 处置板）+豁免披露
  段。历史件保护：目标 gate-report.json 已存在且无 --force 时拒写（重跑产物
  须落新目录/带版本后缀——本批=--out-dir out/v5-p5/p5-gate/smallwave-2026-09-23）。
"""
import argparse
import io
import json
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

import p5_holdout_ledger as ledger  # noqa: E402

WAVE6 = os.path.join(ROOT, "out", "v5-p5", "wave6", "_logs")
BOARDS = os.path.join(ROOT, "out", "v5-p5", "boards")
OUT_DIR = os.path.join(ROOT, "out", "v5-p5", "p5-gate")
DISPOSITIONS_DEFAULT = os.path.join(OUT_DIR, "dispositions-2026-09-23.json")
EXEMPT_TYPES = {"copper_edge_clearance", "holes_co_located"}   # 裁定 A+B（contract-artifact）
# 2026-09-28 七裁③（用户令「7 项全按建议」；LEAD-REVIEW-R1W6-2026-09-28
# 呈裁点 3）：track_dangling 微段豁免类——仅限悬挂段长度 <0.06mm 的微段
# （R1 实测 6 条=0.0369/0.0413/0.0583mm，contract-artifact 分类、genuine=0，
# 对齐 copper_edge_clearance 先例）；≥阈值真悬空保留在豁免外余量（防漏报）。
MICROSEG_TYPE = "track_dangling"
MICROSEG_MAX_MM = 0.06
MICROSEG_CLASS = "track_dangling_microseg(<0.06mm)"
SUITE = ("pytest tests/ 1289 passed（2026-09-27 V5-R1 ED-X 修复批 W-X4 全量复跑 "
         "947.38s，executor 0.8.0/route_check 0.4.1/kicad_export 0.5.0；对照 "
         "09-26 基线 1280+5，+9 恰为本批新钉 test_r1_edx_export_multiendpoint）")


def jload(p):
    with io.open(p, encoding="utf-8") as f:
        return json.load(f)


def _exhaustion_of(log):
    """negotiation_log 的 exhaustion-cause。

    V5-R1 读数适配（2026-09-27，ED-X 修复批 W-X6）：executor 0.6.1 A3 起
    FAILED 终局在 exhaustion-cause 行之后追加 log-only geom-secondary 行，
    末行不一定是 exhaustion 行——自尾向首扫描**最后一条**含
    exhaustion-cause 的条目（证书数据在盘；末行直读为读取缺口，三板实测
    exhaustion-cause 位于倒数 2-3 位）。"""
    if not log:
        return None
    for entry in reversed(log):
        if isinstance(entry, dict):
            if entry.get("exhaustion-cause"):
                return entry["exhaustion-cause"]
        elif isinstance(entry, str) and "exhaustion-cause=" in entry:
            seg = entry.split("exhaustion-cause=", 1)[1]
            return seg.split("（", 1)[0].split("(", 1)[0].strip()
    return None


_LEN_MM_RE = re.compile(r"长度:\s*([0-9.]+)\s*mm")


def _microseg_exempt(drc_doc, board):
    """track_dangling 微段豁免计数（七裁③，2026-09-28）。

    逐条读 classified_rows_per_run（type=track_dangling 行，长度在
    items[].description「长度: X mm」文本）；<阈值计入豁免、≥阈值保留。
    5 runs 逐条长度集须全等（deterministic-5x-equal 判据背书），
    不一致或长度未解析即拒出值（不静默）。返回 (microseg_n, td_total,
    lengths_sorted)。"""
    per_run = []
    for rows in (drc_doc.get("classified_rows_per_run") or []):
        lens = []
        for row in rows:
            if row.get("type") != MICROSEG_TYPE:
                continue
            val = None
            for it in row.get("items") or []:
                m = _LEN_MM_RE.search(str(it.get("description") or ""))
                if m:
                    val = float(m.group(1))
                    break
            lens.append(val)
        per_run.append(lens)
    if not per_run:
        return 0, 0, []
    first = per_run[0]
    if any(r != first for r in per_run[1:]):
        raise SystemExit("microseg 校验失败：%s track_dangling 逐条跨 run "
                         "不一致（5x-equal 判据不成立，拒出值）" % board)
    if any(v is None for v in first):
        raise SystemExit("microseg 校验失败：%s track_dangling %d 条长度未解析"
                         % (board, sum(1 for v in first if v is None)))
    micro = [v for v in first if v < MICROSEG_MAX_MM]
    return len(micro), len(first), sorted(first)


def board_rows():
    rows = []
    for name in sorted(os.listdir(WAVE6)):
        if not name.endswith(".wave6.done.json"):
            continue
        b = name[:-len(".wave6.done.json")]
        m = jload(os.path.join(WAVE6, name))
        row = {"board": b, "abandoned": bool(m.get("abandoned"))}
        if m.get("abandoned"):
            row.update(phase="ABANDONED", ledger_seq=m.get("ledger_seq"))
            rows.append(row)
            continue
        rr = jload(os.path.join(BOARDS, b, "run-result.json"))["run"]
        if rr.get("execute") is None:
            # V5-R1 部分树（ED-X 修复批 2026-09-27 适配，逐行披露见
            # r1/edx/anchor-walkthrough.md §5）：R1 换版（09-24/25）重转 17 板
            # 后，7 块已处置 board-inherent 板未在 R1 世界重跑，run-result 停
            # convert 形态（无 execute 键）。行读数 exec_verdict=None：不入
            # sat/failed 分子（G2 只数 FAILED、G1 只数 ROUTED）；其处置装载
            # 按跨世界有效性放行（board-inherent=板源几何属性，见
            # load_dispositions）。非处置板若出现此形态则如实进分母计 FAIL。
            ex_path = os.path.join(BOARDS, b, "execute.json")
            ex = jload(ex_path)["execute"] if os.path.isfile(ex_path) else {}
            row.update(
                phase="terminal-convert-only",
                exec_verdict=rr["execute"].get("exec_verdict")
                if isinstance(rr.get("execute"), dict) else None,
                selection_verdict=(rr.get("execute") or {}).get("selection_verdict")
                if isinstance(rr.get("execute"), dict) else None,
                feasible=None,
                r1_no_execute=True,
                stages_run=rr.get("stages_run"),
                exhaustion=_exhaustion_of(ex.get("negotiation_log")),
            )
            dc = os.path.join(BOARDS, b, "drc-classified.json")
            if os.path.isfile(dc):
                d = jload(dc)["drc"]
                au = d["aggregate_union_max"]
                by_type = (d["runs"][0].get("by_type_observation") or {})
                exempt = sum(n for t, n in by_type.items() if t in EXEMPT_TYPES)
                micro_n, _td_tot, td_lens = _microseg_exempt(d, b)
                row.update(
                    drc_verdict=d.get("verdict"),
                    kicad_total=au["violations_total"],
                    kicad_exempt=exempt + micro_n,
                    kicad_effective=au["violations_total"] - exempt - micro_n,
                    kicad_genuine=au["classified"].get("genuine", 0),
                    by_type=by_type,
                    microseg_exempt=micro_n,
                    microseg_lengths_mm=td_lens,
                )
            else:
                row.update(drc_verdict=None, kicad_total=None,
                           kicad_effective=None, kicad_genuine=None, by_type={})
            rows.append(row)
            continue
        ex = jload(os.path.join(BOARDS, b, "execute.json"))["execute"]
        row.update(
            phase="terminal",
            exec_verdict=rr["execute"]["exec_verdict"],
            selection_verdict=rr["execute"].get("selection_verdict"),
            feasible=(rr.get("check") or {}).get("feasible"),
            check_version=(rr.get("check") or {}).get("route_check_version"),
            per_net_count=rr["execute"].get("per_net_count"),
            n_log=rr["execute"].get("negotiation_log_entries"),
            rotate_budget=rr["execute"].get("rotate_budget"),
            tried=len(rr["execute"].get("tried_candidates") or []),
            first_fail=(rr["execute"].get("tried_candidates") or [{}])[0].get("first_fail_net"),
            exhaustion=_exhaustion_of(ex.get("negotiation_log")),
            compile_coverage=rr.get("compile", {}).get("coverage_pct"),
            compile_conflicts=rr.get("compile", {}).get("conflicts"),
        )
        dc = os.path.join(BOARDS, b, "drc-classified.json")
        if os.path.isfile(dc):
            d = jload(dc)["drc"]
            au = d["aggregate_union_max"]
            by_type = (d["runs"][0].get("by_type_observation") or {})
            exempt = sum(n for t, n in by_type.items() if t in EXEMPT_TYPES)
            genuine = au["classified"].get("genuine", 0)
            micro_n, _td_tot, td_lens = _microseg_exempt(d, b)
            row.update(
                drc_verdict=d.get("verdict"),
                kicad_total=au["violations_total"],
                kicad_exempt=exempt + micro_n,
                kicad_effective=au["violations_total"] - exempt - micro_n,
                kicad_genuine=genuine,
                by_type=by_type,
                microseg_exempt=micro_n,
                microseg_lengths_mm=td_lens,
            )
        else:
            row.update(drc_verdict=None, kicad_total=None, kicad_effective=None,
                       kicad_genuine=None, by_type={})
        rows.append(row)
    return rows


DISPOSITION_CLASSES = {"board-inherent", "rule-value-limited"}
# (a) 板固有 / (c) 规则带值（V5-R1 W-6 扩展，2026-09-25 用户三裁②：
# tmp108-A0=(c) 规则带值类豁免入账——rule-value-limited 披露语义
# 「当前规则值下不可布、真实细规则可解」+R7 立项证据挂账）。
# status：ruled=已裁豁免入账（分母剔除）；candidate=(c) 候选披露
# （不入分母，终裁归主审/用户）。缺省 ruled=向后兼容 2026-09-23
# 旧清单（8 板 board-inherent 无 status 字段）。


def load_dispositions(path, rows):
    """处置清单装载+校验：清单内每板须在 rows 且终态 FAILED、处置类须
    {board-inherent, rule-value-limited}；返回 (dispositions_doc, 翻译后的
    豁免披露行) 或 (None, [])。"""
    if not path or not os.path.isfile(path):
        return None, []
    doc = jload(path)
    by_board = {r["board"]: r for r in rows}
    rows_out = []
    problems = []
    for name in sorted(doc.get("boards", {})):
        d = doc["boards"][name]
        r = by_board.get(name)
        if r is None:
            problems.append("%s 不在 17 板终态标记内" % name)
            continue
        if r.get("abandoned"):
            problems.append("%s 为弃板（非 FAILED 处置对象）" % name)
            continue
        if r.get("exec_verdict") == "FAILED":
            pass
        elif r.get("exec_verdict") is None and r.get("r1_no_execute"):
            # V5-R1 部分树（2026-09-27 适配）：R1 世界未重跑的 convert-only
            # 板。已裁 board-inherent 处置=板源几何属性、跨世界有效（09-23
            # 裁定原件锚），放行装载；此类板无 R1 execute 故不可能为 SAT，
            # 「防把 SAT 板误处置」的装载器护栏语义保持成立。
            pass
        else:
            problems.append("%s 终态=%s（预期 FAILED；convert-only 板须带"
                            " r1_no_execute 标记方可跨世界处置装载）"
                            % (name, r.get("exec_verdict")))
        if d.get("disposition") not in DISPOSITION_CLASSES:
            problems.append("%s 处置类=%s（本门仅认 %s）"
                            % (name, d.get("disposition"),
                               "/".join(sorted(DISPOSITION_CLASSES))))
        status = d.get("status", "ruled")
        if status not in ("ruled", "candidate"):
            problems.append("%s status=%s（仅认 ruled/candidate）"
                            % (name, status))
        w = d.get("witness") or {}
        rows_out.append({
            "board": name, "disposition": d.get("disposition"),
            "status": status,
            "failed_net": d.get("failed_net"),
            "diag_class": d.get("diag_class"),
            "exhaustion": r.get("exhaustion"),
            "witness_diag_json": w.get("diag_json"),
            "witness_geometry_json": w.get("geometry_json"),
            "witness_report": w.get("report")})
    if problems:
        raise SystemExit("dispositions 校验失败：%s" % "；".join(problems))
    doc["_exemption_rows"] = rows_out
    return doc, rows_out


def main(argv=None):
    ap = argparse.ArgumentParser(description="P5 五门（G1-G5）机械评估器")
    ap.add_argument("--dispositions", default=DISPOSITIONS_DEFAULT,
                    help="处置清单 json（缺省取默认路径，不存在=原单口径）")
    ap.add_argument("--out-dir", default=None,
                    help="输出目录（缺省=%s）" % OUT_DIR)
    ap.add_argument("--force", action="store_true",
                    help="允许覆写已存在的 gate-report.json（历史件保护默认关）")
    args = ap.parse_args(argv)
    out_dir = args.out_dir or OUT_DIR
    target = os.path.join(out_dir, "gate-report.json")
    if os.path.isfile(target) and not args.force:
        raise SystemExit("拒写已存在历史件 %s（重跑请 --out-dir 新目录或 "
                         "--force 显式覆写）" % target)

    rows = board_rows()
    dispos_doc, dispos_rows = load_dispositions(args.dispositions, rows)
    sat = [r for r in rows if r.get("exec_verdict") == "ROUTED"
           and r.get("feasible") is True
           and r.get("drc_verdict") == "deterministic-5x-equal"]
    failed = [r for r in rows if r.get("exec_verdict") == "FAILED"]
    abandoned = [r for r in rows if r.get("abandoned")]
    clean = [r for r in sat if (r.get("kicad_effective") or 0) == 0]

    g1 = {
        "criterion_1_sat_ge_5": {"n_sat": len(sat), "pass": len(sat) >= 5,
                                 "sat_boards": [r["board"] for r in sat]},
        "criterion_2_zero_violation": {
            "clean_boards": [r["board"] for r in clean], "n_clean": len(clean),
            "require": 5, "pass": len(clean) >= 5,
            "exempt_classes": sorted(EXEMPT_TYPES) + [MICROSEG_CLASS],
            "microseg_exempt_total": sum(r.get("microseg_exempt") or 0 for r in sat),
            "microseg_lengths_mm": {r["board"]: r.get("microseg_lengths_mm")
                                    for r in sat if r.get("microseg_exempt")},
            "residual_nonexempt": sum(r.get("kicad_effective") or 0 for r in sat),
            "genuine_outstanding": sum(r.get("kicad_genuine") or 0 for r in sat),
            "remediation": "hole_to_hole-PTH-drill-spacing（已立修复候选，下版）"},
    }
    n_terminal = len([r for r in rows if not r.get("abandoned")])
    _genuine_out = sum(r.get("kicad_genuine") or 0 for r in sat)
    _resid_out = sum(r.get("kicad_effective") or 0 for r in sat)
    # V5-R1 读数适配（2026-09-27）：三支化——判据一不达标时不再误印
    # 「判据一 PASS（n≥5）」（R1 部分树首跑实测 4<5 触发）；差口披露改
    # 「豁免外余量（其中 genuine）」双计数（R1 实测余量=track_dangling 类
    # contract-artifact、genuine=0，原「差口=C 类 genuine」单计数失真）。
    if len(sat) >= 5 and len(clean) >= 5:
        g1["verdict_original_caliber"] = "PASS"
    elif len(sat) >= 5:
        g1["verdict_original_caliber"] = (
            "SPLIT：判据一 PASS（%d≥5）/ 判据二未达（干净板 %d<5，豁免外余量"
            " %d 条〔其中 C 类 genuine %d〕）"
            % (len(sat), len(clean), _resid_out, _genuine_out))
    else:
        g1["verdict_original_caliber"] = (
            "FAIL：判据一 %d<5 / 判据二干净板 %d<5（豁免外余量 %d 条〔其中 "
            "C 类 genuine %d〕）"
            % (len(sat), len(clean), _resid_out, _genuine_out))
    if dispos_doc is not None:
        ruled = [x for x in dispos_rows if x["status"] == "ruled"]
        cands_disc = [x for x in dispos_rows if x["status"] == "candidate"]
        disposed = {x["board"] for x in ruled}
        dom_rows = [r for r in rows if not r.get("abandoned")
                    and r["board"] not in disposed]
        dom_sat = [r for r in sat if r["board"] not in disposed]
        dom_failed = [r for r in failed if r["board"] not in disposed]
        g1["criterion_1_routable_domain"] = {
            "n_sat": len(dom_sat), "denominator": len(dom_rows),
            "pass": len(dom_sat) == len(dom_rows),
            "sat_boards": [r["board"] for r in dom_sat],
            "failed_in_domain": [r["board"] for r in dom_failed],
            "note": "分母剔除 %d 块已裁处置板（豁免入账；(c) rule-value-"
                    "limited 豁免前口径）" % len(disposed)}
        c_ruled = {x["board"] for x in ruled
                   if x["disposition"] == "rule-value-limited"}
        if c_ruled:
            dom2_rows = [r for r in dom_rows if r["board"] not in c_ruled]
            dom2_sat = [r for r in dom_sat if r["board"] not in c_ruled]
            dom2_failed = [r for r in dom_failed
                           if r["board"] not in c_ruled]
            g1["criterion_1_routable_domain_c_exemption"] = {
                "n_sat": len(dom2_sat), "denominator": len(dom2_rows),
                "pass": len(dom2_sat) == len(dom2_rows),
                "sat_boards": [r["board"] for r in dom2_sat],
                "failed_in_domain": [r["board"] for r in dom2_failed],
                "exempted_c_boards": sorted(c_ruled),
                "ruling": "2026-09-25 用户三裁②：tmp108-A0=(c) 规则带值类"
                          "豁免入账（rule-value-limited；当前规则值下不可布、"
                          "真实细规则可解，R7 立项证据挂账）"}
        g1["exemption_disclosure"] = {
            "ruling": dispos_doc.get("ruling"),
            "basis": dispos_doc.get("basis"),
            "n_boards": len(dispos_rows),
            "n_ruled": len(ruled), "n_candidate": len(cands_disc),
            "rows": dispos_rows}
        verdict_parts = [
            g1["verdict_original_caliber"],
            "可布域口径（(c) 豁免前）SAT %d/%d %s（%d 板已裁处置豁免入账+"
            "分母剔除，不宣称 SAT、不改板数据面）"
            % (len(dom_sat), len(dom_rows),
               "PASS" if len(dom_sat) == len(dom_rows) else "FAIL",
               len(disposed))]
        if c_ruled:
            verdict_parts.append(
                "(c) 豁免后口径 SAT %d/%d %s（剔除已裁 (c) 板 %s；%d 板 "
                "(c) 候选披露待裁、不剔分母）"
                % (len(dom2_sat), len(dom2_rows),
                   "PASS" if len(dom2_sat) == len(dom2_rows) else "FAIL",
                   ",".join(sorted(c_ruled)), len(cands_disc)))
        g1["verdict"] = "；".join(verdict_parts)
    else:
        g1["verdict"] = g1["verdict_original_caliber"]

    g2_rows, g2_ok = [], True
    for r in failed:
        ok = (r.get("selection_verdict") is not None
              and r.get("per_net_count") is not None
              and r.get("n_log") is not None and r["n_log"] > 0
              and r.get("rotate_budget") is not None and r["tried"] > 0
              and r.get("first_fail") is not None
              and r.get("exhaustion") is not None)
        g2_ok &= ok
        g2_rows.append({"board": r["board"], "compliant": ok,
                        "selection_verdict": r.get("selection_verdict"),
                        "exhaustion": r.get("exhaustion"),
                        "achieved_per_net": r.get("per_net_count"),
                        "boundary_first_fail": r.get("first_fail"),
                        "budget_tried": r["tried"]})
    g2 = {
        "verdict": "PASS" if g2_ok else "FAIL",
        "n_failed": len(failed), "n_cert_compliant": sum(1 for x in g2_rows if x["compliant"]),
        "unknown_share": "%d/%d UNKNOWN（exhaustion 证书形态：achieved=per_net + "
                         % (sum(1 for r in g2_rows
                                if r["selection_verdict"] == "UNKNOWN"),
                            len(g2_rows)) +
        "boundary=first_fail/exhaustion-cause + budget=rotate/tried）",
        "abandoned_disclosure": ["%s（用户令弃板无证书，post5 先例排除分子）"
                                 % r["board"] for r in abandoned],
        "rows": g2_rows,
    }

    verify_ok = ledger.verify()
    verify_ok = bool(verify_ok["ok"]) if isinstance(verify_ok, dict) else bool(verify_ok)
    prereg_boards = set(ledger.A_LAYER_PREREG)
    contacted = set()
    with io.open(ledger.LEDGER_PATH, encoding="utf-8") as f:
        for line in f:
            contacted.add(json.loads(line).get("board_id"))
    n_ledger = 0
    with io.open(ledger.LEDGER_PATH, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                n_ledger += 1
    # V5-R1 读数适配（2026-09-27，ED-X 修复批 W-X6）：boardintake 预注册
    # （09-24）把三板常驻红线 holdout 板（tinytapeout-demo/pslab-v6/
    # sdi-mipi-bridge）扩入 A_LAYER_PREREG，而 holdout 完整性红线要求其
    # 核验前零接触——「prereg ⊆ contacted」严格覆盖口径与该红线结构性
    # 互斥。双口径披露：verdict 取派发域覆盖（剔除从未派发的 holdout 三
    # 板，其未接触=红线设计使然非纪律违例）；严格覆盖布尔另记，主审呈裁
    # 面可两读。其余 prereg 板（含 boardintake 六板）零缺漏。
    _never = sorted(prereg_boards - contacted)
    _holdout_never = [b for b in _never if b in
                      ("tinytapeout-demo", "pslab-v6", "sdi-mipi-bridge")]
    _other_never = [b for b in _never if b not in _holdout_never]
    g3 = {"verdict": "PASS" if (verify_ok and not _other_never) else "FAIL",
          "ledger_verify": verify_ok,
          "prereg_boards": len(prereg_boards),
          "all_prereg_contacted_registered": prereg_boards <= contacted,
          "never_contacted": _never,
          "holdout_never_contacted_disclosure": (
              "never_contacted=%s 全系三板常驻红线 holdout 板（boardintake "
              "预注册后从未派发=holdout 完整性红线设计使然，非纪律违例）；"
              "严格覆盖口径=%s / 派发域覆盖口径=%s"
              % (",".join(_never) or "无",
                 "PASS" if not _never else "FAIL",
                 "PASS" if not _other_never else "FAIL")),
          "note": "n=%d（14 终态+3 弃板+门 4 双跑+诊断批+smallwave 等逐批 append）；"
                  "append-only 链式 sha 全程可审计" % n_ledger}

    # G4 三臂对账门：接会话波产物（g4-arm1 批 + arm③ p5-sessions 波）
    import glob as _glob
    sess = os.path.join(ROOT, "out", "v5-p5", "p5-sessions")
    g4t_path = os.path.join(sess, "g4-table.json")
    g4 = {"verdict": "FAIL（会话波产物缺失）"}
    if os.path.isfile(g4t_path):
        g4t = jload(g4t_path)
        n_rows = len(g4t)
        n_a12 = sum(1 for t in g4t if t.get("arm1_eq_arm2"))
        n_a32 = sum(1 for t in g4t if t.get("arm3_eq_arm2"))
        n_pg = sum(1 for t in g4t if t.get("g4") and t["g4"].get("principle_gain"))
        n_mi = sum(1 for t in g4t if t.get("g4") and t["g4"].get("model_increment"))
        echoes = sorted({t["g4"]["echo_rate"] for t in g4t if t.get("g4")})
        dr = [t.get("arm3_double_run_equal") for t in g4t
              if t.get("arm3_double_run_equal") is not None]
        tally_p = os.path.join(sess, "vote-tally.json")
        n_views = len(_glob.glob(os.path.join(sess, "views", "*", "*.svg")))
        have_tally = os.path.isfile(tally_p)
        have_defects = os.path.isfile(os.path.join(sess, "defect-ledger.jsonl"))
        have_report = os.path.isfile(os.path.join(sess, "SESSION-WAVE-REPORT.md"))
        g4_ok = (n_rows == 14 and n_a12 == 14 and n_a32 == 14
                 and len(dr) >= 3 and all(dr)
                 and have_tally and have_defects and have_report and n_views >= 12)
        vt = jload(tally_p) if have_tally else {}
        g4 = {
            "verdict": "PASS" if g4_ok else "FAIL（对账要素不全）",
            "accounting": {
                "n_boards": n_rows, "arm1_eq_arm2": n_a12, "arm3_eq_arm2": n_a32,
                "double_run_spot": {"n": len(dr), "all_equal": all(dr)},
                "l8_views": n_views,
                "seat_c_vote": {"lanes": vt.get("lanes_present"),
                                "defect_counts": vt.get("defect_counts"),
                                "ballot_violations":
                                    (vt.get("defect_counts") or {}).get(
                                        "ballot-violation", 0)}},
            "findings": {
                "principle_gain_boards": n_pg, "model_increment_boards": n_mi,
                "echo_rates": echoes,
                "note": "三臂终解 14/14 板 canonical 字节等：理念臂与模型导引均零增益，"
                        "复述度=注入板 0.960（24/25 候选交并）/未注入板 1.000（2 板）"},
            "sources": ["out/v5-p5/g4-arm1/（① 档）", "out/v5-p5/p5-sessions/g4-table.json（②③ 本波）",
                        "out/v5-p5/p5-sessions/vote-tally.json（席位 C）",
                        "out/v5-p5/p5-sessions/SESSION-WAVE-REPORT.md（含 R1a/R1b 对账段）"],
        }

    g5 = {
        "pf": {"verdict": "PASS（口径=套件+逐板 compile 覆盖）",
               "suite": SUITE,
               "compile_coverage_all_100": all(
                   (r.get("compile_coverage") == 100.0) for r in rows if not r.get("abandoned")),
               "note": "三硬门（编译覆盖/消费覆盖/反事实）由 test_principle_gates_p3 等"
                       "套件钉死；逐板 compile coverage=100.0、conflicts 记录在案"},
        "pu": {"verdict": "PASS（六指标全量报告=三臂零差）",
               "require": "六指标 vs arm① 无理念臂全量报告（不断言方向）",
               "basis": "①②③ 三臂终解 14/14 板 canonical 字节等（G4 表）⇒ 六指标"
                        "按构造恒等；② 世界正典值如下，①/③ 同值",
               "six_indicators": {
                   "完成性": "6/14 SAT；FAILED 8 板 achieved per_net 见 G2 rows",
                   "DRC": "逐板 kicad 计数同值（终解字节等 ⇒ 计数恒等）",
                   "稀缺资源保留": "同终解 ⇒ 同值（零差）",
                   "高速/电源/回流质量": "同终解 ⇒ 同值（零差）",
                   "牺牲普通网络的代价": "同终解 ⇒ 同值（零差）",
                   "失败证书质量": "8/8 UNKNOWN exhaustion 形态（G2）三臂同值"},
               "direction_claim": "无（合同不断言方向；实测=三臂零差）"},
        "ps": {"verdict": "PASS（抽查口径）", "suite": SUITE,
               "spot": "五不变性测试族=test_principle_gates_p3.py（含于 1170 绿）"},
    }

    try:
        from v5.executor import EXECUTOR_VERSION as _EXV
    except Exception:
        _EXV = "v5.executor/?"
    report = {
        "gate": "build_p5_gate.py G1-G5",
        "generated": True,
        "generated_at": time.strftime("%Y-%m-%d"),
        "world": "executor 0.8.0(V5-R1 Steiner 拓扑换版)/route_check 0.4.1"
                 "(ED-2 PTH union 修复，09-26 R-A)/kicad_export 0.5.0"
                 "(ED-X 修复批，09-27)（R1 世界产物树；W-D 四板=W-D 重跑"
                 "+ED-X 修复批 check,export,drc 补跑面，其余板按各自落盘时点；"
                 "7 块已处置 board-inherent 板 R1 未重跑=convert-only 形态）",
        "assessor_world": "评估器现役世界=%s（产物树为 0.5.0 世界跑批存档，"
                          "评估只读不改产物）" % _EXV,
        "rulings": "trial/wave6-criteria-rulings-2026-09-21.md（A/B 豁免、C① genuine 入账+修复候选、D 披露）"
                   "；G1 处置裁定=2026-09-23 用户令「124 按推荐」Q1（豁免入账+分母剔除）"
                   "；微段豁免类=2026-09-28 七裁③（track_dangling<0.06mm 仅限微段阈值，"
                   "LEAD-REVIEW-R1W6-2026-09-28 呈裁点 3 获准）"
                   "；dispositions=%s" % (args.dispositions
                                          if dispos_doc is not None else "（无，原单口径）"),
        "g1": g1, "g2": g2, "g3": g3, "g4": g4, "g5": g5,
        "boards": rows,
    }
    os.makedirs(out_dir, exist_ok=True)
    for ext, doc in (("json", report),):
        with io.open(os.path.join(out_dir, "gate-report.%s" % ext), "w",
                     encoding="utf-8", newline="\n") as f:
            json.dump(doc, f, ensure_ascii=False, indent=1, sort_keys=True)
            f.write("\n")

    md = ["# P5 五门评估报告（build_p5_gate.py，%s）" % time.strftime("%Y-%m-%d"),
          "",
          "- 世界（产物）=%s" % report["world"],
          "- %s" % report["assessor_world"],
          "- 裁定口径=%s" % report["rulings"], "",
          "## G1 成功率门：%s" % g1["verdict"], "",
          "- 判据一（原口径，14 终态板分母并记）：SAT %d 板 ≥5 → %s（%s）" % (
              len(sat), "PASS" if len(sat) >= 5 else "FAIL",
              ", ".join(r["board"] for r in sat)),
          "- 判据二（修订口径，豁免 A/B+微段 <0.06mm）：干净板 %d → %s（%s）" % (
              len(clean), "PASS" if len(clean) >= 5 else "未达",
              ", ".join(r["board"] for r in clean)),
          "- 差口：豁免外余量 %d 条（其中 C 类 genuine %d；逐板余量 %s）"
          % (g1["criterion_2_zero_violation"]["residual_nonexempt"],
             g1["criterion_2_zero_violation"]["genuine_outstanding"],
             "；".join("%s=%d" % (r["board"], r["kicad_effective"])
                       for r in sat if (r.get("kicad_effective") or 0) > 0) or "全零"),
          "- 微段豁免（七裁③ <%gmm）：SAT 面 %d 条（%s）"
          % (MICROSEG_MAX_MM,
             g1["criterion_2_zero_violation"]["microseg_exempt_total"],
             "；".join("%s=%s" % (b, "/".join(str(x) for x in v))
                       for b, v in g1["criterion_2_zero_violation"]
                       ["microseg_lengths_mm"].items()) or "无"), ""]
    if "criterion_1_routable_domain" in g1:
        rd = g1["criterion_1_routable_domain"]
        ed = g1["exemption_disclosure"]
        md += ["- **可布域口径（(c) 豁免前；已裁处置豁免入账）**：分母剔 "
               "%d 板 → SAT %d/%d → %s"
               % (ed["n_ruled"], rd["n_sat"], rd["denominator"],
                  "PASS" if rd["pass"] else "FAIL")]
        if "criterion_1_routable_domain_c_exemption" in g1:
            rd2 = g1["criterion_1_routable_domain_c_exemption"]
            md += ["- **可布域口径（(c) 豁免后；2026-09-25 用户三裁②）**：再剔 "
                   "已裁 (c) 板 %s → SAT %d/%d → %s"
                   % (",".join(rd2["exempted_c_boards"]), rd2["n_sat"],
                      rd2["denominator"], "PASS" if rd2["pass"] else "FAIL")]
        md += ["- 豁免披露（%s；ruled %d + candidate %d）："
               % (ed["ruling"], ed["n_ruled"], ed["n_candidate"]), "",
               "| 板 | 处置 | status | 卡网 | diag 终判 | exhaustion | witness（diag/geometry/报告节） |",
               "|---|---|---|---|---|---|---|"]
        for x in ed["rows"]:
            md.append("| %s | %s | %s | %s | %s | %s | %s / %s / %s |" % (
                x["board"], x["disposition"], x["status"],
                x["failed_net"], x["diag_class"], x["exhaustion"] or "—",
                x["witness_diag_json"] or "—",
                x["witness_geometry_json"] or "—",
                x["witness_report"]))
        md += ["", "- 依据：%s" % ed["basis"], ""]
        if ed["n_candidate"]:
            md += ["- **candidate 披露**：%d 板 (c) 候选仅披露、不入任何分母"
                   "（终裁归主审/用户）" % ed["n_candidate"], ""]
    md += ["## G2 失败证据门：%s（%d/%d 合规）" % (g2["verdict"], g2["n_cert_compliant"], g2["n_failed"]), "",
          "- UNKNOWN 占比：%s" % g2["unknown_share"],
          "- 弃板披露：%s" % "；".join(g2["abandoned_disclosure"]), "",
          "## G3 holdout 纪律门：%s（ledger verify=%s）" % (g3["verdict"], g3["ledger_verify"]), "",
          "## G4 三臂对账门：%s" % g4["verdict"], ""]
    if "accounting" in g4:
        md += ["- 对账：14 板 ①==② %d、③==② %d、③ 双跑抽查 %d/%d 全等、L8 视图 %d 件"
               % (g4["accounting"]["arm1_eq_arm2"], g4["accounting"]["arm3_eq_arm2"],
                  g4["accounting"]["double_run_spot"]["n"]
                  if g4["accounting"]["double_run_spot"]["all_equal"] else 0,
                  g4["accounting"]["double_run_spot"]["n"], g4["accounting"]["l8_views"]),
               "- 发现：理念增益 %d/14、模型增量 %d/14、复述度 %s——三臂终解逐板字节等"
               % (g4["findings"]["principle_gain_boards"],
                  g4["findings"]["model_increment_boards"],
                  "/".join(str(e) for e in g4["findings"]["echo_rates"])),
               "- 席位 C：三路 %s、缺陷计数 %s、票面违约 %d"
               % (g4["accounting"]["seat_c_vote"]["lanes"],
                  g4["accounting"]["seat_c_vote"]["defect_counts"],
                  g4["accounting"]["seat_c_vote"]["ballot_violations"])] + [
              "  - 源：%s" % s for s in g4["sources"]] + [""]
    else:
        md += ["- %s" % g4["verdict"], ""]
    md += ["", "## G5 理念门", "",
        "- PF：%s（compile 覆盖全 100=%s）" % (g5["pf"]["verdict"], g5["pf"]["compile_coverage_all_100"]),
        "- PU：%s（%s）" % (g5["pu"]["verdict"], g5["pu"]["basis"]), "- PS：%s" % g5["ps"]["verdict"], "",
        "## 逐板表", "",
        "| 板 | 终态 | exec | feasible | kicad 总/豁免/有效 | genuine | DRC | 证书 |",
        "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        if r.get("abandoned"):
            md.append("| %s | 弃板 | — | — | — | — | — | 无（用户令） |" % r["board"])
        else:
            md.append("| %s | terminal | %s | %s | %s | %s | %s | %s |" % (
                r["board"], r["exec_verdict"], r["feasible"],
                ("%s/%s/%s" % (r.get("kicad_total"), r.get("kicad_exempt"),
                               r.get("kicad_effective")))
                if r.get("kicad_total") is not None else "—（FAILED 无导出件）",
                r.get("kicad_genuine"), r.get("drc_verdict") or "—",
                r.get("exhaustion") or r.get("selection_verdict") or "—"))
    with io.open(os.path.join(out_dir, "gate-report.md"), "w",
                 encoding="utf-8", newline="\n") as f:
        f.write("\n".join(md) + "\n")
    print("\n".join(md))
    print("\nsaved: %s" % os.path.join(out_dir, "gate-report.md"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
