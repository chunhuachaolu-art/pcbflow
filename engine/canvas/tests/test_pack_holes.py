# -*- coding: utf-8 -*-
"""板固孔席位投影回归锚（D-CT-016 修复，2026-09-25 用户裁定采纳）。

面:
- 三实板 holes 计数+格点往返一致（snap 同源）+确定性（facts_json 双跑字节等）；
- state_facts 本体纯度（无 holes 键=链式台账锚面不动）；
- pack_view 副本不改 state_facts 返回对象（防原地污染）；
- 空孔板（holes 缺省）→ facts["holes"] == []。
"""
import json
import os
import sys

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from canvas import integration as integ          # noqa: E402
from canvas import pack as cpk                   # noqa: E402
from canvas.state import state_facts             # noqa: E402

BOARDS = {
    "badgeleds-do-electronics":
        ("out/v5-p5/boards-pre-r1/badgeleds-do-electronics/board.json", 28),
    "pmod-bme280":
        ("out/v5-p5/boards-pre-r1/pmod-bme280/board.json", 33),
    "pmod-crypto":
        ("out/v5-p5/boards-pre-r1/pmod-crypto/board.json", 31)
}


def _st_of(bid):
    board, sha, bpath = integ.load_wrapped_board(
        os.path.join(ROOT, BOARDS[bid][0]))
    return integ.make_loop_state(integ.build_state(board, bpath, sha))


def _inner(st):
    return st._st if hasattr(st, "_st") else st


@pytest.mark.parametrize("bid", sorted(BOARDS))
def test_holes_count_and_roundtrip(bid):
    st = _st_of(bid)                        # LoopStateProxy（pack_view 合同面）
    pv = cpk.pack_view(st)
    facts = json.loads(pv["facts_json"])
    holes = facts["holes"]
    assert len(holes) == BOARDS[bid][1]
    lat = _inner(st).lattice
    for h in holes:
        i, j = lat.snap(h["mm"][0], h["mm"][1])
        assert [i, j] == h["grid"]                       # snap 同源往返
        mx, my = lat.to_mm(i, j)
        assert abs(mx - h["mm"][0]) <= lat.pitch / 2 + 1e-9
        assert abs(my - h["mm"][1]) <= lat.pitch / 2 + 1e-9
        assert h["r_mm"] > 0.0


@pytest.mark.parametrize("bid", sorted(BOARDS))
def test_facts_json_deterministic(bid):
    st = _st_of(bid)
    assert cpk.pack_view(st)["facts_json"] == cpk.pack_view(st)["facts_json"]


@pytest.mark.parametrize("bid", sorted(BOARDS))
def test_state_facts_purity(bid):
    st = _st_of(bid)
    cpk.pack_view(st)                                    # 先跑一次投影
    assert "holes" not in state_facts(_inner(st))        # 链哈希面不动


def test_pack_view_does_not_mutate_state_facts_dict():
    st = _st_of("pmod-bme280")
    before = state_facts(_inner(st))
    cpk.pack_view(st)
    assert state_facts(_inner(st)) == before             # 副本语义


def test_holes_without_lattice_fail_closed():
    """板含孔而 state 无格点阵 → AttributeError（fail-closed，防静默漏投影）。"""
    class _NoLattice(object):
        board = {"holes": [{"pos_mm": [1.0, 1.0], "drill_mm": 0.6}]}
    with pytest.raises(AttributeError):
        cpk._hole_facts(_NoLattice())


def test_no_holes_board_yields_empty_list():
    src = os.path.join(ROOT, BOARDS["badgeleds-do-electronics"][0])
    board, sha, bpath = integ.load_wrapped_board(src)
    raw = json.load(open(src, encoding="utf-8"))
    holeless = dict(raw["board"])
    holeless["holes"] = []
    tmp = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "_tmp_holeless_board.json")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"board": holeless,
                   "provenance": raw.get("provenance", {})}, f)
    try:
        b2, sha2, p2 = integ.load_wrapped_board(tmp)
        st = integ.make_loop_state(integ.build_state(b2, p2, sha2))
        pv = cpk.pack_view(st)
        assert json.loads(pv["facts_json"])["holes"] == []
    finally:
        os.remove(tmp)
