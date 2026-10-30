# -*- coding: utf-8 -*-
"""sidecar 卫生：允许目录、provenance 头、静态检查脚本。"""
import json
import os
import subprocess
import sys

import pytest

from v5 import sidecar
from v5.sidecar import (SidecarViolation, check_file, check_tree, is_allowed_path,
                        sidecar_name, write_sidecar)

PROV = dict(generator="v5.test", generator_version="0.1.0",
            board_sha256="0" * 64)


def test_allowed_root_is_route_v5_out():
    assert len(sidecar.ALLOWED_ROOTS) == 1
    assert sidecar.ALLOWED_ROOTS[0].endswith("route-v5/out")
    assert "E:" in sidecar.ALLOWED_ROOTS[0]  # E 盘实际位置


def test_write_inside_out_ok(tmp_path):
    target = os.path.join(sidecar.ALLOWED_ROOTS[0], "_pytest-tmp",
                          sidecar_name("board-x", "metrics", "json"))
    try:
        write_sidecar(target, {"v": 1}, **PROV)
        doc = json.load(open(target, encoding="utf-8"))
        assert doc["provenance"]["generator"] == "v5.test"
        assert doc["v"] == 1
    finally:
        if os.path.exists(target):
            os.remove(target)
        d = os.path.dirname(target)
        if os.path.isdir(d) and not os.listdir(d):
            os.rmdir(d)


def test_write_outside_rejected(tmp_path):
    target = str(tmp_path / "evil.json")
    with pytest.raises(SidecarViolation):
        write_sidecar(target, {}, **PROV)


def test_corpus_path_rejected():
    """datasets 零写入红线：语料目录路径必须被拒。"""
    bad = "E:/ZCodeData/.zcode/workspace/default/tools/pcbflow/datasets/x.json"
    assert not is_allowed_path(bad)
    with pytest.raises(SidecarViolation):
        sidecar.assert_allowed(bad)


def test_project_root_rejected():
    bad = os.path.join(sidecar.PROJECT_ROOT, "notes.json")
    assert not is_allowed_path(bad)


def test_missing_provenance_detected(tmp_path):
    target = os.path.join(sidecar.ALLOWED_ROOTS[0], "_pytest-tmp-bad.json")
    try:
        with open(target, "w", encoding="utf-8") as f:
            json.dump({"no": "header"}, f)
        problems = check_file(target)
        assert any(p["issue"] == "missing_provenance_header" for p in problems)
    finally:
        if os.path.exists(target):
            os.remove(target)


def test_partial_provenance_detected(tmp_path):
    target = os.path.join(sidecar.ALLOWED_ROOTS[0], "_pytest-tmp-partial.json")
    try:
        with open(target, "w", encoding="utf-8") as f:
            json.dump({"provenance": {"generator": "x"}}, f)
        problems = check_file(target)
        issues = [p["issue"] for p in problems]
        assert "provenance_missing_generator_version" in issues
        assert "provenance_missing_board_sha256" in issues
    finally:
        if os.path.exists(target):
            os.remove(target)


def test_sidecar_name_convention():
    assert sidecar_name("brd-1", "metrics", "json") == "brd-1.metrics.json"


def test_static_check_script_green_on_clean_tree(tmp_path):
    root = os.path.join(sidecar.ALLOWED_ROOTS[0], "_pytest-tmp-run")
    os.makedirs(root, exist_ok=True)
    script = os.path.join(os.path.dirname(sidecar.__file__), "..", "tools", "check_sidecar.py")
    try:
        write_sidecar(os.path.join(root, "b.metrics.json"), {"ok": True}, **PROV)
        proc = subprocess.run([sys.executable, script, root], capture_output=True, text=True)
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert "GREEN" in proc.stdout
    finally:
        import shutil
        shutil.rmtree(root, ignore_errors=True)
