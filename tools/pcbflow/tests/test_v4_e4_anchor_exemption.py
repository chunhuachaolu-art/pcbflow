"""tests/test_v4_e4_anchor_exemption -- V4-E4 W-2 护栏：起点锚定区豁免合同测试。

依据：exec/V4-E4-REALBOARD-ROUTABILITY-TASKBOOK-2026-09-24.md §3 W-2 +
预注册 out/v4-e4-r1/prereg-e4-r1.md §2（sha256 见 prep-record-e4-r1.json）。

四门：
  ① 缺省等价——合成板 ≥3 块（既有语料）无键/显式 False 双跑 byte-exact，
     且无键输出 sha256 与改动前口径钉值（prereg §7 D-0）逐位相等；
  ② 豁免钉值——邻网 pad margin 覆盖起点场景，False 起点格 ∈ blocked、
     True ∉ blocked；solve 级 False 首网零展开、True 有走线；
  ③ 他网视角钉值——nid 的豁默不改变他网 nid' 的 static_blocked_for_net；
  ④ docstring 合同出现断言（grid.static_blocked_for_net / router.solve_board）。
"""

from __future__ import annotations

import hashlib
import json
import os

import pytest

from pcbflow.v4exp import router
from pcbflow.v4exp.grid import GridWorld

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_CMP = os.path.join(_ROOT, "out", "v4-comparative-experiment")

# prereg §7 D-0：改动前（router 5518b78e/grid 5aaf759e 口径）solve_board 输出
# sha256 钉值，request={"route_order": 字典序, "group": "A0"}。
_PRECHANGE_DIGESTS = {
    "dev-f1-01": "641a6f0073d7e7d6c9323e767032ba05c8c96d2d181de29e25e74779821a6c0d",
    "hol-f6-02": "95b9ec5f136377aa79412bce436a8d21ee452a1aad32041b5a4d809c47899d8d",
    "cal-f5-13": "90729116e23bbc9437034b8cd562e0cb525733a0afc116480ed0fe39ba99ddfa",
}


def _board(sid):
    with open(os.path.join(_CMP, "board-snapshot-%s.json" % sid),
              encoding="utf-8") as f:
        return json.load(f)


def _order(board):
    return sorted(str(n["net_id"]) for n in board["nets"])


def _run_bytes(board, request):
    return router.canonical_json(router.solve_board(board, request)).encode("utf-8")


# ---- ① 缺省等价（含改动前口径钉值） ------------------------------------

@pytest.mark.parametrize("sid", sorted(_PRECHANGE_DIGESTS))
def test_default_run_matches_prechange_digest(sid):
    """开关缺省（无键）输出 sha256 与 V4-E4 改动前口径逐位相等（字节零漂移）。"""
    board = _board(sid)
    got = hashlib.sha256(_run_bytes(board, {"route_order": _order(board),
                                            "group": "A0"})).hexdigest()
    assert got == _PRECHANGE_DIGESTS[sid]


@pytest.mark.parametrize("sid", sorted(_PRECHANGE_DIGESTS))
def test_explicit_false_equals_absent_key(sid):
    """显式 anchor_exemption=False 与无键双跑 byte-exact。"""
    board = _board(sid)
    base = {"route_order": _order(board), "group": "A0"}
    absent = _run_bytes(board, dict(base))
    false = _run_bytes(board, dict(base, anchor_exemption=False))
    assert false == absent


# ---- 单元板（邻网 margin 覆盖起点场景） ----------------------------------

def unit_board():
    """2 层 2 网：n2 的 pad pC（0.5×0.5 @ (2.6, 2.0)）margin 增长矩形
    （clearance 0.25 + width 0.25/2 = 0.375 → 覆盖 [1.975, 3.225]×[1.375,
    2.625]）盖住 n1 起点 pad pA 中心格 (2.0, 2.0)；pA 本体 3×3 格
    [1.75..2.25]²。其余空间空旷（n1 True 可走通、False 起点即死）。"""
    return {
        "schema": "pcbflow.v4exp.board/1",
        "scenario_id": "e4-unit-anchor",
        "split": "unit", "family": "e4", "seed": 0,
        "board": {"bbox_mm": [0, 0, 10, 10], "layers": ["F.Cu", "B.Cu"]},
        "rules": {"grid_mm": 0.25, "clearance_mm": 0.25,
                  "width_mm": {"default": 0.25},
                  "via": {"pad_mm": 0.6, "hole_mm": 0.3},
                  "allowed_layers": {"default": ["F.Cu", "B.Cu"]}},
        "pads": [
            {"pad_id": "pA", "net_id": "n1", "x_mm": 2.0, "y_mm": 2.0,
             "w_mm": 0.5, "h_mm": 0.5, "layer": "F.Cu"},
            {"pad_id": "pB", "net_id": "n1", "x_mm": 8.0, "y_mm": 8.0,
             "w_mm": 0.5, "h_mm": 0.5, "layer": "F.Cu"},
            {"pad_id": "pC", "net_id": "n2", "x_mm": 2.6, "y_mm": 2.0,
             "w_mm": 0.5, "h_mm": 0.5, "layer": "F.Cu"},
            {"pad_id": "pD", "net_id": "n2", "x_mm": 8.0, "y_mm": 2.0,
             "w_mm": 0.5, "h_mm": 0.5, "layer": "F.Cu"},
        ],
        "nets": [
            {"net_id": "n1", "net_class": "default", "endpoints": ["pA", "pB"]},
            {"net_id": "n2", "net_class": "default", "endpoints": ["pC", "pD"]},
        ],
        "keepouts": [], "relations": [], "label": "e4-unit",
    }


