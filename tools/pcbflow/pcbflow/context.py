"""TD10/v2.1 §4.3 不可变 ProjectContext。

构造后只读快照：项目/Profile 身份、manifest/profile hash、全部声明输入的
相对路径+sha256+present 三态（null 或文件不存在 ⇒ absent，永不回退默认
项目）、policy hash、toolchain lock hash、schema 版本、输出根。

阶段函数（v3 层）应接收本 context 或其视图，不得读模块全局路径常量。
context_sha256 = 自哈希（剔除该字段自身后的 canonical hash）。
"""

from __future__ import annotations

import os

from . import hashing, manifest as manifest_mod, schemas

_CONTEXT_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["schema_version", "project_id", "profile_id",
                 "manifest_sha256", "profile_sha256", "inputs",
                 "output_root", "context_sha256"],
    "properties": {
        "schema_version": {"const": schemas.SCHEMA_V3},
        "project_id": {"type": "string", "minLength": 1},
        "profile_id": {"type": "string", "minLength": 1},
        "eda": {"type": "object"},
        "manifest_path": {"type": ["string", "null"]},
        "manifest_sha256": {"type": "string"},
        "profile_sha256": {"type": ["string", "null"]},
        "compatibility_mode": {"type": ["string", "null"]},
        "inputs": {"type": "object", "additionalProperties": {
            "type": "object", "additionalProperties": False,
            "required": ["rel_path", "sha256", "present"],
            "properties": {
                "rel_path": {"type": ["string", "null"]},
                "sha256": {"type": ["string", "null"]},
                "present": {"type": "boolean"}}}},
        "policy_hashes": {"type": "object"},
        "toolchain_lock_sha256": {"type": ["string", "null"]},
        "output_root": {"type": "string"},
        "critical_nets": {"type": "array"},
        "params": {"type": "array"},
        "profile_snapshot": {"type": ["object", "null"],
                             "additionalProperties": True},
        "dataset_splits_present": {"type": "boolean"},
        "context_sha256": {"type": "string"},
    },
}


def build_context(manifest_path: str, profile_path: str | None = None,
                  _hash_file=None) -> dict:
    """装载 manifest（+可选显式 profile），解析并哈希全部声明输入。

    只读；文件不存在 ⇒ present=false + sha256=null（缺证据闭门，不猜）。
    _hash_file 注入点仅供测试替身（默认 hashing.sha256_file）。
    """
    mf, mf_sha = manifest_mod.load_manifest(manifest_path)
    errors = manifest_mod.validate_manifest(mf)
    if errors:
        raise ValueError(f"manifest 非法: {errors[:5]}")
    hash_file = _hash_file or hashing.sha256_file

    if profile_path is None:
        # manifest 未显式给 profile ⇒ 按目录约定 profiles/<profile_id>/
        # profile.json 同锚探测（只读；不存在 ⇒ None，不回退）
        cand = os.path.join(os.path.dirname(os.path.abspath(manifest_path)),
                            "profile.json")
        profile_path = cand if os.path.exists(cand) else None

    profile_obj, profile_sha = (None, None)
    if profile_path is not None and os.path.exists(profile_path):
        profile_obj, profile_sha = manifest_mod.load_profile(profile_path)
        p_errors = manifest_mod.validate_profile(profile_obj)
        if p_errors:
            raise ValueError(f"profile 非法: {p_errors[:5]}")

    inputs = {}
    for group, name, rel in manifest_mod.input_entries(mf):
        key = f"{group}.{name}"
        abs_path = manifest_mod.resolve_path(mf, manifest_path, rel)
        if rel is None or abs_path is None:
            inputs[key] = {"rel_path": rel, "sha256": None, "present": False}
            continue
        present = os.path.isfile(abs_path)
        inputs[key] = {
            "rel_path": rel,
            "sha256": hash_file(abs_path) if present else None,
            "present": present,
        }

    policy_hashes = {k: v["sha256"]
                     for k, v in inputs.items() if k.startswith("policy.")
                     and v["sha256"]}
    lock = inputs.get("toolchain.lock_path")

    ctx = {
        "schema_version": schemas.SCHEMA_V3,
        "project_id": mf["project_id"],
        "profile_id": mf["profile_id"],
        "eda": mf.get("eda") or {"name": "kicad"},
        "manifest_path": _rel_to_workroot(manifest_path),
        "manifest_sha256": mf_sha,
        "profile_sha256": profile_sha,
        "compatibility_mode": (mf.get("compatibility") or {}).get("mode"),
        "inputs": inputs,
        "policy_hashes": policy_hashes,
        "toolchain_lock_sha256": lock["sha256"] if lock else None,
        "output_root": mf["outputs"]["root"],
        "critical_nets": list(mf.get("critical_nets") or []),
        "params": list(mf.get("params") or []),
        "dataset_splits_present": bool(mf.get("dataset_splits")),
    }
    if profile_obj is not None:
        ctx["profile_snapshot"] = {
            "critical_net_set": list(profile_obj.get("critical_net_set")
                                     or []),
            "physics_required": list(profile_obj.get("physics_required")
                                     or []),
            "external_required": list(profile_obj.get("external_required")
                                      or []),
            "bring_up_required": bool(profile_obj.get("bring_up_required")),
        }
    ctx["context_sha256"] = _self_hash(ctx)
    return ctx


def _self_hash(ctx: dict) -> str:
    body = {k: v for k, v in ctx.items() if k != "context_sha256"}
    return hashing.sha256_bytes(hashing.canonical_json_bytes(body))


def validate_context(ctx: dict) -> list:
    errs = schemas.validate_spec(_CONTEXT_SCHEMA, ctx)
    if errs:
        return errs
    if ctx["context_sha256"] != _self_hash(ctx):
        errs.append("context_sha256: 自哈希不匹配（context 被篡改或构造缺陷）")
    # null/absent 语义：present=false 必须 sha256=null（不得伪造 hash）
    for key, ent in ctx["inputs"].items():
        if not ent["present"] and ent["sha256"] is not None:
            errs.append(f"inputs.{key}: present=false 但 sha256 非 null")
    return errs


def _rel_to_workroot(path: str) -> str:
    """manifest 路径转为对 workspace 根的相对 posix 路径（仅记录用途）。"""
    try:
        from . import config as _cfg
        rel = os.path.relpath(os.path.abspath(path), _cfg.WORKSPACE_ROOT)
        return rel.replace("\\", "/")
    except ValueError:
        return path.replace("\\", "/")


def config_workroot():
    from . import config as _cfg
    return _cfg.WORKSPACE_ROOT
