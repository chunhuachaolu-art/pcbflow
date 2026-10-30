# -*- coding: utf-8 -*-
"""OPT-11 回归钉（pcbflow-optimap EXEC-R1；升位 0.6.0 → 0.7.0）。

两修复面的最小钉值（路线图 FINAL-ROADMAP-2026-10-08.md:179-187 验收判据）：
- D-A 空成员净类：不再裸 ValueError；mask 侧 empty_net_classes 逐字披露
  （not_available_no_members；A1/EXEC-R3 R3-2 起逐项并载源原宽 v5_width_mm）；
  .kicad_pro 只写非空类。
- D-B 板固孔四类口径：有网 TH 原孔径（oval 长轴对齐 pad 外接盒长轴）、
  有网 NPTH 落 np_thru_hole、无网 NPTH 机械孔落件、无网 plated TH 不落件、
  无 holes 键合成板回退 via_model 孔径；双跑字节等。
"""
import json
import os

import pytest

from v5.adapters.kicad_adapter import convert_bytes, convert_file_with_report
from v5.board import compute_board_sha256, load_board
from v5.kicad_export import (
    VIA_DRILL_MM,
    VERSION,
    kicad_pcb_bytes,
    netclass_mask_table,
    project_kicad_pro_bytes,
)

assert VERSION == "0.7.0"  # 本件钉随升位（A1 条件：必要测试面）

# 源板（合成，adapter 真实入模）：覆盖孔四类 + 空成员净类 + 旋转外接盒 oval。
# - module A（无旋转）：有网 TH circle（drill 0.8）+ 有网 TH oval
#   （pad 1.2×1.9、drill oval 0.6×1.3——外接盒 h>w ⇒ 钻长轴对齐 Y）；
# - module B（90° 旋转）：有网 TH oval（外接盒变 1.9×1.2 ⇒ 钻长轴对齐 X）；
# - module C：无网 NPTH（drill 3.2）⇒ 机械孔 V5-npth-1；
# - module D：无网 TH（drill 2.5）⇒ 不落件；
# - module E：有网 NPTH（drill 1.0）⇒ np_thru_hole 带网；
# - net_class：pwr 带成员 GND；hv 空成员（0.6.0 崩溃形态）。
_SOURCE = """(kicad_pcb
  (version 20171130)
  (layers (0 "F.Cu" signal) (32 "B.Cu" signal))
  (net 0 "")
  (net 1 "GND")
  (net 2 "SIG")
  (net_class "pwr" "power nets" (clearance 0.2) (trace_width 0.5)
    (add_net "GND"))
  (net_class "hv" "empty class" (clearance 1.0) (trace_width 1.0))
  (module A:FP (layer "F.Cu") (at 10 10)
    (pad 1 thru_hole circle (at 1 0) (size 2 2) (drill 0.8) (layers *.Cu) (net 1 GND))
    (pad 2 thru_hole oval (at 0 2) (size 1.2 1.9) (drill oval 0.6 1.3)
      (layers *.Cu) (net 2 SIG)))
  (module B:FP (layer "F.Cu") (at 20 10 90)
    (pad 1 thru_hole oval (at 2 0) (size 1.2 1.9) (drill oval 0.6 1.3)
      (layers *.Cu) (net 1 GND)))
  (module C:FP (layer "F.Cu") (at 30 10)
    (pad 1 np_thru_hole circle (at 0 0) (size 3.2 3.2) (drill 3.2)
      (layers *.Cu *.Mask)))
  (module D:FP (layer "F.Cu") (at 30 20)
    (pad 1 thru_hole circle (at 0 0) (size 2.5 2.5) (drill 2.5)
      (layers *.Cu *.Mask)))
  (module E:FP (layer "F.Cu") (at 5 5)
    (pad 1 np_thru_hole circle (at 0 0) (size 1.6 1.6) (drill 1.0)
      (layers *.Cu *.Mask) (net 1 GND)))
)
"""


@pytest.fixture(scope="module")
def board():
    return convert_bytes(_SOURCE.encode("utf-8"), "opt11-fixture",
                         "synthetic://opt11")


