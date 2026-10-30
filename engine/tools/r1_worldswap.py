# -*- coding: utf-8 -*-
"""V5-R1 W-3 世界换版驱动（D8 全量换版流程同式）。

步骤：
1. 旧世界归档：out/v5-p5/boards/ → boards-pre-r1/（整树 move 零改写；
   已存在归档=停（防二次归档吞新世界））。
2. 全板 re-convert（20 已物化板：D8 17+boardintake 3；逐板新进程
   run_p5_board --stages convert，A 层台账自动登记 operator=
   v5-r1-subagent + extra.taskbook_sha16）。throwing-star-pro（convert-failed
   历史板）同构重跑（预期同错维持，D8 口径）。
3. 普查表（tools/r1_endpoint_census.py）。

用法：python tools/r1_worldswap.py [--archive-only|--convert-only|--census-only]
"""
import argparse
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "out", "v5-p5")
BOARDS = os.path.join(OUT, "boards")
PRE_R1 = os.path.join(OUT, "boards-pre-r1")
OPERATOR = "v5-r1-subagent"
EXTRA = json.dumps({"taskbook_sha16": "305359aef814fc12"})

# 换版面（20 已物化板 + throwing-star 同构保留）
R17 = ["tmp108", "pmod-bme280", "pmod-crypto", "thin-pod",
       "badgeleds-do-electronics", "thatmicpre-v2", "atmega32u4-breakout",
       "dc-scm-rot-jumper-card", "m2-pcie-adapter",
       "om-flexgrid-v4-rigid-pcb", "pmod-i2c24io", "stm32-ds2480-emu",
       "thunderbolt-pcie-adapter", "usb-gigabit-rev-e",
       "axiom-micro-mainboard", "cm5-minima-rev3", "ov9281-dual-camera-board"]
BOARDINTAKE3 = ["esp32-devkit-lipo-rev-c", "torxhat", "ice40hx1k-evb-rev-b"]
THROWING = "throwing-star-pro"


def sh(cmd):
    print("+ %s" % " ".join(cmd), flush=True)
    r = subprocess.run(cmd, cwd=ROOT)
    return r.returncode


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--archive-only", action="store_true")
    ap.add_argument("--convert-only", action="store_true")
    ap.add_argument("--census-only", action="store_true")
    ap.add_argument("--boards", default=None,
                    help="逗号分隔板清单覆盖（断点续跑）")
    args = ap.parse_args(argv)

    if args.census_only:
        return sh([sys.executable, "tools/r1_endpoint_census.py"])

    if not args.convert_only:
        if os.path.isdir(PRE_R1):
            print("HALT: boards-pre-r1/ 已存在（防二次归档吞新世界）")
            return 2
        if not os.path.isdir(BOARDS):
            print("HALT: boards/ 不存在")
            return 2
        os.rename(BOARDS, PRE_R1)
        print("ARCHIVED boards/ -> boards-pre-r1/")
        if args.archive_only:
            return 0

    roster = (args.boards.split(",") if args.boards
              else R17 + BOARDINTAKE3 + [THROWING])
    fails = []
    for b in roster:
        rc = sh([sys.executable, "tools/run_p5_board.py", "--board", b,
                 "--stages", "convert", "--operator", OPERATOR,
                 "--extra-json", EXTRA])
        if rc != 0:
            if b == THROWING:
                print("  (throwing-star-pro 维持 convert-failed 同构，D8 口径)",
                      flush=True)
            else:
                fails.append(b)
    if fails:
        print("CONVERT FAILURES: %s" % fails)
        return 1
    return sh([sys.executable, "tools/r1_endpoint_census.py"])


if __name__ == "__main__":
    sys.exit(main())
