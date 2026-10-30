# -*- coding: utf-8 -*-
"""孤儿 via 批末回收（D-CT-024 对症，2026-09-25 用户裁定）回归锚。

语义: ripup 段不再即时 GC（批末统一）; 同批后续动作可显式 ripup/附着该 via。
单动作批与逐动作 replay 行为不变（apply_batch 末尾三连仍 GC）。
"""
import os
import sys

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from canvas import integration as integ          # noqa: E402
from canvas import protocol                      # noqa: E402

CRYPTO = os.path.join(ROOT, "out/v5-p5/boards/pmod-crypto/board.json")


def _fresh():
    board, sha, bpath = integ.load_wrapped_board(CRYPTO)
    return integ.make_loop_state(integ.build_state(board, bpath, sha))


def _inner(st):
    return st._st if hasattr(st, "_st") else st


def _setup_gnd_stub(inner):
    """GND 网: 段 [5,10]->[6,10] + via@[6,10]（直接 state API 构造，段唯一承载）。"""
    inner.add_seg("GND", inner.net_partitions("GND")[0], "F.Cu",
                  [[5, 10], [6, 10]], "nom")
    via = inner.add_via("GND", [6, 10])
    inner.recompute_connectivity()
    return via["shape_id"], "seg:GND:0"


def test_midbatch_orphan_via_ripup_now_accepted():
    st = _fresh()
    inner = _inner(st)
    via_sid, seg_sid = _setup_gnd_stub(inner)
    res = protocol.apply_batch(inner, [
        {"action": "ripup", "shape_id": seg_sid},
        {"action": "ripup", "shape_id": via_sid},   # 旧语义: 已被即时 GC→拒
        {"action": "submit"}], round_no=0)
    assert res[0]["accepted"] is True and res[1]["accepted"] is True, res
    assert via_sid not in inner.vias and seg_sid not in inner.segs


def test_single_action_ripup_still_sweeps_orphan():
    st = _fresh()
    inner = _inner(st)
    via_sid, seg_sid = _setup_gnd_stub(inner)
    res = protocol.apply_batch(inner, [
        {"action": "ripup", "shape_id": seg_sid}], round_no=0)
    assert res[0]["accepted"] is True
    assert via_sid not in inner.vias           # 批末三连 GC 兜底（replay 同）


def test_midbatch_route_can_attach_to_pending_via():
    st = _fresh()
    inner = _inner(st)
    via_sid, seg_sid = _setup_gnd_stub(inner)
    res = protocol.apply_batch(inner, [
        {"action": "ripup", "shape_id": seg_sid},
        {"action": "route", "net_id": "GND",
         "waypoints": [[5, 10], [6, 10]], "layer": "F.Cu"},  # 端点=本网在场 via
        {"action": "submit"}], round_no=0)
    assert res[0]["accepted"] is True, res[0]
    assert res[1]["accepted"] is True, res[1]   # 旧语义: via 已被回收→拒
    assert via_sid in inner.vias                # 新段承载，批末 GC 不清