def _routes(bd):
    return {"schema_version": "v5.routes.v1", "board_id": bd["board_id"],
            "board_sha256": bd["provenance"]["board_sha256"], "routes": []}


def _text(bd):
    return kicad_pcb_bytes(bd, _routes(bd)).decode("utf-8")


# --------------------------------------------------------------- D-A 空净类

def test_empty_net_class_no_crash_and_disclosure(board):
    """hv 空成员类：export 不抛（0.6.0 裸 ValueError 回归钉）+ 双披露面。"""
    text = _text(board)                       # 不抛即 D-A 回归通过
    assert 'generator_version=%s' % VERSION in text
    doc = json.loads(project_kicad_pro_bytes(board, _routes(board)))
    names = [c["name"] for c in doc["net_settings"]["classes"]]
    assert names == ["Default", "pwr"]        # 空类不写出
    assert doc["net_settings"]["netclass_assignments"] == {"GND": ["pwr"]}
    mask = json.loads(netclass_mask_table(board, _routes(board)))
    # A1（EXEC-R3 R3-2，G1 A 口径）：空成员类披露补源原宽 v5_width_mm
    # （hv 源 trace_width=1.0）——空声明类原值随件保全，adapter 据以恢复
    # board.net_classes 空声明（members=[]，不发明成员）。
    assert mask["empty_net_classes"] == [
        {"name": "hv", "v5_clearance_mm": 1.0, "v5_width_mm": 1.0,
         "status": "not_available_no_members"}]
    assert sorted(mask["classes"]) == ["Default", "pwr"]


# --------------------------------------------------------------- D-B 板固孔

def test_netted_th_original_drill_and_oval_orientation(board):
    text = _text(board)
    # 有网 TH circle：原孔径 0.8（非 via_model 缺省 0.3）
    assert '(pad 1 thru_hole circle (at 0 0) (size 2.0 2.0) (drill 0.8) ' \
           '(layers "*.Cu") (net 1 "GND"))' in text
    # 无旋转 oval：外接盒 1.2×1.9（h>w）⇒ 钻长轴对齐 Y：(0.6 1.3)
    assert '(drill oval 0.6 1.3)' in text
    # 90° 旋转 oval：外接盒 1.9×1.2（w>h）⇒ 钻长轴对齐 X：(1.3 0.6)
    assert '(drill oval 1.3 0.6)' in text
    assert text.count("(drill oval") == 2


def test_netted_npth_and_unnetted_holes_policy(board):
    text = _text(board)
    # 有网 NPTH：np_thru_hole + 原孔径 + 网
    assert '(pad 1 np_thru_hole circle (at 0 0) (size 1.6 1.6) (drill 1.0) ' \
           '(layers "*.Cu" "*.Mask") (net 1 "GND"))' in text
    # 无网 NPTH：机械孔落件（无 net、size=钻径、无发明铜）
    assert '(module "V5-npth-1" (layer "F.Cu") (at 30.0 10.0)' in text
    assert '(pad 1 np_thru_hole circle (at 0 0) (size 3.2 3.2) (drill 3.2) ' \
           '(layers "*.Cu" "*.Mask"))' in text
    assert text.count("V5-npth-") == 1
    # 无网 plated TH：不落件（2.5 只出现在丢弃面=board.holes，不入导出件）
    assert "2.5" not in text


def test_determinism_double_run_bytes_equal(board):
    assert kicad_pcb_bytes(board, _routes(board)) == \
        kicad_pcb_bytes(board, _routes(board))
    assert project_kicad_pro_bytes(board, _routes(board)) == \
        project_kicad_pro_bytes(board, _routes(board))
    assert netclass_mask_table(board, _routes(board)) == \
        netclass_mask_table(board, _routes(board))


