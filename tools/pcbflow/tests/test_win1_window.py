"""WIN-1 单测：窗参数化冻结守卫 + 渐进窗梯三态合同（自包含合成板）。

 Rev-C 实跑不进 pytest（分钟级；实跑证据落 out/coreboard-win1 + 实验报告），
本文件全部用自包含合成板（tmp_path，零 Rev-C 依赖）。验收门：
- route_grid.CERT_WINDOW_NODES 与 build_cert_model 默认窗=600_000 不变；
- 冻结链调用点（residual_cmd）零改动（源文本强制）；
- window_nodes 参数只动门，不动三态合同（SAT=witness、UNSAT=verified 割、
  其余 UNKNOWN；扩窗不自动改判）。
"""

from __future__ import annotations

import inspect
import json

import pytest

from pcbflow import hashing, residual_cmd, route_grid, win1_window


# ---- 合成板（与 test_fc2 同法：最小 KiCad s-expr） ----------------------------
def _board_text(pads, edge=(0.0, 0.0, 60.0, 40.0)):
    nets = sorted({p[2] for p in pads if p[2]})
    lines = ["(kicad_pcb",
             "\t(version 20260206)",
             '\t(generator "pcbflow-win1-test")',
             "\t(layers (0 \"F.Cu\" signal) (6 \"In2.Cu\" signal))",
             '\t(net 0 "")']
    lines += ['\t(net %d "%s")' % (i + 1, n) for i, n in enumerate(nets)]
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


def _wall_pads(net="NW", x=7.5, y0=1.0, y1=39.0, pitch=0.35):
    """双层墙（F+In2 同堵；与 test_fc2._wall_pads 同法）。"""
    out = []
    n = int((y1 - y0) / pitch) + 1
    for i in range(n):
        out.append(("W%d" % (i % 40), str(i), net, x, y0 + i * pitch,
                    0.5, 0.5, ("F.Cu", "In2.Cu")))
    return out


_TINY_EDGE = (0.0, 0.0, 12.0, 8.0)   # 小板：区域节点数少，合成板求解快


def _tiny_pads(with_wall=True):
    pads = [("TA", "1", "N1", 2.0, 4.0, 0.6, 0.6, "F.Cu"),
            ("TB", "1", "N1", 10.0, 4.0, 0.6, 0.6, "F.Cu")]
    if with_wall:
        pads += [("W%d" % i, str(i), "NW", 6.0, 0.6 + i * 0.35, 0.5, 0.5,
                  ("F.Cu", "In2.Cu"))
                 for i in range(int((7.4 - 0.6) / 0.35) + 1)]
    return pads


# ---- 冻结守卫（验收门） --------------------------------------------------------
def test_window_default_frozen():
    assert route_grid.CERT_WINDOW_NODES == 600_000
    sig = inspect.signature(route_grid.build_cert_model)
    assert "window_nodes" in sig.parameters
    # 默认=None → 调用时回退模块常量（保持既有测试的调用时 monkeypatch
    # 语义）；显式传参时按参数走（WIN-1 实验入口）。
    assert sig.parameters["window_nodes"].default is None
    # 其余既有参数签名零改动
    assert list(sig.parameters)[:9] == ["bm", "net", "width", "via_size",
                                        "via_drill", "ax", "ay", "bx", "by"]
    assert sig.parameters["margin_mm"].default == route_grid.CERT_MARGIN_MM


def test_frozen_call_sites_untouched():
    """冻结链全部 build_cert_model 调用点不传 window_nodes（源文本强制）。"""
    import os
    src_path = os.path.join(os.path.dirname(residual_cmd.__file__),
                            "residual_cmd.py")
    with open(src_path, encoding="utf-8") as f:
        src = f.read()
    calls = [ln for ln in src.splitlines()
             if "route_grid.build_cert_model(" in ln]
    assert calls, "residual_cmd 应存在 build_cert_model 调用"
    lines = src.splitlines()
    ctx = "\n".join(
        "\n".join(lines[i:i + 4])
        for i, ln in enumerate(lines)
        if "route_grid.build_cert_model(" in ln)
    assert "window_nodes" not in ctx


