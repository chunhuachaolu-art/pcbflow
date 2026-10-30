"""FC2 单测（§10.6 合成轨 + 证书引擎 + writer/台账）。

Rev-C 两靶实跑不进 pytest（分钟级；实跑证据落 out/revc-fc2 + PHASE-REPORT），
本文件全部用自包含合成板（tmp_path，零 Rev-C 依赖）。
"""

from __future__ import annotations

import json

import pytest

from pcbflow import board_writer, cli, config, residual_cmd, route_grid


# ---- 合成板（最小 KiCad s-expr；pcbagent mirror 可解析） ---------------------
def _board_text(pads, edge=(0.0, 0.0, 60.0, 40.0)):
    """pads=[(ref,num,net,x,y,w,h,layers)]；layers=str 或 tuple。"""
    nets = sorted({p[2] for p in pads if p[2]})
    lines = ["(kicad_pcb",
             "\t(version 20260206)",
             '\t(generator "pcbflow-fc2-test")',
             "\t(layers (0 \"F.Cu\" signal) (6 \"In2.Cu\" signal))",
             '\t(net 0 "")']
    lines += ['\t(net %d "%s")' % (i + 1, n)
              for i, n in enumerate(nets)]
    lines.append('\t(gr_rect (start %g %g) (end %g %g) (layer "Edge.Cuts")'
                 " (width 0.05) (uuid \"e0\"))" % edge)
    for (ref, num, net, x, y, w, h, layers) in pads:
        ls = " ".join('"%s"' % l for l in
                      (layers if isinstance(layers, tuple) else (layers,)))
        lines.append(
            '\t(footprint "T:T" (layer "F.Cu")\n'
            "\t\t(at %g %g)\n"
            '\t\t(property "Reference" "%s")\n'
            '\t\t(pad "%s" smd rect (at 0 0) (size %g %g) (layers %s)'
            ' (net "%s") (uuid "p-%s-%s"))\n'
            "\t)" % (x, y, ref, num, w, h, ls, net, ref, num))
    lines.append(")")
    return "\n".join(lines) + "\n"


def _make_project(tmp_path, pads, edge=(0.0, 0.0, 60.0, 40.0)):
    d = tmp_path / "proj"
    d.mkdir()
    (d / "test.kicad_pcb").write_text(_board_text(pads, edge),
                                      encoding="utf-8")
    return str(d)


def _two_pad(tmp_path, net="N1", ax=5.0, ay=10.0, bx=10.0, by=10.0,
             extra_pads=(), edge=(0.0, 0.0, 60.0, 40.0)):
    pads = [("TA", "1", net, ax, ay, 0.6, 0.6, "F.Cu"),
            ("TB", "1", net, bx, by, 0.6, 0.6, "F.Cu")]
    pads += list(extra_pads)
    return _make_project(tmp_path, pads, edge)


# ---- SAT：witness + writer + uuid 确定性 ------------------------------------
def test_route_sat_witness_and_writer(tmp_path):
    proj = _two_pad(tmp_path)
    bm = route_grid.board_model(proj)
    r = route_grid.route_one(bm, "N1", 5.0, 10.0, [0], 10.0, 10.0, [0])
    assert r["ok"] and r["segments"] and r["length_mm"] >= 5.0
    assert "uuid" not in r
    assert board_writer.route_uuid(r) == board_writer.route_uuid(dict(r))
    r3 = dict(r)
    r3["segments"] = [[0, 5.0, 10.0, 9.0, 10.0]]
    assert board_writer.route_uuid(r3) != board_writer.route_uuid(r)

    text = board_writer.apply_routes(
        open(bm["pcb_path"], encoding="utf-8").read(), [r])
    assert text.count("(segment") == len(r["segments"])
    assert '(net "N1")' in text
    assert text.rstrip().endswith(")")
    # writer 幂等（同输入同输出）
    text2 = board_writer.apply_routes(
        open(bm["pcb_path"], encoding="utf-8").read(), [r])
    assert text == text2


