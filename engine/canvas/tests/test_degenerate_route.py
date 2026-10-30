# -*- coding: utf-8 -*-
"""同锚重合退化网零长 route 合法化回归锚（D-CT-022 协议原语补位，
2026-09-25 用户裁定）。

面:
- 退化网（网内全部分区端点锚同格）零长 route [[P],[P]] 与单点 [[P]] 均接受、
  连通翻 True、落段形态 [P,P]；
- 正常网零长 route 照拒 V_SELF_SNAG（豁免不外溢）；
- 退化网零长但落点非锚照拒；
- 确定性（双建双施加 state_sha256 相等）。
"""
import os
import sys

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from canvas import integration as integ          # noqa: E402
from canvas import protocol                      # noqa: E402
from canvas.state import state_sha256            # noqa: E402

CRYPTO = os.path.join(ROOT, "out/v5-p5/boards/pmod-crypto/board.json")
DEGEN_NET = "unconnected-(U1-Pad1)"     # 双锚同格 [30,3]
DEGEN_PT = [30, 3]
NORMAL_NET = "GND"                      # 正常双锚网


def _fresh():
    board, sha, bpath = integ.load_wrapped_board(CRYPTO)
    st = integ.make_loop_state(integ.build_state(board, bpath, sha))
    return st


def _inner(st):
    return st._st if hasattr(st, "_st") else st


@pytest.mark.parametrize("waypoints", [[[30, 3], [30, 3]], [[30, 3]]])
def test_degenerate_zero_length_accepted(waypoints):
    st = _fresh()
    assert _inner(st).connectivity[DEGEN_NET] is False
    res = protocol.apply_batch(_inner(st), [
        {"action": "route", "net_id": DEGEN_NET,
         "waypoints": waypoints, "layer": "F.Cu"},
        {"action": "submit"}], round_no=0)
    assert res[0]["accepted"] is True, res[0]
    assert _inner(st).connectivity[DEGEN_NET] is True
    segs = _inner(st).segs
    assert len(segs) == 1
    seg = list(segs.values())[0]
    assert [list(p) for p in seg["grid"]] == [DEGEN_PT, DEGEN_PT]


def test_normal_net_zero_length_still_rejected():
    st = _fresh()
    anchors = list(_inner(st).effective_anchors(
        _inner(st).net_partitions(NORMAL_NET)[0]))
    p = list(anchors[0])
    res = protocol.apply_batch(_inner(st), [
        {"action": "route", "net_id": NORMAL_NET,
         "waypoints": [p, p], "layer": "F.Cu"},
        {"action": "submit"}], round_no=0)
    assert res[0]["accepted"] is False
    assert res[0]["code"] == "V_SELF_SNAG"


def test_degenerate_net_off_anchor_rejected():
    st = _fresh()
    q = [DEGEN_PT[0] + 1, DEGEN_PT[1]]
    res = protocol.apply_batch(_inner(st), [
        {"action": "route", "net_id": DEGEN_NET,
         "waypoints": [q, q], "layer": "F.Cu"},
        {"action": "submit"}], round_no=0)
    assert res[0]["accepted"] is False
    assert res[0]["code"] == "V_SELF_SNAG"


def test_deterministic_double_apply():
    shas = []
    for _ in range(2):
        st = _fresh()
        protocol.apply_batch(_inner(st), [
            {"action": "route", "net_id": DEGEN_NET,
             "waypoints": [[30, 3], [30, 3]], "layer": "F.Cu"},
            {"action": "submit"}], round_no=0)
        shas.append(state_sha256(_inner(st)))
    assert shas[0] == shas[1]