def test_start_cell_blocked_without_exemption():
    """②开关 False：n1 起点格 ∈ static_blocked_for_net(n1)[F.Cu]。"""
    world = GridWorld(unit_board(), anchor_exemption=False)
    start = (world.cell_x(2.0), world.cell_y(2.0))
    assert start in world.static_blocked_for_net("n1")[world.layer_index["F.Cu"]]


def test_start_cell_freed_with_exemption():
    """②开关 True：n1 起点格 ∉ blocked（pA 本体 3×3 差集生效）。"""
    world = GridWorld(unit_board(), anchor_exemption=True)
    start = (world.cell_x(2.0), world.cell_y(2.0))
    assert start not in world.static_blocked_for_net("n1")[world.layer_index["F.Cu"]]
    # pA 本体全部 9 格解锁（margin=0 锚区=pad 矩形本体，不外扩）
    body = world.cells_in_rect(world.pad_rect(world.pad_by_id["pA"]), 0)
    freed = body - world.static_blocked_for_net("n1")[world.layer_index["F.Cu"]]
    assert len(body) == 9 and freed == body


def test_solve_false_zero_expansion_true_routes():
    """②solve 级：False 首网 _astar 起点即死（sn=0、failed@n1）；
    True 首网非零展开且全网走通（空旷板可 SAT）。"""
    board = unit_board()
    off = router.solve_board(board, {"route_order": ["n1", "n2"], "group": "A"})
    assert off["status"] == "failed" and off.get("failed_at") == "n1"
    assert off["metrics"]["search_nodes"] == 0 and off["routes"] == []
    on = router.solve_board(board, {"route_order": ["n1", "n2"], "group": "A",
                                    "anchor_exemption": True})
    assert on["metrics"]["search_nodes"] > 0
    assert len(on["routes"]) >= 2 and on["status"] == "sat"


def test_exemption_truthy_normalized():
    """request 真值经 bool() 归一：anchor_exemption=1 与 True 输出 byte-exact。"""
    board = unit_board()
    base = {"route_order": ["n1", "n2"], "group": "A"}
    assert (_run_bytes(board, dict(base, anchor_exemption=1))
            == _run_bytes(board, dict(base, anchor_exemption=True)))


def test_other_net_view_unchanged():
    """③他网视角：nid 的 pad 对他网 blocked 不因开关变化。开关 True 下
    视角网 view(nid) 与 False 的唯一合法差异 = nid 自身 pad 本体差集
    （nid 自己的豁免，per-net 视角）；n1 的 pA 对 n2 仍按 margin 阻挡。"""
    b_off = GridWorld(unit_board(), anchor_exemption=False)
    b_on = GridWorld(unit_board(), anchor_exemption=True)
    own_body = {
        "n1": {c for p in ("pA", "pB")
               for c in b_off.cells_in_rect(b_off.pad_rect(b_off.pad_by_id[p]), 0)},
        "n2": {c for p in ("pC", "pD")
               for c in b_off.cells_in_rect(b_off.pad_rect(b_off.pad_by_id[p]), 0)},
    }
    for nid in ("n1", "n2"):
        off = b_off.static_blocked_for_net(nid)
        on = b_on.static_blocked_for_net(nid)
        assert set(off) == set(on)
        for li in off:
            # 唯一合法差异 = 视角网自己的 pad 本体（其自身豁免）
            assert off[li] - on[li] <= own_body[nid]
    # n1 的 pA 中心格在 n2 视角下仍被阻挡（他网不因开关解封）
    fcu = b_on.layer_index["F.Cu"]
    assert (b_on.cell_x(2.0), b_on.cell_y(2.0)) in b_on.static_blocked_for_net("n2")[fcu]


# ---- ④ docstring 合同出现断言 ---------------------------------------------

def test_docstring_contract_visible():
    assert "anchor_exemption" in GridWorld.static_blocked_for_net.__doc__
    assert "anchor_exemption" in router.solve_board.__doc__
