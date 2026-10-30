# -*- coding: utf-8 -*-
"""v5.drc 判定唯一源：R1/R2/R5/R6/capacity + 版本进证据链 + 单源性静态扫描。"""
import subprocess
import sys

import pytest

from fixtures_v2 import ANA_RECT
from v5 import drc
from v5.drc import Copper, check_all, check_capacity, check_clearance, check_width

RULES = {
    "R1": {"k_a": 0.4, "floor_mm": 0.3},
    "R2": {"min_distance_mm": 3.0, "max_parallel_mm": 5.0},
    "R3": {"unsplittable": True},
    "R4": {"return_via_required": True, "max_distance_mm": 2.0},
    "R5": {"min_clearance_mm": 0.5},
    "R6": {"plane_forbidden": True, "keepout_zones_forbidden": True},
}


def line(net, cid, x0, y0, x1, y1, layer="F.Cu", hw=0.1):
    return Copper(net, cid, layer, polyline=[[x0, y0], [x1, y1]], half_width=hw)


def test_version_string_present():
    assert drc.VERSION.startswith("v5.drc/")
    assert drc.VERSION in drc.DRCReport([], 0).as_dict()["drc_version"]


def test_r5_violation_reported():
    v, checked = check_clearance([line("A", "a1", 0, 0, 10, 0),
                                  line("B", "b1", 0, 0.4, 10, 0.4)], 0.5)
    assert len(v) == 1 and v[0].rule == "R5" and checked == 1
    assert v[0].data["gap_mm"] == pytest.approx(0.4)


def test_r5_exact_edge_is_clean():
    v, _ = check_clearance([line("A", "a1", 0, 0, 10, 0),
                            line("B", "b1", 0, 0.5, 10, 0.5)], 0.5)
    assert v == []


def test_r5_same_net_exempt():
    v, _ = check_clearance([line("A", "a1", 0, 0, 10, 0),
                            line("A", "a2", 0, 0.1, 10, 0.1)], 0.5)
    assert v == []


def test_r5_cross_layer_not_checked():
    v, checked = check_clearance([line("A", "a1", 0, 0, 10, 0),
                                  line("B", "b1", 0, 0.0, 10, 0.0, layer="B.Cu")], 0.5)
    assert v == [] and checked == 0


def test_r5_pad_pad_v2_p9_p7():
    """对抗：V2 P9↔P7 净距 0.4 < 0.5（播种缺陷 D2 命中）。"""
    a = Copper("P9", "P9-band", "F.Cu", band=(2.0, 36.0, 44.0, 36.2))
    b = Copper("P7", "P7-band", "F.Cu", band=(2.0, 36.6, 44.0, 36.8))
    v, _ = check_clearance([a, b], 0.5)
    assert len(v) == 1 and v[0].data["gap_mm"] == pytest.approx(0.4)


def test_r5_endpoint_pad_vs_band():
    """对抗：端点焊盘 (16,36) r0.15 撞 P9 铜带 [36.0,36.2]（V2 表内缺陷）。"""
    pad = Copper("P3", "P3-endpad", "F.Cu", pad=((16.0, 36.0), 0.15))
    band = Copper("P9", "P9-band", "F.Cu", band=(2.0, 36.0, 44.0, 36.2))
    v, _ = check_clearance([pad, band], 0.5)
    assert len(v) == 1


def test_r2_ana_violation():
    """R2：距 ANA 2.5 < 3 且平行 20 > 5。"""
    cu = line("A", "a1", 30.5, 0.0, 30.5, 20.0)
    vs = drc.check_ana_proximity([cu], [("ANA", ANA_RECT)], 3.0, 5.0)
    assert len(vs) == 1 and vs[0].rule == "R2"


def test_r2_far_enough_clean():
    cu = line("A", "a1", 31.0, 0.0, 31.0, 20.0)  # 距 ANA 右缘 3.0
    vs = drc.check_ana_proximity([cu], [("ANA", ANA_RECT)], 3.0, 5.0)
    assert vs == []


def test_r2_close_but_short_parallel_clean():
    cu = line("A", "a1", 30.5, 0.0, 30.5, 4.0)  # 平行仅 4 ≤ 5
    vs = drc.check_ana_proximity([cu], [("ANA", ANA_RECT)], 3.0, 5.0)
    assert vs == []


def test_r1_width_violation_v2_p8():
    v = check_width(0.5, 0.8, "P8")
    assert v is not None and v.rule == "R1"
    assert v.data["planned_mm"] == 0.5


def test_r1_exact_min_clean():
    assert check_width(0.8, 0.8, "P8") is None


def test_capacity_violation_v2_double_f():
    v = check_capacity(4.7, 4.3, "C1-F.Cu")
    assert v is not None and v.rule == "capacity"


def test_capacity_edge_clean():
    assert check_capacity(4.3, 4.3, "C1-F.Cu") is None


def test_r6_keepout_hit():
    cu = line("A", "a1", 10.0, 20.0, 20.0, 20.0)  # 穿 K1 (y∈[16,24], x≤30)
    vs = drc.check_keepout([cu], [("K1", (0.0, 16.0, 30.0, 24.0))])
    assert len(vs) == 1 and vs[0].rule == "R6"


def test_r6_plane_layer():
    cu = line("A", "a1", 10.0, 1.0, 12.0, 1.0, layer="In2.Cu")
    vs = drc.check_keepout([cu], [], plane_layers=("In2.Cu",))
    assert len(vs) == 1


def test_check_all_report_shape_and_version():
    coppers = [line("A", "a1", 0, 0, 10, 0), line("B", "b1", 0, 0.3, 10, 0.3)]
    report = check_all(coppers, RULES)
    d = report.as_dict()
    assert d["drc_version"] == drc.VERSION
    assert not d["clean"] and d["violation_count"] == 1
    assert d["violations"][0]["rule"] == "R5"


def test_check_all_clean_board():
    coppers = [line("A", "a1", 0, 0, 10, 0), line("B", "b1", 0, 5, 10, 5)]
    assert check_all(coppers, RULES).clean


def test_drc_mono_source_static_scan():
    """P0 门：全仓间距判定只出自 v5.drc，静态扫描零旁路。"""
    import os
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    script = os.path.join(root, "tools", "check_drc_mono.py")
    proc = subprocess.run([sys.executable, script], capture_output=True, text=True)
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_envelope_overlap_diagnostic_not_violation():
    """包络重叠但实际合规 → 诊断伪影，不计入违例。"""
    a = line("A", "a1", 0, 0, 10, 0)
    b = line("B", "b1", 0, 1.2, 10, 1.2)  # 实际 1.2 ≥ 2×0.6 伪影判别成立
    overlaps = drc.check_envelope_overlap([a, b])
    assert len(overlaps) == 1 and overlaps[0]["artifact"] is True
    v, _ = check_clearance([a, b], 0.5)
    assert v == []
