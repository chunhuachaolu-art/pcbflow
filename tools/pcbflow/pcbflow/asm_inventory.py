"""TD9 湿区 inventory（SPEC-v3.0-PROPOSAL TD9）：asm_*.py 只读能力快照。

对 out/revc-asm/（历史湿区）与 scripts/（包候选）下的 .py 做零执行静态
扫描，产出每脚本的 hash/行数/docstring 首段/能力特征，附迁移十门缺省值。

红线（TD9 原文约束的模块侧落地）：
  - 只读扫描：本模块不移动/修改/复制任何历史产物；只读文件字节与文本，
    绝不 exec 被扫描脚本。
  - historical_only 是冻结结论：迁移十门（migration_gate）对全新 inventory
    一律记 False——未评估即未通过（fail-closed），本模块不存在任何把
    historical_only 标为可迁移的路径。
  - 产物卫生：inventory 不携带主机绝对路径（excerpt/doc_head 中盘符路径
    掩码为 <abs-path>），脚本路径一律相对 posix 风格；无 wall-clock 键
    （对齐 envelope.FORBIDDEN_CORE_KEYS）。

生成器模式沿用：纯函数确定性、零子进程、零写盘、零网络、标准库 only
（hashing/schemas 为包内既有依赖；本模块不 import config）。
特征抽取为启发式文本扫描（合同口径）：注释/文档字符串中的同形文本
也会命中，扫描结论只作 inventory 证据、不作执行许可。
"""

from __future__ import annotations

import os
import re

from . import hashing, schemas

SCHEMA_VERSION = "3.0"
ARTIFACT_KIND = "asm_inventory"
NOTE = "historical_only 脚本不迁移不改写；本 inventory 为只读快照"

# 湿区根（posix 相对 pcbflow_root；out/* 恒 historical_only）
DEFAULT_ROOTS = ("out/revc-asm", "scripts")

CLASSIFICATION_HISTORICAL = "historical_only"
CLASSIFICATION_PACKAGE = "package_candidate"

# TD9 原文迁移十门：package-owned 脚本进入新执行链的前置条件。
# 全新 inventory 不做任何门评估，十门一律 False（not_evaluated=False）。
MIGRATION_GATE_KEYS = (
    "package_versioned",            # package 版本化
    "schema_io_hash_pinned",        # schema 与输入输出 hash 固定
    "relative_paths_allowlist",     # 相对路径 / allowlist
    "staging_only",                 # staging-only 写域
    "single_writer",                # 单写者
    "transaction_rollback",         # 事务 / rollback
    "machine_drc",                  # 机器 DRC
    "negative_tests",               # 负向测试
    "crash_recovery",               # 崩溃恢复
    "live_board_zero_write_witness",  # live-board 零写见证
)

# 静态特征扫描口径（纯子串/行级正则；不 exec）
_SUBPROCESS_MARKERS = (
    "import subprocess",
    "os.system",
    "os.popen",
    "subprocess.run",
    "subprocess.call",
    "subprocess.Popen",
)
# open(..., 'w'/'a'/'wb'/'ab')：行内 open( 调用后随独立引号写模式
# （含 Path(...).open(...'w')——\bopen 同时命中 .open）。
_OPEN_WRITE_RE = re.compile(r"\bopen\s*\([^\n]*['\"](?:wb|ab|w|a)['\"]")
_WRITE_CALL_MARKERS = ("write_text(", "write_bytes(")
_STDIN_MARKER = "sys.stdin"
_STDOUT_MARKERS = ("print(", "sys.stdout")
_BOARD_TEXT_MARKER = "kicad_pcb"

_TRIPLE_QUOTES = ('"""', "'''")
_DOC_HEAD_SCAN_LINES = 3       # docstring 开引号须出现在前 3 行内
_DOC_HEAD_MAX = 512            # 首段截断上限
_MAX_WRITE_EXCERPTS = 3        # 写盘摘录 ≤3 条（TD9 合同）
_EXCERPT_MAX = 200             # 单条摘录截断上限

# 主机绝对路径（Windows 盘符）掩码：核心产物禁携带（envelope 同口径）
_HOST_PATH_RE = re.compile(r"[A-Za-z]:[\\/][^\s\"'\r\n]*")

# 局部 schema（schemas 支持子集语法；与注册表 schema 同风格）
_HASH64_RE = "^[0-9a-f]{64}$"
_REL_POSIX_RE = "^[A-Za-z0-9._/+-]+$"   # 相对 posix；禁反斜杠/盘符/空白

