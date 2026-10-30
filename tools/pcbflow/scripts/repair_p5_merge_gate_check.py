# -*- coding: utf-8 -*-
"""REPAIR-P5 W-3 仓库合入验收边界检查（merge-gate-check）。

任务书 exec/REPAIR-P5-SIGNOFF-BOUNDARY-TASKBOOK-2026-09-13.md §3 W-3：
「合入签核」（区别于生产签核）四门中**机器可查的前三门**的轻量检查器：
  G1 全量 0F/0E（对照 baseline.json；collect-only 实测对账 + 可选 --pytest-log 终读解析）
  G2 REPAIR-P2 fail-closed 注入矩阵绿（tests/test_fail_closed_injection.py 实跑）
  G3 保护锚一致（受保护三件 + M0 三锚，期望值跟随登记件链）
  G4 主审独立复核四件套记录在案（人工面，仅登记不判绿）
输出 out/repair-p5/merge-gate-check-r1.json（--out 可覆盖）。
本脚本只读检查+写自身产物；不重跑全量（~45 分钟级，见 baseline.json 刷新纪律）。
"""
import argparse
import json
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from pcbflow.hashing import canonical_json_bytes, sha256_file

REPO = Path(__file__).resolve().parents[1]  # tools/pcbflow

# M0 只读单件锚期望值：critic/svg_route_package 自 V4.2 立锚以来零变更（P3S/P4 复核），
# 无盘上登记件持值——期望值载体=REPAIR-P5 任务书 §5（L2 冻结件，**只载前 8 位 hex**，
# 故按前缀比对、不编造完整值）；route_grid 为 P3S 授权变更后新锚，
# 跟随 out/repair-p3s/anchor-change-registration.json（完整 64 位）。
M0_ANCHOR_TASKBOOK_PREFIX8 = {
    "pcbflow/critic.py": "42fe2769",
    "pcbflow/svg_route_package.py": "28135ec4",
}
P3S_ANCHOR_REG = "out/repair-p3s/anchor-change-registration.json"
INJECTION_TEST = "tests/test_fail_closed_injection.py"


def _run(cmd, cwd):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


def _parse_pytest_tail(stdout: str):
    """从 pytest -q 输出解析计数。

    P2 教训④（EXP 在案）：-q 输出在管道/文件重定向下**末尾总结行缺失**——
    计数只能取两处可靠源：
    - collect-only：逐文件汇总行 ``path.py: N`` 求和（末行汇总若在则交叉校验）；
    - 运行输出：进度块行（含 ``[ N%]``）的逐字符统计（.=passed/x=xfailed/F=failed/E=error）。
    """
    passed = failed = errors = xfailed = 0
    for line in stdout.splitlines():
        if "[100%]" in line or re.search(r"\[\s*\d+%\]", line):
            for ch in line:
                if ch == ".":
                    passed += 1
                elif ch == "x":
                    xfailed += 1
                elif ch == "F":
                    failed += 1
                elif ch == "E":
                    errors += 1
    # collect-only 文件级汇总行求和（若有；末行汇总缺失时唯一可靠源）
    collected = sum(int(n) for n in
                    re.findall(r"^\S+\.py:\s*(\d+)\s*$", stdout, re.M)) or None
    return {"passed": passed, "failed": failed, "errors": errors,
            "xfailed": xfailed, "collected": collected}


def gate1_full_suite(args) -> dict:
    baseline = json.loads((REPO / "baseline.json").read_text(encoding="utf-8"))
    result = baseline.get("result", {})
    struct_ok = (result.get("failed") == 0 and result.get("errors") == 0
                 and result.get("total_collected", 0) > 0)
    details = {
        "gate": "G1 全量 0F/0E（对照 baseline.json）",
        "baseline_reading": {
            "total_collected": result.get("total_collected"),
            "passed": result.get("passed"), "failed": result.get("failed"),
            "errors": result.get("errors"), "xfailed": result.get("xfailed"),
            "recorded_at": baseline.get("recorded_at"),
        },
    }
    # 机器可查子项 a：collect-only 实测收集数对账
    cp = _run([sys.executable, "-m", "pytest", "--collect-only", "-q"], REPO)
    counts = _parse_pytest_tail(cp.stdout)
    collect_match = (counts["collected"] is not None
                     and counts["collected"] == result.get("total_collected"))
    details["collect_only"] = {
        "exit_code": cp.returncode,
        "collected_observed": counts["collected"],
        "baseline_total": result.get("total_collected"),
        "match": collect_match,
    }
    # 机器可查子项 b：可选 --pytest-log 终读解析（全量实跑文本）
    if args.pytest_log:
        log = Path(args.pytest_log)
        if log.is_file():
            counts2 = _parse_pytest_tail(log.read_text(encoding="utf-8",
                                                       errors="replace"))
            log_ok = counts2["failed"] == 0 and counts2["errors"] == 0
            details["pytest_log"] = {"path": str(log),
                                     "parsed": counts2, "zero_f_zero_e": log_ok}
        else:
            details["pytest_log"] = {"path": str(log),
                                     "status": "not_available",
                                     "reason": "日志文件不存在（fail-closed 如实登记）"}
    else:
        details["pytest_log"] = {
            "status": "not_available",
            "reason": "未提供 --pytest-log（全量实跑摘要；提供后解析 0F/0E）"}
    verdict_parts = [struct_ok, collect_match]
    if "zero_f_zero_e" in details.get("pytest_log", {}):
        verdict_parts.append(details["pytest_log"]["zero_f_zero_e"])
    details["verdict"] = "pass" if all(verdict_parts) else "fail"
    return details


