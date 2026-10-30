"""TD10 Project Manifest 装载与验证（SPEC-v3.0 §2 TD10；吸收 v2.1 §4）。

Manifest 是唯一项目入口；null 显式表示缺失输入，永不回退任何默认项目
（L7 缺证据闭门律 / v2.1 §4.2 末句）。路径一律相对（posix 正斜杠），
按 path_base（workspace_root|manifest_dir）解析；禁回退段与主机绝对路径。

格式决策：v2.1 §4.2 示例为 YAML；v3.0 落地为 canonical JSON——理由：
canonical_json_bytes 是全链 hash 脊柱（hashing.py），JSON 免解析器依赖且
byte-exact 可重放。偏差记录于 V3-MATRIX。

生成器模式：本模块只读（open 'r'），零写盘、零子进程。
"""

from __future__ import annotations

import json
import os
import re

from . import config, hashing, schemas

# 相对路径合法性（与 schemas._REL_POSIX 同口径；此处独立声明防循环语义漂移）
_REL_POSIX_OK = re.compile(r"^[A-Za-z0-9._/+-]+$")
_WINDOWS_DRIVE = re.compile(r"^[A-Za-z]:")


def load_manifest(path: str) -> tuple[dict, str]:
    """只读装载 manifest；返回 (obj, canonical_sha256)。"""
    with open(path, "r", encoding=config.ENCODING) as f:
        obj = json.load(f)
    return obj, hashing.sha256_bytes(hashing.canonical_json_bytes(obj))


def load_profile(path: str) -> tuple[dict, str]:
    """只读装载 profile；返回 (obj, canonical_sha256)。"""
    with open(path, "r", encoding=config.ENCODING) as f:
        obj = json.load(f)
    return obj, hashing.sha256_bytes(hashing.canonical_json_bytes(obj))


def validate_manifest(obj) -> list:
    """schema 严格验证 + 语义检查（路径合法/null 语义/allowlist 存在性）。"""
    errors = schemas.validate("project_manifest", obj)
    if errors:
        return errors
    for group in ("inputs", "backtest", "policy", "external_authority"):
        for name, val in (obj.get(group) or {}).items():
            if val is None:
                continue  # null=缺失输入，合法（不是错误；context 侧如实记 absent）
            if isinstance(val, str):
                errors.extend(_path_semantic(f"{group}.{name}", val))
            elif isinstance(val, list):
                for i, item in enumerate(val):
                    if item is not None:
                        errors.extend(_path_semantic(
                            f"{group}.{name}[{i}]", item))
    root = obj.get("outputs", {}).get("root")
    if isinstance(root, str):
        errors.extend(_path_semantic("outputs.root", root))
    lock_path = (obj.get("toolchain") or {}).get("lock_path")
    if isinstance(lock_path, str):
        errors.extend(_path_semantic("toolchain.lock_path", lock_path))
    # compatibility_default 必须显式打警告（v2.1 §4.1：不得静默用默认项目）
    compat = obj.get("compatibility")
    if compat and compat.get("mode") == "compatibility_default" \
            and not compat.get("warning"):
        errors.append("compatibility: compatibility_default 必须显式 "
                      "warning=true（不得静默回退）")
    return errors


def validate_profile(obj) -> list:
    errors = schemas.validate("profile", obj)
    if errors:
        return errors
    # v2.1 §11.1：批检=severity-error、终检=severity-all 双口径分列（const 已
    # 强制）；层角色不得全为 plane（至少一个信号层才能承载布线语义）
    layers = obj.get("layers") or []
    if layers and not any(l["role"] == "signal" for l in layers):
        errors.append("layers: 无信号层（role=signal）——物理上不可布线")
    return errors


def _path_semantic(where: str, p: str) -> list:
    errs = []
    if not isinstance(p, str) or not p:
        errs.append(f"{where}: 空/非字符串路径")
        return errs
    if not _REL_POSIX_OK.match(p):
        errs.append(f"{where}: 非 posix 相对路径 {p[:80]!r}"
                    "（仅 [A-Za-z0-9._/+-]，正斜杠）")
    if _WINDOWS_DRIVE.match(p) or p.startswith("/"):
        errs.append(f"{where}: 绝对路径 {p[:80]!r}（manifest 只收相对路径）")
    return errs
    # 注：'..' 段由 resolve_path 的 realpath 包含性检查拦截（防 symlink/
    # junction 逃逸）；纯结构层无法判界，不在此重复。


def path_base(manifest: dict) -> str:
    return manifest.get("path_base") or "workspace_root"


def base_dir(manifest: dict, manifest_path: str) -> str:
    """路径解析基目录（manifest 中相对路径的锚）。"""
    if path_base(manifest) == "manifest_dir":
        return os.path.dirname(os.path.abspath(manifest_path))
    return config.WORKSPACE_ROOT


def resolve_path(manifest: dict, manifest_path: str, rel: str | None) \
        -> str | None:
    """相对路径 → 绝对路径（只算不读写）。None/非法/越界输入返回 None
    （调用方必须按缺失处理，不得猜默认）。

    越界 = realpath 解析后逃出允许根：path_base=manifest_dir ⇒ 必须落在
    PCBFLOW_ROOT（工具根）内；workspace_root ⇒ WORKSPACE_ROOT 内。
    这是 symlink/junction 逃逸与目录穿越的机器拦截点。"""
    if rel is None:
        return None
    if _path_semantic("resolve", rel):
        return None
    abs_path = os.path.join(base_dir(manifest, manifest_path),
                            *rel.split("/"))
    real = os.path.realpath(abs_path)
    allowed_root = os.path.realpath(
        config.PCBFLOW_ROOT
        if path_base(manifest) == "manifest_dir"
        else config.WORKSPACE_ROOT)
    if not (real == allowed_root
            or real.startswith(allowed_root + os.sep)):
        return None
    return abs_path


def input_entries(manifest: dict) -> list:
    """展平全部声明输入为 (group, name, rel_path|None) 三元组列表。"""
    out = []
    for group in ("inputs", "backtest", "policy", "external_authority"):
        for name, val in (manifest.get(group) or {}).items():
            if isinstance(val, list):
                for i, item in enumerate(val):
                    out.append((group, f"{name}[{i}]", item))
            else:
                out.append((group, name, val))
    tc = manifest.get("toolchain") or {}
    if tc.get("lock_path") is not None:
        out.append(("toolchain", "lock_path", tc["lock_path"]))
    return out