# ---- UNSAT：墙体证书 + 独立复核 ----------------------------------------------
def _wall_pads(net="NW", x=7.5, y0=1.0, y1=39.0, pitch=0.35):
    """双层墙（F+In2 同堵；否则 A*/证书模型可经 In2 合法绕行）。"""
    out = []
    n = int((y1 - y0) / pitch) + 1
    for i in range(n):
        out.append(("W%d" % (i % 40), str(i), net, x, y0 + i * pitch,
                    0.5, 0.5, ("F.Cu", "In2.Cu")))
    return out


def test_cert_unsat_wall_verified(tmp_path):
    proj = _two_pad(tmp_path, extra_pads=_wall_pads())
    bm = route_grid.board_model(proj)
    r = route_grid.route_one(bm, "N1", 5.0, 10.0, [0], 10.0, 10.0, [0])
    assert not r["ok"]
    model, unk = route_grid.build_cert_model(
        bm, "N1", r["width"], r["via_size"], r["via_drill"],
        5.0, 10.0, 10.0, 10.0)
    assert model is not None, unk
    cert = route_grid.solve_cert(model)
    assert cert["reachable_b"] is False
    assert not cert.get("cert_broken")
    assert cert["cut_groups"]
    assert cert["cut_count"] > 0
    assert route_grid.verify_cert(model, cert)
    rules = {g["why"]["rule"] for g in cert["cut_groups"]}
    assert any(ru != "cert_scope_window" for ru in rules)


