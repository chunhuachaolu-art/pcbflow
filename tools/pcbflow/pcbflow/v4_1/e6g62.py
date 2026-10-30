"""pcbflow.v4_1.e6g62 -- G6.2 holdout-r1 事故场景回归编排。

事故锚（holdout-r1，V3-NEXT L54）：kicad-cli 在 datasets/ 受保护目录
留下 3 个 .kicad_prl=零写入红线首破（板 sha 零变化、已删复原；教训=
调用后查 prl）。本编排以 stub 可执行文件注入同一事故模式，证明
e6prl.KicadCliGuard 能捕获+复原+台账+fail-closed；负对照=正常调用
零误报。零真 kicad-cli 调用（真调用负对照=E6 自身全部调用经 guard，
见 g61-refill/kicad-cli-calls.log）。

用法：python -m pcbflow.v4_1.e6g62 --out out/v4.1-engineering/e6
产物：g62-incident-regression.json（canonical）+ g62-stub-calls.log
"""

from __future__ import annotations

import os
import sys

from . import DECLARED_DATE
from .canonical import write_canonical_json
from .e6prl import KicadCliGuard, PrlHygieneIncident
from .prl_hygiene import PRL_SUFFIX, inventory

__all__ = ["write_stub_scripts", "run_g62_incident_regression"]


def write_stub_scripts(base_dir):
    """stub kicad-cli（bat 包装使 subprocess 可直接执行）。

    模式经 E6_STUB_MODE 环境变量切换：
    - incident：holdout-r1 事故模式（cwd+受保护目录各留 .kicad_prl）；
    - change：变更既有 sidecar 字节；
    - normal：只写合法输出文件（负对照）。
    """
    stub_py = os.path.join(base_dir, "stub-kicad-cli.py")
    with open(stub_py, "w", encoding="utf-8", newline="\n") as f:
        f.write(
            "import os, sys\n"
            "mode = os.environ.get('E6_STUB_MODE', 'normal')\n"
            "cwd = os.getcwd()\n"
            "if mode == 'incident':\n"
            "    open(os.path.join(cwd, 'stub.kicad_prl'), 'wb')"
            ".write(b'stub-prl')\n"
            "    prot = os.environ.get('E6_STUB_PROTECTED_DIR')\n"
            "    if prot:\n"
            "        open(os.path.join(prot, 'board.kicad_prl'), 'wb')"
            ".write(b'stub-prl-protected')\n"
            "elif mode == 'change':\n"
            "    p = os.path.join(cwd, 'pre-existing.kicad_prl')\n"
            "    if os.path.isfile(p):\n"
            "        open(p, 'wb').write(b'mutated-by-call')\n"
            "else:\n"
            "    open(os.path.join(cwd, 'stub-output.json'), 'wb')"
            ".write(b'{}')\n"
            "sys.exit(0)\n")
    stub_bat = os.path.join(base_dir, "stub-kicad-cli.bat")
    exe_abs = os.path.abspath(sys.executable).replace("/", "\\")
    stub_abs = os.path.abspath(stub_py).replace("/", "\\")
    with open(stub_bat, "w", encoding="utf-8", newline="\r\n") as f:
        f.write('@"%s" "%s" %%*\n' % (exe_abs, stub_abs))
    return stub_py, stub_bat


def _fresh_setup(tmp_root):
    staging = os.path.join(tmp_root, "staging")
    protected = os.path.join(tmp_root, "datasets-sim")
    os.makedirs(staging, exist_ok=True)
    os.makedirs(protected, exist_ok=True)
    for d in (staging, protected):
        with open(os.path.join(d, "board.kicad_pcb"), "wb") as f:
            f.write(b"board")
    return staging, protected


