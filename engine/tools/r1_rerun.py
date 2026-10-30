# -*- coding: utf-8 -*-
"""V5-R1 W-6 换版重跑驱动：14 终态板全链（compile→execute→check→export→drc）。

板序=可布域 6 板（轻）先行+board-inherent 8 板殿后串行（D8 同式）；逐板
新进程（run_p5_board，A 层台账 operator=v5-r1-subagent+extra.taskbook_sha16）。
断点续跑：--boards 覆盖。esp32 攻坚对照板单独批（不在 14 终态面）。
"""
import argparse
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OPERATOR = "v5-r1-subagent"
EXTRA = '{"taskbook_sha16":"305359aef814fc12"}'

# 可布域 6 板（判据一 SAT 面；R2 §4.1 同名单）先行——轻板快反馈
SAT6 = ["tmp108", "pmod-bme280", "pmod-crypto", "thin-pod",
        "badgeleds-do-electronics", "thatmicpre-v2"]
# board-inherent 8 板殿后（重板 dc-scm/om 殿后串行）
INHERENT8 = ["atmega32u4-breakout", "m2-pcie-adapter", "stm32-ds2480-emu",
             "usb-gigabit-rev-e", "thunderbolt-pcie-adapter",
             "pmod-i2c24io", "dc-scm-rot-jumper-card",
             "om-flexgrid-v4-rigid-pcb"]

LOG_DIR = os.path.join(ROOT, "out", "v5-p5", "r1", "logs")


def sh(cmd, log_path):
    with open(log_path, "ab") as lf:
        lf.write(("\n+ %s\n" % " ".join(cmd)).encode("utf-8"))
        lf.flush()
        r = subprocess.run(cmd, cwd=ROOT, stdout=lf, stderr=subprocess.STDOUT)
    return r.returncode


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--boards", default=None, help="逗号覆盖（断点续跑）")
    ap.add_argument("--stages", default="compile,execute,check,export,drc")
    args = ap.parse_args(argv)
    os.makedirs(LOG_DIR, exist_ok=True)
    roster = args.boards.split(",") if args.boards else SAT6 + INHERENT8
    fails = []
    for b in roster:
        t0 = time.time()
        log_path = os.path.join(LOG_DIR, "run-%s.log" % b)
        rc = sh([sys.executable, "tools/run_p5_board.py", "--board", b,
                 "--stages", args.stages, "--operator", OPERATOR,
                 "--extra-json", EXTRA], log_path)
        print("%-32s rc=%d  %.0fs" % (b, rc, time.time() - t0), flush=True)
        if rc != 0:
            fails.append(b)
    if fails:
        print("RERUN FAILURES: %s" % fails)
        return 1
    print("ALL OK (%d boards)" % len(roster))
    return 0


if __name__ == "__main__":
    sys.exit(main())
