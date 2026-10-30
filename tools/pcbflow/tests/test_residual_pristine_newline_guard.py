"""R5 —— `residual_cmd._replay_pristine_text` 读板口径的**守卫测试**。

R5 任务书 §6 第 2 条：`pcbflow/residual_cmd.py:316-318` 的
`_replay_pristine_text` 用默认文本模式读板（Python 通用换行把 `\\r\\n`
归一成 `\\n`），是把 `board_writer` 的 `eol="auto"` 接进这条链时的静默陷阱。
**优先做法是不改该读取**（改它会改写既有 FC2/ASM 产物与 hash 台账），
改为本守卫测试钉死契约 + 在函数 docstring 写明陷阱（R5 已加，见
residual_cmd.py:317-339）。

本文件钉死三件事：
1. 行为：`_replay_pristine_text` 对 CRLF 板返回**归一化**文本（无 `\\r`），
   等于 `open(..., encoding="utf-8")` 的结果，且**不等于** `newline=""` 结果；
2. 台账口径：`replay-plan.json` 的 `pristine_sha256` 是归一化文本的 sha256
   （真实 FC2 workspace 逐字节交叉核对；同时反证原始字节的 sha256 与之不同，
   即"改成 newline='' 会让台账变值"）；
3. 源码口径：`build_replay` 里的 `text_hash_note` 字面量（residual_cmd.py
   归一化声明）仍在，防止有人悄悄把口径改掉却留着旧台账。

临时目录用 `tempfile.mkdtemp()`（本环境沙箱拒绝 pytest tmp_path 的
`getbasetemp`，见主审通报），不用 `tmp_path` fixture。
"""

import inspect
import json
import os
import shutil
import tempfile
import uuid

import pytest

from pcbflow import config
from pcbflow import hashing
from pcbflow import residual_cmd as rc

_CRLF_BOARD = (
    '(kicad_pcb (version 20260206) (generator "pcbflow")\r\n'
    "\t(segment\r\n"
    "\t\t(start 1 2)\r\n"
    "\t\t(end 3 4)\r\n"
    "\t\t(width 0.25)\r\n"
    '\t\t(layer "F.Cu")\r\n'
    '\t\t(net "N1")\r\n'
    "\t)\r\n"
    ")\r\n"
)

_NOTE_LITERAL = "换行归一化文本（CRLF→LF）口径"
_FC2_PLAN = os.path.join(config.PCBFLOW_ROOT, rc.FC2_OUT_DEFAULT,
                         "replay-plan.json")


def _mk_pristine(text):
    """临时 p3 目录 + pristine 副本（byte-exact 写入，不归一化）。

    注意：本会话沙箱下 `tempfile.mkdtemp()` 建出的目录**不可写**
    （`PermissionError: [Errno 13]`，实测），`os.mkdir` 建出的可以，
    故这里用 `os.mkdir` + 唯一名；失败则返回 None（调用方 skip）。
    """
    d = os.path.join(tempfile.gettempdir(), "r5-pristine-" + uuid.uuid4().hex)
    try:
        os.mkdir(d)
    except OSError:
        return None
    try:
        with open(os.path.join(d, rc.PRISTINE_NAME), "w", encoding="utf-8",
                  newline="") as f:
            f.write(text)
    except OSError:
        shutil.rmtree(d, ignore_errors=True)
        return None
    return d


def test_replay_pristine_text_normalizes_crlf_by_design():
    d = _mk_pristine(_CRLF_BOARD)
    if d is None:
        pytest.skip("本沙箱不允许创建临时目录（os.mkdir 亦失败）")
    try:
        got = rc._replay_pristine_text({"p3": d})
        path = os.path.join(d, rc.PRISTINE_NAME)
        with open(path, encoding="utf-8") as f:
            universal = f.read()
        with open(path, encoding="utf-8", newline="") as f:
            raw = f.read()
        assert raw.count("\r\n") == 9 and raw.count("\n") == 9   # 纯 CRLF
        assert "\r" not in got                       # 归一化：无 CR
        assert got == universal                      # 通用换行模式
        assert got != raw                            # 与 newline="" 不同
        assert got == _CRLF_BOARD.replace("\r\n", "\n")
        # 台账口径：pristine_sha256 取归一化文本的 sha256（与原始字节不同）
        assert hashing.sha256_bytes(got.encode("utf-8")) != \
            hashing.sha256_bytes(raw.encode("utf-8"))
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_replay_pristine_text_missing_file_raises_filenotfound():
    """文件缺失 → FileNotFoundError（不吞异常、不返回空串）。"""
    d = os.path.join(config.PCBFLOW_ROOT, "tests")
    assert not os.path.exists(os.path.join(d, rc.PRISTINE_NAME))
    with pytest.raises(FileNotFoundError):
        rc._replay_pristine_text({"p3": d})


def test_text_hash_note_declares_normalized_hash_scope():
    """`build_replay` 必须仍声明"归一化文本口径"（源码字面量，非仅产物）。"""
    src = inspect.getsource(rc.build_replay)
    assert _NOTE_LITERAL in src
    assert "writer 链统一 LF 落盘" in src


@pytest.mark.skipif(not os.path.exists(_FC2_PLAN),
                    reason="FC2 replay-plan.json 历史产物不存在")
def test_real_fc2_ledger_hash_is_in_normalized_newline_domain():
    """真实 FC2 产物的逐字节交叉核对（改读取方式必然改写该台账）。

    实测（2026-09-11）：`out/revc-fc2/workspace/p3-replay/pristine.kicad_pcb`
    = 382528 B、17986 个 CRLF、0 个裸 LF；
      sha256(归一化文本) = 13e5d933d1de0b2ff53692521fc4820832794946d19433080f0920d208f09172
      sha256(原始字节)   = 1ba6b25975935288e14a86db0ae364aeedf586ced92337cedbc3b1d833d114cf
    `replay-plan.json` 的 `replay.pristine_sha256` == 前者（**不是**后者）。
    """
    ws = rc._workspace_dirs(rc.FC2_OUT_DEFAULT)
    path = os.path.join(ws["p3"], rc.PRISTINE_NAME)
    with open(_FC2_PLAN, encoding="utf-8") as f:
        plan = json.load(f)
    ledger_sha = plan["replay"]["pristine_sha256"]
    assert plan["replay"]["text_hash_note"] == (
        "本节 sha256=换行归一化文本（CRLF→LF）口径；板副本经 writer 链统一"
        " LF 落盘，kicad-cli 已验证可解析")
    if not os.path.exists(path):
        pytest.skip("FC2 pristine 副本不存在（产物已归档）")
    with open(path, encoding="utf-8") as f:
        normalized = f.read()
    with open(path, encoding="utf-8", newline="") as f:
        raw = f.read()
    assert normalized != raw                     # 真实 pristine 是 CRLF 板
    assert raw.count("\r\n") > 0
    assert hashing.sha256_bytes(normalized.encode("utf-8")) == ledger_sha
    assert hashing.sha256_bytes(raw.encode("utf-8")) != ledger_sha
    assert rc._replay_pristine_text(ws) == normalized