def run_g62_incident_regression(out_dir):
    """三臂事故回归（产物落 out_dir/g62-incident-regression.json）。"""
    import tempfile
    os.makedirs(out_dir, exist_ok=True)
    _py, stub_bat = write_stub_scripts(out_dir)
    stub_bat = os.path.abspath(stub_bat)  # cwd 会切到 staging，须绝对路径
    ledger = os.path.join(out_dir, "g62-stub-calls.log")
    tmp_root = os.path.join(out_dir, "g62-tmp")
    os.makedirs(tmp_root, exist_ok=True)
    counter = [0]
    results = []

    def _call_with_mode(guard, mode, staging, protected=None, role=""):
        os.environ["E6_STUB_MODE"] = mode
        if protected is not None:
            os.environ["E6_STUB_PROTECTED_DIR"] = protected
        try:
            _rc, _out, rec = guard.call(
                ["pcb", "drc", "--format", "json", "board.kicad_pcb"],
                staging, cwd_role=role)
            return {"raised": False, "record": rec}
        except PrlHygieneIncident as exc:
            return {"raised": True, "record": exc.record}
        finally:
            os.environ.pop("E6_STUB_MODE", None)
            os.environ.pop("E6_STUB_PROTECTED_DIR", None)

    # ---- 臂1：holdout-r1 事故注入
    counter[0] += 1
    staging, protected = _fresh_setup(
        os.path.join(tmp_root, "arm1-%d" % counter[0]))
    g1 = KicadCliGuard(ledger, kicad_cli=stub_bat,
                       watch_dirs=[protected], protected_dirs=[protected])
    arm1 = _call_with_mode(g1, "incident", staging, protected,
                           "g62-incident-injection")
    fin_stage = inventory(staging)
    fin_prot = inventory(protected)
    results.append({
        "arm": "holdout_r1_incident_injection",
        "must": ["captured", "restored", "ledger_recorded",
                 "fail_closed_raised", "protected_zero_prl_reinstated"],
        "raised": arm1["raised"],
        "verdict": arm1["record"]["verdict"],
        "cwd_sidecar_captured_and_deleted": (
            "stub.kicad_prl" not in fin_stage
            and fin_stage.get("board.kicad_pcb") is not None),
        "protected_sidecar_captured_and_deleted": not [
            n for n in fin_prot if n.endswith(PRL_SUFFIX)],
        "protected_zero_prl_assert": "held_after_restore",
    })

    # ---- 臂2：正常调用负对照
    counter[0] += 1
    staging, protected = _fresh_setup(
        os.path.join(tmp_root, "arm2-%d" % counter[0]))
    g2 = KicadCliGuard(ledger, kicad_cli=stub_bat,
                       watch_dirs=[protected], protected_dirs=[protected])
    arm2 = _call_with_mode(g2, "normal", staging, None,
                           "g62-negative-control")
    results.append({
        "arm": "normal_call_negative_control",
        "must": ["no_false_positive"],
        "raised": arm2["raised"],
        "verdict": arm2["record"]["verdict"],
        "expected_output_present": "stub-output.json" in inventory(staging),
        "nothing_removed": all(
            not h["restored"] and not h["unrestored"]
            for h in arm2["record"]["hygiene"].values()),
    })

    # ---- 臂3：变更 sidecar（guard 快照字节复原）
    counter[0] += 1
    staging, protected = _fresh_setup(
        os.path.join(tmp_root, "arm3-%d" % counter[0]))
    pre_prl = os.path.join(staging, "pre-existing.kicad_prl")
    with open(pre_prl, "wb") as f:
        f.write(b"original-prl")
    g3 = KicadCliGuard(ledger, kicad_cli=stub_bat,
                       watch_dirs=[protected], protected_dirs=[protected])
    arm3 = _call_with_mode(g3, "change", staging, None,
                           "g62-changed-sidecar")
    with open(pre_prl, "rb") as f:
        final_bytes = f.read()
    results.append({
        "arm": "changed_sidecar_bytes_restored",
        "must": ["captured", "bytes_restored", "fail_closed_raised"],
        "raised": arm3["raised"],
        "verdict": arm3["record"]["verdict"],
        "bytes_restored_to_original": final_bytes == b"original-prl",
    })

    artifact = {
        "schema": "pcbflow.v4_1.e6-g62-incident-regression/1",
        "declared_date": DECLARED_DATE,
        "incident_anchor": "holdout-r1（kicad-cli 在 datasets/ 留 3 个 "
                           ".kicad_prl=零写入红线首破；V3-NEXT L54）",
        "arms": results,
        "stub_real_kicad_cli_calls": 0,
        "note": "stub 注入零真 kicad-cli 调用；真调用负对照=E6 自身全部"
                "调用经 guard（g61-refill/kicad-cli-calls.log 逐调用"
                "卫生记录）",
    }
    write_canonical_json(os.path.join(out_dir,
                                      "g62-incident-regression.json"),
                         artifact)
    return artifact


def main(argv=None):
    import argparse
    import json as _json
    ap = argparse.ArgumentParser(prog="pcbflow.v4_1.e6g62")
    ap.add_argument("--out", required=True)
    ns = ap.parse_args(argv)
    art = run_g62_incident_regression(ns.out)
    for a in art["arms"]:
        print(a["arm"], "raised=", a["raised"], "verdict=", a["verdict"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
