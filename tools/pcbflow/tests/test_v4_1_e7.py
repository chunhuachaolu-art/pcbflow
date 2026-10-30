# -*- coding: utf-8 -*-
"""tests/test_v4_1_e7.py -- E7 对外证据与资格包测试（hermetic，零 datasets
依赖、零 kicad-cli、零网络零模型）。

覆盖：静态 net surface、选板冻结规则（Path A/Path B/预算界/平手序）、
批 record 双口径 commit 门、QoR 分列表与 S2 备用支/S3 判定、fail-closed
路径、canonical 输出纪律。
"""

from __future__ import annotations

import json
import pathlib

import pytest

from pcbflow.v4_1 import e7
from pcbflow.v4_1.canonical import dumps_canonical


# --------------------------------------------------------------- 板文本构造

def _board_text(pads, segments=(), zones=()):
    """最小 KiCad 10 板文本（pads=[(ref,pad,net,x,y)]）。"""
    fps = []
    for ref, pad, net, x, y in pads:
        net_node = ('\n\t\t\t(net "%s")' % net) if net else ""
        fps.append("""
	(footprint "pkg:%s"
		(layer "F.Cu")
		(uuid "u-%s")
		(at %.4f %.4f)
		(property "Reference" "%s" (at 0 0 0) (uuid "p-%s"))
		(pad "%s" smd rect (at 0 0) (size 1.0 1.0) (layers "F.Cu")%s
			(uuid "pad-%s"))
	)""" % (ref, ref, x, y, ref, ref, pad, net_node, ref))
    segs = "".join("""
	(segment (start %s %s) (end %s %s) (width 0.2) (layer "F.Cu")
		(net "%s") (uuid "s-%d"))""" % (a[0], a[1], a[2], a[3], a[4], i)
        for i, a in enumerate(segments))
    zn = "".join("""
	(zone (net "%s") (layer "F.Cu") (uuid "z-%d")
		(polygon (pts (xy 0 0) (xy 10 0) (xy 10 10) (xy 0 10))))""" % (n, i)
        for i, n in enumerate(zones))
    return """(kicad_pcb (version 20260206)
	(general)
	(paper "A4")
	(layers (0 "F.Cu" signal) (31 "B.Cu" signal))
	(net "GND")%s
	%s%s%s
)""" % ("".join('\n\t(net "%s")' % n
                for n in {p[2] for p in pads if p[2] and p[2] != "GND"}),
        "".join(fps), segs, zn)


def _pads():
    # SDA 两 pad、SCL 两 pad（signal）；GND 两 pad；单 pad 网不计
    return [
        ("U1", "1", "SDA", 1.0, 1.0), ("U1", "2", "SDA", 2.0, 1.0),
        ("U1", "3", "SCL", 3.0, 1.0), ("U2", "1", "SCL", 4.0, 1.0),
        ("U1", "9", "GND", 5.0, 1.0), ("U2", "9", "GND", 6.0, 1.0),
        ("U3", "1", "ONEPAD", 7.0, 1.0),
    ]


# --------------------------------------------------------------- 静态 screen

class TestSignalNetSurface:
    def test_surface_counts(self):
        sig, gnd, copper, pads = e7.signal_net_surface(
            _board_text(_pads()))
        assert sig == ["SCL", "SDA"]
        assert gnd == ["GND"]
        assert copper == ["F.Cu", "B.Cu"]
        assert pads == 7

    def test_parse_fail_closed(self):
        with pytest.raises(Exception):
            e7.signal_net_surface("(kicad_pcb (version 20260206))")

    def test_agnd_dgnd_gndlike(self):
        pads = _pads() + [("U4", "1", "AGND", 1.0, 2.0),
                          ("U4", "2", "AGND", 1.0, 3.0)]
        sig, gnd, _c, _p = e7.signal_net_surface(_board_text(pads))
        assert "AGND" in gnd and "AGND" not in sig


# --------------------------------------------------------------- 选板规则

