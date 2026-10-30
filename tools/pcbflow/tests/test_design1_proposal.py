# -*- coding: utf-8 -*-
"""DESIGN-1 纯函数/账本测试（test_design1_ 前缀；不触板、不触网）。

唯一例外（REPAIR-P1 W-5 锚参数化）：板前缀登记检查只读 board 文件算
sha（不写、不触网），把 LIVE_BOARD_SHA_PREFIX 与 live 板实测对账。"""

from __future__ import annotations

import math
import os

import pytest

from pcbflow import config, design1_proposal as D1, hashing


# ---- 类 B：PTH 环带几何 -------------------------------------------------------
def test_design1_pth_rim_band_zero_margin_for_j4_pad():
    """J3/J4 PTH 焊盘（r_pad=0.85, drill r=0.5）：d_min=0.85=r_pad → 零裕量。"""
    band = D1.pth_rim_band(0.85, 0.5)
    assert band["d_min"] == pytest.approx(0.85)
    assert band["on_pad_open"] is True
    assert band["zero_margin"] is True


def test_design1_pth_rim_band_no_annulus_when_pad_too_small():
    """pad 半径小于 d_min → 无可落铜环带（fail-closed 语义）。"""
    band = D1.pth_rim_band(0.8, 0.5)
    assert band["on_pad_open"] is False
    assert D1.rim_endpoints(0.0, 0.0, 0.8, 0.5, (0,)) == []


def test_design1_rim_endpoints_d_override_must_stay_in_band():
    """d 越出 [d_min, r_pad] 即报错；带内 d 合成坐标正确。"""
    with pytest.raises(ValueError):
        D1.rim_endpoints(2.63, 26.11, 0.85, 0.5, (0,), d=0.95)
    rims = D1.rim_endpoints(2.63, 26.11, 1.05, 0.5, (180,), d=0.95)
    assert len(rims) == 1
    assert rims[0]["x"] == pytest.approx(2.63 - 0.95, abs=1e-3)
    assert rims[0]["y"] == pytest.approx(26.11, abs=1e-3)
    assert rims[0]["zero_margin"] is False


def test_design1_pad_lock_mechanism_quantifies_cell_disk_semantics():
    """0.05 邻格心落在钻孔盘内 → pt_prim_dist=0 → 全层格堵。"""
    mech = D1.pad_lock_mechanism(0.85, 0.5)
    assert mech["spoke_cell_inside_hole_disk"] is True
    assert mech["dist_spoke_to_hole"] == 0.0
    assert mech["locked"] is True
    assert mech["required_min"] == pytest.approx(0.35)


def test_design1_enlarge_pth_pad_rewrites_size_exactly():
    """pad 加大：只改目标 pad 的 (size)，旧值如实回读（板文本级）。"""
    board = ('(kicad_pcb "x"\n (footprint "J4"\n'
             '  (property "Reference" "J4")\n'
             '  (pad "12" thru_hole circle (at 0 0) (size 1.7 1.7)'
             ' (drill 1.0))\n'
             '  (pad "13" thru_hole circle (at 0 2.54) (size 1.7 1.7)'
             ' (drill 1.0))\n )\n)\n')
    new_text, chg = D1.enlarge_pth_pad(board, "J4", "13", 2.1)
    assert chg == {"old_size": 1.7, "new_size": 2.1}
    assert "(size 2.1000 2.1000)" in new_text
    assert new_text.count("(size 1.7 1.7)") == 1  # pad 12 不动
    assert new_text.count("(drill 1.0)") == 2           # drill 零改动
    with pytest.raises(ValueError):
        D1.enlarge_pth_pad(board, "J99", "13", 2.1)


def test_design1_smd_endpoint_offsets_clamped_to_pad_rect():
    """SMD 焊盘端点偏移：出矩形项剔除，界内项坐标正确。"""
    offs = D1.smd_endpoint_offsets(22.325, 14.65, 1.5, 0.3,
                                   [(-0.7, 0.0), (0.0, -0.1), (0.0, 0.2)])
    assert [(o["dx"], o["dy"]) for o in offs] == [(-0.7, 0.0), (0.0, -0.1)]
    assert offs[0]["x"] == pytest.approx(21.625)


