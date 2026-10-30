"""REPAIR-P1 W-2：入库基线快照断言（机器可断言的合入门）。

消费 `baseline.json`（仓库根，唯一权威读数来源）+ 盘上登记清单
`known_open.json`：

1. baseline.json 存在、结构合法（result 键族/受保护三件 sha 齐备）；
2. failed_list / error_list 为空、result.failed / result.errors == 0
   （「全量 0 failed / 0 errors」是唯一合入门）；R-17（2026-09-24）起
   增 known_open 过渡形态：非零 failed 须与 known_open 登记三方精确相等
   （见 test_baseline_records_zero_failures docstring）；
3. `pytest --collect-only` 收集数与 baseline.json.result.total_collected
   精确对账（一个不多一个不少）；
4. known_open 非空时与盘上显式登记清单精确匹配（多/少皆 fail）；
   为空时登记清单必须同为空；
5. 受保护三件（pcbflow/cli.py、pcbflow/config.py、toolchain_lock.json）
   当前 sha256 与快照逐位一致（保护锚零漂移的机器断言）。

接口合同（任务书 W-2）：只读消费 baseline.json，不重跑套件（耗时控制）；
收集对账用 --collect-only 子进程（显式换独立 basetemp，避免清掉正在
运行的主套件 tmp）。
"""

import hashlib
import json
import os
import re
import subprocess
import sys

import pytest

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BASELINE_PATH = os.path.join(_REPO_ROOT, "baseline.json")
_KNOWN_OPEN_PATH = os.path.join(_REPO_ROOT, "known_open.json")

_RESULT_KEYS = ("passed", "failed", "errors", "xfailed", "warnings",
                "total_collected", "duration_s", "exit_code")
_PROTECTED_KEYS = ("pcbflow/cli.py", "pcbflow/config.py",
                   "toolchain_lock.json")


def _load_baseline():
    with open(_BASELINE_PATH, encoding="utf-8") as f:
        return json.load(f)


def _load_known_open_registry():
    with open(_KNOWN_OPEN_PATH, encoding="utf-8") as f:
        return json.load(f)


def _sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def test_baseline_file_exists_and_structure_valid():
    assert os.path.isfile(_BASELINE_PATH), "baseline.json 缺失（入库件，勿手改；刷新=重跑全量后整件重写）"
    b = _load_baseline()
    for key in ("recorded_at", "command", "working_directory", "environment",
                "result", "failed_list", "error_list", "known_open",
                "protected_files_sha256", "recorded_by"):
        assert key in b, "baseline.json 缺键：%s" % key
    for key in _RESULT_KEYS:
        assert key in b["result"], "result 缺键：%s" % key
    assert set(_PROTECTED_KEYS) <= set(b["protected_files_sha256"]), \
        "protected_files_sha256 必须含受保护三件"


def test_baseline_records_zero_failures():
    """0F/0E 唯一合入门 + R-17 known_open 过渡形态（2026-09-24）。

    非零 failed 合法当且仅当：failed_list、baseline.known_open、盘上
    known_open.json 三方逐项精确相等（每条 failed=已登记已知开放项，
    登记依据见 known_open 注释性说明件），且 errors 仍为 0、exit_code=1。
    授权链=exec/USER-RULINGS-2026-09-24.md R-17（REPAIR-G1+ D-7 停线项
    known_open 过渡裁定）；第三形态（未登记裸失败挂账）仍非法。
    """
    b = _load_baseline()
    reg = _load_known_open_registry()
    if b["result"]["failed"] == 0:
        assert b["failed_list"] == [], "failed_list 非空：第三形态（裸失败挂账）非法，走 xfail(strict) 或 known_open"
        assert b["result"]["exit_code"] == 0
    else:
        assert sorted(b["failed_list"]) == sorted(b["known_open"]) == sorted(reg), (
            "known_open 过渡形态不闭合（三方须精确相等）："
            "failed_list=%s known_open=%s registry=%s"
            % (sorted(b["failed_list"]), sorted(b["known_open"]), sorted(reg)))
        assert b["result"]["failed"] == len(b["failed_list"]), (
            "result.failed 与 failed_list 条数不一致")
        assert b["result"]["exit_code"] == 1
    assert b["result"]["errors"] == 0
    assert b["error_list"] == [], "error_list 非空：第三形态（裸错误挂账）非法"


def test_baseline_known_open_matches_on_disk_registry_exactly():
    """known_open 与盘上登记清单双向精确匹配（多/少皆 fail）。"""
    assert os.path.isfile(_KNOWN_OPEN_PATH), "known_open.json 缺失（known_open 的盘上显式登记清单）"
    b = _load_baseline()
    reg = _load_known_open_registry()
    assert isinstance(reg, list), "known_open.json 必须是列表"
    assert sorted(b["known_open"]) == sorted(reg), (
        "known_open 与登记清单不一致：baseline=%s registry=%s"
        % (sorted(b["known_open"]), sorted(reg)))


def test_protected_files_hashes_match_snapshot():
    b = _load_baseline()
    for rel in _PROTECTED_KEYS:
        abs_path = os.path.join(_REPO_ROOT, rel.replace("/", os.sep))
        assert os.path.isfile(abs_path), "受保护件缺失：%s" % rel
        got = _sha256_file(abs_path)
        assert got == b["protected_files_sha256"][rel], (
            "受保护件漂移：%s got %s want %s（任何变更须用户批准+新锚追加）"
            % (rel, got[:8], b["protected_files_sha256"][rel][:8]))


def test_collected_count_matches_baseline_total():
    """收集对账：--collect-only 收集数 == baseline.total_collected。"""
    env = dict(os.environ)
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only",
         "--basetemp=.pytest-tmp-collectprobe"],
        cwd=_REPO_ROOT, env=env, capture_output=True, text=True,
        timeout=900, encoding="utf-8", errors="replace")
    tail = proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else ""
    m = re.search(r"(\d+) tests? collected", tail)
    assert m, "collect-only 汇总行解析失败：%r" % tail
    got = int(m.group(1))
    want = _load_baseline()["result"]["total_collected"]
    assert got == want, (
        "收集数与基线不一致：got %d want %d（套件增删测试后须重跑全量并整件重写 baseline.json，注明增量来源）"
        % (got, want))