def test_region_nodes_matches_gate_math(tmp_path):
    """region_nodes 纯计数 == 真实门 detail.nodes（同式强制）。"""
    proj = _make_project(tmp_path, _tiny_pads(with_wall=False),
                         edge=_TINY_EDGE)
    bm = route_grid.board_model(proj)
    bb = bm["mirror"].bbox()
    geom = win1_window.region_nodes(bb, 2.0, 4.0, 10.0, 4.0,
                                    route_grid.CERT_MARGIN_MM)
    model, unk = route_grid.build_cert_model(
        bm, "N1", 0.15, 0.6, 0.3, 2.0, 4.0, 10.0, 4.0, window_nodes=1)
    assert model is None and unk[0] == "region_over_window"
    assert unk[1]["nodes"] == geom["nodes"]
    assert unk[1]["window"] == 1


# ---- 三态合同（window_nodes 只动门，不动合同） ---------------------------------
def test_window_gate_lift_enables_verified_unsat(tmp_path):
    """同一 blocked 板：小窗=region_over_window；精确窗=verified 割 UNSAT。"""
    proj = _make_project(tmp_path, _tiny_pads(with_wall=True),
                         edge=_TINY_EDGE)
    bm = route_grid.board_model(proj)
    geom = win1_window.region_nodes(bm["mirror"].bbox(), 2.0, 4.0, 10.0,
                                    4.0, route_grid.CERT_MARGIN_MM)
    model_small, unk = route_grid.build_cert_model(
        bm, "N1", 0.15, 0.6, 0.3, 2.0, 4.0, 10.0, 4.0, window_nodes=30)
    assert model_small is None
    assert unk[0] == "region_over_window"
    assert unk[1]["window"] == 30
    model, unk2 = route_grid.build_cert_model(
        bm, "N1", 0.15, 0.6, 0.3, 2.0, 4.0, 10.0, 4.0,
        window_nodes=geom["nodes"])
    assert model is not None, unk2
    cert = route_grid.solve_cert(model)
    assert cert["reachable_b"] is False and not cert.get("cert_broken")
    assert route_grid.verify_cert(model, cert)
    rules = {g["why"]["rule"] for g in cert["cut_groups"]}
    assert any(ru != "cert_scope_window" for ru in rules)


def test_window_lift_never_fakes_unsat(tmp_path):
    """开阔板（无墙）：任意窗下模型有候选通径 → 必 UNKNOWN，不出 UNSAT。"""
    proj = _make_project(tmp_path, _tiny_pads(with_wall=False),
                         edge=_TINY_EDGE)
    bm = route_grid.board_model(proj)
    geom = win1_window.region_nodes(bm["mirror"].bbox(), 2.0, 4.0, 10.0,
                                    4.0, route_grid.CERT_MARGIN_MM)
    model, unk = route_grid.build_cert_model(
        bm, "N1", 0.15, 0.6, 0.3, 2.0, 4.0, 10.0, 4.0,
        window_nodes=geom["nodes"])
    assert model is not None, unk
    cert = route_grid.solve_cert(model)
    assert cert.get("reachable_b") is True   # 候选通径 ≠ 证书


# ---- run_row 渐进梯 -------------------------------------------------------------
def _stub_router_fail(width=0.15, via_size=0.6, via_drill=0.3):
    return {"ok": False, "fail": "stub", "blocks": [], "refine_rounds": 1,
            "width": width, "via_size": via_size, "via_drill": via_drill,
            "segments": [], "vias": [], "length_mm": 0.0}


def _tiny_row(tmp_path):
    return {"row_id": "RES-901", "net": "N1", "ax": 2.0, "ay": 4.0,
            "alayers": [0], "bx": 10.0, "by": 4.0, "blayers": [0]}


