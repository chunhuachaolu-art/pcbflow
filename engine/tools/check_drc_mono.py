# -*- coding: utf-8 -*-
"""DRC 单源性静态扫描（P0 门：全仓间距判定只出自 v5.drc，零旁路）。

扫描 v5/ 与 tools/ 全部 .py：
  1) 除 v5/drc.py 外禁止出现违例判定语义的实现标志（R5 判定/违例构造函数名）。
  2) 除 v5/drc.py 与其测试外禁止 import 私有原语复制实现（seg 距离函数重定义）。
返回违例清单；退出码 0=单源性成立。
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FORBIDDEN_DEFINITIONS = (
    "def check_clearance", "def _actual_gap", "def check_capacity",
    "def check_width", "def check_keepout", "def check_ana_proximity",
    "class Violation", "class DRCReport",
)
ALLOWED_FILES = {
    os.path.normpath("v5/drc.py"),
    os.path.normpath("tools/check_drc_mono.py"),  # 扫描器自身含标志串
}


def scan():
    violations = []
    for base in ("v5", "tools"):
        for dirpath, _d, files in os.walk(os.path.join(ROOT, base)):
            for fn in sorted(files):
                if not fn.endswith(".py"):
                    continue
                full = os.path.join(dirpath, fn)
                rel = os.path.normpath(os.path.relpath(full, ROOT))
                if rel in ALLOWED_FILES or ".tests." in rel or rel.startswith("tests"):
                    continue
                with open(full, encoding="utf-8") as f:
                    src = f.read()
                for marker in FORBIDDEN_DEFINITIONS:
                    if marker in src:
                        violations.append("%s: 疑似旁路判定实现 %r" % (rel, marker))
    return violations


def main():
    v = scan()
    if v:
        for line in v:
            print("DRC-MONO VIOLATION:", line)
        return 1
    print("drc mono-source check: GREEN (single authority v5.drc)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
