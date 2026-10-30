# -*- coding: utf-8 -*-
"""canvas.authority —— kicad-cli DRC 外权威聚合（Lane-K2；合同 §1 authority 节）。

kicad_cli_aggregate(export_dir, runs=5, max_rounds=3)：P5-UP3-aggregate-v1
口径——每轮 runs 跑 kicad-cli pcb drc、至多 max_rounds 轮、出现全等轮即停
取该轮、无全等轮=union-max+披露；返回 {drc_clean, unconnected,
aggregate_report}。

**文档化决定（逐字披露）**：

- **协议口径**（P5-UP3-aggregate-v1，tools/run_p5_board.py 0.2.0 起实战同
  源语义，本件为合同钉的 K2 自有件）：
  - 全等判据=轮内各跑 ``violations_total`` 全等（P5 原口径单指标；by-type
    漂移由 union-max 覆盖披露）；
  - 全等轮出现即停，判据锚定该轮；至多 max_rounds 轮；
  - 无全等轮 → verdict="nondeterministic-disclosed"，判据=全部已跑逐类
    并集最大值（union-max）。
- **drc_clean = 聚合 violations_total == 0**；**unconnected = 聚合
  unconnected_items 计数**（连通复核口径，合同 §1 authority 节）。
- **staging 域 fail-closed**：export_dir（realpath）必须在
  ``<repo>/out/canvas-toolchain/staging/`` 之下——kicad-cli 对输入目录写
  ``.kicad_prl``，绝不指向 boards/、datasets/（合同 §4 路径约定）。
- **kicad-cli 失败 fail-closed 不吞**：退出码非零/输出非法 JSON/可执行缺
  失（FileNotFoundError 透传）→ RuntimeError（带轮/跑定位与 stderr 摘要），
  不静默改道。
- 原始 DRC 报告即用即删（系统临时域 tempfile，不落导出目录）。
- 调用形态（P5 10.0.5 实战口径）：
  ``kicad-cli pcb drc --output <tmp.json> --format json --severity-all
  --units mm <pcb>``，timeout 600s。
- **确定性**：无时间戳；rounds_totals/逐跑读数全量入 aggregate_report
  （canonical 可序列化）。
"""

import glob
import hashlib
import json
import os
import subprocess
import tempfile

GENERATOR = "canvas.authority"
VERSION = "1.0.0"
PROTOCOL_NAME = "P5-UP3-aggregate-v1"

KICAD_CLI = "F:/kicad/bin/kicad-cli.exe"  # 合同 §0 锚
_CLI_TIMEOUT_S = 600

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STAGING_ROOT = os.path.join(_REPO_ROOT, "out", "canvas-toolchain", "staging")

#: DRC JSON 报告消费键（kicad-cli 10.0.5 实测形态；缺键=空集，报错口径见上）
_DRC_KEYS = ("violations", "unconnected_items", "schematic_parity")


def _norm(path):
    return os.path.normpath(os.path.realpath(path)).replace("\\", "/")


def _assert_staging(export_dir):
    real = _norm(export_dir)
    root = _norm(STAGING_ROOT)
    if real != root and not real.startswith(root + "/"):
        raise ValueError(
            "export_dir 越界: %s（只准 out/canvas-toolchain/staging/ 之下——"
            "kicad-cli 会写输入目录 .kicad_prl，绝不指向 boards/、datasets/）"
            % export_dir)
    return real


def _run_cli(args):
    """kicad-cli 子进程（capture、timeout；失败异常自然透传/包装）。"""
    return subprocess.run([KICAD_CLI] + list(args), capture_output=True,
                          text=True, timeout=_CLI_TIMEOUT_S)


def _cli_version():
    proc = _run_cli(["version"])
    if proc.returncode != 0:
        raise RuntimeError(
            "kicad-cli version 探测失败（exit=%d）: %s"
            % (proc.returncode, (proc.stderr or "")[:300]))
    return proc.stdout.strip()