def _screen_row(slug, parse="ok", excluded=None, sig=10, cu=2,
                gnd=("GND",)):
    row = {"slug": slug, "dataset_path": "x", "holdout_designation": "y",
           "excluded": excluded, "parse": parse,
           "signal_net_surface": sig, "gnd_net_names": list(gnd),
           "copper_layers": cu}
    return row


def _make_e7(tmp_path, rows, drc):
    """构造 select_boards 输入树：board-screen.json + drc-screen/*/screen-drc.json。"""
    e7_dir = tmp_path / "e7"
    e7_dir.mkdir(exist_ok=True)
    screen = {"schema": "pcbflow.v4_1.e7-board-screen/1",
              "declared_date": "2026-09-12", "boards": rows,
              "exclusion_list": {}}
    (e7_dir / "board-screen.json").write_text(
        dumps_canonical(screen), encoding="utf-8")
    for slug, unc in drc.items():
        d = e7_dir / "drc-screen" / slug
        d.mkdir(parents=True)
        obj = {"violations": [{"severity": "error"}] * 0,
               "unconnected_items": [{"items": []}] * unc}
        (d / "screen-drc.json").write_text(
            dumps_canonical(obj), encoding="utf-8")
    return e7_dir


class TestSelectBoards:
    def test_path_a_ranking(self, tmp_path):
        rows = [_screen_row("b1", sig=5), _screen_row("b2", sig=5),
                _screen_row("b3", sig=5)]
        e7_dir = _make_e7(tmp_path, rows, {"b1": 9, "b2": 12, "b3": 3})
        sel = e7.select_boards(str(e7_dir))
        assert sel["path_taken"] == "A"
        assert [s["slug"] for s in sel["selected"]] == ["b2", "b1"]

    def test_path_a_row_budget_exclusion(self, tmp_path):
        rows = [_screen_row("big", sig=5), _screen_row("s1", sig=5),
                _screen_row("s2", sig=5)]
        e7_dir = _make_e7(tmp_path, rows, {"big": 61, "s1": 4, "s2": 2})
        sel = e7.select_boards(str(e7_dir))
        assert sel["path_taken"] == "A"
        assert sel["not_selected_over_row_budget"] == ["big"]
        assert [s["slug"] for s in sel["selected"]] == ["s1", "s2"]

    def test_path_b_stratified(self, tmp_path):
        rows = [_screen_row("l2a", cu=2, sig=18), _screen_row("l2b", cu=2, sig=14),
                _screen_row("l4a", cu=4, sig=57), _screen_row("l4b", cu=4, sig=56),
                _screen_row("huge", cu=4, sig=370)]
        e7_dir = _make_e7(tmp_path, rows,
                          {s: 0 for s in ("l2a", "l2b", "l4a", "l4b", "huge")})
        sel = e7.select_boards(str(e7_dir))
        assert sel["path_taken"] == "B"
        assert [s["slug"] for s in sel["selected"]] == ["l2a", "l4a"]
        assert sel["not_selected_over_net_budget"] == ["huge"]

    def test_path_b_single_stratum_fallback(self, tmp_path):
        rows = [_screen_row("l2a", cu=2, sig=18), _screen_row("l2b", cu=2, sig=14)]
        e7_dir = _make_e7(tmp_path, rows, {"l2a": 0, "l2b": 0})
        sel = e7.select_boards(str(e7_dir))
        assert [s["slug"] for s in sel["selected"]] == ["l2a", "l2b"]

    def test_missing_drc_fail_closed(self, tmp_path):
        rows = [_screen_row("b1")]
        e7_dir = _make_e7(tmp_path, rows, {})  # 无 DRC 产物
        with pytest.raises(e7.E7Error):
            e7.select_boards(str(e7_dir))

    def test_no_feasible_board_blocked(self, tmp_path):
        rows = [_screen_row("huge", cu=4, sig=370)]
        e7_dir = _make_e7(tmp_path, rows, {"huge": 0})
        with pytest.raises(e7.E7Error):
            e7.select_boards(str(e7_dir))


