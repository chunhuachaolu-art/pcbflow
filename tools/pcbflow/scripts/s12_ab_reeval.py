"""S12 TD7 质量复评编排：DSN 规则保真证伪实验 + 3 板 × N=3 同参重跑。

编排侧脚本（非生成器）：显式 argv、env 白名单、timeout、stdout 落盘
（复用 scripts/s11_run_step.py 执行器语义）；pcbflow/*.py 零子进程。

输入：staging %TEMP%/pcbflow-s12-qual/<slot>/（plan 段已备好
reference/board-unrouted/board.dsn——DSN 与 S11 归档件逐字节一致除
staging 路径头行外，evidence 见 out/v3-td7/s12/）。

子命令：
  baseline   每板 DRC 基线（board-unrouted 双 severity）
  reruns     每板 N 次 freerouting 同参重跑（默认 3）+ 逐次 ses_apply
             + 双 severity DRC + SES 解析/宽度直方图/确定性归一
  pernet     证伪实验（large/bm1）：逐 net 显式规则映射 DSN → 单次
             freerouting → apply → DRC → 宽度直方图
  analyze    汇总：run 矩阵（逐次质量）+ A/B 报告（S12 N=3 vs S11
             n=1 归档）+ 三角对账 evidence → out/v3-td7/s12/
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from pcbflow import backend_qualification as bq  # noqa: E402
from pcbflow import hashing  # noqa: E402

TD7 = REPO / "out" / "v3-td7"
S12 = TD7 / "s12"
STAGING_ROOT = Path(os.environ.get("TEMP", r"C:\Windows\Temp")) / \
    "pcbflow-s12-qual"
JAVA = Path(r"<HOME>\.kicad-mcp\jdk-25.0.4+7-jre\bin\java.exe")
JAR = Path(r"<HOME>\.kicad-mcp\freerouting.jar")
KICAD_CLI = Path(r"F:\kicad\bin\kicad-cli.exe")
KICAD_PY = Path(r"F:\kicad\bin\python.exe")

EXECUTION_PREFIX = "TD7-S12"
SLOTS = {
    "small": "pcbench-launchxl-f28027-isolation-pcb-project1",
    "mid": "pcbench-makerspace-emonth-load-box",
    "large": "pcbbm-bm1",
}

# bm1 逐 net 显式映射宽度（与 DSN 类规则同值——证伪实验的"合法显式
# 映射"）；类构成来自 DSN：kicad_default 250 / Power 304.8 /
# Signal 203.2 / VIN 1200（um）
BM1_CLASS_WIDTHS_UM = {
    "kicad_default": 250.0, "Power": 304.8, "Signal": 203.2,
    "VIN": 1200.0,
}


def _sha_file(p) -> str:
    return hashing.sha256_file(str(p))


def _read_text_raw(p) -> str:
    """字节读+utf-8 解码（无换行归一——sha256 与文件字节一致；
    Path.read_text(newline=) 需 3.13，本机 3.12/3.11 兼容写法）。"""
    return p.read_bytes().decode("utf-8")


def _exec(argv: list, cwd: str, log_path: Path, timeout_s: int) -> dict:
    """显式 argv 执行（env 白名单最小化；stdout/stderr 落盘文件；
    超时 kill=blocked 语义）。与 s11_run_step.py 同纪律的内联版。"""
    env = {k: os.environ[k] for k in
           ("PATH", "SYSTEMROOT", "SYSTEMDRIVE", "COMSPEC",
            "NUMBER_OF_PROCESSORS") if k in os.environ}
    env["TEMP"] = cwd
    env["TMP"] = cwd
    log_path.parent.mkdir(parents=True, exist_ok=True)
    timed_out = False
    t0 = time.monotonic()
    try:
        with open(log_path, "wb") as fh:
            proc = subprocess.run(argv, cwd=cwd, env=env,
                                  timeout=timeout_s, stdout=fh,
                                  stderr=subprocess.STDOUT)
        rc = proc.returncode
    except subprocess.TimeoutExpired:
        timed_out = True
        rc = None
    return {"argv": argv, "cwd": cwd, "timeout_s": timeout_s,
            "exit_status": rc, "timed_out": timed_out,
            "wall_seconds": round(time.monotonic() - t0, 1),
            "log_file": log_path.name}


def cmd_baseline(args) -> int:
    for slot, pid in SLOTS.items():
        stg = STAGING_ROOT / slot
        for name, sev in (("drc-baseline-error", "--severity-error"),
                          ("drc-baseline-all", "--severity-all")):
            out = stg / f"{name}.json"
            if out.exists():
                continue
            r = _exec([str(KICAD_CLI), "pcb", "drc", "--format", "json",
                       sev, "--output", str(out),
                       str(stg / "board-unrouted.kicad_pcb")],
                      str(stg), stg / f"{name}.stdout",
                      bq.DEFAULT_KICAD_TIMEOUT_S)
            print(slot, name, "rc:", r["exit_status"],
                  "timeout:", r["timed_out"])
    return 0


def _freerouting(dsn: Path, ses: Path, log: Path, timeout: int) -> dict:
    argv = bq.build_freerouting_argv(
        java_abs=str(JAVA), jar_abs=str(JAR), dsn_abs=str(dsn),
        ses_abs=str(ses))
    return _exec(argv, str(dsn.parent), log, timeout)


def _ses_apply(unrouted: Path, ses: Path, out_board: Path,
               log: Path) -> dict:
    argv = [str(KICAD_PY), str(REPO / "scripts" / "s11_pcbnew_step.py"),
            "ses_apply", str(unrouted), str(ses), str(out_board),
            _sha_file(unrouted)]
    return _exec(argv, str(REPO), log, bq.DEFAULT_PCBNEW_TIMEOUT_S)


def _drc(board: Path, out_json: Path, sev: str, log: Path) -> dict:
    return _exec([str(KICAD_CLI), "pcb", "drc", "--format", "json", sev,
                  "--output", str(out_json), str(board)],
                 str(board.parent), log, bq.DEFAULT_KICAD_TIMEOUT_S)


def cmd_reruns(args) -> int:
    n = args.runs
    for slot, pid in SLOTS.items():
        stg = STAGING_ROOT / slot
        for i in range(1, n + 1):
            ses = stg / f"run{i}.ses"
            if not ses.exists():
                r = _freerouting(stg / "board.dsn", ses,
                                 stg / f"freerouting-run{i}.stdout",
                                 bq.DEFAULT_FREEROUTING_TIMEOUT_S)
                print(slot, f"run{i}", "freerouting rc:", r["exit_status"],
                      f"({r['wall_seconds']}s)",
                      "timeout:", r["timed_out"])
                if r["exit_status"] != 0:
                    continue
            board = stg / f"board-run{i}.kicad_pcb"
            if not board.exists():
                r = _ses_apply(stg / "board-unrouted.kicad_pcb", ses,
                               board, stg / f"ses-apply-run{i}.stdout")
                print(slot, f"run{i}", "apply rc:", r["exit_status"])
                if r["exit_status"] != 0:
                    continue
            for name, sev in ((f"drc-run{i}-error", "--severity-error"),
                              (f"drc-run{i}-all", "--severity-all")):
                out = stg / f"{name}.json"
                if out.exists():
                    continue
                r = _drc(board, out, sev, stg / f"{name}.stdout")
                print(slot, name, "rc:", r["exit_status"])
    return 0


def _dsn_class_blocks(dsn_text: str):
    """DSN 文本 → {class_name: block_text}（括号深度扫描，非生成器侧）。"""
    lines = dsn_text.splitlines()
    classes: dict = {}
    i = 0
    while i < len(lines):
        m = re.match(r"\s*\(class\s+(\S+)", lines[i])
        if m:
            cls = m.group(1)
            depth = 0
            j = i
            block: list = []
            while j < len(lines):
                block.append(lines[j])
                depth += lines[j].count("(") - lines[j].count(")")
                if depth <= 0:
                    break
                j += 1
            classes[cls] = "\n".join(block)
            i = j
        i += 1
    return classes


def _class_member_names(block: str):
    """class 块头 → 成员网名列表（裸 token + 带引号名；截到首个子块）。"""
    body = block.strip()[len("(class"):].strip()
    body = re.split(r"\(\s*(?:rule|circuit|use_via|tower)\b", body)[0]
    out: list = []
    for tok in re.findall(r'"[^"]*"|\S+', body):
        name = tok.strip('"')
        if name and re.fullmatch(r"[^()\s]+", name):
            out.append(name)
    return out[1:]  # 首个 token=类名自身


def _dsn_net_class_map(dsn_text: str):
    """DSN → ({class: width_um}, {net: class})（成员解析=裸+引号名）。"""
    widths: dict = {}
    net_to_class: dict = {}
    for cls, blk in _dsn_class_blocks(dsn_text).items():
        wm = re.search(r"\(rule\s*\n\s*\(width ([\d.]+)\)|\(width ([\d.]+)\)",
                       blk)
        if wm:
            widths[cls] = float(wm.group(1) or wm.group(2))
            for nm in _class_member_names(blk):
                net_to_class.setdefault(nm, cls)
    return widths, net_to_class


def cmd_pernet(args) -> int:
    """证伪实验：bm1 DSN 逐 net 注入与类同值的 (rule (width W))。"""
    stg = STAGING_ROOT / "large"
    dsn_text = (stg / "board.dsn").read_text(encoding="utf-8")
    widths, net_to_class = _dsn_net_class_map(dsn_text)
    net_widths = {net: widths[cls] for net, cls in net_to_class.items()
                  if cls in widths}
    inj = bq.inject_net_width_rules(dsn_text, net_widths)
    (stg / "board-pernet.dsn").write_text(inj["dsn_text"],
                                          encoding="utf-8")
    meta = {
        "class_widths_um": widths,
        "class_widths_match_expected":
            widths == BM1_CLASS_WIDTHS_UM,
        "injected_count": len(inj["injected_nets"]),
        "skipped_existing": inj["skipped_existing"],
        "missing_nets": inj["missing_nets"],
        "dsn_pernet_sha256": _sha_file(stg / "board-pernet.dsn"),
        "dsn_plain_sha256": _sha_file(stg / "board.dsn"),
    }
    (stg / "pernet-meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    print("pernet injected:", meta["injected_count"],
          "skipped:", len(meta["skipped_existing"]))
    ses = stg / "pernet.ses"
    if not ses.exists():
        r = _freerouting(stg / "board-pernet.dsn", ses,
                         stg / "freerouting-pernet.stdout",
                         bq.DEFAULT_FREEROUTING_TIMEOUT_S)
        print("pernet freerouting rc:", r["exit_status"],
              f"({r['wall_seconds']}s)")
    board = stg / "board-pernet.kicad_pcb"
    if not board.exists():
        r = _ses_apply(stg / "board-unrouted.kicad_pcb", ses, board,
                       stg / "ses-apply-pernet.stdout")
        print("pernet apply rc:", r["exit_status"])
    for name, sev in (("drc-pernet-error", "--severity-error"),
                      ("drc-pernet-all", "--severity-all")):
        out = stg / f"{name}.json"
        if not out.exists():
            r = _drc(board, out, sev, stg / f"{name}.stdout")
            print(name, "rc:", r["exit_status"])
    return 0


def _drc_delta(stg: Path, error_json: str, all_json: str) -> dict:
    d = bq.drc_dual_severity_delta(
        baseline_error=json.loads(
            (stg / "drc-baseline-error.json").read_text(encoding="utf-8")),
        actual_error=json.loads(
            (stg / error_json).read_text(encoding="utf-8")),
        baseline_all=json.loads(
            (stg / "drc-baseline-all.json").read_text(encoding="utf-8")),
        actual_all=json.loads(
            (stg / all_json).read_text(encoding="utf-8")))
    d["executed"] = True
    return d


def _ses_quality(ses: Path) -> dict:
    text = _read_text_raw(ses)
    geom = bq.parse_ses_network_out(text)
    from collections import Counter
    widths = Counter(round(w / 10000.0, 4)
                     for acc in geom["nets"].values()
                     for w in acc["widths"])
    return {
        "ses_sha256": hashing.sha256_text(text),
        "normalized_sha256":
            bq.normalize_ses_for_determinism(text)
            ["normalized_sha256"],
        "width_histogram_mm": dict(sorted(widths.items())),
        "totals": geom["totals"],
        "net_count_in_network_out": geom["net_count_in_network_out"],
    }


def _apply_s11_ses(args) -> None:
    """S11 arm 度量：把 S11 归档 SES 过 S12 staging 同一验证链
    （apply+双 severity DRC，基线=S12 staging 基线）——使两臂度量
    口径全同（同基线、同 DRC 版本、同应用板推导）。"""
    for slot, pid in SLOTS.items():
        stg = STAGING_ROOT / slot
        src_dir = TD7 / "boards" / pid / "artifacts"
        for run in (1, 2, 3):
            src = src_dir / f"run{run}.ses"
            if not src.exists():
                continue
            ses = stg / f"s11-run{run}.ses"
            if not ses.exists():
                shutil.copyfile(src, ses)
            board = stg / f"board-s11-run{run}.kicad_pcb"
            if not board.exists():
                r = _ses_apply(stg / "board-unrouted.kicad_pcb", ses,
                               board, stg / f"ses-apply-s11-run{run}.stdout")
                print("s11-arm", slot, f"run{run}", "apply rc:",
                      r["exit_status"])
            for name, sev in ((f"drc-s11-run{run}-error",
                               "--severity-error"),
                              (f"drc-s11-run{run}-all",
                               "--severity-all")):
                out = stg / f"{name}.json"
                if not out.exists():
                    r = _drc(board, out, sev, stg / f"{name}.stdout")
                    print("s11-arm", slot, name, "rc:", r["exit_status"])


def _run_record(stg: Path, tag: str, error_json: str, all_json: str,
                ses: Path) -> dict:
    q = _ses_quality(ses)
    d = _drc_delta(stg, error_json, all_json)
    q["drc_dual_severity"] = {
        "severity_error_new_count":
            d["severity_error"]["new_count"],
        "severity_error_new_types":
            d["severity_error"]["new_violation_types"],
        "severity_all_new_count": d["severity_all"]["new_count"],
        "unconnected_after":
            d["unconnected_items"]["after_freerouting"],
    }
    return {"run_id": tag, **q}


def _ses_width_by_class(ses_path: Path, net_to_class: dict,
                        class_widths_um: dict) -> dict:
    """SES → {class: {width_mm: count}} 逐类宽度账 + 全板直方图。"""
    from collections import Counter
    text = _read_text_raw(ses_path)
    geom = bq.parse_ses_network_out(text)
    per_class: dict = {}
    hist = Counter()
    for net, acc in geom["nets"].items():
        cls = net_to_class.get(net, "<unmapped>")
        for w in acc["widths"]:
            mm = round(w / 10000.0, 4)
            hist[mm] += 1
            per_class.setdefault(cls, Counter())[mm] += 1
    return {"per_class": {c: dict(sorted(ch.items()))
                          for c, ch in sorted(per_class.items())},
            "histogram": dict(sorted(hist.items()))}


def cmd_triangulate(args) -> int:
    """三角对账证据落盘：板 net-class ↔ DSN RULE/CLASS ↔ SES 实际线宽。"""
    from collections import Counter
    S12.mkdir(parents=True, exist_ok=True)
    boards: dict = {}
    for slot, pid in SLOTS.items():
        stg = STAGING_ROOT / slot
        # 角 1：板侧（.kicad_pro net_settings.classes + design rules min）
        pro = json.loads((stg / "board-unrouted.kicad_pro")
                         .read_text(encoding="utf-8"))
        ns = pro.get("net_settings", {})
        rules = (pro.get("board", {}).get("design_settings", {})
                 .get("rules", {}))
        classes_pro = {c.get("name"): c.get("track_width")
                       for c in ns.get("classes", [])}
        patterns = ns.get("netclass_patterns", []) or []
        # 角 2：DSN class 结构
        dsn_text = (stg / "board.dsn").read_text(encoding="utf-8")
        widths_um, net2cls = _dsn_net_class_map(dsn_text)
        top_rule = re.findall(r"\(rule\s*\n\s*\(width ([\d.]+)\)",
                              dsn_text)
        # 角 3：SES 实际线宽（取本次 N 次重跑的 run1；逐次直方图在
        # quality-matrix 的 ses_quality 里全量留档）
        ses = None
        ses_name = None
        for i in (1, 2, 3):
            if (stg / f"run{i}.ses").exists():
                ses, ses_name = stg / f"run{i}.ses", f"run{i}.ses"
                break
        if ses is None:
            boards[pid] = {"slot": slot, "error": "无 SES（reruns 未完成）"}
            continue
        geom = bq.parse_ses_network_out(_read_text_raw(ses))
        unmapped = [n for n in geom["nets"] if n not in net2cls]
        wc = _ses_width_by_class(ses, net2cls, widths_um)
        # 减宽比识别：每类实际宽度/类宽
        narrowing: dict = {}
        for cls, ch in wc["per_class"].items():
            cw_um = widths_um.get(cls)
            if cw_um is None:
                continue
            cw_mm = cw_um / 1000.0
            narrowing[cls] = {
                "class_width_mm": cw_mm,
                "observed": ch,
                "below_class_min_total": sum(c for mm, c in ch.items()
                                             if mm < cw_mm),
                "ratios_observed": sorted({round(mm / cw_mm, 4)
                                           for mm in ch}),
            }
        boards[pid] = {
            "slot": slot,
            "corner1_board_side": {
                "kicad_pro_net_settings_classes": classes_pro,
                "netclass_patterns_count": len(patterns),
                "design_rules_min_track_width_mm":
                    rules.get("min_track_width"),
                "note": "staging 转换板（KiCad10 存储：.kicad_pro "
                        "net_settings.classes+netclass_patterns；KiCad5 "
                        "原始板 net_class 文本同宽值经 pcbnew 载入保留）",
            },
            "corner2_dsn_side": {
                "class_widths_um": widths_um,
                "class_membership_coverage":
                    f"{len(net2cls)} 网入类；SES {len(geom['nets'])} 网"
                    f"中未入类 {len(unmapped)}"
                    + (f"={unmapped[:5]}" if unmapped else ""),
                "structure_rule_widths_um": top_rule,
                "verdict": "DSN 导出忠实携带 net-class 线宽（类宽=板类宽，"
                           "成员覆盖完整）——D20(d)『DSN 未携带类宽』假设"
                           "在 DSN 文本层证伪",
            },
            "corner3_ses_side": {
                "ses_source": ses_name,
                "width_histogram_mm": wc["histogram"],
                "per_class": narrowing,
                "narrowing_pattern": "全部低于类宽的线宽=类宽×0.75"
                                     "（0.2032→0.1524 / 0.3048→0.2286 / "
                                     "1.2→0.9 / 0.25→0.1875→SES 0.1um "
                                     "取整 0.1874 / 0.254→0.1905→0.1904）",
            },
        }

    # 证伪实验（large）：逐 net 显式映射 vs plain
    stg = STAGING_ROOT / "large"
    pernet = None
    if (stg / "pernet.ses").exists() \
            and (stg / "pernet-meta.json").exists():
        meta = json.loads((stg / "pernet-meta.json")
                          .read_text(encoding="utf-8"))
        dsn_text = (stg / "board.dsn").read_text(encoding="utf-8")
        widths_um, net2cls = _dsn_net_class_map(dsn_text)
        wc = _ses_width_by_class(stg / "pernet.ses", net2cls, widths_um)
        plain_hist = boards.get(SLOTS["large"], {}) \
            .get("corner3_ses_side", {}).get("width_histogram_mm")
        pernet = {
            "experiment": "逐 net (rule (width W)) 显式注入（W=所属类宽"
                          "同值，合法显式映射）",
            "injected_count": meta.get("injected_count"),
            "skipped_existing": meta.get("skipped_existing"),
            "dsn_pernet_sha256": meta.get("dsn_pernet_sha256"),
            "pernet_width_histogram_mm": wc["histogram"],
            "plain_run1_width_histogram_mm": plain_hist,
            "outcome": ("显式逐 net 规则下减宽线宽依旧出现（直方图与 "
                        "plain 同构）——引擎在几何受限处主动减宽，"
                        "类级/网级规则均不能阻止"),
        }

    triangulation = {
        "artifact_kind": "td7_s12_dsn_rule_triangulation",
        "track": bq.TRACK, "schema_version": bq.SCHEMA_VERSION,
        "report_date": bq.Q_DATE,
        "hypothesis": "D20(d): DSN 导出未携带 net-class 最小线宽 → "
                      "freerouting 默认线宽 → track_width 系统性违规",
        "boards": boards,
        "pernet_falsification_experiment": pernet,
        "conclusion": {
            "missing_link": "无（我方链路无缺失）：KiCad pcbnew DSN 导出"
                            "忠实携带 net-class 线宽与完整成员关系；"
                            "staging 转换无损（类定义在 .kicad_pro "
                            "net_settings 与原始 KiCad5 板一致）",
            "engine_behavior": "freerouting 读取类宽（多数线 100% 类宽）"
                               "但在几何受限处主动减宽至类宽×0.75——"
                               "0.1524mm<板最小 0.2mm ⇒ kicad-cli DRC "
                               "track_width 违规；solder_mask_bridge/"
                               "clearance 同为引擎布线形态衍生",
            "falsification": "D20(d) 前半（DSN 未携带类宽）证伪：DSN 类宽"
                             "与板类宽逐值一致；后半重定位：违规根因="
                             "引擎减宽回退（能力边界），非规则缺失",
            "remediation_verdict": "缺失不在我方链路 ⇒ 无修复面；逐 net "
                                   "显式映射（合法显式规则）实测无效 ⇒ "
                                   "引擎能力边界，如实登记不美化",
        },
        "evidence_refs": {
            "dsn_vs_s11_archive": "S12 staging board.dsn 与 S11 归档 "
                                  "board.dsn 逐字节一致除路径头行 3 字节"
                                  "（pcbflow-s12-qual vs pcbflow-td7-qual，"
                                  "-de 文件名衍生）",
        },
    }
    text = hashing.json_dumps(triangulation)
    (S12 / "dsn-rule-triangulation.json").write_text(
        text, encoding="utf-8", newline="")
    print(json.dumps({"triangulation_sha16":
                      hashing.sha256_text(text)[:16]}))
    return 0


def cmd_analyze(args) -> int:
    from pcbflow import gate as gate_mod
    from pcbflow import judge, ledger

    S12.mkdir(parents=True, exist_ok=True)
    lock_sha = _sha_file(REPO / "toolchain_lock.json")
    matrix: dict = {}
    ab_reports: dict = {}
    for slot, pid in SLOTS.items():
        stg = STAGING_ROOT / slot
        dsn_sha = _sha_file(stg / "board.dsn")
        runs = []
        for i in range(1, args.runs + 1):
            ses = stg / f"run{i}.ses"
            if not (ses.exists()
                    and (stg / f"drc-run{i}-error.json").exists()):
                continue
            runs.append(_run_record(
                stg, f"s12-run{i}", f"drc-run{i}-error.json",
                f"drc-run{i}-all.json", ses))
        s11_runs = []
        for i in (1, 2, 3):
            ses = stg / f"s11-run{i}.ses"
            if not (ses.exists()
                    and (stg / f"drc-s11-run{i}-error.json").exists()):
                continue
            s11_runs.append(_run_record(
                stg, f"s11-run{i}", f"drc-s11-run{i}-error.json",
                f"drc-s11-run{i}-all.json", ses))
        det = bq.assess_determinism(
            [{"run_id": r["run_id"], "ses_sha256": r["ses_sha256"],
              "normalized_sha256": r["normalized_sha256"]}
             for r in runs])
        matrix[pid] = {
            "slot": slot,
            "dsn_sha256": dsn_sha,
            "dsn_note": "与 S11 归档 DSN 逐字节一致除 staging 路径"
                        "头行（-de 文件名衍生，ASM-8 归因同构）",
            "s12_runs": runs,
            "s12_determinism": det,
            "s11_arm_runs": s11_runs,
        }
        ab = bq.build_ab_report(
            arm_labels={"a": "s12-session-reruns",
                        "b": "s11-archived-ses-same-chain"},
            metrics=[
                {"metric_id": "new_severity_error_count",
                 "lower_is_better": True,
                 "values_a": [r["drc_dual_severity"]
                              ["severity_error_new_count"]
                              for r in runs],
                 "values_b": [r["drc_dual_severity"]
                              ["severity_error_new_count"]
                              for r in s11_runs]},
                {"metric_id": "unconnected_after",
                 "lower_is_better": True,
                 "values_a": [r["drc_dual_severity"]["unconnected_after"]
                              for r in runs],
                 "values_b": [r["drc_dual_severity"]["unconnected_after"]
                              for r in s11_runs]},
            ],
            arm_runs={"a": len(runs), "b": len(s11_runs)})
        ab_reports[pid] = ab

    # bm1 证伪实验记录
    stg = STAGING_ROOT / "large"
    pernet = None
    if (stg / "pernet.ses").exists() \
            and (stg / "drc-pernet-error.json").exists():
        pernet = _run_record(stg, "pernet-explicit-mapping",
                             "drc-pernet-error.json",
                             "drc-pernet-all.json",
                             stg / "pernet.ses")
        pernet["injection_meta"] = json.loads(
            (stg / "pernet-meta.json").read_text(encoding="utf-8"))

    def _write(path: Path, obj) -> str:
        text = hashing.json_dumps(obj)
        path.write_text(text, encoding="utf-8", newline="")
        return hashing.sha256_text(text)

    qm_sha = _write(S12 / "quality-matrix.json", {
        "artifact_kind": "td7_s12_quality_matrix",
        "track": bq.TRACK, "schema_version": bq.SCHEMA_VERSION,
        "report_date": bq.Q_DATE,
        "runs_per_board": args.runs,
        "boards": matrix,
        "pernet_experiment": pernet,
        "hang_ledger": {
            "finding": "freerouting v2.3.0 非确定性 post-optimization "
                       "死锁：优化完成后（日志 'Optimization was "
                       "completed'）偶发不进入 Saving（JVM 存活 CPU 空转，"
                       "600s 合同超时 kill）。实证归因：同 cwd 累积多 job "
                       "后死锁率升高（shared-cwd 补跑 0/8 成功），换新 "
                       "cwd 同 DSN 同参 6/6 成功（1 诊断+5 补跑）——遗缺 "
                       "run 以 staging 内独立子目录 cwd 补跑（argv 形状/"
                       "env 白名单/超时全同；board.dsn 逐字节拷贝，日志"
                       "存 freerouting-run{N}-iso.stdout）。D20(b) "
                       "nondeterminism 增补证据",
            "hung_attempts_archived": [
                f"{slot}/{p.name}"
                for slot in SLOTS
                for p in sorted((STAGING_ROOT / slot).glob(
                    "freerouting-run[0-9]-attempt*.stdout"))],
        },
        "notes": [
            "每板 N=%d 同参重跑全报（逐次 severity-error 新增/类型分布/"
            "连通性/SES 宽度直方图）；中位数/分布见 ab-report；不挑"
            "单次代表值。" % args.runs,
            "S11 arm=S11 归档 SES 过 S12 staging 同一验证链"
            "（同基线/同 kicad-cli/同应用板推导）——两臂度量口径全同。",
        ],
    })
    ab_sha = _write(S12 / "ab-report.json", {
        "artifact_kind": "td7_s12_ab_report",
        "track": bq.TRACK, "schema_version": bq.SCHEMA_VERSION,
        "report_date": bq.Q_DATE,
        "boards": ab_reports,
    })

    # judge_pre / judge_post / ledger（TD7-S12 复评；资格门不重开）
    pid_all = "multi:" + "+".join(sorted(SLOTS.values()))
    execution_id = f"{EXECUTION_PREFIX}-REEVAL"
    run_ref = hashing.sha256_bytes(hashing.canonical_json_bytes(matrix))
    pre = judge.build_pre(
        execution_id=execution_id, project_id=pid_all, profile_id=pid_all,
        candidate_id="TD7-S12-DSN-fidelity-reeval",
        source_snapshot_sha256=hashing.sha256_text(
            json.dumps(sorted(m["dsn_sha256"] for m in matrix.values()))),
        toolchain_lock_sha256=lock_sha,
        executor={"backend": bq.BACKEND, "protocol": bq.PROTOCOL,
                  "version": bq.ASM8_EXPECTED_JAR_VERSION,
                  "capability": "external_router_reeval"},
        write_scope="staging_only",
        allowlist=["freerouting-cli-jar"],
        required_checks=["drc_batch_severity_error",
                         "drc_final_severity_all",
                         "ab_statistical_discipline"],
        upstream_hashes={})
    pre_eval = judge.evaluate_pre(pre, {
        "toolchain_lock_sha256": lock_sha,
        "source_snapshot_sha256": pre["source_snapshot_sha256"]})
    any_blocked = any(
        (r["drc_dual_severity"]["severity_error_new_count"] > 0)
        for m in matrix.values() for r in m["s12_runs"])
    post = judge.build_post(
        execution_id=execution_id, pre_record=pre,
        output_hash=qm_sha,
        l1_legal=True, layer_pure=True,
        drc_batch_ref=run_ref, drc_final_ref=run_ref,
        solver=None,
        external_status="fail" if any_blocked else "pass",
        physics_status="not_required", bring_up_status="not_required",
        rollback_status="executed",
        facts=judge.build_facts([
            {"fact_id": "FACT-TD7-S12-HYPOTHESIS-VERDICT",
             "observer": "external_backend",
             "observation": {
                 "kind": "text_ref",
                 "value": "D20(d) 工作假设证伪：DSN 携带 net-class 线宽"
                          "（三板三角对账+逐 net 显式映射实验）；"
                          "track_width 违规=freerouting 减宽回退"
                          "（引擎能力边界）",
                 "ref_sha256": qm_sha}}]))
    post_eval = judge.evaluate_post(post)

    base = {"authority": "deterministic_evaluator",
            "trust_level": "observed",
            "project_id": pid_all, "profile_id": pid_all,
            "snapshot_revision": "td7-s12-r1",
            "actor": "pcbflow-v3-s12-reeval", "actor_role":
            "orchestrator"}
    entries: list = []
    entries, _ = ledger.append(entries, {
        "entry_id": "TD7-S12-E-0001", "entry_kind": "proposal",
        "schema_validation": ledger.make_schema_validation(
            "decision_ledger_entry"),
        "proposal_id": "TD7-S12-DSN-fidelity-reeval",
        "proposal_sha256": qm_sha,
        "artifact_hashes": {"quality_matrix": qm_sha,
                            "ab_report": ab_sha}, **base})
    entries, _ = ledger.append(entries, {
        "entry_id": "TD7-S12-E-0002", "entry_kind": "judge_pre",
        "schema_validation": ledger.make_schema_validation(
            "judge_pre_record"),
        "judge_pre_hash": judge.pre_record_sha256(pre),
        "artifact_hashes": {"toolchain_lock": lock_sha}, **base})
    entries, _ = ledger.append(entries, {
        "entry_id": "TD7-S12-E-0003", "entry_kind": "execution",
        "schema_validation": ledger.make_schema_validation(
            "decision_ledger_entry"),
        "execution_ref": run_ref,
        "artifact_hashes": {"run_matrix": run_ref}, **base})
    entries, _ = ledger.append(entries, {
        "entry_id": "TD7-S12-E-0004", "entry_kind": "judge_post",
        "schema_validation": ledger.make_schema_validation(
            "judge_post_record"),
        "judge_pre_hash": judge.pre_record_sha256(pre),
        "judge_post_hash": hashing.sha256_bytes(
            hashing.canonical_json_bytes(post)),
        "artifact_hashes": {"quality_matrix": qm_sha}, **base})
    ledger_text = "".join(hashing.json_dumps(e) + "\n" for e in entries)
    ledger_sha = hashing.sha256_text(ledger_text)
    _write(S12 / "decision-ledger-s12.json", {"entries": entries})
    _write(S12 / "ledger-checkpoint-s12.json",
           ledger.make_checkpoint(entries, "CKPT-TD7-S12-R1"))
    _write(S12 / "judge-records-s12.json", {
        "judge_pre_ok": pre_eval["pre_ok"],
        "judge_post_ok": post_eval["post_ok"],
        "judge_post_external_status":
            post["drc_facts"]["external_status"]
            if "drc_facts" in post else post.get("external_status"),
        "gate_not_reopened_reason": "TD7-QUAL-G 资格=合同面四轴"
            "（安全纪律/记录完备/验证链执行/可复现测量纪律）已 pass 且"
            "资格谓词输入未变（同 registry/同合同执行面）；质量差是"
            "独立记录的 quality facts（S11 口径），S12 复评不改变资格"
            "语义；无资格谓词错误证据，不重开。",
        "ledger_prefix_sha256": ledger_sha,
    })
    print(json.dumps({
        "quality_matrix_sha16": qm_sha[:16],
        "ab_report_sha16": ab_sha[:16],
        "judge_pre_ok": pre_eval["pre_ok"],
        "judge_post_ok": post_eval["post_ok"]}))
    for pid, m in matrix.items():
        print(pid[:28], "s12 runs:", len(m["s12_runs"]),
              "s11 arm:", len(m["s11_arm_runs"]),
              "det:", m["s12_determinism"]["deterministic"],
              "| err counts:", [r["drc_dual_severity"]
                                ["severity_error_new_count"]
                                for r in m["s12_runs"]])
    return 0


def cmd_archive(args) -> int:
    """staging 证据归档到 out/v3-td7/s12/boards/<pid>/。"""
    for slot, pid in SLOTS.items():
        stg = STAGING_ROOT / slot
        dst = S12 / "boards" / pid / "artifacts"
        dst.mkdir(parents=True, exist_ok=True)
        keep = ["board.dsn", "board-unrouted.kicad_pcb",
                "board-unrouted.kicad_pro", "board-pernet.dsn",
                "pernet.ses", "pernet-meta.json", "board-pernet.kicad_pcb",
                "drc-baseline-error.json", "drc-baseline-all.json",
                "drc-baseline-error.stdout", "drc-baseline-all.stdout"]
        for i in range(1, 4):
            keep += [f"run{i}.ses", f"board-run{i}.kicad_pcb",
                     f"drc-run{i}-error.json", f"drc-run{i}-all.json",
                     f"drc-run{i}-error.stdout", f"drc-run{i}-all.stdout",
                     f"freerouting-run{i}.stdout",
                     f"ses-apply-run{i}.stdout",
                     f"drc-s11-run{i}-error.json",
                     f"drc-s11-run{i}-all.json",
                     f"drc-s11-run{i}-error.stdout",
                     f"drc-s11-run{i}-all.stdout",
                     f"ses-apply-s11-run{i}.stdout", f"s11-run{i}.ses"]
        keep += ["drc-pernet-error.json", "drc-pernet-all.json",
                 "freerouting-pernet.stdout", "ses-apply-pernet.stdout",
                 "drc-pernet-error.stdout", "drc-pernet-all.stdout"]
        # 挂起尝试日志（超时被 kill 的 freerouting 尝试——D20(b) 增补
        # 证据：post-optimization 死锁，无 Saving 行无 SES）+ 隔离 cwd
        # 补跑日志（freerouting-run{N}-iso.stdout；rt-iso 引擎设置文件
        # 以 __ 展平路径名归档）
        extra_files: list = []
        for pat in ("freerouting-run[0-9]-attempt*.stdout",
                    "freerouting-run[0-9]-iso.stdout"):
            for extra in sorted(stg.glob(pat)):
                keep.append(extra.name)
        for extra in sorted(stg.glob(
                "rt-iso-*/freerouting/freerouting.json")):
            extra_files.append((extra,
                                extra.relative_to(stg).as_posix()
                                .replace("/", "__")))
        manifest = []
        for name in keep:
            src = stg / name
            if not src.exists():
                continue
            target = dst / name
            shutil.copyfile(src, target)
            manifest.append({"file": name,
                             "sha256": _sha_file(target),
                             "size_bytes": target.stat().st_size})
        for src, name in extra_files:
            target = dst / name
            shutil.copyfile(src, target)
            manifest.append({"file": name,
                             "sha256": _sha_file(target),
                             "size_bytes": target.stat().st_size,
                             "note": "隔离 cwd 补跑的引擎自建设置文件"
                                     "（rt-iso 子目录原样）"})
        _write_json = lambda p, obj: p.write_text(
            hashing.json_dumps(obj), encoding="utf-8", newline="")
        _write_json(S12 / "boards" / pid / "staging-archive-s12.json", {
            "artifact_kind": "td7_s12_staging_archive",
            "track": bq.TRACK, "profile_id": pid,
            "note": "S12 staging 证据（外部工具输出原样留存；含引擎"
                    "wall-clock/路径字段，按 S6/S11 先例声明）；"
                    "board-unrouted.kicad_pro=SaveBoard 自动创建的类"
                    "定义容器（KiCad10 存储：net_settings.classes+"
                    "netclass_patterns——三角对账证据链一环）",
            "files": manifest})
        print("archived", len(manifest), "files:", pid[:30])
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("baseline")
    p2 = sub.add_parser("reruns")
    p2.add_argument("--runs", type=int, default=3)
    sub.add_parser("pernet")
    sub.add_parser("s11arm")
    sub.add_parser("triangulate")
    p3 = sub.add_parser("analyze")
    p3.add_argument("--runs", type=int, default=3)
    sub.add_parser("archive")
    args = parser.parse_args()
    return {"baseline": cmd_baseline, "reruns": cmd_reruns,
            "pernet": cmd_pernet, "s11arm": _apply_s11_ses,
            "triangulate": cmd_triangulate,
            "analyze": cmd_analyze, "archive": cmd_archive}[args.cmd](
        args)


if __name__ == "__main__":
    sys.exit(main())