def gate2_injection_matrix() -> dict:
    t0 = time.monotonic()
    cp = _run([sys.executable, "-m", "pytest", INJECTION_TEST, "-q"], REPO)
    dur = round(time.monotonic() - t0, 1)
    counts = _parse_pytest_tail(cp.stdout)
    ok = (cp.returncode == 0 and counts["failed"] == 0
          and counts["errors"] == 0 and counts["passed"] > 0)
    return {
        "gate": "G2 REPAIR-P2 fail-closed 注入矩阵绿",
        "command": f"python -m pytest {INJECTION_TEST} -q",
        "exit_code": cp.returncode,
        "parsed": counts,
        "duration_s": dur,
        "verdict": "pass" if ok else "fail",
    }


def gate3_anchors() -> dict:
    findings, ok = [], True
    baseline = json.loads((REPO / "baseline.json").read_text(encoding="utf-8"))
    # a) 受保护三件：期望值=baseline.json（入库权威，随两步法刷新自动跟随）
    for rel, want in baseline.get("protected_files_sha256", {}).items():
        got = sha256_file(REPO / rel)
        match = got == want
        ok &= match
        findings.append({"file": rel, "expected_from": "baseline.json",
                         "match": match, "observed": got[:16],
                         "expected": want[:16]})
    # b) route_grid.py：期望值=P3S 授权变更登记件（自动跟随登记链）
    reg = json.loads((REPO / P3S_ANCHOR_REG).read_text(encoding="utf-8"))
    want = reg["new_sha256"]
    got = sha256_file(REPO / "pcbflow/route_grid.py")
    match = got == want
    ok &= match
    findings.append({"file": "pcbflow/route_grid.py",
                     "expected_from": P3S_ANCHOR_REG,
                     "match": match, "observed": got[:16],
                     "expected": want[:16]})
    # c) critic/svg_route_package：期望值=P5 任务书 §5 冻结前 8 位（按前缀比对）
    for rel, want8 in M0_ANCHOR_TASKBOOK_PREFIX8.items():
        got = sha256_file(REPO / rel)
        match = got.startswith(want8)
        ok &= match
        findings.append({"file": rel,
                         "expected_from": "REPAIR-P5 任务书 §5（前 8 位，前缀比对）",
                         "match": match, "observed": got[:16],
                         "expected": want8})
    return {
        "gate": "G3 保护锚一致（受保护三件+M0 三锚）",
        "files": findings,
        "verdict": "pass" if ok else "fail",
    }


def gate4_lead_review_record() -> dict:
    reviews = sorted((REPO / "exec").glob("LEAD-REVIEW-*.md"),
                     key=lambda p: p.stat().st_mtime, reverse=True)
    recent = [{"file": p.name,
               "mtime": datetime.fromtimestamp(p.stat().st_mtime)
               .strftime("%Y-%m-%d %H:%M")}
              for p in reviews[:3]]
    return {
        "gate": "G4 主审独立复核四件套记录在案（人工面，仅登记不判绿）",
        "total_lead_reviews": len(reviews),
        "recent": recent,
        "verdict": "recorded" if reviews else "not_available",
        "note": "四门口径：机器三门（G1–G3）绿 + 本门复核记录在案 ⇒ 合入签核过；"
                "复核内容本身属人工审阅面（审查才是验收门纪律）",
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default="out/repair-p5/merge-gate-check-r1.json")
    ap.add_argument("--pytest-log", default=None,
                    help="可选：最近全量 pytest -q 输出文本（解析 0F/0E 终读）")
    ap.add_argument("--skip-g2", action="store_true",
                    help="跳过注入矩阵实跑（调试用；verdict=not_available）")
    args = ap.parse_args(argv)

    g1 = gate1_full_suite(args)
    g2 = ({"gate": "G2 REPAIR-P2 fail-closed 注入矩阵绿",
           "verdict": "not_available",
           "reason": "--skip-g2（调试跳过实跑）"} if args.skip_g2
          else gate2_injection_matrix())
    g3 = gate3_anchors()
    g4 = gate4_lead_review_record()

    machine_gates = [g1, g2, g3]
    overall = ("merge_gate_pass" if all(g["verdict"] == "pass"
                                        for g in machine_gates)
               and g4["verdict"] == "recorded"
               else "merge_gate_fail_or_pending")
    artifact = {
        "artifact_kind": "merge_gate_check",
        "schema_version": "1.0",
        "generated_by": "scripts/repair_p5_merge_gate_check.py (REPAIR-P5 W-3)",
        "checked_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S+08:00"),
        "definition": "STATUS.md「仓库合入验收边界（合入签核）」节；"
                      "区别于生产签核（production_signoff_ready=false 维持）",
        "gates": {"G1": g1, "G2": g2, "G3": g3, "G4": g4},
        "overall": overall,
    }
    out = REPO / args.out if not Path(args.out).is_absolute() else Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(canonical_json_bytes(artifact))
    print(f"[merge_gate_check] overall={overall}")
    for k, g in artifact["gates"].items():
        print(f"  {k}: {g['verdict']}")
    print(f"  → {out}")
    return 0 if overall == "merge_gate_pass" else 1


if __name__ == "__main__":
    sys.exit(main())
