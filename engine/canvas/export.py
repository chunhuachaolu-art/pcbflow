# -*- coding: utf-8 -*-
"""canvas.export —— 实例化态 → KiCad 导出（Lane-K2；合同 §1 export 节）。

export_kicad(st, out_dir)：canvas.instantiate.instantiate(st) 取 routes →
v5.kicad_export.write_kicad_pcb 落 .kicad_pcb + 配套 .kicad_pro（导出器
单入口双件落盘——pro 由 write_kicad_pcb 内部调 project_kicad_pro_bytes
先推导成功后才动盘，半成品不落）。export_routes(board, routes, out_dir)：
board+routes 直给旁路（st 为合同签名桩/无 instantiate 真件时）。

**文档化最小决定（逐字披露）**：

- **instantiate 缝**：export_kicad 运行期延迟 import canvas.instantiate
  （K1 并行车道，未落地=RuntimeError fail-closed，不静默改道）。真接线=
  编排体集成冒烟。
- **routes 行→文档包装**：instantiate 返回的 routes 是**导出行列表**
  （合同 §1 instantiate 节），而 v5.kicad_export 合同要求 v5.routes.v1
  **文档**（schema_version/board_id/board_sha256/routes）。本件只做包装
  （几何行本体出自 instantiate，非平行实现）：board_id 取
  ``st.board["board_id"]``，board_sha256 取 ``st.board_sha256``（构造期
  冻结锚）。export_routes 的 routes 已是文档则原样透传；是列表则同规则
  包装（board_sha256 回退板 provenance，再无则 v5.board.compute_board_sha256
  重算）。
- **落盘域**：write_kicad_pcb 带 v5.sidecar 校验（只准 out/ 之下）——
  本件导出一律落 staging 副本目录（out/canvas-toolchain/staging/…），绝不
  写 boards/、datasets/（合同 §4）。文件名=``<board_id>.kicad_pcb``。
- **fail-closed 透传**：非法 board/routes 抛 v5.kicad_export.ExportError
  （ValueError 子类）原样透传，不吞不译（合同形状校验归导出器单源）。
- **确定性**：导出器纯函数保证同输入双跑字节等；本件只加确定性包装。
"""

import os

import v5.kicad_export
from v5.board import compute_board_sha256

GENERATOR = "canvas.export"
VERSION = "1.0.0"
ROUTES_SCHEMA_VERSION = "v5.routes.v1"


def _wrap_routes_doc(board, board_sha256, routes):
    """routes 行列表 → v5.routes.v1 文档（已是 dict 文档则原样透传）。"""
    if isinstance(routes, dict):
        return routes
    if not isinstance(routes, list):
        raise TypeError("routes 须为 v5.routes.v1 文档 dict 或导出行 list，"
                        "实得 %s" % type(routes).__name__)
    return {
        "schema_version": ROUTES_SCHEMA_VERSION,
        "board_id": board["board_id"],
        "board_sha256": board_sha256,
        "routes": routes,
    }


def _write_both(board, doc, out_dir):
    """write_kicad_pcb 双件落盘（sidecar 校验在导出器内，fail-closed 透传）。"""
    out_dir = os.fspath(out_dir)
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, board["board_id"] + ".kicad_pcb")
    v5.kicad_export.write_kicad_pcb(board, doc, path)  # .kicad_pcb + .kicad_pro
    return {
        "kicad_pcb": path,
        "kicad_pro": os.path.splitext(path)[0] + ".kicad_pro",
        "n_routes": len(doc["routes"]),
        "board_id": board["board_id"],
    }


def export_kicad(st, out_dir):
    """实例化态 st → out_dir/<board_id>.kicad_pcb(+.kicad_pro)。

    调 canvas.instantiate.instantiate(st)（延迟加载，真接线=编排体集成
    冒烟）取 {coppers, routes, holes_norm, anchors_mm}；routes（导出行列表）
    与 st.board 一并交 v5.kicad_export。
    """
    import importlib
    try:
        module = importlib.import_module("canvas.instantiate")
    except ImportError as exc:
        raise RuntimeError(
            "instantiate 缝未接线: canvas.instantiate 未落地（K1 并行车"
            "道）——真接线=编排体集成冒烟；桩态请走 export_routes 旁路"
        ) from exc
    instantiate = getattr(module, "instantiate", None)
    if not callable(instantiate):
        raise RuntimeError(
            "instantiate 缝未接线: canvas.instantiate 无 instantiate 可调用"
            "——真接线=编排体集成冒烟")
    inst = instantiate(st)
    routes = inst["routes"]
    board = st.board
    board_sha256 = st.board_sha256
    doc = _wrap_routes_doc(board, board_sha256, routes)
    return _write_both(board, doc, out_dir)


def export_routes(board, routes, out_dir):
    """board + routes 直给旁路（合同 §1 export 节 K2 任务书钉的旁路参数）。

    routes=v5.routes.v1 文档（透传）或导出行列表（本件包装）。非法输入由
    v5.kicad_export.ExportError 原生透传（fail-closed，不落半成品）。
    """
    if not isinstance(board, dict):
        raise TypeError("board 须为 dict，实得 %s" % type(board).__name__)
    prov = board.get("provenance") or {}
    board_sha256 = prov.get("board_sha256") or compute_board_sha256(board)
    doc = _wrap_routes_doc(board, board_sha256, routes)
    return _write_both(board, doc, out_dir)
