"""pcbflow.v4_1 预检器/checker 单元测试（保守带、跨层、custom 保守、
patch 候选链、fail-closed）。"""

from __future__ import annotations

from pathlib import Path

import pytest

from pcbflow.v4_1.board_parse import parse_board_text
from pcbflow.v4_1.board_parse_alt import parse_board_text_alt
from pcbflow.v4_1.checker import (CheckerBlocked,
                                  IndependentGeometryChecker,
                                  build_check_items)
from pcbflow.v4_1.netclasses import NetClass, NetClassTable
from pcbflow.v4_1.precheck import (AdvisoryPrecheckV41, PrecheckBlocked,
                                   build_geom_items, patch_final_segments)

REPO = Path(__file__).resolve().parent.parent


def _table(clear=0.2):
    return NetClassTable({"Default": NetClass("Default", clear, 0.15)},
                         {}, [], "declared_defaults:test")


BOARD = """(kicad_pcb (version 20260206)
  (layers (0 "F.Cu" signal) (1 "In1.Cu" signal) (31 "B.Cu" signal))
  (footprint "F1" (layer "F.Cu") (at 10 10)
    (property "Reference" "U1" (at 0 0) (layer "F.SilkS"))
    (pad "1" smd roundrect (at 0 0) (size 1.5 0.3)
      (layers "F.Cu" "F.Mask") (roundrect_rratio 0.25) (net "NET_P")
      (uuid "pad-00000000-0000-0000-0000-000000000001"))
    (pad "2" thru_hole circle (at 5 0) (size 0.9 0.9) (drill 0.4)
      (layers "*.Cu" "*.Mask") (net "NET_TH")
      (uuid "pad-00000000-0000-0000-0000-000000000002"))
    (pad "3" smd custom (at -5 0) (size 0.87 2.79)
      (layers "F.Cu") (net "NET_CUST")
      (uuid "pad-00000000-0000-0000-0000-000000000003")
      (primitives (gr_poly (pts (xy 0.435 -1.395) (xy 0.435 1.395)
        (xy -0.125 1.945) (xy -1.015 1.945) (xy -1.015 -1.945)
        (xy -0.125 -1.945)) (width 0) (fill yes))))
  )
  (segment (start 20 20) (end 30 20) (width 0.15) (layer "F.Cu")
    (net "NET_S") (uuid "seg-00000000-0000-0000-0000-000000000001"))
)
"""


@pytest.fixture(scope="module")
def engines():
    a = parse_board_text(BOARD)
    b = parse_board_text_alt(BOARD)
    table = _table()
    return (AdvisoryPrecheckV41(build_geom_items(a), table),
            IndependentGeometryChecker(build_check_items(b), table),
            a, b)


def test_hard_violation_and_legal(engines):
    pre, chk, _, _ = engines
    # 硬违例：走线压向 roundrect 1.5x0.3 @ (10,10)，expected 0.095
    r1 = pre.check_segment("NET_T", "F.Cu", 0.15, 9.5, 10.32, 10.5, 10.32)
    assert r1["verdict"] == "violation"
    assert r1["violations"][0]["flag_class"] == "hard_violation"
    assert r1["violations"][0]["pred_clearance_mm"] == pytest.approx(0.095)
    # 合法侧：0.45-0.15-0.075 = 0.225
    r2 = pre.check_segment("NET_T", "F.Cu", 0.15, 9.5, 10.45, 10.5, 10.45)
    assert r2["verdict"] == "clean"
    assert r2["min_foreign_clearance_mm"] == pytest.approx(0.225)
    # checker 同判
    c1 = chk.check_segment("NET_T", "F.Cu", 0.15, 9.5, 10.32, 10.5, 10.32)
    assert c1["verdict"] == "violation"
    c2 = chk.check_segment("NET_T", "F.Cu", 0.15, 9.5, 10.45, 10.5, 10.45)
    assert c2["verdict"] == "clean"


def test_conservative_band_flagging(engines):
    """expected=0.205（[0.2,0.21) 带内）-> 判违例=保守带行为（登记 FP）。"""
    pre, chk, _, _ = engines
    # y=10.43 -> 0.43-0.15-0.075 = 0.205
    r = pre.check_segment("NET_T", "F.Cu", 0.15, 9.5, 10.43, 10.5, 10.43)
    assert r["verdict"] == "violation"
    assert r["violations"][0]["flag_class"] == "conservative_band"
    assert r["violations"][0]["pred_clearance_mm"] == pytest.approx(0.205)
    c = chk.check_segment("NET_T", "F.Cu", 0.15, 9.5, 10.43, 10.5, 10.43)
    assert c["verdict"] == "violation"


def test_tht_pad_obstacle_on_inner_layer(engines):
    """THT pad（*.Cu）在 In1.Cu 亦为障碍（P3 近似漏报源的修复验证）。"""
    pre, chk, _, _ = engines
    # THT pad @(15,10) d=0.9；In1.Cu 走线 expected = 0.62-0.45-0.075 = 0.095
    r = pre.check_segment("NET_T", "In1.Cu", 0.15, 13.5, 10.62, 16.5, 10.62)
    assert r["verdict"] == "violation"
    hit = [v for v in r["violations"] if v["item_ref"].endswith("U1.2")]
    assert hit and hit[0]["pred_clearance_mm"] == pytest.approx(0.095)
    c = chk.check_segment("NET_T", "In1.Cu", 0.15, 13.5, 10.62, 16.5, 10.62)
    assert c["verdict"] == "violation"