# ---- 类 A：口袋墙 / 移位账单 ---------------------------------------------------
def _tr(net, x1, y1, x2, y2, name="F.Cu"):
    return {"layer": 0, "layer_name": name, "net": net,
            "x1": x1, "y1": y1, "x2": x2, "y2": y2, "width": 0.2}


def test_design1_pocket_wall_census_and_protected_nets():
    """口袋墙 census：端点命中半径内入账；exclude=目标网、protect=已收网。"""
    tracks = [
        _tr("FMC_SDNE0", 22.0, 33.65, 21.0, 33.65),   # 目标网自身 → 豁免
        _tr("VDDA", 22.0, 34.0, 21.0, 34.0),          # 1.5mm 内 → 入账
        _tr("3V3", 22.0, 30.5, 21.0, 30.5),           # 已收网且在另一口袋 → 不入
        _tr("QSPI_IO1", 30.0, 40.0, 31.0, 40.0),      # 远离 → 不入
    ]
    vias = [{"x": 22.3, "y": 33.0, "net": "ADC_A0", "size": 0.6,
             "drill": 0.3}]
    wall = D1.pocket_wall(tracks, vias, 22.325, 33.65, 1.5,
                          exclude_nets={"FMC_SDNE0"},
                          protect_nets={"3V3", "GPIO_PE2"})
    assert wall["counts"]["segments"] == 1
    assert wall["counts"]["vias"] == 1
    assert wall["net_histogram"] == {"ADC_A0": 1, "VDDA": 1}  # 段+过孔网属
    assert wall["protected_hits"] == 0


def test_design1_pocket_wall_protected_hits_counted_not_stripped():
    """已收网的命中段计入 protected_hits 且绝不入剥除账。"""
    tracks = [_tr("3V3", 22.0, 33.9, 21.0, 33.9)]
    wall = D1.pocket_wall(tracks, [], 22.325, 33.65, 1.5,
                          exclude_nets={"GNDA"},
                          protect_nets={"3V3", "GPIO_PE2"})
    assert wall["counts"]["segments"] == 0
    assert wall["protected_hits"] == 1
    assert len(wall["protected_items"]) == 1


def test_design1_shift_gap_after_reports_axis_and_sign():
    """移位后间隙：西移增大与东邻距离；负值=重叠量（双轴账）。"""
    a = [0.0, 0.0, 10.0, 10.0]
    b = [12.0, 0.0, 20.0, 10.0]
    west = D1.shift_gap_after(a, b, -1.0, 0.0)
    assert west == {"axis": "x", "gx": 3.0, "gy": -10.0, "gap_mm": 3.0}
    ov = D1.shift_gap_after(a, b, 3.0, 0.0)
    assert ov["gx"] == -1.0 and ov["gap_mm"] == -1.0 and ov["axis"] == "x"


def test_design1_u1_shift_candidates_deterministic():
    cands = D1.u1_shift_candidates((35.0, 22.9))
    assert [(c["dx"], c["dy"]) for c in cands] == [(-1.0, 0.0), (-2.0, 0.0)]


def test_design1_blast_radius_summary_counts_and_obligation():
    bill = {"segments": [{"net": "GND"}, {"net": "GND"}, {"net": "3V3"}],
            "vias": [],
            "counts": {"segments_total": 3, "vias_total": 0}}
    s = D1.blast_radius_summary(bill, "U1")
    assert s["segments"] == 3 and s["vias"] == 0 and s["nets"] == 2
    assert "3 段（2 网）" in s["obligation"]


# ---- verdict 行 / 矩阵 / waiver ------------------------------------------------
def _ladder(ok=False):
    return [{"margin_mm": 3.0,
             "route": {"ok": ok, "fail": None if ok else "A* 不可达",
                       "blocks": [], "width": 0.2, "via_size": 0.6,
                       "via_drill": 0.3, "refine_rounds": 0,
                       "segments": [] if not ok else
                       [[0, 0.0, 0.0, 1.0, 0.0]],
                       "vias": [], "length_mm": 0.0 if not ok else 1.0}}]


