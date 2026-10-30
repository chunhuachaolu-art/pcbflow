# -*- coding: utf-8 -*-
"""canvas.authority 测试（Lane-K2）——假 kicad-cli 注入（不依赖真件）。

覆盖：fail-closed 矩阵（退出码非零/输出解析失败→报错不吞）、聚合协议读数
（全等轮即停/无全等轮 union-max+披露）、staging 域守门、pcb 数量守门。

假件：fake_cli.bat → fake_impl.py（behavior.txt 控制行为：fixed/fail-exit/
bad-json/drift；calls.txt 记全局调用序）。测试域=out/canvas-toolchain/
staging/lane-k2-test-auth-*（staging 域内自管，teardown 清理）。
真跑冒烟见 test_k2_smoke_real.py。
"""

import json
import os
import shutil

import pytest

import canvas.authority as authority
from canvas.authority import kicad_cli_aggregate

_REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STAGING = os.path.join(_REPO, "out", "canvas-toolchain", "staging")

FAKE_IMPL = r'''# -*- coding: utf-8 -*-
"""假 kicad-cli（仅测试用）：behavior.txt 控制行为，calls.txt 记调用序。"""
import json
import os
import sys

here = os.path.dirname(os.path.abspath(__file__))
args = sys.argv[1:]

calls_file = os.path.join(here, "calls.txt")
calls = 0
if os.path.exists(calls_file):
    with open(calls_file, encoding="utf-8") as f:
        calls = int((f.read() or "0").strip())
calls += 1
with open(calls_file, "w", encoding="utf-8") as f:
    f.write(str(calls))

if args and args[0] == "version":
    print("fake-kicad-cli 10.0.5")
    sys.exit(0)

with open(os.path.join(here, "behavior.txt"), encoding="utf-8") as f:
    behavior = f.read().split()
mode = behavior[0]
out = None
for i, a in enumerate(args):
    if a == "--output" and i + 1 < len(args):
        out = args[i + 1]

if mode == "fail-exit":
    sys.stderr.write("fake kicad-cli simulated failure\n")
    sys.exit(3)
if mode == "bad-json":
    with open(out, "w", encoding="utf-8") as f:
        f.write("{not-json")
    sys.exit(0)
if mode == "fixed":
    n_v, n_u = int(behavior[1]), int(behavior[2])
    doc = {"violations": [{"type": "clearance", "desc": "fake %d" % k}
                          for k in range(n_v)],
           "unconnected_items": [{"item": k} for k in range(n_u)],
           "schematic_parity": []}
    with open(out, "w", encoding="utf-8") as f:
        json.dump(doc, f)
    sys.exit(0)
if mode == "drift":
    n = max(1, calls - 1)  # 首次调用是 version 探测
    doc = {"violations": [{"type": "clearance"} for _ in range(n)],
           "unconnected_items": [], "schematic_parity": []}
    with open(out, "w", encoding="utf-8") as f:
        json.dump(doc, f)
    sys.exit(0)
sys.stderr.write("unknown mode %r\n" % mode)
sys.exit(9)
'''

FAKE_BAT = "@echo off\r\n@python \"%~dp0fake_impl.py\" %*\r\n@exit /b %ERRORLEVEL%\r\n"


@pytest.fixture
def fake_cli(tmp_path, monkeypatch):
    """staging 域内造假 kicad-cli；返回 set_behavior(mode, *nums) 控制器。"""
    d = os.path.join(STAGING, "lane-k2-test-auth-%s" % tmp_path.name[-8:])
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "fake_impl.py"), "w", encoding="utf-8") as f:
        f.write(FAKE_IMPL)
    bat = os.path.join(d, "fake_cli.bat")
    with open(bat, "w", encoding="utf-8") as f:
        f.write(FAKE_BAT)
    with open(os.path.join(d, "mini.kicad_pcb"), "w", encoding="utf-8") as f:
        f.write("(kicad_pcb fake-for-lane-k2-test)\n")

    def set_behavior(mode, *nums):
        with open(os.path.join(d, "behavior.txt"), "w",
                  encoding="utf-8") as f:
            f.write(" ".join([mode] + [str(n) for n in nums]))

    set_behavior("fixed", "0", "0")
    monkeypatch.setattr(authority, "KICAD_CLI", bat)
    yield set_behavior
    shutil.rmtree(d, ignore_errors=True)


