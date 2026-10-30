"""确定性序列化与哈希（SPEC §2.2）。纯函数、零 IO。

生成器模式（Mimosa 钩子约束/HANDOFF §4）：.py 不写文件；
产物在内存构建（canonical_json_bytes），由 CLI 打到 stdout，
shell 重定向落盘。同输入 ⇒ byte-exact 同输出（测试强制）。
"""

from __future__ import annotations

import hashlib
import json

from . import config


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode(config.ENCODING)).hexdigest()


def sha256_file(path: str) -> str:
    """只读哈希（输入清单/锚点验证用；.py 仍不落盘）。"""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_json_bytes(obj) -> bytes:
    """UTF-8、LF、sort_keys、固定 indent、结尾换行。"""
    text = json_dumps(obj)
    return (text + config.NEWLINE).encode(config.ENCODING)


def json_dumps(obj) -> str:
    return json.dumps(
        obj,
        ensure_ascii=config.JSON_ENSURE_ASCII,
        indent=config.JSON_INDENT,
        sort_keys=config.JSON_SORT_KEYS,
    )


def jsonl_bytes(entries) -> bytes:
    """JSONL 账本字节（逐条 sort_keys、无缩进、行尾 \\n；零 IO 纯函数）。

    REPAIR-P3 W-4 收编正身：此前同一公式在 approvals/r2/r3/r4、archive、
    autotune_chain、physics_chain 七处独立重写（SEC-PERF §SEC-C「JSONL
    账本家族 ×7 互相逐位一致」）；收编等价验证=out/repair-p3/
    vendored-consolidation-r1.md。与 json_dumps 的分界=本函数无 indent
    且逐条尾换行（账本追加式口径），json_dumps 有 indent 且无尾换行
    （单文档 canonical 口径）——两口径并存是设计而非漂移。
    """
    return "".join(
        json.dumps(e, ensure_ascii=config.JSON_ENSURE_ASCII,
                   sort_keys=config.JSON_SORT_KEYS) + "\n"
        for e in entries).encode(config.ENCODING)
