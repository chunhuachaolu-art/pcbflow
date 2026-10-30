"""pcbflow.v4_1.canonical -- canonical JSON 序列化（从 baseline.json 先例：
UTF-8 / LF / sort_keys / indent=1 / ensure_ascii=False）。

红线：无 wall-clock（日期用声明常量）、无主机绝对路径。
"""

from __future__ import annotations

import json

__all__ = ["dumps_canonical", "write_canonical_json"]


def dumps_canonical(obj):
    """obj -> canonical JSON 文本（str；LF 行尾；尾随换行）。"""
    return json.dumps(obj, ensure_ascii=False, sort_keys=True,
                      indent=1) + "\n"


def write_canonical_json(path, obj):
    """canonical 写盘（UTF-8、LF、newline="" 防 CRLF 翻译）。"""
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(dumps_canonical(obj))
