"""pcbflow.v4_1 解析路径 A/B 单元测试 + 交叉对拍 + 负向 fail-closed。"""

from __future__ import annotations

from pathlib import Path

import pytest

from pcbflow.v4_1.board_parse import BoardParseError, parse_board_text
from pcbflow.v4_1.board_parse_alt import (BoardParseAltError,
                                          parse_board_text_alt)

REPO = Path(__file__).resolve().parent.parent
SNAPSHOT = REPO / "out/v4-exec/p3-revc/per-net-batch/snapshot-pristine.kicad_pcb"

MINI_BOARD = """(kicad_pcb (version 20260206)
  (layers (0 "F.Cu" signal) (1 "In1.Cu" signal) (31 "B.Cu" signal))
  (footprint "SOIC-8" (layer "F.Cu") (at 10 20 90)
    (property "Reference" "U9" (at 0 0) (layer "F.SilkS"))
    (pad "1" smd rect (at -1.9 0.75 90) (size 0.6 1.7)
      (layers "F.Cu" "F.Mask" "F.Paste") (net "NET_A")
      (uuid "u1-00000000-0000-0000-0000-000000000001"))
    (pad "2" smd roundrect (at 1.9 0.75) (size 0.6 1.7)
      (layers "F.Cu" "F.Mask") (roundrect_rratio 0.25) (net "NET_B")
      (uuid "u1-00000000-0000-0000-0000-000000000002"))
    (pad "3" thru_hole circle (at 0 0) (size 0.9 0.9) (drill 0.4)
      (layers "*.Cu" "*.Mask") (net "NET_C")
      (uuid "u1-00000000-0000-0000-0000-000000000003"))
    (pad "4" smd oval (at 0 -1.5 270) (size 1.2 0.5)
      (layers "F.Cu") (net "NET_D")
      (uuid "u1-00000000-0000-0000-0000-000000000004"))
  )
  (segment (start 1 1) (end 2 2) (width 0.2) (layer "F.Cu") (net "NET_A")
    (uuid "s1-00000000-0000-0000-0000-000000000001"))
  (via (at 3 3) (size 0.6) (drill 0.3) (layers "F.Cu" "B.Cu") (net "NET_A")
    (uuid "v1-00000000-0000-0000-0000-000000000001"))
)
"""


@pytest.fixture(scope="module")
def mini_a():
    return parse_board_text(MINI_BOARD)


@pytest.fixture(scope="module")
def mini_b():
    return parse_board_text_alt(MINI_BOARD)


# ---------------------------------------------------------------- 正向

def test_mini_board_shapes_and_layers(mini_a):
    pads = {p["pad_id"]: p for p in mini_a["pads"]}
    assert set(pads) == {"U9.1", "U9.2", "U9.3", "U9.4"}
    assert pads["U9.1"]["shape"] == "rect"
    assert pads["U9.2"]["corner_radius_mm"] == pytest.approx(0.15)  # 0.25*0.6
    assert pads["U9.3"]["layers"] == ["B.Cu", "F.Cu", "In1.Cu"]     # *.Cu
    assert pads["U9.4"]["shape"] == "oval"
    # 总旋转 = footprint 90 + pad 相对 90 = 180（pad1）；pad2 = 90+0 = 90
    assert pads["U9.1"]["rotation_deg"] == 180.0
    assert pads["U9.2"]["rotation_deg"] == 90.0
    # 焊盘中心：局部 (1.9, 0.75) 经 footprint 90° 旋转（x'=y, y'=-x）
    # -> 板坐标 (10+0.75, 20-1.9) = (10.75, 18.1)
    assert pads["U9.2"]["x_mm"] == pytest.approx(10.75)
    assert pads["U9.2"]["y_mm"] == pytest.approx(18.1)


def test_mini_board_cross_parse_agreement(mini_a, mini_b):
    assert mini_a["copper_layers"] == mini_b["copper_layers"]
    assert mini_a["segments"] == mini_b["segments"]
    assert mini_a["vias"] == mini_b["vias"]
    assert mini_a["pads"] == mini_b["pads"]
    assert mini_a["stats"] == mini_b["stats"]


@pytest.mark.skipif(not SNAPSHOT.is_file(), reason="Rev-C snapshot absent")
def test_real_snapshot_cross_parse_agreement():
    text = SNAPSHOT.read_text(encoding="utf-8")
    a = parse_board_text(text)
    b = parse_board_text_alt(text)
    assert a["stats"] == b["stats"]
    assert a["stats"]["segment_count"] == 2372
    assert a["stats"]["via_count"] == 358
    assert a["stats"]["pad_count"] == 564
    assert a["segments"] == b["segments"]
    assert a["vias"] == b["vias"]
    assert a["pads"] == b["pads"]
    # custom 基元显式登记（2 个电感焊盘，非静默）
    assert a["unsupported_items"] == b["unsupported_items"]
    assert {u["pad_id"] for u in a["unsupported_items"]} == {"L1.1", "L1.2"}
    assert all(u["primitive_pt_count"] == 10
               for u in a["unsupported_items"])
    # U1.109 锚（G1.1 证据）
    u1109 = {p["pad_id"]: p for p in a["pads"]}["U1.109"]
    assert u1109["shape"] == "roundrect"
    assert (u1109["x_mm"], u1109["y_mm"]) == (47.675, 23.65)
    assert u1109["corner_radius_mm"] == pytest.approx(0.075)
    assert u1109["net_id"] == "FMC_BA1"


