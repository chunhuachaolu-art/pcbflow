"""pcbagent 兄弟仓依赖预检（REPAIR-P3 W-3，2026-09-22）。

pcbflow 引擎位对兄弟仓 tools/pcbagent 的依赖是跨仓路径约定，不是 PyPI
包（pyproject.toml [project.optional-dependencies].engine；挂载口径 =
route_grid.load_adapter 的 WORKSPACE_ROOT/tools/pcbagent）。本模块是该
依赖的 fail-closed 预检层：缺席/不完整/导入链断时给结构化 not_available
报告（PcbagentNotAvailable.report），不得裸 ImportError/ModuleNotFoundError
崩出去。

本层是 route_grid.load_adapter 的**调用侧包装**：route_grid.py 属 M0 只读
单件锚（sha b37878bd…），本体零触碰；需要缺件语义的调用方一律走
load_adapter_checked()。
"""

from __future__ import annotations

import os

from . import config, route_grid


class PcbagentNotAvailable(RuntimeError):
    """pcbagent 缺件的结构化拒绝（非 ImportError 子类；报告挂 .report）。

    report 形状：{dependency, pkg_root, required_modules,
                 available: False, status: "not_available", reason: str}
    """

    def __init__(self, report: dict):
        super().__init__(report["reason"])
        self.report = report


def pkg_root() -> str:
    """pcbagent 仓根（与 route_grid.load_adapter 同一口径）。"""
    return os.path.join(config.WORKSPACE_ROOT, "tools", "pcbagent")


def preflight() -> dict:
    """零导入纯探测：仓根在位 + adapter 模块文件齐 → available=True。

    模块清单单一事实源 = route_grid.PCBAGENT_ADAPTER_FILES（M0 锚常量，
    只读复用）；目录在位但文件缺 = 同样 not_available（不完整包）。
    """
    root = pkg_root()
    report: dict = {
        "dependency": "pcbagent",
        "pkg_root": root,
        "required_modules": list(route_grid.PCBAGENT_ADAPTER_FILES),
    }
    if not os.path.isdir(root):
        report.update({
            "available": False,
            "status": "not_available",
            "reason": (
                f"pcbagent 兄弟仓缺席：{root} 不存在（engine 可选依赖，"
                "路径约定见 pyproject.toml [project.optional-dependencies].engine）"
            ),
        })
        return report
    missing = sorted(
        name for name in route_grid.PCBAGENT_ADAPTER_FILES
        if not os.path.isfile(os.path.join(root, "pcbagent", name))
    )
    if missing:
        report.update({
            "available": False,
            "status": "not_available",
            "reason": f"pcbagent 包不完整：缺 adapter 模块文件 {missing}",
        })
        return report
    report.update({"available": True, "status": "ok", "reason": ""})
    return report


def load_adapter_checked():
    """route_grid.load_adapter 的 fail-closed 入口（调用侧唯一推荐入口）。

    在位且齐件 → 原样返回 load_adapter() 的 adapter dict；
    缺席/不完整 → PcbagentNotAvailable（结构化 not_available+原因）；
    文件齐但导入链断（坏包）→ 同口径结构化拒绝（ImportError 族收口；
    route_grid 自身的 subprocess 守卫 RuntimeError 等显式拒绝原样穿透）。
    """
    report = preflight()
    if not report["available"]:
        raise PcbagentNotAvailable(report)
    try:
        return route_grid.load_adapter()
    except ImportError as exc:  # 含 ModuleNotFoundError；坏包收口
        raise PcbagentNotAvailable({
            **report,
            "available": False,
            "status": "not_available",
            "reason": f"pcbagent 在位但导入失败：{exc}",
        }) from exc
