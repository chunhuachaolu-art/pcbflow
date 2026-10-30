"""REPAIR-P3 W-3 依赖预检测试：pcbagent 缺席 fail-closed（不得裸 ImportError）。

三形态负向：仓根缺席 / 包不完整（缺模块文件）/ 文件齐但导入链断；
正向：真实仓在位 preflight available=True，load_adapter_checked 返回
route_grid.load_adapter 同一形状（不重复跑重的 BoardMirror 构建，只验键集）。

route_grid.py 属 M0 只读单件锚——本测试零改动锚本体，缺席模拟全部经
monkeypatch config.WORKSPACE_ROOT + sys.path/sys.modules 还原实现。
"""

from __future__ import annotations

import sys

import pytest

from pcbflow import config, pcbagent_dep, route_grid


def test_preflight_real_env_available():
    report = pcbagent_dep.preflight()
    assert report["available"] is True
    assert report["status"] == "ok"
    assert report["dependency"] == "pcbagent"
    assert report["required_modules"] == list(
        route_grid.PCBAGENT_ADAPTER_FILES)


def test_missing_repo_reports_not_available(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "WORKSPACE_ROOT", str(tmp_path))
    report = pcbagent_dep.preflight()
    assert report["available"] is False
    assert report["status"] == "not_available"
    assert str(tmp_path) in report["reason"]
    assert "engine" in report["reason"]        # 指回 pyproject 路径约定


def test_missing_repo_load_adapter_checked_is_structured(monkeypatch, tmp_path):
    """W-3 主断言：缺席时不得裸 ModuleNotFoundError 崩溃。"""
    monkeypatch.setattr(config, "WORKSPACE_ROOT", str(tmp_path))
    with pytest.raises(pcbagent_dep.PcbagentNotAvailable) as ei:
        pcbagent_dep.load_adapter_checked()
    # 非_errno：结构化拒绝不是 ImportError 族（裸崩形态必须绝迹）
    assert not isinstance(ei.value, ImportError)
    assert ei.value.report["status"] == "not_available"
    assert ei.value.report["available"] is False
    assert ei.value.report["reason"]
    assert str(ei.value) == ei.value.report["reason"]


def test_incomplete_pkg_reports_missing_modules(monkeypatch, tmp_path):
    root = tmp_path / "tools" / "pcbagent" / "pcbagent"
    root.mkdir(parents=True)
    (root / "mirror.py").write_text("", encoding="utf-8")
    monkeypatch.setattr(config, "WORKSPACE_ROOT", str(tmp_path))
    report = pcbagent_dep.preflight()
    assert report["available"] is False
    assert report["status"] == "not_available"
    # 只落了 mirror.py → 其余六模块逐一点名、mirror.py 不在点名列
    assert "缺 adapter 模块文件" in report["reason"]
    for name in route_grid.PCBAGENT_ADAPTER_FILES:
        if name != "mirror.py":
            assert name in report["reason"]
    assert "mirror.py" not in report["reason"].split("缺 adapter 模块文件 ")[1]
    with pytest.raises(pcbagent_dep.PcbagentNotAvailable):
        pcbagent_dep.load_adapter_checked()


def test_files_present_but_broken_import_is_structured(monkeypatch, tmp_path):
    """文件齐但模块体自爆 ImportError → 收口为结构化 not_available。"""
    root = tmp_path / "tools" / "pcbagent" / "pcbagent"
    root.mkdir(parents=True)
    for name in route_grid.PCBAGENT_ADAPTER_FILES:
        (root / name).write_text("", encoding="utf-8")
        # 桩须为常规包：真实 pcbagent（带 __init__）可能被先前测试遗留
        # 在 sys.path 上，命名空间桩会被导入解析整体绕过（run#2 实录）
        (root / "__init__.py").write_text("", encoding="utf-8")
    (root / "geometry.py").write_text(
        'raise ImportError("broken stub")\n', encoding="utf-8")
    monkeypatch.setattr(config, "WORKSPACE_ROOT", str(tmp_path))
    sys.path_backup = list(sys.path)
    # 全量套件上下文里真实 pcbagent 可能已被先前测试导入缓存——
    # 清场防缓存绕过（坏桩必须真的被导入）；finally 恢复原模块集
    mods_backup = {k: v for k, v in sys.modules.items()
                   if k == "pcbagent" or k.startswith("pcbagent.")}
    for k in list(mods_backup):
        del sys.modules[k]
    try:
        with pytest.raises(pcbagent_dep.PcbagentNotAvailable) as ei:
            pcbagent_dep.load_adapter_checked()
        assert not isinstance(ei.value, ImportError)
        assert ei.value.report["status"] == "not_available"
        assert "导入失败" in ei.value.report["reason"]
    finally:
        sys.path[:] = sys.path_backup
        for k in [k for k in sys.modules
                  if k == "pcbagent" or k.startswith("pcbagent.")]:
            del sys.modules[k]
        sys.modules.update(mods_backup)