def test_design1_endpoint_variant_row_requires_independent_check_for_sat():
    """ok 步存在但独立复核缺/败 → 如实 UNKNOWN（禁自动改判）。"""
    row = D1.endpoint_variant_row("RPL-X", "NET", "B", {"kind": "track_end"},
                                  _ladder(ok=True), None, 591)
    assert row["design1_status"] == "UNKNOWN"
    row2 = D1.endpoint_variant_row("RPL-X", "NET", "B", {"kind": "track_end"},
                                   _ladder(ok=True),
                                   {"all_ok": True,
                                    "seg_bad": [], "via_bad": []}, 591)
    assert row2["design1_status"] == "SAT"
    assert row2["witness"]["segments"] == 1


def test_design1_decision_matrix_sorts_sat_first_then_cost():
    rows = [
        {"row_id": "RPL-B", "net": "N2", "design1_class": "A",
         "candidate_kind": "u1_shift", "design1_status": "UNKNOWN",
         "witness": None, "blast_radius": {"segments": 149, "vias": 0},
         "engineering": {"magnitude": D1.ENGINEERING_LAYOUT}},
        {"row_id": "RPL-A", "net": "N1", "design1_class": "B",
         "candidate_kind": "endpoint_variant", "design1_status": "SAT",
         "witness": {"segments": 44, "vias": 0, "length_mm": 16.7},
         "blast_radius": {}, "engineering": {"magnitude":
                                             D1.ENGINEERING_DATA}},
        {"row_id": "RPL-C", "net": "N3", "design1_class": "A",
         "candidate_kind": "pocket_wall_strip", "design1_status": "SAT",
         "witness": {"segments": 10, "vias": 0, "length_mm": 9.0},
         "blast_radius": {"segments": 22, "vias": 1},
         "engineering": {"magnitude": D1.ENGINEERING_BOARD}},
    ]
    m = D1.decision_matrix(rows)
    assert [r["row_id"] for r in m] == ["RPL-A", "RPL-C", "RPL-B"]
    view = D1.matrix_view(m)
    assert view[0]["rank"] == 1 and view[0]["status"] == "SAT"
    assert "用户批准（数据级）" in view[0]["premise"]
    assert "重布义务" in view[1]["premise"]


def test_design1_waiver_row_template_fields():
    w = D1.waiver_row("RPL-054", "SWDIO", "cert-ref", "cond", "mfg", "fn",
                      "reopen")
    assert w["status"] == "KNOWN-OPEN(waive 候选)"
    for k in ("certificate_ref", "accept_conditions",
              "manufacturing_impact", "functional_impact", "reopen_trigger",
              "waive_statement_template"):
        assert w[k]
    assert "RPL-054" in w["waive_statement_template"]


def test_design1_target_rows_and_prefixes_unchanged():
    """5 目标行钉死 + 已收网保护清单（漂移防护）。"""
    assert D1.TARGET_ROWS == {"FMC_SDNE0": "RPL-038", "GNDA": "RPL-039",
                              "LTDC_VSYNC": "RPL-052", "SWDIO": "RPL-054",
                              "VBAT": "RPL-056"}
    assert D1.APPLIED_NETS == ("3V3", "GPIO_PE2")


@pytest.mark.skipif(not os.path.isfile(str(config.REVC_BOARD)),
                    reason="真实板不存在")
def test_design1_live_board_sha_prefix_registered():
    """板前缀登记=live 板实测（REPAIR-P1 W-5 锚参数化，R4③ 形态 d）。

    原形态 `LIVE_BOARD_SHA_PREFIX == "dbfea089"` 硬编码 2026-09-11 时点
    值；改为与 live 板实测 sha 对账——tripwire 语义不变（常量过时即
    fail，提示重登记），消除「板变更→手刷常量」的 M1 循环。
    """
    assert D1.LIVE_BOARD_SHA_PREFIX == \
        hashing.sha256_file(config.REVC_BOARD)[:8]
