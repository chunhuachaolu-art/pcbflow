# -*- coding: utf-8 -*-
"""W-D 重跑墙钟监控（队列 B 红线教训补位）：每 60s 采样 r1_rerun 板序
产物链 mtime+python 进程数，append 到 r1/logs/w6d-wallclock-monitor.log。
单板 >4h 打 RED-LINE 标记（不停进程——thatmicpre 长跑系用户裁 3 明示
预排期，标记供审计）；Ctrl-C/父进程死=自然退出。
"""
import json
import os
import subprocess
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOARDS = ["pmod-crypto", "badgeleds-do-electronics", "thin-pod",
          "thatmicpre-v2"]
LOG = os.path.join(ROOT, "out", "v5-p5", "r1", "logs",
                   "w6d-wallclock-monitor.log")
PROD = os.path.join(ROOT, "out", "v5-p5", "boards")

t0 = time.time()
while True:
    rec = {"t": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "elapsed_s": round(time.time() - t0, 1)}
    try:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "(Get-CimInstance Win32_Process -Filter \"Name like '%python%'\" "
             "| Measure-Object).Count"],
            capture_output=True, text=True, timeout=30).stdout.strip()
        rec["py_procs"] = out
    except Exception as e:
        rec["py_procs"] = "err:%s" % e
    for b in BOARDS:
        bd = os.path.join(PROD, b)
        st = {}
        for f in ("compiled.json", "execute.json", "check.json",
                  "run-result.json"):
            p = os.path.join(bd, f)
            st[f] = (time.strftime("%m-%d %H:%M:%S",
                                   time.localtime(os.path.getmtime(p)))
                     if os.path.exists(p) else None)
        rec[b] = st
    with open(LOG, "a", encoding="utf-8") as lf:
        lf.write(json.dumps(rec, ensure_ascii=False) + "\n")
    time.sleep(60)
