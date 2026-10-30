"""② 审计单元测试（合成几何，不依赖 Rev-C）：逃逸/transit/走廊预算/层计划/方向/pin-swap。

夹具要点：单排封装的每个焊盘天然占 N+S 两侧（自身 bbox 即整排），
要形成"单侧场"必须造双排芯片（行焊盘落在 bbox 边缘上）。
"""

from pcbflow import audit_cmd, config, geo


def _mk(ref, pads):
    return {"ref": ref, "x": 0.0, "y": 0.0, "rot": 0.0,
            "pads": [{"ref": ref, "num": n, "net": net, "x": x, "y": y,
                      "w": w, "h": h} for (n, net, x, y, w, h) in pads]}


def _mk_from_pads(ref, pad_dicts):
    """用现成 pad dict（如 _row 产物）组装封装（合并多排用）；统一重写 ref。"""
    return {"ref": ref, "x": 0.0, "y": 0.0, "rot": 0.0,
            "pads": [dict(p, ref=ref) for p in pad_dicts]}


def _row(ref, nets, x0, y0, dx, w=0.3, h=0.6):
    return _mk(ref, [(str(i + 1), net, x0 + i * dx, y0, w, h)
                     for i, net in enumerate(nets)])


def _two_row_chip(ref, north_nets, south_nets, x0, y_north, y_south, dx=1.0):
    """双排芯片 + 两端 GND 填充列：信号焊盘落在 bbox 边内部 → 单侧 [N]/[S]。

    南排焊盘编号 +100 偏移（(ref,num) 是 pad 键，禁止撞号——LQFP 同理）。
    """
    nn = ["GND"] + list(north_nets) + ["GND"]
    ss = ["GND"] + list(south_nets) + ["GND"]
    n = _row("t", nn, x0 - dx, y_north, dx)["pads"]
    s = _row("t", ss, x0 - dx, y_south, dx)["pads"]
    for p in s:
        p["num"] = str(100 + int(p["num"]))
    return _mk_from_pads(ref, n + s)


def test_escape_deficit_certificate_on_boxed_field():
    """U1 北排被电容排压住 → 北场出缺口证书；南排（净空）无缺口。"""
    sig = [f"S{i}" for i in range(8)]
    board = geo.finalize_board({
        "U1": _two_row_chip("U1", sig, sig, 10.0, 20.0, 30.0),
        # 填充列外仍要盖住信号焊盘 11..18 → 9 只从 9.2 起步
        "CAP": _row("CAP", ["GND"] * 9, 9.2, 18.0, 1.0),
    })
    esc = audit_cmd.escape_check(board, lambda n: None)
    fn = esc["fields"]["U1|N"]
    fs = esc["fields"]["U1|S"]
    assert fn["has_deficit"] and len(fn["blocked_transit_nets"]) == 8
    assert not fs["has_deficit"]
    for i in range(8):
        assert f"S{i}" in esc["blocked_by_net"]


def test_escape_local_hop_not_fatal():
    """去耦式场内短跳（对端互相在带内）不占逃逸需求 → 不产生 fatal。"""
    board = geo.finalize_board({
        "U1": _row("U1", ["V1", "V2"], 10.0, 20.0, 2.0),
        "C1": _mk("C1", [("1", "V1", 11.0, 17.9, 0.3, 0.6),
                         ("2", "GND", 11.0, 16.9, 0.3, 0.6)]),
    })
    esc = audit_cmd.escape_check(board, lambda n: None)
    assert esc["escape_fatal_nets"] == []
    assert "V1" not in esc["blocked_by_net"]


def test_escape_fatal_rail_boxed_everywhere():
    """多点多被围死的轨（≥4 个 transit 焊盘全堵）→ 网级致命。"""
    rail = ["RAIL"] * 5
    filler = ["GND"] * 5
    board = geo.finalize_board({
        "U1": _two_row_chip("U1", rail, filler, 10.0, 20.0, 30.0),
        "U2": _two_row_chip("U2", rail, filler, 30.0, 20.0, 30.0),
        # 7 只盖住信号焊盘 11..15（含填充列外侧）
        "CAPN": _row("CAPN", ["GND"] * 7, 9.2, 18.0, 1.0),
        "CAPN2": _row("CAPN2", ["GND"] * 7, 29.2, 18.0, 1.0),
    })
    esc = audit_cmd.escape_check(board, lambda n: None)
    assert "RAIL" in esc["escape_fatal_nets"]


