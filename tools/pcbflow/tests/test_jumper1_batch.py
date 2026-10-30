# -*- coding: utf-8 -*-
"""JUMPER-1 纯函数/账本测试（不碰 live 板；几何用合成数据，账本只读 evidence）。

覆盖：
- 跳线设计记录不变量（裸焊盘↔锁定铜搭接、0603 几何、逃逸端点在 pad 上）；
- 裸焊盘/0603 放置预检（census 证据越界必须报问题；合法放置零问题）；
- footprint 文本构建确定性 + uuid 内容派生 + 回读解析（sexpr_min）；
- assemble_staged_text 纯函数组合（CRLF 保持、前缀保持、尾闭合）；
- DRC 记账/新增违规归类/staging 门语义（合成 DRC 账目）；
- SWDIO 飞线工单（坐标与账本证据一致、板面零改动）；
- apply1 口径复用（witness_vs_board 合成闭环）。
"""

import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from pcbflow import board_writer  # noqa: E402

_OUT = os.path.join(os.path.dirname(HERE), "out", "coreboard-jumper1")


def _load_j1():
    spec = importlib.util.spec_from_file_location(
        "jumper1_orchestrate",
        os.path.join(_OUT, "jumper1_orchestrate.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _census(site):
    with open(os.path.join(_OUT, "probe_sites.json"),
              encoding="utf-8") as f:
        return json.load(f)[site]


def _evidence(name):
    with open(os.path.join(_OUT, "evidence", name), encoding="utf-8") as f:
        return json.load(f)


# ---- 设计记录不变量 ------------------------------------------------------------
def test_jumper1_design_records_invariants():
    J1 = _load_j1()
    assert set(J1.DESIGNS) == {"LTDC_VSYNC", "VBAT"}
    for net, d in J1.DESIGNS.items():
        assert d["net"] == net
        # 裸焊盘矩形 = at ± size/2（自洽）
        r = d["bare_pad"]["rect"]
        at, size = d["bare_pad"]["at"], d["bare_pad"]["size"]
        assert abs((r[0] + r[2]) / 2 - at[0]) < 1e-9
        assert abs((r[1] + r[3]) / 2 - at[1]) < 1e-9
        assert abs(r[2] - r[0] - size[0]) < 1e-9
        assert abs(r[3] - r[1] - size[1]) < 1e-9
        # 逃逸起点=0603 某一 pad 心（±0.825）
        p1 = (d["r0603"]["at"][0] - 0.825, d["r0603"]["at"][1])
        p2 = (d["r0603"]["at"][0] + 0.825, d["r0603"]["at"][1])
        assert tuple(d["escape_from"]) in (p1, p2)
        # 逃逸终点=网内既有铜（目标端点）
        assert d["target_endpoint"]["at"] == \
            {"LTDC_VSYNC": [22.325, 17.15],
             "VBAT": [22.325, 14.65]}[net]


def test_jumper1_bare_pad_overlaps_locked_copper():
    J1 = _load_j1()
    # LTDC_VSYNC：裸焊盘与 J3.5 圆铜（r0.85）搭接带存在
    d = J1.DESIGNS["LTDC_VSYNC"]
    assert J1.circle_rect_overlap((64.23, 21.95), 0.85,
                                  d["bare_pad"]["rect"])
    # 且保守孔距（同网孔按 min_hole_clearance 校验口径）仍 ≥0.75
    assert J1.pt_rect_dist(64.23, 21.95, d["bare_pad"]["rect"]) >= 0.75 - 1e-9
    # VBAT：裸焊盘压竖直走线（x 6.3598..6.6598 ∩ 焊盘矩形）
    r = J1.DESIGNS["VBAT"]["bare_pad"]["rect"]
    assert r[0] <= 6.3598 and r[2] >= 6.6598
    # 走线顶端 y=35.0698 在焊盘 y 范围内（搭接带非空）
    assert r[1] <= 35.0698 <= r[3]


def test_jumper1_geometry_primitives_synthetic():
    J1 = _load_j1()
    assert J1.pt_rect_dist(0, 0, (1, 1, 2, 2)) == (2 ** 0.5)
    assert J1.pt_rect_dist(1.5, 1.5, (1, 1, 2, 2)) == 0.0
    assert J1.rect_rect_gap((0, 0, 1, 1), (2, 0, 3, 1)) == 1.0
    assert J1.rect_rect_gap((0, 0, 2, 2), (1, 1, 3, 3)) == -1.0
    assert J1.circle_rect_overlap((0, 0), 1.0, (0.5, -0.5, 1.5, 0.5))
    assert not J1.circle_rect_overlap((0, 0), 1.0, (2, 2, 3, 3))


# ---- 放置预检（census 证据） ----------------------------------------------------
def test_jumper1_placement_precheck_passes_on_design():
    J1 = _load_j1()
    for net, site in (("LTDC_VSYNC", "J3.5_LTDC_VSYNC"),
                      ("VBAT", "VBAT_trackend")):
        problems = J1.validate_bare_pad_placement(
            J1.DESIGNS[net], _census(site)) + \
            J1.validate_r0603_placement(J1.DESIGNS[net], _census(site))
        assert problems == [], (net, problems)


def test_jumper1_placement_precheck_rejects_bad_design():
    J1 = _load_j1()
    census = _census("VBAT_trackend")
    # 裸焊盘东移压上 GND 过孔 → 必须报问题
    import copy
    d = copy.deepcopy(J1.DESIGNS["VBAT"])
    d["bare_pad"]["rect"] = (7.9, 34.6, 9.1, 35.5)
    d["bare_pad"]["at"] = (8.5, 35.05)
    d["bare_pad"]["size"] = (1.2, 0.9)
    problems = J1.validate_bare_pad_placement(d, census)
    assert problems, "东移压 GND 过孔必须报问题"
    # 0603 挪到 J4 列上（含 PTH）→ pad 间隙/courtyard 必须报问题
    d2 = copy.deepcopy(J1.DESIGNS["VBAT"])
    d2["r0603"]["at"] = [5.17, 33.73]
    problems2 = J1.validate_r0603_placement(d2, census)
    assert problems2, "0603 压 J4 PTH 列必须报问题"


# ---- footprint 文本构建与回读 ---------------------------------------------------
def test_jumper1_footprint_text_deterministic_and_parses():
    from pcbflow.sexpr_min import parse, find_all
    J1 = _load_j1()
    for net in ("LTDC_VSYNC", "VBAT"):
        t1 = J1.jumper_nodes_text(J1.DESIGNS[net])
        t2 = J1.jumper_nodes_text(J1.DESIGNS[net])
        assert t1 == t2  # 确定性
        assert "\r\n" in t1  # CRLF（live 板行尾口径）
        root = parse(t1)
        fps = [c for c in root
               if isinstance(c, list) and c and c[0] == "footprint"]
        assert len(fps) == 2
        pads = find_all(["root"] + root, "pad")
        assert len(pads) == 3  # 裸焊盘 1 + 0603 两
        for pad in pads:
            netnodes = [c for c in pad[2:] if isinstance(c, list)
                        and c and c[0] == "net"]
            assert netnodes and netnodes[0][1] == net
        # uuid 全唯一（内容派生）
        import re
        u = re.findall(r'\(uuid "([^"]+)"\)', t1)
        assert len(u) == len(set(u))
        for x in u:
            assert len(x) == 36 and x.count("-") == 4


def test_jumper1_uuid_content_derived_namespace():
    J1 = _load_j1()
    u = J1._juuid("JU1:pad1")
    assert u == J1._juuid("JU1:pad1")
    assert u != J1._juuid("JU1:pad2")
    assert len(u) == 36 and u.count("-") == 4


def test_jumper1_assemble_staged_text_idempotent_prefix():
    J1 = _load_j1()
    pristine = "(kicad_pcb\r\n\t(version 20260206)\r\n\t(foo 1)\r\n)\r\n"
    staged = J1.assemble_staged_text(pristine, ["LTDC_VSYNC"])
    assert staged.startswith(pristine.rstrip()[:-1])  # 前缀保持（剥尾）
    assert staged.endswith(")" + pristine[pristine.rstrip().__len__():])
    assert "\r\n" in staged
    # 单网两次组合一致；两网组合 ≠ 单网但同为超集前缀
    staged2 = J1.assemble_staged_text(pristine, ["LTDC_VSYNC"])
    assert staged == staged2
    both = J1.assemble_staged_text(pristine, ["LTDC_VSYNC", "VBAT"])
    assert both.startswith(staged.rstrip()[:-1])
    # LF 板 → LF 节点（eol=auto 探测）
    pristine_lf = pristine.replace("\r\n", "\n")
    staged_lf = J1.assemble_staged_text(pristine_lf, ["LTDC_VSYNC"])
    assert "\r\n" not in staged_lf


def test_jumper1_verify_staged_board_selfcheck():
    J1 = _load_j1()
    pristine = ("(kicad_pcb\r\n\t(version 20260206)\r\n"
                "\t(segment\r\n\t\t(start 1 1)\r\n\t\t(end 2 2)\r\n"
                "\t\t(width 0.15)\r\n\t\t(layer \"F.Cu\")\r\n"
                "\t\t(net \"GND\")\r\n\t\t(uuid \"aaaaaaaa-1111-2222-3333-"
                "444444444444\")\r\n\t)\r\n)\r\n")
    base = {"segments": 1, "vias": 0}
    staged = J1.assemble_staged_text(pristine, ["LTDC_VSYNC"])
    assert J1.verify_staged_board(staged, ["LTDC_VSYNC"], base) == []
    bad = J1.verify_staged_board(staged, ["VBAT"], base)
    assert bad, "缺 VBAT footprint 必须报问题"


# ---- DRC 记账与门语义（合成账目） -----------------------------------------------
def _acct(total_by_type_sev, unc):
    return {"violations_total": sum(total_by_type_sev.values()),
            "violations_by_severity": {},
            "violations_by_type_severity": total_by_type_sev,
            "unconnected_count": unc}


def test_jumper1_drc_account_and_new_violation_classification():
    J1 = _load_j1()
    base = _acct({"silk_over_copper|warning": 81,
                  "clearance|error": 10}, 55)
    post = _acct({"silk_over_copper|warning": 83,
                  "clearance|error": 10}, 54)
    new = J1.classify_new_violations(base, post)
    assert new == {"silk_over_copper|warning": 2}
    assert J1.stage_gate(base, post, {"expected_unconnected_delta": -1})[
        "gate_ok"] is True
    # error 新增 → 门必须拒
    post_bad = _acct({"silk_over_copper|warning": 83,
                      "clearance|error": 11}, 54)
    g = J1.stage_gate(base, post_bad,
                      {"expected_unconnected_delta": -1})
    assert g["gate_ok"] is False and g["new_error_count"] == 1
    # unconnected 未降 → 门必须拒
    g2 = J1.stage_gate(base, _acct({"silk_over_copper|warning": 83}, 55),
                       {"expected_unconnected_delta": -1})
    assert g2["gate_ok"] is False and g2["unconnected_ok"] is False


def test_jumper1_stage_gate_matches_evidence_shape():
    """t0 基线账目存在且 staging 门以它为基线（账本只读）。"""
    J1 = _load_j1()
    t0 = _evidence("t0-baseline.json")
    assert t0["account_refill_all"]["unconnected_count"] == 55
    assert t0["account_refill_all"]["violations_by_severity"] \
        .get("error") == 10
    for net, d in J1.DESIGNS.items():
        assert d["expected_unconnected_delta"] == -1


# ---- SWDIO 飞线工单 --------------------------------------------------------------
def test_jumper1_swdio_workorder_matches_evidence():
    J1 = _load_j1()
    wo = J1.swdio_workorder()
    assert wo["board_change"] == "none"
    assert wo["from_pad"]["at"] == [2.63, 26.11]  # J4.13（cert 环带东点 3.58 = 心+0.95）
    assert wo["to_pad"]["at"] == [47.675, 16.15]  # U1.124（S1 row variant B）
    assert wo["from_pad"]["net"] == "SWDIO" == wo["to_pad"]["net"]
    import math
    assert abs(wo["straight_line_mm"] -
               math.hypot(45.045, -9.96)) < 1e-2
    assert wo["manhattan_mm"] == 55.005
    assert any(n["net"] == "SWCLK" for n in wo["neighbors_do_not_short"])
    assert wo["row_id"] == "RPL-054"


# ---- apply1 口径复用（witness 对账） ---------------------------------------------
def test_jumper1_writer_route_witness_closed_loop():
    J1 = _load_j1()
    route = {"net": "VBAT", "width": 0.3, "via_size": 0.6, "via_drill": 0.3,
             "segments": [[0, 9.125, 33.9, 12.0, 33.9],
                          [0, 12.0, 33.9, 12.0, 30.0]],
             "vias": []}
    wr = J1._as_writer_route(route)
    uuid = board_writer.route_uuid(wr)
    board_text = board_writer.apply_routes(
        "(kicad_pcb\n)", [wr], eol=None)
    acct = J1.A1.extract_net_nodes(board_text, uuid)
    assert J1.A1.witness_vs_board(wr, acct) == []
    # 篡改一段 → 必须报 mismatch
    acct["segments"][0]["start"] = [9.125, 33.91]
    assert J1.A1.witness_vs_board(wr, acct)


def test_jumper1_rows_verdicts_consistent_with_batch():
    """rows 已存在时：verdict 与 assemble 批次口径一致（账本自洽）。"""
    J1 = _load_j1()
    path = os.path.join(_OUT, "evidence", "jumper1-results.json")
    if not os.path.exists(path):
        return  # assemble 前跳过（纯函数测试不强制产物时序）
    res = _evidence("jumper1-results.json")
    for net, v in res["nets"].items():
        row_path = os.path.join(
            _OUT, "rows", "%s_%s.json" % (v["row_id"], net))
        row = json.load(open(row_path, encoding="utf-8"))
        assert row["verdict"] == v["verdict"]
        if v["verdict"] == "SAT_GATE_PASS":
            assert v["gate"]["gate_ok"] is True
            assert row["independent_check"]["all_ok"] is True
    passing = sorted(n for n, v in res["nets"].items()
                     if v["verdict"] == "SAT_GATE_PASS")
    assert res["apply_batch"] == passing