_ITEM_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["script_rel_path", "sha256", "line_count", "classification",
                 "capabilities", "doc_head", "migration_gate"],
    "properties": {
        "script_rel_path": {"type": "string", "pattern": _REL_POSIX_RE,
                            "maxLength": 256},
        "sha256": {"type": "string", "pattern": _HASH64_RE},
        "line_count": {"type": "integer", "minimum": 0},
        "classification": {"enum": [CLASSIFICATION_HISTORICAL,
                                    CLASSIFICATION_PACKAGE]},
        "capabilities": {
            "type": "object", "additionalProperties": False,
            "required": ["subprocess_use", "file_write_patterns",
                         "board_text_touch", "stdin_generator",
                         "stdout_only_writes"],
            "properties": {
                "subprocess_use": {"type": "boolean"},
                "file_write_patterns": {"type": "array", "maxItems": 3,
                                        "items": {"type": "string",
                                                  "maxLength": _EXCERPT_MAX}},
                "board_text_touch": {"type": "boolean"},
                "stdin_generator": {"type": "boolean"},
                "stdout_only_writes": {"type": "boolean"},
            },
        },
        "doc_head": {"oneOf": [{"type": "null"},
                               {"type": "string",
                                "maxLength": _DOC_HEAD_MAX}]},
        "migration_gate": {
            "type": "object", "additionalProperties": False,
            "required": list(MIGRATION_GATE_KEYS),
            "properties": {k: {"type": "boolean"}
                           for k in MIGRATION_GATE_KEYS},
        },
    },
}

_COUNT_KEYS = ("total", "historical_only", "package_candidate",
               "subprocess_use", "file_write_patterns", "board_text_touch",
               "stdin_generator", "stdout_only_writes")

INVENTORY_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["schema_version", "artifact_kind", "generated_from_roots",
                 "items", "counts", "note"],
    "properties": {
        "schema_version": {"const": SCHEMA_VERSION},
        "artifact_kind": {"const": ARTIFACT_KIND},
        "generated_from_roots": {"type": "array",
                                 "items": {"type": "string",
                                           "pattern": _REL_POSIX_RE,
                                           "maxLength": 128}},
        "items": {"type": "array", "items": _ITEM_SCHEMA},
        "counts": {
            "type": "object", "additionalProperties": False,
            "required": list(_COUNT_KEYS),
            "properties": {k: {"type": "integer", "minimum": 0}
                           for k in _COUNT_KEYS},
        },
        "note": {"type": "string", "minLength": 1, "maxLength": 256},
    },
}


# ---------------------------------------------------------------------------
# 纯文本扫描核心（scan_text：零 IO，可纯内存测试；scan_script 只读一层）
# ---------------------------------------------------------------------------

def _mask_host_paths(text: str) -> str:
    """盘符绝对路径掩码（核心产物卫生；掩码不改变其余文本）。"""
    return _HOST_PATH_RE.sub("<abs-path>", text)


def _extract_doc_head(text: str) -> str | None:
    """模块 docstring 首段：开引号须在前 3 行内，正文可跨行。

    可失败返回 None：前 3 行无 triple-quote、闭引号缺失、首段为空。
    """
    lines = text.splitlines()
    head = "\n".join(lines[:_DOC_HEAD_SCAN_LINES])
    start, quote = None, None
    for q in _TRIPLE_QUOTES:
        pos = head.find(q)
        if pos >= 0 and (start is None or pos < start):
            start, quote = pos, q
    if quote is None:
        return None
    body_text = head[start + len(quote):] + "\n" + "\n".join(
        lines[_DOC_HEAD_SCAN_LINES:])
    end = body_text.find(quote)
    if end < 0:
        return None
    para: list = []
    for ln in body_text[:end].splitlines():
        if not ln.strip():
            if para:
                break           # 首段终止于首个空行
            continue            # 跳过段前空行
        para.append(ln.strip())
    if not para:
        return None
    return _mask_host_paths("\n".join(para))[:_DOC_HEAD_MAX]


def _scan_capabilities(text: str) -> dict:
    """静态能力特征（纯文本扫描，不 exec）：子进程/写盘/板文本/stdin/stdout。"""
    file_write_patterns: list = []
    for line in text.splitlines():
        if len(file_write_patterns) >= _MAX_WRITE_EXCERPTS:
            break
        if (_OPEN_WRITE_RE.search(line)
                or any(m in line for m in _WRITE_CALL_MARKERS)):
            file_write_patterns.append(
                _mask_host_paths(line.strip())[:_EXCERPT_MAX])
    writes_files = bool(file_write_patterns)
    has_stdout = any(m in text for m in _STDOUT_MARKERS)
    return {
        "subprocess_use": any(m in text for m in _SUBPROCESS_MARKERS),
        "file_write_patterns": file_write_patterns,
        "board_text_touch": _BOARD_TEXT_MARKER in text,
        "stdin_generator": _STDIN_MARKER in text,
        "stdout_only_writes": (not writes_files) and has_stdout,
    }


