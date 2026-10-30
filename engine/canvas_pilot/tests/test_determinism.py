# -*- coding: utf-8 -*-
"""确定性双跑字节等 ≥3 例（打包/状态序列化/台账链 双跑逐字节一致）。"""
import json
import os
import sys

sys.path.insert(0, os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..")))

from v5.canonical import canonical_json
from canvas_pilot import lattice as _lat
from canvas_pilot import packer, protocol, state as _state
from canvas_pilot.conftest import micro_board


def fresh_state():
    board = micro_board()
    lat = _lat.Lattice.from_board(board, 0.5)
    st = _state.CanvasState(board, "<m>", "0" * 64, lat,
                            _lat.anchor_map(board, lat))
    st.recompute_connectivity()
    return st


def apply(st, acts, r):
    return protocol.apply_batch(
        st, protocol.parse_batch(json.dumps({"round": r, "actions": acts}), r), r)


def test_determinism_1_state_bytes():
    """同编辑序列双跑 → 状态 canonical bytes 逐字节等。"""
    acts = [
        {"action": "route", "net_id": "N1",
         "waypoints": [[1, 1], [5, 1], [5, 5], [19, 15]], "layer": "F.Cu"},
        {"action": "via", "net_id": "N1", "grid": [5, 1]},
        {"action": "submit"},
    ]
    outs = []
    for _ in range(2):
        st = fresh_state()
        apply(st, acts, 1)
        outs.append(canonical_json(st.as_dict()))
    assert outs[0] == outs[1]


def test_determinism_2_packer_bytes():
    """盲包双跑: SVG 与 facts canonical bytes 逐字节等（轮号相同输入）。"""
    states = []
    for _ in range(2):
        st = fresh_state()
        apply(st, [
            {"action": "route", "net_id": "N1",
             "waypoints": [[1, 1], [3, 1]], "layer": "F.Cu"},
            {"action": "submit"}], 1)
        states.append(st)
    svgs = [packer.pack_svg(s, 2, [{"code": "V_CLEARANCE", "grid_hint": [4, 4]}])
            for s in states]
    facts = [canonical_json(packer.pack_facts(
        s, 2, [{"code": "V_CLEARANCE", "grid_hint": [4, 4]}]))
        for s in states]
    assert svgs[0] == svgs[1]
    assert facts[0] == facts[1]


def test_determinism_3_ingest_results_bytes():
    """含拒收的混合批双跑: 逐动作结果与末态连通账本字节等。"""
    acts = [
        {"action": "route", "net_id": "N1",
         "waypoints": [[1, 1], [3, 1]], "layer": "F.Cu"},
        {"action": "route", "net_id": "N2",
         "waypoints": [[19, 1], [3, 1]], "layer": "F.Cu"},  # 贴邻 → 拒
        {"action": "via", "net_id": "N1", "grid": [2, 1]},
        {"action": "submit"},
    ]
    outs = []
    for _ in range(2):
        st = fresh_state()
        res = apply(st, acts, 1)
        outs.append(canonical_json(
            {"results": res, "conn": st.connectivity,
             "n_segs": len(st.segs), "n_vias": len(st.vias)}))
    assert outs[0] == outs[1]


def test_determinism_4_ledger_chain(tmp_path):
    """台账链双跑（同 payload 序列）→ jsonl 全文逐字节等。"""
    from canvas_pilot.ledger import Ledger
    payloads = [{"k": "round_pack", "x": 1}, {"k": "round_ingest", "x": 2},
                {"k": "round_pack", "x": 3}]
    texts = []
    for _ in range(2):
        p = tmp_path / ("ledger-%d.jsonl" % _)
        lg = Ledger(str(p))
        for pl in payloads:
            lg.append(pl["k"], pl)
        ok, n, bad = lg.verify()
        assert ok and n == 3
        texts.append(open(str(p), "rb").read())
    assert texts[0] == texts[1]
