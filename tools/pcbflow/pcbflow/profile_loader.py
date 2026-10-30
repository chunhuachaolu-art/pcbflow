"""G0 profile 声明装载器（REPAIR-P4 W-1，profiles/revc-coreboard/）。

fail-closed：profile 缺失 / 坏 JSON / 必需节或键缺失 → ProfileError 硬失败
（REPAIR-P2 口径；不静默回落源码内嵌值——回落=未经 profile 的第二条行为
路径，违背 G0「源码不再固化 Rev-C 项目事实」的目标）。

快照纪律（行为等价关键）：config_sha256 / feedforward_config_sha256 是
「模块大写属性集」canonical dumps 的 sha（audit_cmd.py / feedforward.py），
不是文件 sha。因此装载方必须保持大写常量名与值零增删——本装载器仅供
模块初始化取值，模块内新增成员一律用小写名。

标准库自足（json/hashlib/os），不依赖包内模块——config 在 import 期调用
本模块，避免循环导入。
"""

from __future__ import annotations

import hashlib
import json
import os
from functools import lru_cache

#: 必需顶层节（装载时校验；缺任一=ProfileError）
REQUIRED_SECTIONS = ("compile", "config", "enum", "net_registry",
                     "feedforward", "check_cmd", "signoff_cmd")

#: profile 声明 schema 版本（本装载器认识的唯一版本）
PROFILE_SCHEMA_VERSION = "pcbflow-g0-profile/1.0"


class ProfileError(Exception):
    """profile 装载失败（缺失/坏 JSON/键缺失/版本不符）——fail-closed 硬失败。"""


def profile_path(root: str, profile_id: str = "revc-coreboard") -> str:
    return os.path.join(root, "profiles", profile_id, "profile.json")


@lru_cache(maxsize=4)
def load_profile(root: str, profile_id: str = "revc-coreboard") -> dict:
    """装载并校验 profile 声明；任何缺口抛 ProfileError（无静默回落）。

    lru_cache：多模块 import 期共享一次 parse；返回对象视为只读（_sha256/
    _path 元数据键由本函数附加）。
    """
    path = profile_path(root, profile_id)
    try:
        with open(path, "rb") as f:
            raw = f.read()
    except OSError as exc:
        raise ProfileError("profile_missing:%s (%s)" % (path, exc)) from exc
    try:
        pf = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProfileError("profile_bad_json:%s (%s)" % (path, exc)) from exc
    if not isinstance(pf, dict):
        raise ProfileError("profile_not_object:%s" % path)
    if pf.get("schema_version") != PROFILE_SCHEMA_VERSION:
        raise ProfileError("profile_schema_version_mismatch:%s got=%r want=%r"
                           % (path, pf.get("schema_version"),
                              PROFILE_SCHEMA_VERSION))
    if pf.get("profile_id") != profile_id:
        raise ProfileError("profile_id_mismatch:%s got=%r want=%r"
                           % (path, pf.get("profile_id"), profile_id))
    missing = [s for s in REQUIRED_SECTIONS if s not in pf]
    if missing:
        raise ProfileError("profile_missing_sections:%s %s"
                           % (path, ",".join(missing)))
    pf["_sha256"] = hashlib.sha256(raw).hexdigest()  # 小写键：不入模块 vars 快照惯例由消费方保证
    pf["_path"] = path
    return pf


def require(mapping, *keys):
    """嵌套取键；缺键=ProfileError（带完整键路径，供审计）。"""
    cur = mapping
    trail = []
    for k in keys:
        trail.append(k)
        if not isinstance(cur, dict) or k not in cur:
            raise ProfileError("profile_key_missing:" + ".".join(trail))
        cur = cur[k]
    return cur


def as_tuple(value):
    """JSON 数组 → tuple（config 历史常量的 tuple 形态保持；json dumps 两者同字节）。"""
    return tuple(value)