def _single_drc_run(pcb_path, round_idx, run_idx):
    """单跑 kicad-cli pcb drc → 计数 dict（报告即用即删）。"""
    with tempfile.TemporaryDirectory(prefix="lane-k2-drc-") as tmp:
        report = os.path.join(tmp, "drc.json")
        proc = _run_cli(["pcb", "drc", "--output", report,
                         "--format", "json", "--severity-all",
                         "--units", "mm", pcb_path])
        where = "round=%d run=%d pcb=%s" % (round_idx, run_idx, pcb_path)
        if proc.returncode != 0:
            raise RuntimeError(
                "kicad-cli drc 退出码 %d（%s）fail-closed: %s"
                % (proc.returncode, where, (proc.stderr or "")[:300]))
        try:
            with open(report, encoding="utf-8") as f:
                drc = json.load(f)
        except (OSError, ValueError) as exc:
            raise RuntimeError(
                "kicad-cli drc 输出解析失败（%s）fail-closed: %s"
                % (where, exc)) from exc
        if not isinstance(drc, dict):
            raise RuntimeError(
                "kicad-cli drc 输出非 JSON 对象（%s）fail-closed: %r"
                % (where, type(drc).__name__))
    violations = drc.get("violations", [])
    unconnected = drc.get("unconnected_items", [])
    by_type = {}
    for item in violations:
        if isinstance(item, dict) and "type" in item:
            by_type[item["type"]] = by_type.get(item["type"], 0) + 1
    return {
        "round": round_idx, "run": run_idx,
        "violations_total": len(violations),
        "unconnected_items": len(unconnected),
        "schematic_parity": len(drc.get("schematic_parity", [])),
        "by_type": dict(sorted(by_type.items())),
    }


def _union_max(runs):
    """逐类并集最大值（P5-UP3 nondeterministic-disclosed 判据）。"""
    type_keys = sorted({t for r in runs for t in r["by_type"]})
    return {
        "violations_total": max(r["violations_total"] for r in runs),
        "unconnected_items": max(r["unconnected_items"] for r in runs),
        "schematic_parity": max(r["schematic_parity"] for r in runs),
        "by_type": {t: max(r["by_type"].get(t, 0) for r in runs)
                    for t in type_keys},
    }


def kicad_cli_aggregate(export_dir, runs=5, max_rounds=3):
    """export_dir（staging 域，含恰一 .kicad_pcb）→ P5-UP3 聚合结果。

    返回 {"drc_clean": bool, "unconnected": int, "aggregate_report": dict}。
    kicad-cli 缺失/失败 fail-closed（FileNotFoundError/RuntimeError 透传，
    不吞不静默改道）。
    """
    staging_dir = _assert_staging(export_dir)
    if runs < 1 or max_rounds < 1:
        raise ValueError("runs/max_rounds 须 ≥1，实得 runs=%r max_rounds=%r"
                         % (runs, max_rounds))
    pcbs = sorted(glob.glob(os.path.join(staging_dir, "*.kicad_pcb")))
    if not pcbs:
        raise FileNotFoundError("export_dir 无 .kicad_pcb: %s" % staging_dir)
    if len(pcbs) > 1:
        raise ValueError("export_dir 含多个 .kicad_pcb（歧义）: %r" % (pcbs,))
    pcb_path = pcbs[0]
    with open(pcb_path, "rb") as f:
        export_sha256 = hashlib.sha256(f.read()).hexdigest()

    version = _cli_version()

    rounds_runs = []
    for round_idx in range(1, max_rounds + 1):
        round_runs = [_single_drc_run(pcb_path, round_idx, run_idx)
                      for run_idx in range(1, runs + 1)]
        rounds_runs.append(round_runs)
        if len({r["violations_total"] for r in round_runs}) == 1:
            break  # 全等轮出现，判据锚定该轮即停
    all_runs = [r for rs in rounds_runs for r in rs]
    stable = (len(set(r["violations_total"] for r in rounds_runs[-1])) == 1)
    verdict = ("deterministic-equal" if stable
               else "nondeterministic-disclosed")
    criterion_runs = rounds_runs[-1] if stable else all_runs
    aggregate = _union_max(criterion_runs)

    report = {
        "protocol": {
            "name": PROTOCOL_NAME,
            "runs_per_round": runs,
            "max_rounds": max_rounds,
            "equality_criterion": "violations_total（P5-UP3 原口径）",
            "rule": ("每轮 %d 跑，一轮 violations_total 全等→deterministic-"
                     "equal（锚该轮）；否则至多 %d 轮；仍无全等轮→"
                     "nondeterministic-disclosed，判据=全部已跑逐类并集最大值"
                     % (runs, max_rounds)),
        },
        "generator": GENERATOR,
        "generator_version": VERSION,
        "verdict": verdict,
        "n_rounds": len(rounds_runs),
        "n_runs": len(all_runs),
        "rounds_totals": [[r["violations_total"] for r in rs]
                          for rs in rounds_runs],
        "criterion": ("第 %d 轮（全等轮）" % len(rounds_runs) if stable
                      else "全部 %d 跑（union-max）" % len(all_runs)),
        "aggregate_union_max": aggregate,
        "kicad_cli": {"path": KICAD_CLI, "version": version},
        "export_sha256": export_sha256,
        "export_dir": staging_dir,
        "pcb_file": os.path.basename(pcb_path),
        "runs": all_runs,
    }
    return {
        "drc_clean": aggregate["violations_total"] == 0,
        "unconnected": aggregate["unconnected_items"],
        "aggregate_report": report,
    }