def test_corridor_budget_deficit_flags_members():
    """C-0053：需求宽 > 净空 gap 的走廊 → 成员网 fatal；充裕走廊不 fatal。"""
    bus8 = [f"B{i}" for i in range(8)]
    bus6 = [f"C{i}" for i in range(6)]
    board = geo.finalize_board({
        "U1": _row("U1", bus8 + bus6, 10.0, 15.0, 0.5),
        "U2": _row("U2", bus8, 30.0, 15.0, 0.5),
        "J9": _row("J9", bus6, 10.0, 16.3, 0.5),  # 与 U1 bbox 净空 1.0mm < 1.65
    })
    structures = {"buses": [
        {"bus_id": "BUS_B", "members": bus8, "member_count": 8,
         "endpoint_refs": ["U1", "U2"]},
        {"bus_id": "BUS_C", "members": bus6, "member_count": 6,
         "endpoint_refs": ["U1", "J9"]},
    ]}
    corb = audit_cmd.corridor_budget_check(board, structures)
    by = {c["bus_id"]: c for c in corb["corridors"]}
    assert by["BUS_B"]["gap_mm"] > by["BUS_B"]["required_mm"]
    assert not by["BUS_B"]["fatal"]
    assert by["BUS_C"]["deficit"] and by["BUS_C"]["fatal"]
    assert sorted(corb["fatal_nets"]) == sorted(bus6)


def test_layer_plan_via_counts():
    """层计划：单层网 0 换层；双层网 2 次换层 vs via_policy 上限（≤2 达标）。"""
    board = geo.finalize_board({
        "U1": _mk("U1", [("1", "USB_P", 10.0, 10.0, 0.3, 0.6),
                         ("2", "FMC_D0", 12.0, 10.0, 0.3, 0.6)]),
        "J1": _mk("J1", [("1", "FMC_D0", 30.0, 10.0, 0.3, 0.6)]),
    })
    nets = {"USB_P": [{"ref": "U1", "pin": "1"}],
            "FMC_D0": [{"ref": "U1", "pin": "2"}, {"ref": "J1", "pin": "1"}]}
    allowed = {"USB_P": ["F.Cu"], "FMC_D0": ["F.Cu", "In2.Cu"]}
    structures = {"return_tree": {"planes": {}}}
    ret = audit_cmd.return_check(board, nets, lambda n: "FMC_ADDR", allowed.get,
                                 structures)
    assert ret["layer_plan_violations"] == []


def test_orientation_faces_target():
    """东列焊盘朝东、目标在东 → facing=1.0。"""
    board = geo.finalize_board({
        "U1": _mk("U1", [("1", "A0", 14.0, 18.0, 0.3, 0.6),
                         ("2", "A1", 14.0, 22.0, 0.3, 0.6),
                         ("3", None, 10.0, 18.0, 0.3, 0.6),
                         ("4", None, 10.0, 22.0, 0.3, 0.6)]),
        "U2": _mk("U2", [("1", "A0", 40.0, 18.0, 0.3, 0.6),
                         ("2", "A1", 40.0, 22.0, 0.3, 0.6)]),
    })
    structures = {"buses": [{"bus_id": "BUS_A", "members": ["A0", "A1"],
                             "member_count": 2, "endpoint_refs": ["U1", "U2"]}]}
    ori = audit_cmd.orientation_check(board, structures)
    assert ori["per_bus"][0]["facing_frac"] == 1.0


def test_pinmux_zero_candidates_without_af_source():
    """AF 表缺失 → 零候选 + 缺失源登记（不虚构 proposal）。"""
    pmx = audit_cmd.pinmux_check()
    assert pmx["candidates"] == []
    assert pmx["missing_sources"][0]["source"] == "mcu_alternate_function_table"
