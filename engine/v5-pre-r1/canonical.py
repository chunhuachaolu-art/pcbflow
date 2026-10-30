# -*- coding: utf-8 -*-
"""canonical json 序列化（任务书 §3.4）。

规则：键序固定（字典序）、无 wall-clock、无主机路径、UTF-8、紧凑分隔符、
拒绝 NaN/Inf。同输入双跑字节相等是硬性测试（P0 门）。
"""
import json

_SEPARATOR = (",", ":")


class CanonicalError(ValueError):
    """不可序列化对象（非 JSON 类型、NaN/Inf 等）。"""


def canonical_json(obj) -> bytes:
    """确定性序列化为 bytes。任何非 JSON 兼容值（含 float nan/inf）抛 CanonicalError。"""
    try:
        text = json.dumps(
            obj, sort_keys=True, ensure_ascii=False,
            separators=_SEPARATOR, allow_nan=False,
        )
    except (ValueError, TypeError) as exc:
        raise CanonicalError("canonical 序列化失败: %s" % exc) from exc
    return text.encode("utf-8")


def canonical_text(obj) -> str:
    return canonical_json(obj).decode("utf-8")


def canonical_roundtrip(obj):
    """序列化→反序列化→再序列化字节相等；返回首序列化 bytes 与终值。"""
    first = canonical_json(obj)
    loaded = json.loads(first.decode("utf-8"))
    second = canonical_json(loaded)
    if first != second:
        raise CanonicalError("canonical round-trip 字节不等")
    return first, loaded


def canonical_sha256(obj) -> str:
    import hashlib
    return hashlib.sha256(canonical_json(obj)).hexdigest()


def sha256_bytes(data: bytes) -> str:
    import hashlib
    return hashlib.sha256(data).hexdigest()
