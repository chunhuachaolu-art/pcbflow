"""toolchain lock（SPEC §2.3）。纯函数、零 IO、零子进程。

Mimosa 钩子约束（HANDOFF §4 生成器模式）：.py 不执行子进程、不写文件。
探测由会话在 shell 中完成，探测值以 JSON 经 stdin 传给
scripts/probe_toolchain.py（本模块 make_lock 组装），stdout 重定向落盘。
load_lock 只读加载；版本/能力不满足时调用方必须返回 blocked/unknown。
"""

from __future__ import annotations

import json
import os

from . import config

KICAD_CLI = r"F:\kicad\bin\kicad-cli.exe"
KICAD_PYTHON = r"F:\kicad\bin\python.exe"

# 探测项清单（scripts/probe_toolchain.py 的 stdin 契约）
REQUIRED_PROBES = [
    "kicad_cli_version", "kicad_python_version", "pcbnew_version",
    "kipy_version", "runtime_python_version", "runtime_numpy_version",
    "kicad_numpy_version", "os",
]


def make_lock(probes: dict) -> dict:
    """探测值 → lock dict。缺项显式记 null + note，不猜。"""
    missing = [k for k in REQUIRED_PROBES if k not in probes]
    if missing:
        raise ValueError(f"missing probes: {missing}")
    kipy = probes["kipy_version"]
    return {
        "schema_version": config.SCHEMA_TOOLCHAIN_LOCK,
        "kicad_cli": {"path": KICAD_CLI, "version": probes["kicad_cli_version"]},
        "kicad_python": {
            "path": KICAD_PYTHON,
            "version": probes["kicad_python_version"],
            "pcbnew": probes["pcbnew_version"],
            "numpy": probes["kicad_numpy_version"],
        },
        # kipy 未安装如实记（DRC 只走 kicad-cli：HANDOFF §4，kipy board_rules 导入即崩）
        "kipy": ({"version": kipy} if kipy
                 else {"version": None, "note": "not_installed_in_kicad_python"}),
        "python": {"version": probes["runtime_python_version"]},
        "numpy": {"version": probes["runtime_numpy_version"]},
        "pcbnew": {"version": probes["pcbnew_version"]},
        "freerouting": {"version": None, "optional": True, "note": "locked_when_called"},
        "jdk": {"version": None, "optional": True, "note": "locked_when_called"},
        "os": probes["os"],
        "schema_versions": {
            "envelope": config.SCHEMA_ENVELOPE,
            "constraints": config.SCHEMA_CONSTRAINTS,
            "coverage": config.SCHEMA_COVERAGE,
            "impedance_targets": config.SCHEMA_IMPEDANCE,
        },
        "notes": [
            "probes executed in-session via shell; pcbflow .py runs no subprocess (Mimosa hook)",
            "freerouting/jdk locked only when actually called (SPEC §2.3)",
        ],
    }


def load_lock(path: str | None = None) -> dict | None:
    """只读加载 lock；缺失返回 None（调用方如实记 not_probed）。"""
    p = path or os.path.join(config.PCBFLOW_ROOT, "toolchain_lock.json")
    if not os.path.exists(p):
        return None
    with open(p, "r", encoding=config.ENCODING) as f:
        return json.load(f)