def test_custom_pad_conservative_bbox(engines):
    """custom 基元（backlog）：顶点包围盒超集 + 显式登记。"""
    pre, chk, _, _ = engines
    # custom pad @(5,10) 基元 y 跨 [-1.945,1.945] -> 板 y 跨 [8.055,11.945]
    # 走线 y=12.1：bbox 距 = 12.1-11.945-hw = 0.08 违例（保守超集）
    r = pre.check_segment("NET_T", "F.Cu", 0.15, 3.5, 12.1, 6.5, 12.1)
    assert r["verdict"] == "violation"
    hit = [v for v in r["violations"] if v["item_ref"].endswith("U1.3")]
    assert hit
    assert hit[0]["conservative_approximation"] is not None
    assert "custom" in hit[0]["conservative_approximation"]
    c = chk.check_segment("NET_T", "F.Cu", 0.15, 3.5, 12.1, 6.5, 12.1)
    assert c["verdict"] == "violation"


def test_same_net_and_protected_exemption(engines):
    pre, _, _, _ = engines
    # 同网：candidate NET_S 走向自身既有段 —— 无约束
    r = pre.check_segment("NET_S", "F.Cu", 0.15, 20, 20.05, 30, 20.05)
    assert r["verdict"] == "clean"
    # protected 网豁免（批内互不约束，批 DRC 兜底口径）
    pre2 = AdvisoryPrecheckV41(build_geom_items(parse_board_text(BOARD)),
                               _table(), protected_nets=["NET_P"])
    r2 = pre2.check_segment("NET_T", "F.Cu", 0.15, 9.5, 10.32, 10.5, 10.32)
    assert r2["verdict"] == "clean"


def test_candidate_validation_fail_closed(engines):
    pre, chk, _, _ = engines
    with pytest.raises(PrecheckBlocked):
        pre.check_segment("NET_T", "F.Cu", 0.0, 0, 0, 1, 0)
    with pytest.raises(PrecheckBlocked):
        pre.check_segment("NET_T", "F.Cu", 0.15, float("nan"), 0, 1, 0)
    with pytest.raises(PrecheckBlocked):
        AdvisoryPrecheckV41([], None)  # net class 表缺失 = fail-closed
    with pytest.raises(CheckerBlocked):
        IndependentGeometryChecker([], None)
    with pytest.raises(CheckerBlocked):
        chk.check_segment("NET_T", "F.Cu", -0.2, 0, 0, 1, 0)
    with pytest.raises(CheckerBlocked):
        chk.check_segment("NET_T", "F.Cu", 0.15, float("inf"), 0, 1, 0)


def test_patch_final_segments_and_check_patch():
    a = parse_board_text(BOARD)
    pre = AdvisoryPrecheckV41(build_geom_items(a), _table())
    seg_uuid = "seg-00000000-0000-0000-0000-000000000001"
    patch = {
        "patch_id": "P#TEST#ch#k1", "net_id": "NET_T",
        "text_ops": {
            "insert_segment": {"net": "NET_T", "layer": "F.Cu",
                               "width": 0.15, "start": [9.5, 10.32],
                               "end": [10.5, 10.32]},
            "modify": [{"uuid": seg_uuid, "replace_coord": [20, 20],
                        "new_coord": [9.5, 10.32]}],
        },
    }
    segs = patch_final_segments(a, patch)
    assert len(segs) == 2
    assert segs[0]["x1"] == 9.5 and segs[0]["y1"] == 10.32
    r = pre.check_patch(a, patch)
    assert r["verdict"] == "violation"       # 倒角段硬违例（G1.1 同构）
    assert r["per_segment"][0]["uuid"] == seg_uuid
    # 未知 uuid -> blocked
    bad = {"patch_id": "X", "net_id": "NET_T",
           "text_ops": {"modify": [{"uuid": "ghost", "replace_coord": [0, 0],
                                    "new_coord": [1, 1]}],
                        "insert_segment": None}}
    with pytest.raises(PrecheckBlocked):
        patch_final_segments(a, bad)
    # 端点不匹配 -> blocked
    bad2 = {"patch_id": "X", "net_id": "NET_T",
            "text_ops": {"modify": [{"uuid": seg_uuid,
                                     "replace_coord": [7, 7],
                                     "new_coord": [1, 1]}],
                         "insert_segment": None}}
    with pytest.raises(PrecheckBlocked):
        patch_final_segments(a, bad2)
    # 空 patch -> blocked
    with pytest.raises(PrecheckBlocked):
        patch_final_segments(a, {"patch_id": "E", "text_ops": {}})


def test_move_vertex_patch_shape():
    a = parse_board_text(BOARD)
    pre = AdvisoryPrecheckV41(build_geom_items(a), _table())
    seg_uuid = "seg-00000000-0000-0000-0000-000000000001"
    patch = {"patch_id": "P#TEST#mv", "net_id": "NET_S",
             "text_ops": {"modify": [
                 {"uuid": seg_uuid, "replace_coord": [20, 20],
                  "new_coord": [21, 21]}],
                 "insert_segment": None}}
    r = pre.check_patch(a, patch)
    assert r["verdict"] == "clean"
    assert r["per_segment"][0]["verdict"] == "clean"