@pytest.mark.skipif(not SNAPSHOT.is_file(), reason="Rev-C snapshot absent")
def test_real_snapshot_ratio_full_precision_allowed():
    """roundrect_rratio 全精度（>6 位小数）合法——无量纲比率非 mm 坐标。"""
    text = SNAPSHOT.read_text(encoding="utf-8").replace(
        "(roundrect_rratio 0.25)", "(roundrect_rratio 0.1923076923)", 1)
    a = parse_board_text(text)
    b = parse_board_text_alt(text)
    assert any(p["corner_radius_mm"] == pytest.approx(
        0.1923076923 * min(p["w_mm"], p["h_mm"]))
        for p in a["pads"] if p["shape"] == "roundrect")
    assert a["pads"] == b["pads"]


# ---------------------------------------------------------------- 负向

def _board(pad_body, fp_at="(at 0 0)"):
    return ('(kicad_pcb (version 1)\n'
            '  (layers (0 "F.Cu" signal))\n'
            '  (footprint "X" (layer "F.Cu") %s\n'
            '    (property "Reference" "U1" (at 0 0) (layer "F.SilkS"))\n'
            '    %s\n'
            '  )\n'
            ')\n' % (fp_at, pad_body))


_PAD_FULL = ('(pad "1" smd rect (at 0 0) (size 1 1) (layers "F.Cu") '
             '(net "N") (uuid "p1"))')


def _neg_cases():
    return [
        # 缺必需子节点
        (_board(_PAD_FULL.replace("(at 0 0) ", "")), "pad 缺 (at)"),
        (_board(_PAD_FULL.replace("(size 1 1) ", "")), "pad 缺 (size)"),
        (_board(_PAD_FULL.replace("(layers \"F.Cu\") ", "")),
         "pad 缺 (layers)"),
        (_board(_PAD_FULL, fp_at=""), "footprint 缺 (at)"),
        # 非法形态枚举
        (_board(_PAD_FULL.replace("smd rect", "smd trapezoid")),
         "非法形态枚举"),
        # 形状退化
        (_board(_PAD_FULL.replace("(size 1 1)", "(size 0 1)")), "零尺寸"),
        (_board(_PAD_FULL.replace("(size 1 1)", "(size -1 1)")), "负尺寸"),
        # 圆角比越界（0.7 > 0.5 上限）
        (_board(_PAD_FULL.replace(
            "smd rect", "smd roundrect").replace(
            "(layers", "(roundrect_rratio 0.7) (layers")), "圆角比越界"),
        # 非有限数
        (_board(_PAD_FULL, fp_at="(at nan 0)"), "NaN token"),
        (_board(_PAD_FULL, fp_at="(at inf 0)"), "Inf token"),
        # 坐标离格（mm 量纲 >6 位小数）
        (_board(_PAD_FULL, fp_at="(at 0.0000001 0)"), "坐标离格"),
        ('(kicad_pcb (version 1)\n  (layers (0 "F.Cu" signal))\n'
         '  (segment (start 1.0000001 0) (end 2 0) (width 0.2) '
         '(layer "F.Cu") (net "N") (uuid "s1"))\n)\n',
         "segment 坐标离格"),
        # 非数值 token
        (_board(_PAD_FULL, fp_at="(at abc 0)"), "非数值 token"),
        # roundrect 缺 rratio
        (_board(_PAD_FULL.replace("smd rect", "smd roundrect")),
         "roundrect 缺 rratio"),
    ]


@pytest.mark.parametrize("text,why", _neg_cases(),
                         ids=[c[1] for c in _neg_cases()])
def test_parse_a_fail_closed(text, why):
    with pytest.raises(BoardParseError):
        parse_board_text(text)


@pytest.mark.parametrize("text,why", _neg_cases(),
                         ids=[c[1] for c in _neg_cases()])
def test_parse_b_fail_closed(text, why):
    with pytest.raises(BoardParseAltError):
        parse_board_text_alt(text)


def test_parse_a_multiple_roots_fail_closed():
    with pytest.raises(BoardParseError):
        parse_board_text("(kicad_pcb) (kicad_pcb)")


def test_parse_b_unbalanced_fail_closed():
    with pytest.raises(BoardParseAltError):
        parse_board_text_alt("(kicad_pcb (version 1)")


def test_custom_pad_primitive_extraction_both_paths():
    board = MINI_BOARD.replace(
        '(pad "4" smd oval (at 0 -1.5 270) (size 1.2 0.5)\n'
        '      (layers "F.Cu") (net "NET_D")',
        '(pad "4" smd custom (at 0 -1.5 270) (size 1.2 0.5)\n'
        '      (layers "F.Cu") (net "NET_D")\n'
        '      (primitives (gr_poly (pts (xy 0.1 0.2) (xy 0.3 0.4)) '
        '(width 0) (fill yes)))')
    a = parse_board_text(board)
    b = parse_board_text_alt(board)
    p4a = {p["pad_id"]: p for p in a["pads"]}["U9.4"]
    p4b = {p["pad_id"]: p for p in b["pads"]}["U9.4"]
    assert p4a == p4b
    assert p4a["shape"] == "custom"
    assert p4a["primitive_pts"] == [[0.1, 0.2], [0.3, 0.4]]
    assert a["unsupported_items"][0]["pad_id"] == "U9.4"
