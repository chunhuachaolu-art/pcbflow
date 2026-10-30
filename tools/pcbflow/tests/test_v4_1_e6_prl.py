"""tests/test_v4_1_e6_prl -- G6.2 prl 卫生制度化测试。

依据：任务书 §3 E6 G6.2 + prereg-e6.json g62；事故锚=holdout-r1
（kicad-cli 在 datasets/ 受保护目录留 .kicad_prl=零写入红线首破）。

事故回归（stub 注入零真 kicad-cli 调用）：
- 注入 holdout-r1 模式（cwd+受保护目录各留 sidecar）→ guard 必须
  捕获+复原+台账+复原后 fail-closed raise；
- 负对照=正常调用零误报；
- 变更 sidecar=guard 快照字节复原；
- 白名单/上限/缺目录 fail-closed。
"""

from __future__ import annotations

import json
import os

import pytest

from pcbflow.v4_1.e6g62 import write_stub_scripts
from pcbflow.v4_1.e6prl import (EXIT_BLOCKED, EXIT_INCIDENT_RESTORED,
                                KicadCliGuard, PrlHygieneIncident,
                                load_kicad_cli_path)
from pcbflow.v4_1.prl_hygiene import PRL_SUFFIX, inventory


@pytest.fixture()
def stub(tmp_path):
    _py, bat = write_stub_scripts(str(tmp_path))
    return os.path.abspath(bat)


def _setup_dirs(tmp_path):
    staging = tmp_path / "staging"
    protected = tmp_path / "datasets-sim"
    for d in (staging, protected):
        d.mkdir()
        (d / "board.kicad_pcb").write_bytes(b"board")
    return str(staging), str(protected)


def _guard(stub_bat, ledger, protected):
    return KicadCliGuard(ledger, kicad_cli=stub_bat,
                         watch_dirs=[protected], protected_dirs=[protected])


def _run(stub_bat, mode, staging, protected, ledger):
    os.environ["E6_STUB_MODE"] = mode
    os.environ["E6_STUB_PROTECTED_DIR"] = protected
    try:
        rc, out, rec = _guard(stub_bat, ledger, protected).call(
            ["pcb", "drc", "--format", "json", "board.kicad_pcb"],
            staging, cwd_role="test")
        return {"raised": False, "record": rec}
    except PrlHygieneIncident as exc:
        return {"raised": True, "record": exc.record}
    finally:
        os.environ.pop("E6_STUB_MODE", None)
        os.environ.pop("E6_STUB_PROTECTED_DIR", None)


# ---------------------------------------------------------------- 事故回归

def test_holdout_r1_incident_captured_restored_fail_closed(tmp_path, stub):
    """事故注入：捕获+复原+台账+fail-closed raise+受保护零 prl 复原。"""
    staging, protected = _setup_dirs(tmp_path)
    ledger = str(tmp_path / "ledger.log")
    res = _run(stub, "incident", staging, protected, ledger)
    assert res["raised"], "事故未 fail-closed（牙齿失效）"
    rec = res["record"]
    assert rec["verdict"] == "incident_restored"
    # 复原终态：两目录回 pristine（无 stub sidecar）
    assert "stub.kicad_prl" not in inventory(staging)
    assert not [n for n in inventory(protected)
                if n.endswith(PRL_SUFFIX)]
    # 台账已记录（先于 raise）
    line = json.loads(open(ledger, encoding="utf-8").read().splitlines()[0])
    assert line["verdict"] == "incident_restored"
    roles = {h["role"] for h in line["hygiene"].values()}
    assert roles == {"cwd", "protected"}
    assert any(h["restored"] for h in line["hygiene"].values())


def test_normal_call_negative_control_no_false_positive(tmp_path, stub):
    """负对照：正常调用（只写合法输出）零误报。"""
    staging, protected = _setup_dirs(tmp_path)
    ledger = str(tmp_path / "ledger.log")
    res = _run(stub, "normal", staging, protected, ledger)
    assert res["raised"] is False
    assert res["record"]["verdict"] == "clean"
    assert os.path.isfile(os.path.join(staging, "stub-output.json"))  # 合法产物未被误删
    assert all(not h["restored"] and not h["unrestored"]
               for h in res["record"]["hygiene"].values())


def test_changed_sidecar_bytes_restored(tmp_path, stub):
    """变更 sidecar：guard 调用前快照 -> 字节复原 + fail-closed。"""
    staging, protected = _setup_dirs(tmp_path)
    pre = os.path.join(staging, "pre-existing.kicad_prl")
    open(pre, "wb").write(b"original-prl")
    res = _run(stub, "change", staging, protected,
               str(tmp_path / "ledger.log"))
    assert res["raised"]
    assert open(pre, "rb").read() == b"original-prl"


def test_pre_existing_protected_prl_untouched_not_deleted(tmp_path, stub):
    """受保护目录既有 prl 不在本调用窗口产生变化=不误删（守恒）。"""
    staging, protected = _setup_dirs(tmp_path)
    keeper = os.path.join(protected, "legacy.kicad_prl")
    open(keeper, "wb").write(b"legacy")
    res = _run(stub, "normal", staging, protected,
               str(tmp_path / "ledger.log"))
    assert res["raised"]  # 零 prl 断言 violated=blocked 语义
    assert open(keeper, "rb").read() == b"legacy"  # 不误删既有文件
    assert res["record"]["verdict"] == "blocked"


# ---------------------------------------------------------------- fail-closed 面

def test_subcommand_whitelist(tmp_path, stub):
    staging, protected = _setup_dirs(tmp_path)
    g = _guard(stub, str(tmp_path / "l.log"), protected)
    with pytest.raises(ValueError, match="白名单"):
        g.call(["evil-cmd", "--x"], staging)


def test_missing_cwd_fail_closed(tmp_path, stub):
    g = KicadCliGuard(str(tmp_path / "l.log"), kicad_cli=stub)
    with pytest.raises(ValueError, match="cwd"):
        g.call(["pcb", "drc"], str(tmp_path / "nope"))


def test_call_cap_fail_closed(tmp_path, stub):
    staging, protected = _setup_dirs(tmp_path)
    g = _guard(stub, str(tmp_path / "l.log"), protected)
    g.call_cap = 1
    _run(stub, "normal", staging, protected, str(tmp_path / "l2.log"))
    with pytest.raises(ValueError, match="触顶"):
        g2 = KicadCliGuard(str(tmp_path / "l3.log"), kicad_cli=stub,
                           call_cap=1)
        g2.call(["pcb", "drc"], staging)
        g2.call(["pcb", "drc"], staging)


def test_load_kicad_cli_path_from_toolchain_lock(tmp_path):
    src = os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "toolchain_lock.json")
    path = load_kicad_cli_path(src)
    assert path.lower().endswith("kicad-cli.exe")
    with open(str(tmp_path / "empty.json"), "w") as f:
        f.write("{}")
    with pytest.raises(ValueError):
        load_kicad_cli_path(str(tmp_path / "empty.json"))
    with pytest.raises(ValueError):
        load_kicad_cli_path(str(tmp_path / "missing.json"))


def test_exit_code_constants_documented():
    assert EXIT_INCIDENT_RESTORED == 90
    assert EXIT_BLOCKED == 91
