# -*- coding: utf-8 -*-
"""canvas.export 测试（Lane-K2）。

桩仅测试用、非平行实现；真件集成由编排体冒烟（export↔instantiate）。
覆盖：export_routes 文档透传/列表包装、双跑字节等（≥2）、export_kicad
instantiate 缝（stub 模块注入）、fail-closed 矩阵（非法 board/routes →
v5.kicad_export 原生报错透传、不落半成品）。

落盘域=out/canvas-toolchain/staging/（v5.sidecar 只准 out/ 之下；测试子域
lane-k2-test-export-*，teardown 清理）。
"""

import json
import os
import shutil
import sys
import types

import pytest

import v5.kicad_export
from v5.canonical import canonical_json

from canvas.export import export_kicad, export_routes
from canvas.tests.test_k2_pack import BOARD, StubState

_REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STAGING = os.path.join(_REPO, "out", "canvas-toolchain", "staging")

ROUTES_ROWS = [
    {"partition_id": "PT1", "net_id": "N1", "layer": "F.Cu",
     "polyline": [[0.0, 0.0], [5.0, 0.0]], "width": 0.25,
     "transition_vias": [], "return_vias": []},
    {"partition_id": "PT2", "net_id": "N2", "layer": "B.Cu",
     "polyline": [[0.0, 1.0], [5.0, 1.0]], "width": 0.3},
]
ROUTES_DOC = {
    "schema_version": "v5.routes.v1",
    "board_id": BOARD["board_id"],
    "board_sha256": BOARD["provenance"]["board_sha256"],
    "routes": ROUTES_ROWS,
}


@pytest.fixture
def out_dir(tmp_path):
    d = os.path.join(STAGING, "lane-k2-test-export-%s" % tmp_path.name[-8:])
    os.makedirs(d, exist_ok=True)
    yield d
    shutil.rmtree(d, ignore_errors=True)  # 测试子域清理（staging 域内自管）


def _files(d):
    return sorted(os.listdir(d))


def test_export_routes_doc_passthrough(out_dir):
    """routes 已是 v5.routes.v1 文档 → 原样透传导出器，双件落盘。"""
    result = export_routes(BOARD, ROUTES_DOC, out_dir)
    assert result["n_routes"] == 2 and result["board_id"] == BOARD["board_id"]
    assert _files(out_dir) == ["k2-stub-board.kicad_pcb",
                               "k2-stub-board.kicad_pro",
                               "k2-stub-board.netclass-mask.json"]
    with open(result["kicad_pcb"], "rb") as f:
        assert f.read() == v5.kicad_export.kicad_pcb_bytes(BOARD, ROUTES_DOC)
    with open(result["kicad_pro"], "rb") as f:
        assert f.read() == v5.kicad_export.project_kicad_pro_bytes(
            BOARD, ROUTES_DOC)


def test_export_routes_list_wrap(out_dir):
    """routes 为导出行列表 → 本件包装成文档（board_sha256 取板 provenance）。"""
    result = export_routes(BOARD, ROUTES_ROWS, out_dir)
    with open(result["kicad_pcb"], "rb") as f:
        assert f.read() == v5.kicad_export.kicad_pcb_bytes(BOARD, ROUTES_DOC)


def test_export_double_run_byte_equal(out_dir):
    """确定性双跑字节等 ≥2：同输入 3 次导出，.kicad_pcb/.kicad_pro 两两等。"""
    blobs = []
    for i in range(3):
        sub = os.path.join(out_dir, "run%d" % i)
        result = export_routes(BOARD, ROUTES_DOC, sub)
        blobs.append((open(result["kicad_pcb"], "rb").read(),
                      open(result["kicad_pro"], "rb").read()))
    assert blobs[0] == blobs[1] == blobs[2]


def test_export_kicad_seam_with_stub_instantiate(out_dir, monkeypatch):
    """export_kicad：stub canvas.instantiate（sys.modules 注入）供 routes 行。"""
    calls = []

    def fake_instantiate(st):
        calls.append(st)
        return {"coppers": [], "routes": [dict(r) for r in ROUTES_ROWS],
                "holes_norm": [], "anchors_mm": []}

    stub = types.ModuleType("canvas.instantiate")
    stub.instantiate = fake_instantiate
    monkeypatch.setitem(sys.modules, "canvas.instantiate", stub)

    st = StubState()
    result = export_kicad(st, out_dir)
    assert calls == [st]  # instantiate 收到 st 本体
    assert result["n_routes"] == 2
    with open(result["kicad_pcb"], "rb") as f:
        assert f.read() == v5.kicad_export.kicad_pcb_bytes(BOARD, ROUTES_DOC)


def test_export_kicad_gap_when_no_instantiate(out_dir, monkeypatch):
    """instantiate 缝未接线（canvas.instantiate 不可用）→ RuntimeError 不静默。

    canvas.instantiate 真件在位时此桩断言退役（真接线=编排体集成冒烟）。
    """
    try:
        import canvas.instantiate  # noqa: F401
        pytest.skip("canvas.instantiate 真件已落地（K1）：缝已接线非本测范围")
    except ImportError:
        pass
    monkeypatch.setitem(sys.modules, "canvas.instantiate", None)
    st = StubState()
    with pytest.raises(RuntimeError, match="instantiate 缝未接线"):
        export_kicad(st, out_dir)
    assert _files(out_dir) == []  # 不落半成品


def test_fail_closed_bad_board_no_r5(out_dir):
    """非法 board（R5 缺失）→ v5.kicad_export 原生 ExportError 透传。"""
    bad = dict(BOARD, hard_rules={})
    with pytest.raises(v5.kicad_export.ExportError, match="R5"):
        export_routes(bad, ROUTES_DOC, out_dir)
    assert _files(out_dir) == []


def test_fail_closed_bad_routes_unknown_net(out_dir):
    """非法 routes（未知网）→ ExportError 原生透传。"""
    bad_rows = [dict(ROUTES_ROWS[0], net_id="NOPE")]
    with pytest.raises(v5.kicad_export.ExportError, match="未知网"):
        export_routes(BOARD, bad_rows, out_dir)
    assert _files(out_dir) == []


def test_fail_closed_schema_mismatch(out_dir):
    """routes 文档 schema_version 不符 → ExportError 原生透传。"""
    bad = dict(ROUTES_DOC, schema_version="v0.zzz")
    with pytest.raises(v5.kicad_export.ExportError, match="schema_version"):
        export_routes(BOARD, bad, out_dir)
    assert _files(out_dir) == []


def test_fail_closed_non_dict_board(out_dir):
    """board 非 dict → 本件 TypeError（输入形态守门）。"""
    with pytest.raises(TypeError, match="board 须为 dict"):
        export_routes(["not", "a", "board"], ROUTES_DOC, out_dir)


def test_fail_closed_routes_wrong_type(out_dir):
    """routes 非文档非列表 → 本件 TypeError。"""
    with pytest.raises(TypeError, match="routes 须为"):
        export_routes(BOARD, "not-routes", out_dir)