def test_run_row_unsat_upgrade_via_corridor(tmp_path, monkeypatch):
    """梯：frozen_600k 门拒 → corridor 精确窗 verified 割 → UNSAT 升级。"""
    monkeypatch.setattr(win1_window, "WIN1_BASELINE_WINDOW", 30)
    proj = _make_project(tmp_path, _tiny_pads(with_wall=True),
                         edge=_TINY_EDGE)
    bm = route_grid.board_model(proj)
    row = _tiny_row(tmp_path)
    result = win1_window.run_row(bm, row, router_result=_stub_router_fail())
    assert result["status"] == "UNSAT"
    assert result["upgrade_from"] == "UNKNOWN(region_over_window)"
    tiers = [(s["tier"], s.get("skipped"), s["status"]) for s in
             result["steps"]]
    assert tiers[0][:2] == ("frozen_600k", False)
    assert result["steps"][0]["status"] == "UNKNOWN"
    assert "region_over_window" in result["steps"][0]["unknown_reason"]
    assert tiers[1][:2] == ("corridor", False)
    assert result["steps"][1]["status"] == "UNSAT"
    assert result["certificate"]["verified"] is True
    # 板级梯运行（corridor certified → 范围强化）
    assert tiers[2][:2] == ("board", False)
    # 确定性：同输入同字节
    result2 = win1_window.run_row(bm, row, router_result=_stub_router_fail())
    assert (hashing.canonical_json_bytes(result)
            == hashing.canonical_json_bytes(result2))


def test_run_row_board_tier_skipped_when_corridor_open(tmp_path,
                                                       monkeypatch):
    """开阔板：corridor=候选通径 UNKNOWN → board 梯确定性跳过（同判必然），
    终态如实 UNKNOWN，绝无伪造证书。"""
    monkeypatch.setattr(win1_window, "WIN1_BASELINE_WINDOW", 30)
    proj = _make_project(tmp_path, _tiny_pads(with_wall=False),
                         edge=_TINY_EDGE)
    bm = route_grid.board_model(proj)
    row = _tiny_row(tmp_path)
    result = win1_window.run_row(bm, row, router_result=_stub_router_fail())
    assert result["status"] == "UNKNOWN"
    assert result["certificate"] is None
    assert "候选通径" in result["unknown_reason"]
    board_step = result["steps"][-1]
    assert board_step["tier"] == "board" and board_step["skipped"] is True


def test_run_row_router_sat_is_real_upgrade(tmp_path):
    """路由器见 witness（无墙小板）→ SAT 升级，witness 在案。"""
    proj = _make_project(tmp_path, _tiny_pads(with_wall=False),
                         edge=_TINY_EDGE)
    bm = route_grid.board_model(proj)
    row = _tiny_row(tmp_path)
    result = win1_window.run_row(bm, row)   # 不 stub → 真实 route_one
    assert result["status"] == "SAT"
    assert result["witness"]["segments"] >= 1
    assert result["ladder"]   # 梯仍随行（记录用，未走）


def test_unknown_rows_from_fail_closed():
    def _mk(counts_unknown):
        rows = [{"solver_status": "UNKNOWN",
                 "unknown_reason": "unknown:region_over_window"
                                   "({'nodes': 1, 'window': 2})"},
                {"solver_status": "UNKNOWN",
                 "unknown_reason": "unknown:missing_basis:x"},
                {"solver_status": "UNSAT", "unknown_reason": None}]
        return {"rows": rows,
                "counts": {"SAT": 0, "UNSAT": 1, "UNKNOWN": counts_unknown}}
    got = win1_window.unknown_rows_from(_mk(1))
    assert len(got) == 1
    with pytest.raises(RuntimeError):
        win1_window.unknown_rows_from(_mk(2))


def test_ladder_deterministic_and_ordered():
    bb = (0.0, 0.0, 70.0, 70.0)
    lad = win1_window.window_ladder(bb, 2.63, 26.11, 47.675, 16.15)
    assert [s["tier"] for s in lad] == ["frozen_600k", "corridor", "board"]
    wins = [s["window_nodes"] for s in lad]
    assert wins == sorted(wins) and len(set(wins)) == len(wins)
    assert wins[0] == 600_000
    # 小区域行：corridor 已在 600k 内 → 梯只到 frozen（去重）
    lad2 = win1_window.window_ladder(bb, 2.63, 26.11, 3.0, 16.15)
    assert [s["tier"] for s in lad2] == ["frozen_600k"]
