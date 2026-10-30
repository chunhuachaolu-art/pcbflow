# -*- coding: utf-8 -*-
"""EXPORT-SEMANTICS-R1 回归（D-CT-033 修复钉）: 导出行过孔两面——
①画板 via → routes 行 transition_vias（合同 K1「via→孔 mm」routes 侧）；
②锚端到达层 ∉ 端点 pad 铜层集 → 真实端点 mm 派生端点过孔（跨层连通由
端点过孔承担——v5 世界模型）；③同层/通孔锚不派生；④悬空端不派生；
⑤v5 导出器可消费（(via) 行落盘）。"""
import copy

from v5 import board as v5board
from v5 import kicad_export

from canvas import instantiate as cin
from canvas import state as cst
from canvas.tests.test_k1_fixtures import synth_state, apply_ok


def _board_with_smd_endpoint():
    """合成板 + PB 端点 1 改单层 SMD（layers=["F.Cu"]）——异层锚情形。"""
    st0 = synth_state()
    board = copy.deepcopy(st0.board)
    for part in board["partitions"]:
        if part["partition_id"] == "PB":
            part["geometry"]["pad_terminals"][1]["layers"] = ["F.Cu"]
    prov = dict(board["provenance"])
    prov.pop("board_sha256", None)
    board["provenance"] = prov
    sha = v5board.compute_board_sha256(board)
    board["provenance"]["board_sha256"] = sha
    lat = cst.Lattice.from_board(board)
    st = cst.CanvasState(v5board.load_board(board), "<synth-k1-smd>", sha,
                         lat, cst.anchor_map(board, lat))
    st.recompute_connectivity()
    return st


def test_canvas_via_exported_into_routes_transition_vias():
    st = synth_state()
    apply_ok(st, [
        {"action": "route", "net_id": "NET-A",
         "waypoints": [[4, 4], [20, 4]], "layer": "F.Cu"},
        {"action": "via", "net_id": "NET-A", "grid": [10, 4]},
    ])
    inst = cin.instantiate(st)
    rows = [r for r in inst["routes"] if r["net_id"] == "NET-A"]
    assert len(rows) == 1
    tv = rows[0]["transition_vias"]
    assert tv == [[5.0, 2.0]]            # 格点 (10,4) → mm（pitch 0.5 原点 0）


def test_anchor_via_derived_when_layer_not_in_pad_copper():
    st = _board_with_smd_endpoint()
    # PB 锚 (4,16)-(20,16)；B.Cu 段接两端 → 端点 1（SMD F.Cu）应派生 via
    apply_ok(st, [{"action": "route", "net_id": "NET-B",
                   "waypoints": [[4, 16], [20, 16]], "layer": "B.Cu"}])
    inst = cin.instantiate(st)
    rows = [r for r in inst["routes"] if r["net_id"] == "NET-B"]
    assert len(rows) == 1
    assert rows[0]["transition_vias"] == [[10.0, 8.0]]   # 端点 1 真实端点 mm


def test_no_anchor_via_for_through_hole_or_same_layer():
    st = synth_state()                    # 全部端点 layers="all"（通孔）
    apply_ok(st, [
        {"action": "route", "net_id": "NET-A",
         "waypoints": [[4, 4], [20, 4]], "layer": "F.Cu"},
        {"action": "route", "net_id": "NET-B",
         "waypoints": [[4, 16], [20, 16]], "layer": "B.Cu"},
    ])
    inst = cin.instantiate(st)
    for row in inst["routes"]:
        assert "transition_vias" not in row

    st2 = _board_with_smd_endpoint()      # SMD F.Cu 锚 + F.Cu 段=同层不派生
    apply_ok(st2, [{"action": "route", "net_id": "NET-B",
                    "waypoints": [[4, 16], [20, 16]], "layer": "F.Cu"}])
    inst2 = cin.instantiate(st2)
    rows = [r for r in inst2["routes"] if r["net_id"] == "NET-B"]
    assert "transition_vias" not in rows[0]


def test_no_via_for_non_anchor_free_end():
    st = synth_state()
    # 段从本网 via 格点出发（badgeleds 形态：首端=via 非 pad 锚）——
    # 只导出画板 via 本体，不为 via 端点派生端点过孔
    apply_ok(st, [
        {"action": "via", "net_id": "NET-A", "grid": [8, 4]},
        {"action": "route", "net_id": "NET-A",
         "waypoints": [[8, 4], [20, 4]], "layer": "F.Cu"},
    ])
    inst = cin.instantiate(st)
    rows = [r for r in inst["routes"] if r["net_id"] == "NET-A"]
    assert len(rows) == 1
    assert rows[0]["transition_vias"] == [[4.0, 2.0]]   # 恰=画板 via，无派生


def test_routes_document_consumable_by_v5_exporter_writes_via():
    st = _board_with_smd_endpoint()
    apply_ok(st, [
        {"action": "route", "net_id": "NET-A",
         "waypoints": [[4, 4], [20, 4]], "layer": "F.Cu"},
        {"action": "route", "net_id": "NET-B",
         "waypoints": [[4, 16], [20, 16]], "layer": "B.Cu"},
        {"action": "via", "net_id": "NET-A", "grid": [12, 4]},
    ])
    doc = cin.routes_document(st)
    data = kicad_export.kicad_pcb_bytes(st.board, doc).decode("utf-8")
    vias = [l for l in data.split("\n") if l.strip().startswith("(via")]
    # 派生端点过孔（NET-B SMD 锚）+ 画板 via（NET-A (12,4)→(6.0,2.0)）
    assert len(vias) == 2
    assert any("(at 10.0 8.0)" in l and "(net 2)" in l for l in vias)
    assert any("(at 6.0 2.0)" in l and "(net 1)" in l for l in vias)
    for l in vias:
        assert '(layers "F.Cu" "B.Cu")' in l      # 全叠层通孔