# --------------------------------------------------------------- 批 record

def _drc(viol, unc, extra=None):
    v = [{"severity": "error", "type": "clearance",
          "items": [{"description": "x[%d]" % i,
                     "pos": {"x": float(i), "y": 0.0}}]}
         for i in range(viol)]
    return {"violations": v, "unconnected_items": [{"items": []}] * unc}


def _mk_batch(e7_dir, slug, batch, base_viol, base_unc, chal_viol,
              chal_unc, refill=None):
    bd = e7_dir / "boards" / slug
    st = bd / "l2-batches" / "staging"
    st.mkdir(parents=True)
    board = _board_text(_pads())
    (st / "revc.kicad_pcb").write_text(board, encoding="utf-8")
    bdir = bd / "l2-batches" / batch
    bdir.mkdir(parents=True)
    (bdir / "candidates.json").write_text(dumps_canonical(
        {"schema": "pcbflow.v4_1.e4-batch-plan/1",
         "batch": batch, "candidate_rows": 3}), encoding="utf-8")
    (bdir / "apply-record.json").write_text(dumps_canonical(
        {"schema": "pcbflow.v4_1.e4-batch-apply/1", "batch": batch,
         "pre_hash_sha256": e7._sha_file(str(st / "revc.kicad_pcb")),
         "post_hash_sha256": "f" * 64, "ops_count": 5,
         "prl_inventory_before": {}}), encoding="utf-8")
    (bdir / "challenger.kicad_pcb").write_text(
        board + "\n", encoding="utf-8")
    (bdir / "drc-error-norefill.json").write_text(
        dumps_canonical(_drc(chal_viol, chal_unc)), encoding="utf-8")
    (bdir / "baseline-error-norefill.json").write_text(
        dumps_canonical(_drc(base_viol, base_unc)), encoding="utf-8")
    if refill is not None:
        rv, ru = refill
        (bdir / "drc-error-refill.json").write_text(
            dumps_canonical(_drc(rv, ru)), encoding="utf-8")
        (bdir / "baseline-error-refill.json").write_text(
            dumps_canonical(_drc(base_viol, base_unc)), encoding="utf-8")


class TestBatchRecord:
    def _e7dir(self, tmp_path):
        d = tmp_path / "e7"
        d.mkdir()
        (d / "progress.json").unlink(missing_ok=True)
        return d

    def test_commit_when_clean(self, tmp_path):
        e7_dir = self._e7dir(tmp_path)
        _mk_batch(e7_dir, "b1", "batch-01", 4, 10, 4, 7, refill=(4, 7))
        rec = e7.batch_record("b1", "batch-01", str(e7_dir))
        assert rec["verdict"] == "commit"
        assert rec["committed_rows"] == 3
        assert rec["unconnected_delta_norefill"] == -3
        assert rec["zone_gate_applied"] is True

    def test_rollback_on_added_error_norefill(self, tmp_path):
        e7_dir = self._e7dir(tmp_path)
        _mk_batch(e7_dir, "b1", "batch-01", 4, 10, 6, 7, refill=(4, 7))
        rec = e7.batch_record("b1", "batch-01", str(e7_dir))
        assert rec["verdict"] == "rollback"
        assert rec["committed_rows"] == 0
        assert len(rec["added_error_keys_norefill"]) == 2

    def test_rollback_on_added_error_refill_only(self, tmp_path):
        # norefill 干净但 refill 口径新增 ⇒ 双口径门拦截（E6 接线牙齿）
        e7_dir = self._e7dir(tmp_path)
        _mk_batch(e7_dir, "b1", "batch-01", 4, 10, 4, 7, refill=(5, 7))
        rec = e7.batch_record("b1", "batch-01", str(e7_dir))
        assert rec["verdict"] == "rollback"

    def test_rollback_on_unconnected_regression(self, tmp_path):
        e7_dir = self._e7dir(tmp_path)
        _mk_batch(e7_dir, "b1", "batch-01", 4, 10, 4, 11, refill=(4, 11))
        rec = e7.batch_record("b1", "batch-01", str(e7_dir))
        assert rec["verdict"] == "rollback"

    def test_no_zone_refill_files_gate_copied(self, tmp_path):
        e7_dir = self._e7dir(tmp_path)
        _mk_batch(e7_dir, "b1", "batch-01", 4, 10, 4, 8, refill=None)
        rec = e7.batch_record("b1", "batch-01", str(e7_dir))
        assert rec["zone_gate_applied"] is False
        assert rec["verdict"] == "commit"


