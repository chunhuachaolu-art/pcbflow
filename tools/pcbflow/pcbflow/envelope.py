"""统一输出 envelope（SPEC §2.1）+ 核心产物禁区扫描。

四字段不得互相替代（SPEC §0.1）：
  status        ok|failed|blocked|unknown   —— 这次工作是否完成
  verdict       pass|fail|waived|yellow|red  —— 质量结论
  checker_status executed|not_executed|error —— （检查器级字段）
  gate_status   pending|pass|fail|waived|blocked ——（约束门级字段）

envelope 顶层只出现 status/verdict；checker_status/gate_status 属于
data 内的检查/约束条目，禁止互相替代。
"""

from __future__ import annotations

import re

from . import config

STATUS_VALUES = {"ok", "failed", "blocked", "unknown"}
VERDICT_VALUES = {"pass", "fail", "waived", "yellow", "red"}
DETERMINISM_VALUES = {"byte_exact", "semantic", "not_claimed"}

# 核心产物禁区（SPEC §2.2）：这些键/值模式不得出现在核心产物任何层级。
FORBIDDEN_CORE_KEYS = {
    "date", "started_at", "finished_at", "elapsed_s", "run_s", "run_seconds",
    "total_s", "host", "hostname", "session", "session_id", "timestamp",
    "created_at", "generated_at", "user", "username", "cwd",
}
# 主机绝对路径盘符（Windows）——核心产物中禁止出现。
# SEC-B-01 修复（SEC-PERF-REVIEW-2026-09-19）：旧正则只匹配反斜杠形态，
# `C:/Users/...`（正斜杠）全部漏检（实证 out/coreboard-probe1/verdicts/
# probe1-fmc-failcert.json:43402）；对照 copper_loop.py:125。负向后行断言
# 防 URL 误拦（`https://` 的 s:/ 不得命中）。
_ABS_PATH_RE = re.compile(r"(?<![A-Za-z0-9])[A-Za-z]:[\\/][^\"]*")


def build_envelope(
    *,
    command: str,
    status: str,
    verdict: str,
    inputs: list,
    artifacts: list,
    metrics: dict | None = None,
    diagnostics: list | None = None,
    data: dict | None = None,
    config_sha256: str | None = None,
    spec_refs: list | None = None,
    determinism_claim: str = "byte_exact",
    waivers: list | None = None,
    solver: dict | None = None,
    run_metadata: dict | None = None,
    command_kind: str | None = None,
    schema_version: str | None = None,
) -> dict:
    """command_kind/schema_version：v1.3 envelope 增量字段（SPEC §14.2/A3）。
    默认 None → 不写入/沿用全局 SCHEMA_ENVELOPE，既有调用输出 byte-exact 不变。"""
    assert status in STATUS_VALUES, status
    assert verdict in VERDICT_VALUES, verdict
    assert determinism_claim in DETERMINISM_VALUES, determinism_claim
    assert command_kind is None or command_kind in {"core", "advisory"}, command_kind
    out = {
        "schema_version": schema_version or config.SCHEMA_ENVELOPE,
        "tool": "pcbflow",
        "tool_version": config.TOOL_VERSION,
        "command": command,
        "status": status,
        "verdict": verdict,
        "deterministic": determinism_claim != "not_claimed",
        "determinism_claim": determinism_claim,
        "inputs": inputs,
        "config_sha256": config_sha256,
        "spec_refs": spec_refs or [],
        "artifacts": artifacts,
        "metrics": metrics or {},
        "diagnostics": diagnostics or [],
        "waivers": waivers or [],
        "solver": solver or {},
        "run_metadata": run_metadata or {},
        "data": data or {},
    }
    if command_kind is not None:
        out["command_kind"] = command_kind
    return out


def scan_forbidden_core_fields(obj, path="$"):
    """递归扫描核心产物禁区。返回违规列表 [(path, kind, value)]。

    kind: key=禁区键名；abs_path=主机绝对路径。
    输入文件内的源文本（如 spec 引文）不豁免 —— 核心产物一律禁。
    """
    hits = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if str(k).lower() in FORBIDDEN_CORE_KEYS:
                hits.append((f"{path}.{k}", "key", str(k)))
            hits.extend(scan_forbidden_core_fields(v, f"{path}.{k}"))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            hits.extend(scan_forbidden_core_fields(v, f"{path}[{i}]"))
    elif isinstance(obj, str):
        if _ABS_PATH_RE.search(obj):
            hits.append((path, "abs_path", obj[:80]))
    return hits
