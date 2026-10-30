# -*- coding: utf-8 -*-
"""Lane-K2 authority 真跑冒烟 1 例（真板真引擎基线）。

链路：badgeleds-do-electronics 真板（board.json board 体，只读）+ 同目录
execute.json 的 routes_doc（真引擎解）→ canvas.export.export_routes 导出
out/canvas-toolchain/staging/lane-k2-smoke/ → canvas.authority.
kicad_cli_aggregate 真跑聚合（F:/kicad/bin/kicad-cli.exe，默认 5 跑×至多
3 轮）。聚合报告落 smoke 目录 aggregate-report.json（冒烟读数留档）。

P5 基线（out/v5-p5/boards/badgeleds-do-electronics/drc-classified.json）：
deterministic-5x-equal、violations_total=0、unconnected=0（同板同版 10.0.5
零违例口径）——本冒烟为同输入同导出器复跑，读数应与基线一致。

kicad-cli 不存在/不可执行=blocked：skip 并打印 blocked 原因（原样返回处置
见 lane-k2 REPORT.md；不静默改道）。
"""

import json
import os

import pytest

import v5.board
from v5.canonical import canonical_json

from canvas.authority import KICAD_CLI, kicad_cli_aggregate
from canvas.export import export_routes

_REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BOARD_DIR = os.path.join(_REPO, "out", "v5-p5", "boards-pre-r1",
                         "badgeleds-do-electronics")
SMOKE_DIR = os.path.join(_REPO, "out", "canvas-toolchain", "staging",
                         "lane-k2-smoke")


def _kicad_cli_available():
    if not os.path.isfile(KICAD_CLI):
        return "blocked: kicad-cli 不存在 %s" % KICAD_CLI
    import subprocess
    try:
        proc = subprocess.run([KICAD_CLI, "version"], capture_output=True,
                              text=True, timeout=60)
    except (OSError, subprocess.SubprocessError) as exc:
        return "blocked: kicad-cli 不可执行 %s（%s）" % (KICAD_CLI, exc)
    if proc.returncode != 0:
        return "blocked: kicad-cli version 退出码 %d" % proc.returncode
    return None


def test_real_smoke_export_and_aggregate():
    blocked = _kicad_cli_available()
    if blocked is not None:
        print(blocked)
        pytest.skip(blocked)  # blocked 原文透传（处置=lane-k2 REPORT.md）
    # ---- 真板真引擎基线（只读）
    with open(os.path.join(BOARD_DIR, "board.json"), encoding="utf-8") as f:
        board = json.load(f)["board"]  # wrap 件取 board 体（合同 §0）
    v5.board.load_board(board)  # schema+哈希链复算（v5.board 锚）
    with open(os.path.join(BOARD_DIR, "execute.json"), encoding="utf-8") as f:
        routes_doc = json.load(f)["routes_doc"]  # 真引擎解（v5.routes.v1 文档）
    assert routes_doc["board_sha256"] == board["provenance"]["board_sha256"]

    # ---- 导出（staging 副本；kicad-cli 会写 .kicad_prl 到本目录）
    exported = export_routes(board, routes_doc, SMOKE_DIR)
    assert os.path.isfile(exported["kicad_pcb"])
    assert os.path.isfile(exported["kicad_pro"])
    assert exported["n_routes"] == len(routes_doc["routes"])

    # ---- 真跑聚合（P5-UP3-aggregate-v1）
    result = kicad_cli_aggregate(SMOKE_DIR)
    assert set(result) == {"drc_clean", "unconnected", "aggregate_report"}
    report = result["aggregate_report"]
    assert report["n_runs"] >= 5 and report["n_rounds"] >= 1
    assert all(len(rd) == 5 for rd in report["rounds_totals"])
    assert report["kicad_cli"]["version"].startswith("10.0.5")
    # P5 基线对照（同板同版零违例口径）
    assert result["drc_clean"] is True, report["rounds_totals"]
    assert result["unconnected"] == 0
    assert report["verdict"] == "deterministic-equal"

    with open(os.path.join(SMOKE_DIR, "aggregate-report.json"), "wb") as f:
        f.write(canonical_json(result))
    print("SMOKE-READOUT drc_clean=%s unconnected=%d verdict=%s n_rounds=%d "
          "n_runs=%d" % (result["drc_clean"], result["unconnected"],
                         report["verdict"], report["n_rounds"],
                         report["n_runs"]))