# --------------------------------------------------------------- QoR/S2/S3

def _mk_pair(e7_dir, slug, chal_unc_delta=0, chal_new_err=0,
             fr_status="completed", fr_new_err=648, fr_unc_delta=-66):
    bd = e7_dir / "boards" / slug
    bd.mkdir(parents=True)
    base = {"norefill": {"violations_total": 4, "severity_error": 4,
                         "unconnected_items": 115},
            "refill": {"violations_total": 4, "severity_error": 4,
                       "unconnected_items": 113},
            "zone_audit_flag_classes": [],
            "zone_audit_commit_blocked_without_refill_drc": False,
            "divergent": True}
    fin = {"norefill": {"violations_total": 4 + chal_new_err,
                        "severity_error": 4 + chal_new_err,
                        "unconnected_items": 115 + chal_unc_delta},
           "refill": {"violations_total": 4 + chal_new_err,
                      "severity_error": 4 + chal_new_err,
                      "unconnected_items": 113 + chal_unc_delta},
           "severity_all": None, "hash_chain_verified": True}
    fr = None
    if fr_status is not None:
        fr = {"status": fr_status,
              "drc_baseline": {"norefill": {"severity_error": 4,
                                            "unconnected_items": 115},
                               "refill": {"severity_error": 4,
                                          "unconnected_items": 113}},
              "drc_final": {"norefill": {"severity_error": 4 + fr_new_err,
                                         "unconnected_items":
                                             115 + fr_unc_delta},
                            "refill": {"severity_error": 4 + fr_new_err // 2,
                                       "unconnected_items":
                                           113 + fr_unc_delta}},
              "new_track_length_mm": 1.0, "new_via_count": 1}
    pair = {"schema": "pcbflow.v4_1.e7-board-pair/1",
            "declared_date": "2026-09-12", "board": slug,
            "rows_total": 100, "required_net_count": 10,
            "batch_count": 1,
            "batches": [{"batch": "batch-01", "verdict": "rollback",
                         "no_change_batch": False, "committed_rows": 0,
                         "unconnected_delta_norefill": 0,
                         "unconnected_delta_refill": 0,
                         "added_error_keys_norefill": 0,
                         "added_error_keys_refill": 0}],
            "baseline": base, "challenger_final": fin,
            "committed_rows_total": 0, "freerouting": fr,
            "unconnected_improvement_norefill": 0,
            "unconnected_improvement_refill": 0,
            "s2_disclosure": "S2 R32"}
    (bd / "board-pair.json").write_text(dumps_canonical(pair),
                                        encoding="utf-8")


def _mk_sel(e7_dir, slugs):
    sel = {"schema": "pcbflow.v4_1.e7-board-selection/1",
           "declared_date": "2026-09-12",
           "selected": [{"slug": s} for s in slugs]}
    (e7_dir / "board-selection.json").write_text(
        dumps_canonical(sel), encoding="utf-8")