def test_roundtrip_reimport_holes_survive(board, tmp_path):
    """导出件 re-import：孔类别计数与孔径集合逐项可核对。"""
    pcb = tmp_path / "opt11.kicad_pcb"
    pro = tmp_path / "opt11.kicad_pro"
    data = kicad_pcb_bytes(board, _routes(board))
    pcb.write_bytes(data)
    pro.write_bytes(project_kicad_pro_bytes(board, _routes(board)))
    board2, rep2 = convert_file_with_report(str(pcb), "opt11-rt")
    holes = board2["holes"]
    assert rep2["holes_pth"] == 3 and rep2["holes_npth"] == 2
    assert sorted(round(h["drill_mm"], 9) for h in holes) == \
        [0.8, 1.0, 1.3, 1.3, 3.2]
    assert [n["net_id"] for n in board2["nets"]] == ["GND", "SIG"]


def _hand_board_no_holes():
    bd = {
        "schema_version": "v5.board.v1",
        "board_id": "hand-no-holes",
        "stackup": [
            {"id": "F.Cu", "kind": "signal", "preferred_direction": "any",
             "available": True},
            {"id": "B.Cu", "kind": "signal", "preferred_direction": "any",
             "available": True},
        ],
        "workspace": {"x_min": 0.0, "y_min": 0.0, "x_max": 40.0, "y_max": 30.0},
        "zones": [],
        "partitions": [{
            "partition_id": "PA", "ptype": "MISC",
            "geometry": {
                "endpoints": [[10.0, 10.0], [30.0, 10.0]],
                "pad_terminals": [
                    {"endpoint": 0, "shape": "circle", "size_mm": [1.5],
                     "layers": "all"},
                    {"endpoint": 1, "shape": "circle", "size_mm": [1.5],
                     "layers": "all"},
                ],
            },
            "layer_policy": "any", "width_prior": {"w_min": 0.3, "w_max": 1.0},
            "current_a": 0, "speed_class": "unknown", "note": "hand",
        }],
        "nets": [{"net_id": "NA", "partitions": ["PA"]}],
        "hard_rules": {
            "R1": {"k_a": 0.4, "floor_mm": 0.3},
            "R2": {"min_distance_mm": 3.0, "max_parallel_mm": 5.0},
            "R3": {"unsplittable": True},
            "R4": {"return_via_required": True, "max_distance_mm": 2.0},
            "R5": {"min_clearance_mm": 0.5},
            "R6": {"plane_forbidden": True, "keepout_zones_forbidden": True},
        },
        "principle_registry": [],
        "provenance": {"source_type": "synthetic", "source_uri": "synthetic://hand",
                       "source_sha256": "0" * 64, "adapter": "hand"},
    }
    bd["provenance"]["board_sha256"] = compute_board_sha256(bd)
    load_board(bd)
    return bd


def test_no_holes_key_falls_back_to_via_model_drill():
    """缺 holes 键（合成板缺省路径）：TH 回退 via_model 孔径——0.6.0 行为钉。"""
    bd = _hand_board_no_holes()
    text = kicad_pcb_bytes(bd, _routes(bd)).decode("utf-8")
    assert text.count('(drill %s)' % repr(float(VIA_DRILL_MM))) == 2
    assert "np_thru_hole" not in text and "V5-npth-" not in text


def test_holes_validation_fail_closed():
    """board.holes 非法形状/非正孔径：ExportError fail-closed（键路径）。"""
    from v5.kicad_export import ExportError
    bd = _hand_board_no_holes()
    bd["holes"] = [{"pos_mm": [1.0, 1.0], "drill_mm": 0.0, "plated": True,
                    "shape": "circle"}]
    bd["provenance"]["board_sha256"] = compute_board_sha256(bd)
    load_board(bd)
    with pytest.raises(ExportError) as ei:
        kicad_pcb_bytes(bd, _routes(bd))
    assert "board.holes[0].drill_mm" in str(ei.value)
    # oval 孔缺 size_mm（schema 不条件必带，导出消费口径 fail-closed）
    bd["holes"] = [{"pos_mm": [1.0, 1.0], "drill_mm": 0.5, "plated": True,
                    "shape": "oval"}]
    bd["provenance"]["board_sha256"] = compute_board_sha256(bd)
    load_board(bd)
    with pytest.raises(ExportError) as ei:
        kicad_pcb_bytes(bd, _routes(bd))
    assert "board.holes[0].size_mm" in str(ei.value)