def scan_text(text: str) -> dict:
    """纯内存扫描 .py 文本：{line_count, doc_head, capabilities}（零 IO）。"""
    return {
        "line_count": len(text.splitlines()),
        "doc_head": _extract_doc_head(text),
        "capabilities": _scan_capabilities(text),
    }


def scan_script(abs_path: str) -> dict:
    """只读扫描单个 .py：sha256 + 行数 + docstring 首段 + 静态特征。

    绝不 exec 被扫描脚本；只读取（bytes 哈希 + utf-8 容错解码）。
    """
    with open(abs_path, "r", encoding="utf-8", errors="replace") as f:
        text = f.read()
    return {
        "sha256": hashing.sha256_file(abs_path),
        **scan_text(text),
    }


# ---------------------------------------------------------------------------
# inventory 构建（只读遍历；historical 产物零改动）
# ---------------------------------------------------------------------------

def default_pcbflow_root() -> str:
    """默认仓库根（包目录上一级；本模块不 import config，常量内聚）。"""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _classify(script_rel_path: str) -> str:
    """按根前缀分类：out/*=historical_only（冻结），scripts/*=package_candidate。

    其他根 fail-closed 抛错——宁可失败也不得给出未知分类（更不得把
    historical 标为可迁移）。
    """
    top = script_rel_path.split("/", 1)[0]
    if top == "out":
        return CLASSIFICATION_HISTORICAL
    if top == "scripts":
        return CLASSIFICATION_PACKAGE
    raise ValueError(
        f"无法分类 {script_rel_path!r}：仅支持 out/*（historical_only）与 "
        f"scripts/*（package_candidate）两类根")


def _iter_py_files(base_dir: str):
    """确定性遍历 base_dir 下 *.py（递归；剪枝 __pycache__；字典序）。"""
    for dirpath, dirnames, filenames in os.walk(base_dir):
        dirnames[:] = sorted(d for d in dirnames if d != "__pycache__")
        for name in sorted(filenames):
            if name.endswith(".py"):
                full = os.path.join(dirpath, name)
                rel = os.path.relpath(full, base_dir).replace(os.sep, "/")
                yield full, rel


def build_inventory(pcbflow_root: str | None = None,
                    roots: tuple = DEFAULT_ROOTS) -> dict:
    """构建湿区只读快照：roots 下每 *.py 一项 + 顶层计数。

    红线：只读（不移动/修改/复制历史产物）；migration_gate 十门恒 False。
    根目录缺失 fail-closed 抛 FileNotFoundError（宁失败不静默缺项）。
    """
    root_dir = (os.fspath(pcbflow_root) if pcbflow_root is not None
                else default_pcbflow_root())
    items: list = []
    for root in roots:
        root_posix = root.replace(os.sep, "/")
        base = os.path.join(root_dir, *root_posix.split("/"))
        if not os.path.isdir(base):
            raise FileNotFoundError(f"inventory root 不存在: {root!r}")
        for abs_path, rel_within in _iter_py_files(base):
            rel = f"{root_posix}/{rel_within}"
            scanned = scan_script(abs_path)
            items.append({
                "script_rel_path": rel,
                "sha256": scanned["sha256"],
                "line_count": scanned["line_count"],
                "classification": _classify(rel),
                "capabilities": scanned["capabilities"],
                "doc_head": scanned["doc_head"],
                "migration_gate": {k: False for k in MIGRATION_GATE_KEYS},
            })
    items.sort(key=lambda it: it["script_rel_path"])

    def _count(key: str) -> int:
        return sum(1 for it in items if it["capabilities"][key])

    counts = {
        "total": len(items),
        CLASSIFICATION_HISTORICAL: sum(
            1 for it in items
            if it["classification"] == CLASSIFICATION_HISTORICAL),
        CLASSIFICATION_PACKAGE: sum(
            1 for it in items
            if it["classification"] == CLASSIFICATION_PACKAGE),
        "subprocess_use": _count("subprocess_use"),
        "file_write_patterns": _count("file_write_patterns"),
        "board_text_touch": _count("board_text_touch"),
        "stdin_generator": _count("stdin_generator"),
        "stdout_only_writes": _count("stdout_only_writes"),
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "artifact_kind": ARTIFACT_KIND,
        "generated_from_roots": list(roots),
        "items": items,
        "counts": counts,
        "note": NOTE,
    }


def validate_inventory(inv) -> list:
    """严格验证 inventory（本模块局部 schema，经 schemas.validate_spec）。

    覆盖：script_rel_path 相对 posix、sha256 64hex、classification enum、
    十门布尔、fail-closed 多余键。返回错误列表（[] = 合法）。
    """
    return schemas.validate_spec(INVENTORY_SCHEMA, inv)