class TestQorAndS2S3:
    def _e7dir(self, tmp_path):
        d = tmp_path / "e7"
        d.mkdir(exist_ok=True)
        return d

    def test_s2_triggered_when_unconnected_worse(self, tmp_path):
        e7_dir = self._e7dir(tmp_path)
        _mk_sel(e7_dir, ["b1"])
        _mk_pair(e7_dir, "b1", chal_unc_delta=0, chal_new_err=0,
                 fr_status="completed", fr_new_err=648, fr_unc_delta=-66)
        q = e7.qor_table(str(e7_dir))
        assert q["boards"][0]["diff_023_check"][
            "differential_worse_than_freerouting"] is True
        assert q["boards"][0]["diff_023_check"]["worse_by_new_error"] \
            is False
        s = e7.s2_s3_check(str(e7_dir))
        assert s["s2_backup_branch"]["triggered"] is True
        assert s["s3"]["triggered"] is False

    def test_not_comparable_when_fr_not_completed(self, tmp_path):
        e7_dir = self._e7dir(tmp_path)
        _mk_sel(e7_dir, ["b1"])
        _mk_pair(e7_dir, "b1", fr_status="not_completed")
        q = e7.qor_table(str(e7_dir))
        assert q["boards"][0]["diff_023_check"][
            "differential_worse_than_freerouting"] \
            == "not_comparable_freerouting_not_completed"

    def test_not_worse_when_challenger_wins_both(self, tmp_path):
        e7_dir = self._e7dir(tmp_path)
        _mk_sel(e7_dir, ["b1"])
        _mk_pair(e7_dir, "b1", chal_unc_delta=-10, chal_new_err=0,
                 fr_status="completed", fr_new_err=648, fr_unc_delta=-5)
        q = e7.qor_table(str(e7_dir))
        assert q["boards"][0]["diff_023_check"][
            "differential_worse_than_freerouting"] is False

    def test_s3_triggered_on_committed_regression(self, tmp_path):
        e7_dir = self._e7dir(tmp_path)
        _mk_sel(e7_dir, ["b1"])
        _mk_pair(e7_dir, "b1", fr_status=None)
        pair = json.loads((e7_dir / "boards" / "b1" /
                           "board-pair.json").read_text(encoding="utf-8"))
        pair["batches"][0]["verdict"] = "commit"
        pair["batches"][0]["added_error_keys_norefill"] = 2
        (e7_dir / "boards" / "b1" / "board-pair.json").write_text(
            dumps_canonical(pair), encoding="utf-8")
        e7.qor_table(str(e7_dir))
        s = e7.s2_s3_check(str(e7_dir))
        assert s["s3"]["triggered"] is True
        assert s["s3"]["findings"][0]["kind"] == "committed_with_added_error"

    def test_ps_arm_preregistered_disposition(self, tmp_path):
        e7_dir = self._e7dir(tmp_path)
        _mk_sel(e7_dir, ["b1"])
        _mk_pair(e7_dir, "b1")
        q = e7.qor_table(str(e7_dir))
        ps = q["boards"][0]["kicad_ps"]
        assert ps["status"] == "not_run_headless_with_reason"
        assert ps["objective"] == "not_applicable"
        assert "人工" in ps["manual_participation_disclosure"]
        assert "参与度" in ps["manual_participation_disclosure"]


# --------------------------------------------------------------- 纪律

class TestDiscipline:
    def test_canonical_outputs_carry_declared_date_only(self, tmp_path):
        e7_dir = tmp_path / "e7"
        e7_dir.mkdir()
        rows = [_screen_row("b1", sig=5), _screen_row("b2", sig=5)]
        _make = _make_e7(tmp_path, rows, {"b1": 3, "b2": 5})
        sel = e7.select_boards(str(_make))
        text = (_make / "board-selection.json").read_text(encoding="utf-8")
        assert "declared_date" in sel
        assert "2026-09-12" in text
        for bad in ("timestamp", "evaluated_at", "measured_at"):
            assert bad not in sel

    def test_universe_paths_rooted_at_datasets(self):
        for _slug, rel, _src in e7.CANDIDATE_UNIVERSE:
            assert rel.startswith("datasets/"), rel

    def test_exclusions_only_shrink(self):
        universe = {s for s, _r, _src in e7.CANDIDATE_UNIVERSE}
        assert set(e7.EXCLUSIONS) <= universe
