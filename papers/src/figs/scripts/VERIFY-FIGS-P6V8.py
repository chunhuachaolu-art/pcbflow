# -*- coding: utf-8 -*-
"""VERIFY-FIGS-P6V8 — 编排 QC 跑批薄入口（QC 返修席 2026-10-05 增）。

缘起：编排件（.zcode/workflow-runs/dwfrun-3c7d90b9-d441-41c6-9ab4-a664905a181a.mjs）
QC 段以无连字符名 VERIFY-FIGS-P6V8.py 调用，而 P6-V8 席产品件为有连字符
VERIFY-FIGS-P6-V8.py —— 名字不匹配导致编排跑批 exit 2（FAIL，[Errno 2] No such
file or directory），检查逻辑本身全绿。

处置：本件不含任何检查逻辑，仅转发执行同目录主脚本 VERIFY-FIGS-P6-V8.py 并
原样传播其退出码与输出（runpy 直跑，SystemExit 自然冒泡）——单一事实源，
无双拷贝漂移；断言口径与主脚本逐字一致（只增不改红线下的返修件）。
"""
import os
import runpy
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_MAIN = os.path.join(_HERE, "VERIFY-FIGS-P6-V8.py")
if not os.path.exists(_MAIN):
    print(f"[entry] 主脚本缺失：{_MAIN}", file=sys.stderr)
    sys.exit(3)
sys.argv[0] = _MAIN
runpy.run_path(_MAIN, run_name="__main__")
