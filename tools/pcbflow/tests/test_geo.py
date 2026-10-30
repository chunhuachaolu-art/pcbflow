"""几何提取测试：坐标变换约定（opens.csv 83 端点验证过的约定 A）、侧别、采样。

约定 A（KiCad 屏幕逆时针、y 向下）：
  ax = fx + px·cos + py·sin ; ay = fy + py·cos − px·sin
"""

import math

from pcbflow import geo


def test_transform_matches_opens_csv_convention():
    """约定 A 抽样复核：R5 rot=90 pad1（opens.csv 口径下 USB_DM_C 焊盘）。"""
    # R5 at (53.3, 18.3) rot 90；pad1 local (-0.825, 0)
    x, y = geo.transform(-0.825, 0.0, 53.3, 18.3, 90.0)
    assert abs(x - 53.3) < 1e-9 and abs(y - 19.125) < 1e-9


def test_transform_zero_rotation_identity_translation():
    x, y = geo.transform(1.0, -2.0, 10.0, 20.0, 0.0)
    assert (x, y) == (11.0, 18.0)


def test_finalize_board_sides_and_bbox():
    board = geo.finalize_board({
        "A": {"ref": "A", "x": 0.0, "y": 0.0, "rot": 0.0, "pads": [
            {"ref": "A", "num": "1", "net": "n1", "x": 0.0, "y": -1.0, "w": 0.3, "h": 0.3},
            {"ref": "A", "num": "2", "net": "n1", "x": 0.0, "y": 1.0, "w": 0.3, "h": 0.3},
            {"ref": "A", "num": "3", "net": None, "x": 2.0, "y": 0.0, "w": 0.3, "h": 0.3},
        ]},
    })
    by_num = {p["num"]: p for p in board["pads"]}
    assert by_num["1"]["side"] == ["N", "W"]  # 角垫：两条边并列 → 双侧
    assert by_num["2"]["side"] == ["S", "W"]  # 左列 → W 并列
    assert by_num["3"]["side"] == ["E"]
    assert board["bbox"] == (0.0, -1.0, 2.0, 1.0)


def test_corner_pad_gets_two_sides():
    """角垫与两条边并列 → 记两侧（保守计数）。"""
    board = geo.finalize_board({
        "B": {"ref": "B", "x": 0.0, "y": 0.0, "rot": 0.0, "pads": [
            {"ref": "B", "num": "1", "net": "n", "x": 0.0, "y": 0.0, "w": 0.3, "h": 0.3},
            {"ref": "B", "num": "2", "net": "n", "x": 2.0, "y": 2.0, "w": 0.3, "h": 0.3},
        ]},
    })
    p1 = next(p for p in board["pads"] if p["num"] == "1")
    assert set(p1["side"]) == {"N", "W"}


def test_seg_samples_endpoints_and_count():
    pts = geo.seg_samples(0.0, 0.0, 10.0, 0.0, 3.0)
    assert pts[0] == (0.0, 0.0) and pts[-1] == (10.0, 0.0)
    assert len(pts) == int(math.ceil(10.0 / 3.0)) + 1
    assert geo.seg_samples(1.0, 1.0, 1.0, 1.0, 0.5) == [(1.0, 1.0)]