def test_cert_verify_negative(tmp_path):
    proj = _two_pad(tmp_path, extra_pads=_wall_pads())
    bm = route_grid.board_model(proj)
    model, _unk = route_grid.build_cert_model(
        bm, "N1", 0.15, 0.6, 0.3, 5.0, 10.0, 10.0, 10.0)
    cert = route_grid.solve_cert(model)
    # 割组删半 → 闭包不封闭 → 复核必须 False
    broken = dict(cert)
    broken["cut_groups"] = cert["cut_groups"][:len(cert["cut_groups"]) // 2]
    assert not route_grid.verify_cert(model, broken)
    # 论据篡改（cell 改到不堵的格）→ 论据重算失败 → False
    falsified = dict(cert)
    falsified["cut_groups"] = [dict(g) for g in cert["cut_groups"]]
    for g in falsified["cut_groups"]:
        if g["kind"] == "cell":
            g["items"] = [[i[0] + 40, i[1]] for i in g["items"]]
            break
    assert not route_grid.verify_cert(model, falsified)


# ---- UNKNOWN：区域超窗 --------------------------------------------------------
def test_cert_unknown_region_over_window(tmp_path, monkeypatch):
    monkeypatch.setattr(route_grid, "CERT_WINDOW_NODES", 30)
    proj = _two_pad(tmp_path)
    bm = route_grid.board_model(proj)
    model, unk = route_grid.build_cert_model(
        bm, "N1", 0.15, 0.6, 0.3, 5.0, 10.0, 10.0, 10.0)
    assert model is None and unk[0] == "region_over_window"


def test_route_sat_with_gap_in_wall(tmp_path):
    """墙留 4mm 缺口 → A* 应 SAT（三态不误伤可布网）。"""
    wall = [p for p in _wall_pads() if not (8.0 <= p[4] <= 12.0)]
    proj = _two_pad(tmp_path, extra_pads=wall)
    bm = route_grid.board_model(proj)
    r = route_grid.route_one(bm, "N1", 5.0, 10.0, [0], 10.0, 10.0, [0])
    assert r["ok"]


# ---- writer：③ placement 重放 ------------------------------------------------
def test_writer_apply_placement(tmp_path):
    pads = [("J1", "1", "N1", 35.0, 65.5, 0.6, 0.6, "F.Cu"),
            ("U1", "1", "N2", 5.0, 5.0, 0.6, 0.6, "F.Cu")]
    text = _board_text(pads, edge=(0.0, 0.0, 70.0, 70.0))
    rows = [{"ref": "J1", "x": "10.85", "y": "66.75", "rot": "90",
             "side": "F", "zone": "CONN"}]
    out = board_writer.apply_placement(text, rows)
    from pcbflow import sexpr_min
    root = sexpr_min.parse(out)[0]
    got = {}
    for fp in sexpr_min.find_all(root, "footprint"):
        ref = None
        for prop in sexpr_min.find_all(fp, "property"):
            if sexpr_min.get_str(prop, 1) == "Reference":
                ref = sexpr_min.get_str(prop, 2)
        at = sexpr_min.find_first(fp, "at")
        got[ref] = tuple(at[1:])
    assert got["J1"] == ("10.85", "66.75", "90")
    assert got["U1"] == ("5", "5")
    with pytest.raises(ValueError):
        board_writer.apply_placement(text, [{"ref": "NOPE", "x": "1",
                                             "y": "1", "rot": "0"}])


# ---- DRC 台账解析（合成 JSON） ------------------------------------------------
def test_drc_ledger_join(tmp_path, monkeypatch):
    drc = tmp_path / "drc"
    drc.mkdir()
    def viol(t, sev, desc):
        return {"type": t, "severity": sev,
                "items": [{"description": desc}]}
    (drc / "baseline-all.json").write_text(json.dumps({
        "violations": [viol("copper_edge_clearance", "error", "edge A")],
        "unconnected_items": [{"a": 1}] * 30}), encoding="utf-8")
    (drc / "batch-1.json").write_text(json.dumps({
        "violations": [viol("copper_edge_clearance", "error", "edge A")],
        "unconnected_items": [{"a": 1}] * 20}), encoding="utf-8")
    (drc / "batch-2.json").write_text(json.dumps({
        "violations": [viol("copper_edge_clearance", "error", "edge A"),
                       viol("clearance", "error", "NEW X")],
        "unconnected_items": [{"a": 1}] * 10}), encoding="utf-8")
    (drc / "final-all.json").write_text(json.dumps({
        "violations": [viol("copper_edge_clearance", "error", "edge A")],
        "unconnected_items": [{"a": 1}] * 12}), encoding="utf-8")
    led = residual_cmd._drc_ledger(str(drc))
    assert led["batches"][0]["accepted"] is True
    assert led["batches"][1]["accepted"] is False
    assert led["batches"][1]["new_vs_baseline"] == 1
    assert led["zero_new_errors"] is False
    assert led["final_all"]["new_vs_baseline"] == 0
    assert led["final_all"]["unconnected"] == 12


# ---- CLI 守卫 -----------------------------------------------------------------
def test_cli_replay_board_requires_guard():
    assert cli.main(["residual", "--select", "replay_board"]) == \
        config.EXIT_FAILED


# ---- §10.6 合成 30 网全布 100% 布通 -------------------------------------------
def test_synthetic_30_nets_full_route(tmp_path):
    edge = (0.0, 0.0, 70.0, 46.0)
    pads = []
    for i in range(30):
        y = 2.0 + i * 1.4
        pads.append(("A%d" % i, "1", "SN%d" % i, 5.0, y, 0.5, 0.5, "F.Cu"))
        pads.append(("B%d" % i, "1", "SN%d" % i, 65.0, y, 0.5, 0.5, "F.Cu"))
    proj = _make_project(tmp_path, pads, edge)
    bm = route_grid.board_model(proj)
    ok = 0
    for i in range(30):
        r = route_grid.route_one(bm, "SN%d" % i, 5.0, 2.0 + i * 1.4, [0],
                                 65.0, 2.0 + i * 1.4, [0])
        assert r["ok"], ("SN%d" % i, r["fail"], r["blocks"][:2])
        ok += 1
    assert ok == 30
