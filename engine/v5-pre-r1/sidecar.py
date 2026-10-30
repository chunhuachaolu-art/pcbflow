# -*- coding: utf-8 -*-
"""sidecar 卫生（任务书 §3.5）。

- sidecar=一切派生件（测量 json、SVG 视图、缓存、日志、失败证书）：
  只准写 out/<run-id>/ 与 evidence 目录；工程根、语料/datasets 目录零写入（测试化）。
- 命名 <board-id>.<kind>.<ext>；头部带 provenance（generator 版本+输入 board_sha256）。
"""
import json
import os

from . import canonical

PROVENANCE_KEYS = ("generator", "generator_version", "board_sha256")

# 允许写入根（E 盘实际位置；C 盘路径为 junction 别名，不再用于新写入）。
# 统一正斜杠，避免 Windows os.path.join 反斜杠混入登记与比较。
# Public archive: the engine root is resolved from this file's location
# (override with PCBFLOW_ENGINE_ROOT). Originally a fixed path on the
# author's machine.
PROJECT_ROOT = os.environ.get(
    "PCBFLOW_ENGINE_ROOT",
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))).replace("\\", "/")
ALLOWED_ROOTS = (
    PROJECT_ROOT + "/out",
)


class SidecarViolation(ValueError):
    pass


def is_allowed_path(path):
    real = os.path.normpath(os.path.realpath(path)).replace("\\", "/")
    for root in ALLOWED_ROOTS:
        root_real = os.path.normpath(os.path.realpath(root)).replace("\\", "/")
        if real == root_real or real.startswith(root_real + "/"):
            return True
    return False


def assert_allowed(path):
    if not is_allowed_path(path):
        raise SidecarViolation("sidecar 越界写入: %s（只准 out/ 下）" % path)


def sidecar_name(board_id, kind, ext):
    return "%s.%s.%s" % (board_id, kind, ext)


def write_sidecar(path, payload, generator, generator_version, board_sha256):
    """带 provenance 头的 canonical sidecar 落盘。路径越界即抛 SidecarViolation。"""
    assert_allowed(path)
    header = {
        "provenance": {
            "generator": generator,
            "generator_version": generator_version,
            "board_sha256": board_sha256,
        }
    }
    doc = dict(header)
    doc.update(payload)
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "wb") as f:
        f.write(canonical.canonical_json(doc))
    return path


def check_file(path):
    """单文件检查：路径允许 + 可解析 + provenance 头齐全。返回问题列表。"""
    problems = []
    if not is_allowed_path(path):
        problems.append({"path": path, "issue": "path_outside_allowed_roots"})
        return problems
    if path.endswith(".json"):
        try:
            with open(path, encoding="utf-8") as f:
                doc = json.load(f)
        except (ValueError, OSError) as exc:
            problems.append({"path": path, "issue": "unparsable: %s" % exc})
            return problems
        prov = doc.get("provenance") if isinstance(doc, dict) else None
        if not isinstance(prov, dict):
            problems.append({"path": path, "issue": "missing_provenance_header"})
        else:
            for key in PROVENANCE_KEYS:
                if key not in prov:
                    problems.append({"path": path, "issue": "provenance_missing_%s" % key})
    return problems


def check_tree(root):
    """递归检查目录树（用于静态检查脚本与测试）。root 本身必须在允许根下。"""
    problems = []
    if not os.path.isdir(root):
        return problems
    for dirpath, _dirnames, filenames in os.walk(root):
        for fn in sorted(filenames):
            problems.extend(check_file(os.path.join(dirpath, fn)))
    return problems