def test_fixed_deterministic_equal(fake_cli):
    """固定输出（2 违例/1 未连）→ 全等轮即停：n_rounds=1、n_runs=5。"""
    fake_cli("fixed", 2, 1)
    result = kicad_cli_aggregate(os.path.dirname(authority.KICAD_CLI))
    assert result["drc_clean"] is False
    assert result["unconnected"] == 1
    report = result["aggregate_report"]
    assert report["verdict"] == "deterministic-equal"
    assert report["n_rounds"] == 1 and report["n_runs"] == 5
    assert report["rounds_totals"] == [[2] * 5]
    assert report["aggregate_union_max"]["violations_total"] == 2
    assert report["protocol"]["name"] == "P5-UP3-aggregate-v1"
    assert report["kicad_cli"]["version"] == "fake-kicad-cli 10.0.5"
    json.dumps(report)  # canonical 可序列化


def test_fixed_clean(fake_cli):
    """固定零违例 → drc_clean=True、unconnected=0。"""
    fake_cli("fixed", 0, 0)
    result = kicad_cli_aggregate(os.path.dirname(authority.KICAD_CLI))
    assert result["drc_clean"] is True and result["unconnected"] == 0


def test_drift_union_max_disclosed(fake_cli):
    """逐跑漂移（totals 1..15 无全等轮）→ union-max+披露，至多 3 轮 15 跑。"""
    fake_cli("drift")
    result = kicad_cli_aggregate(os.path.dirname(authority.KICAD_CLI))
    report = result["aggregate_report"]
    assert report["verdict"] == "nondeterministic-disclosed"
    assert report["n_rounds"] == 3 and report["n_runs"] == 15
    flat = [t for rd in report["rounds_totals"] for t in rd]
    assert flat == list(range(1, 16))
    assert report["aggregate_union_max"]["violations_total"] == 15
    assert result["drc_clean"] is False


def test_fail_closed_cli_exit_code(fake_cli):
    """kicad-cli 退出码非零 → RuntimeError 不吞（带轮/跑定位）。"""
    fake_cli("fail-exit")
    with pytest.raises(RuntimeError, match="退出码 3"):
        kicad_cli_aggregate(os.path.dirname(authority.KICAD_CLI))


def test_fail_closed_bad_json(fake_cli):
    """输出非法 JSON（退出码 0）→ 解析失败 fail-closed。"""
    fake_cli("bad-json")
    with pytest.raises(RuntimeError, match="解析失败"):
        kicad_cli_aggregate(os.path.dirname(authority.KICAD_CLI))


def test_staging_guard(fake_cli, tmp_path):
    """export_dir 越出 staging 域 → ValueError（.kicad_prl 写入域守门）。"""
    with pytest.raises(ValueError, match="越界"):
        kicad_cli_aggregate(str(tmp_path))


def test_no_pcb_fail_closed(fake_cli, tmp_path):
    d = os.path.join(STAGING, "lane-k2-test-auth-empty-%s" % tmp_path.name[-8:])
    os.makedirs(d, exist_ok=True)
    try:
        with pytest.raises(FileNotFoundError, match="无 .kicad_pcb"):
            kicad_cli_aggregate(d)
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_two_pcbs_ambiguous(fake_cli):
    d = os.path.dirname(authority.KICAD_CLI)
    with open(os.path.join(d, "second.kicad_pcb"), "w",
              encoding="utf-8") as f:
        f.write("(kicad_pcb second)\n")
    try:
        with pytest.raises(ValueError, match="歧义"):
            kicad_cli_aggregate(d)
    finally:
        os.remove(os.path.join(d, "second.kicad_pcb"))


def test_bad_params_fail_closed(fake_cli):
    with pytest.raises(ValueError, match="runs/max_rounds"):
        kicad_cli_aggregate(os.path.dirname(authority.KICAD_CLI), runs=0)
