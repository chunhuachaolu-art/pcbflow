# -*- coding: utf-8 -*-
"""无模型端到端冒烟 1 例: 合成微板脚本驱动全链
init → new-round → （脚本代批=协议合法的完整布线）→ ingest → 全连通
→ export（v5.routes.v1 复核 + kicad_pcb 字节导出）→ 状态/盲包落盘形态。"""
import json
import os
import sys

sys.path.insert(0, os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..")))

from v5.route_check import validate_routes
from v5.kicad_export import kicad_pcb_bytes
from canvas_pilot import lattice as _lat
from canvas_pilot import loop, packer, protocol, state as _state, verify
from canvas_pilot.conftest import micro_board
from canvas_pilot.ledger import Ledger


def test_smoke_end_to_end(tmp_path, monkeypatch):
    # ---- init: 微板画板状态（隔离: OUT 重定向到 tmp, 不触真实产物域）
    from v5 import board as v5board
    board = micro_board()
    # load_board 同款落链: generator 键入哈希视图、board_sha256 键被剥
    board["provenance"] = {"generator": "canvas-pilot-test",
                           "generator_version": "0.1.0"}
    sha = v5board.compute_board_sha256(board)
    board["provenance"]["board_sha256"] = sha
    assert v5board.compute_board_sha256(board) == sha
    lat = _lat.Lattice.from_board(board, 0.5)
    st = _state.CanvasState(board, "<smoke>", sha, lat,
                            _lat.anchor_map(board, lat))
    st.recompute_connectivity()
    assert st.routed_nets() == 0

    # ---- round 1: 盲包（facts 禁项自检内嵌于 pack_facts）
    facts = packer.pack_facts(st, 1, [])
    assert facts["unrouted_nets"] == ["N1", "N2"]
    svg = packer.pack_svg(st, 1, [])
    assert 'data-role="lattice"' in svg

    # ---- 脚本代批: 两网各走自带上/下行带; N1 经 via 跨层链（覆盖段-via-段
    # 衔接、批内累积视图、链审计全连通）
    acts = [
        {"action": "route", "net_id": "N1",
         "waypoints": [[1, 1], [10, 1]], "layer": "F.Cu"},
        {"action": "via", "net_id": "N1", "grid": [10, 1]},
        {"action": "route", "net_id": "N1",
         "waypoints": [[10, 1], [19, 1]], "layer": "B.Cu"},
        {"action": "route", "net_id": "N2",
         "waypoints": [[1, 15], [19, 15]], "layer": "F.Cu"},
        {"action": "submit"},
    ]
    res = protocol.apply_batch(
        st, protocol.parse_batch(json.dumps({"round": 1, "actions": acts}), 1), 1)
    assert all(r["accepted"] for r in res[:4]), res
    st.recompute_connectivity()
    assert st.routed_nets() == 2

    # ---- 状态不变量: 落铜后 DRC 全量干净
    assert verify.full_check(st) == []

    # ---- export: v5.routes.v1 同源复核 + kicad_pcb 字节
    doc = loop.build_routes_doc(st)
    assert validate_routes(st.board, doc) is True
    pcb = kicad_pcb_bytes(st.board, doc)
    assert pcb.startswith(b"(kicad_pcb") and len(pcb) > 1000

    # ---- 真实 runner 链（tmp 域 ledger）
    lg = Ledger(str(tmp_path / "ledger.jsonl"))
    lg.append("smoke_pack", {"round": 1})
    lg.append("smoke_ingest", {"accepted": 2})
    ok, n, bad = lg.verify()
    assert ok and n == 2
