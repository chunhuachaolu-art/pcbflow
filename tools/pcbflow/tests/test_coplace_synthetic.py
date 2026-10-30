"""③ 合成板红→绿（FB1 核心门）：≥12 封装人为压红 → 确定性爬山预算内翻绿，
placement-spec §8 布局规范门全过；转换器可重放；确定性双跑 byte-exact。

构造真值（红种子，全部一阶可解）：
  - U2 距 U1 仅 1.1mm（FMC 20 网需 4.1）→ 通道预算红；
  - U7 连 QSPI flash 塞进 U1 体 interior → 体间距红 + QSPI 通道红 + 分区红；
  - C1..C5 去耦散在南远端（>3mm）+ C3 旋转 90° → 就近红 + 方向红；
  - C6（U7 VCC 去耦）远在 U1 内 → 就近红；
  - CIN/COUT 散在功率区外 → 归属半径红 + 分区红；
  - C9 压在 Y1 晶振 3mm 净空内 → 保护区红；
  - R5/R6 远在 USB 区外 → 分区红；
  - U8 模拟件塞进 U1 体 → 体间距红 + 分区红。
锚件 10 件（J1-J5/U1/U2/Y1/Y2/U6）全程锁死。本文件断言模型对构造真值的
行为；阈值/步长改动必须先改真值认知再改这里。
"""

import json

import pytest

from pcbflow import config, coplace_cmd, envelope, geo, hashing

LIB_0402 = "C_0402"
LIB_0603 = "R_0603"
LIB_SOIC8 = "SOIC_8"
LIB_SOT235 = "SOT-23-5"
LIB_SOT236 = "SOT-23-6"
LIB_XTAL = "XTAL_3215"
LIB_QFP = "LQFP24x24"
LIB_TSOP = "TSOP-II-54"
LIB_CONN4 = "CONN_2x2"
LIB_USBC = "USB_C_6pad"


def _mk(ref, lib, pads):
    """pads: [(num, net, x, y, w, h)]（绝对坐标，mm）。"""
    return {"ref": ref, "lib": lib, "x": 0.0, "y": 0.0, "rot": 0.0,
            "pads": [{"ref": ref, "num": n, "net": net, "x": x, "y": y,
                      "w": w, "h": h} for (n, net, x, y, w, h) in pads]}


def _place(fp, x, y, rot=0.0):
    """把局部 pad 图样安放到 (x,y,rot)（旋转仅 90° 步进，整型语义）。"""
    import math
    r = math.radians(rot)
    c, s = math.cos(r), math.sin(r)
    fx = fy = 0.0
    for p in fp["pads"]:
        dx, dy = p["x"], p["y"]
        p["x"] = x + dx * c + dy * s
        p["y"] = y + dy * c - dx * s
    fp["x"], fp["y"], fp["rot"] = x, y, rot
    return fp


def _cap(ref, net, x, y, rot=0.0):
    fp = _mk(ref, LIB_0402, [
        ("1", net, -0.5, 0.0, 0.5, 0.6), ("2", "GND", 0.5, 0.0, 0.5, 0.6)])
    return _place(fp, x, y, rot)


def _res(ref, net, x, y, rot=0.0):
    fp = _mk(ref, LIB_0603, [
        ("1", net, -0.5, 0.0, 0.5, 0.6), ("2", net + "_X", 0.5, 0.0, 0.5, 0.6)])
    return _place(fp, x, y, rot)


def build_synth():
    fp = {}
    # U1（锚件）：东排 FMC+QSPI，南排 电源+USB，北排 OSC（焊盘=局部偏移）
    east = [("E%d" % i, net, 11.7, -8.5 + i * 0.5, 0.6, 0.3)
            for i, net in enumerate([f"F{i}" for i in range(20)]
                                    + [f"Q{i}" for i in range(6)])]
    south = [("S1", "SW_NODE", -11.0, 11.7, 0.3, 0.6),
             ("S2", "3V3", -10.0, 11.7, 0.3, 0.6),
             ("S3", "3V3", -8.0, 11.7, 0.3, 0.6),
             ("S4", "3V3", -6.0, 11.7, 0.3, 0.6),
             ("S5", "3V3", -4.0, 11.7, 0.3, 0.6),
             ("S6", "3V3", -2.0, 11.7, 0.3, 0.6),
             ("S7", "5V", 0.0, 11.7, 0.3, 0.6),
             ("S8", "5V", 2.0, 11.7, 0.3, 0.6),
             ("S9", "USB_DP", 6.0, 11.7, 0.3, 0.6),
             ("S10", "USB_DM", 7.0, 11.7, 0.3, 0.6),
             ("S11", "GND", 9.0, 11.7, 0.3, 0.6)]
    north = [("N1", "OSC_IN", 6.0, -11.7, 0.3, 0.6),
             ("N2", "OSC_OUT", 7.0, -11.7, 0.3, 0.6),
             ("N3", "GND", -10.0, -11.7, 0.3, 0.6),
             ("N4", "GND", -8.0, -11.7, 0.3, 0.6)]
    fp["U1"] = _place(_mk("U1", LIB_QFP, east + south + north), 24.0, 24.0)
    # U2（锚件，种子=FMC 通道仅 1.1mm）：西排 F0..F19 面向 U1，东排 GND
    u2w = [("W%d" % i, f"F{i}", -11.0, -4.75 + i * 0.5, 0.6, 0.3)
           for i in range(20)]
    u2e = [("E%d" % i, "GND", 11.0, -4.75 + i * 0.5, 0.6, 0.3)
           for i in range(20)]
    fp["U2"] = _place(_mk("U2", LIB_TSOP, u2w + u2e), 48.4, 20.25)
    # J1-J4（锚件）：小 2x2 连接器，无边介问题
    for ref, (x, y) in (("J1", (35.0, 66.0)), ("J2", (35.0, 4.0)),
                        ("J3", (66.0, 35.0)), ("J4", (4.0, 35.0))):
        pads = [("1", "GND", -0.635, -1.27, 0.6, 0.6),
                ("2", "GND", 0.635, -1.27, 0.6, 0.6),
                ("3", "GND", -0.635, 1.27, 0.6, 0.6),
                ("4", "GND", 0.635, 1.27, 0.6, 0.6)]
        fp[ref] = _place(_mk(ref, LIB_CONN4, pads), x, y)
    # J5（锚件，USB）+ U6（锚件，ESD）
    fp["J5"] = _place(_mk("J5", LIB_USBC, [
        ("1", "USB_DP", -0.7, -0.5, 0.5, 0.6), ("2", "USB_DM", 0.7, -0.5, 0.5, 0.6),
        ("3", "GND", -0.7, 0.5, 0.5, 0.6), ("4", "GND", 0.7, 0.5, 0.5, 0.6),
        ("5", "VBUS", -1.8, 0.0, 0.5, 0.6), ("6", "GND", 1.8, 0.0, 0.5, 0.6)]),
        52.0, 50.0)
    fp["U6"] = _place(_mk("U6", LIB_SOT236, [
        ("1", "USB_DP", -0.95, 1.35, 0.6, 0.4), ("2", "GND", -0.95, 0.45, 0.6, 0.4),
        ("3", "GND", -0.95, -0.45, 0.6, 0.4), ("4", "USB_DM", 0.95, 1.35, 0.6, 0.4),
        ("5", "GND", 0.95, 0.45, 0.6, 0.4), ("6", "GND", 0.95, -0.45, 0.6, 0.4)]),
        58.0, 46.0)
    # 晶振（锚件）
    fp["Y1"] = _place(_mk("Y1", LIB_XTAL, [
        ("1", "OSC_IN", -1.0, 0.0, 0.6, 0.5), ("2", "OSC_OUT", 1.0, 0.0, 0.6, 0.5)]),
        40.0, 10.0)
    fp["Y2"] = _place(_mk("Y2", LIB_XTAL, [
        ("1", "OSC32_IN", -1.0, 0.0, 0.6, 0.5),
        ("2", "OSC32_OUT", 1.0, 0.0, 0.6, 0.5)]), 43.5, 10.0)
    # 功率链（U3/L1 锚件语义同 Rev-C；CIN/COUT 非锚件）
    fp["U3"] = _place(_mk("U3", LIB_SOIC8, [
        ("1", "5V", -0.95, 1.35, 0.6, 0.4), ("2", "SW_NODE", -0.95, 0.45, 0.6, 0.4),
        ("3", "SW_NODE", -0.95, -0.45, 0.6, 0.4), ("4", "GND", -0.95, -1.35, 0.6, 0.4),
        ("5", "GND", 0.95, -1.35, 0.6, 0.4), ("6", "GND", 0.95, -0.45, 0.6, 0.4),
        ("7", "GND", 0.95, 0.45, 0.6, 0.4), ("8", "5V", 0.95, 1.35, 0.6, 0.4)]),
        10.0, 58.0)
    fp["L1"] = _place(_mk("L1", "L_0805", [
        ("1", "SW_NODE", -1.0, 0.0, 0.8, 0.7), ("2", "3V3", 1.0, 0.0, 0.8, 0.7)]),
        16.0, 58.0)
    # ---- 非锚件（优化变量）---- 种子=人为压红
    fp["C1"] = _cap("C1", "5V", 8.0, 52.0)          # 远离 5V 引脚
    fp["C2"] = _cap("C2", "5V", 12.0, 55.0)
    fp["C3"] = _cap("C3", "3V3", 20.0, 53.0, rot=90.0)  # 方向违例种子
    fp["C4"] = _cap("C4", "3V3", 28.0, 54.0)
    fp["C5"] = _cap("C5", "3V3", 34.0, 52.0)
    fp["CIN"] = _cap("CIN", "5V", 2.0, 50.0)        # 功率区外+归属半径外
    fp["COUT"] = _cap("COUT", "3V3", 30.0, 64.0)
    fp["C9"] = _cap("C9", "GND", 40.5, 9.2)         # 晶振净空入侵者
    fp["R5"] = _res("R5", "USB_DP", 44.0, 40.0)     # USB 区外
    fp["R6"] = _res("R6", "USB_DM", 46.5, 40.0)
    fp["U8"] = _place(_mk("U8", LIB_SOT235, [
        ("1", "ADC_A0", -0.95, 1.35, 0.6, 0.4), ("2", "GND", -0.95, 0.45, 0.6, 0.4),
        ("3", "3V3", -0.95, -0.45, 0.6, 0.4), ("4", "ADC_A1", 0.95, 1.35, 0.6, 0.4),
        ("5", "VREF", 0.95, -0.45, 0.6, 0.4)]), 30.0, 44.0)  # 模拟区外（南）
    u7pads = [("1", "Q0", -0.95, 1.35, 0.6, 0.4), ("2", "Q1", -0.95, 0.45, 0.6, 0.4),
              ("3", "Q2", -0.95, -0.45, 0.6, 0.4), ("4", "Q3", -0.95, -1.35, 0.6, 0.4),
              ("5", "Q4", 0.95, 1.35, 0.6, 0.4), ("6", "3V3", 0.95, 0.45, 0.6, 0.4),
              ("7", "GND", 0.95, -0.45, 0.6, 0.4), ("8", "Q5", 0.95, -1.35, 0.6, 0.4)]
    fp["U7"] = _place(_mk("U7", LIB_SOIC8, u7pads), 44.0, 32.0)  # QSPI 区外
    fp["C6"] = _cap("C6", "3V3", 44.0, 28.0)        # U7 VCC 去耦远置

    board = geo.finalize_board({k: v for k, v in fp.items()})
    for f in board["footprints"].values():
        f["lib"] = next(x["lib"] for x in fp.values() if x["ref"] == f["ref"])

    # U2 可动（设计基线可自由修改；FMC 通道翻绿需 U2 东移）——锚件仅 9 件
    anchors = [{"ref": r} for r in ("J1", "J2", "J3", "J4", "J5",
                                    "U1", "Y1", "Y2", "U6")]
    structures = {
        "anchors": anchors,
        "power_tree": {"rails": ["3V3", "5V"]},
        "buses": [
            {"bus_id": "BUS_FMC", "members": [f"F{i}" for i in range(20)],
             "member_count": 20, "endpoint_refs": ["U1", "U2"],
             "symmetry_class": None},
            {"bus_id": "BUS_QSPI", "members": [f"Q{i}" for i in range(6)],
             "member_count": 6, "endpoint_refs": ["U1", "U7"],
             "symmetry_class": None},
            {"bus_id": "BUS_USB", "members": ["USB_DP", "USB_DM"],
             "member_count": 2,
             "endpoint_refs": ["J5", "R5", "R6", "U1", "U6"],
             "symmetry_class": "usb_pair"},
        ],
    }
    seed = {
        "buses": [
            {"bus_id": "BUS_FMC",
             "endpoints": [{"ref": "U1", "dominant_exit_side": "E"},
                           {"ref": "U2", "dominant_exit_side": "W"}],
             "corridor": {"object": "U1-U2", "demand_width_mm": 4.1,
                          "formula": "C-0053"}},
            {"bus_id": "BUS_QSPI",
             "endpoints": [{"ref": "U1", "dominant_exit_side": "E"},
                           {"ref": "U7", "dominant_exit_side": "W"}],
             "corridor": {"object": "U1-U7", "demand_width_mm": 1.65,
                          "formula": "C-0053"}},
            {"bus_id": "BUS_USB",
             "endpoints": [{"ref": "J5", "dominant_exit_side": "W"},
                           {"ref": "R5", "dominant_exit_side": "E"},
                           {"ref": "R6", "dominant_exit_side": "E"},
                           {"ref": "U1", "dominant_exit_side": "E"},
                           {"ref": "U6", "dominant_exit_side": "W"}],
             "corridor": {"object": "J5-R5-R6-U1-U6", "demand_width_mm": 1.3,
                          "formula": "C-0053"}},
        ],
        "registry_snapshot_hash": "synthetic-seed-hash",
    }
    net_names = sorted({p["net"] for f in fp.values() for p in f["pads"]
                        if p["net"]})
    net_ids = {n: "N%04d" % (i + 1) for i, n in enumerate(net_names)}
    reg_hash = hashing.sha256_bytes(hashing.canonical_json_bytes(net_ids))
    zones = {
        "power_SW": {"refs": ["U3", "L1", "CIN", "COUT"],
                     "rect": [4.0, 52.0, 20.0, 66.0]},
        "qspi_E": {"refs": ["U7", "C6"], "rect": [50.0, 26.0, 68.0, 40.0]},
        "usb_SE": {"refs": ["R5", "R6", "J5"], "rect": [48.0, 44.0, 68.0, 68.0]},
        "decap_U1": {"refs": ["C1", "C2", "C3", "C4", "C5"],
                     "rect": [10.0, 30.0, 30.0, 38.0]},
        "analog_NW": {"refs": ["U8"], "rect": [2.0, 2.0, 10.0, 10.0]},
        "crystal_NE": {"refs": ["Y1", "Y2"], "rect": [36.0, 6.0, 48.0, 14.0]},
        "storage_E": {"refs": ["U2"], "rect": [40.0, 12.0, 68.0, 30.0]},
    }
    ctx = coplace_cmd.build_context(
        board, structures, seed, net_ids, reg_hash,
        zones_declared=zones, channel_keepouts=["BUS_FMC", "BUS_QSPI"],
        board_rect=(0.0, 0.0, 70.0, 70.0),
        power_chain={"buck": "U3", "inductor": "L1",
                     "cin": "CIN", "cout": "COUT"})
    st = coplace_cmd.state_from_board(board)
    return {"board": board, "structures": structures, "seed": seed,
            "ctx": ctx, "st": st, "anchors": [a["ref"] for a in anchors]}


@pytest.fixture(scope="module")
def synth():
    return build_synth()


def test_synth_seeded_red(synth):
    """红种子：≥6 门红且逐门命中构造真值。"""
    ev = coplace_cmd.evaluate(synth["ctx"], synth["st"])
    assert ev["verdict"] == "red"
    assert len(synth["board"]["footprints"]) >= 12
    red = set(ev["hard_fail_gates"])
    assert {"channel_budget", "proximity", "keepout", "zone_purity",
            "orientation"} <= red, red
    chan = {r["bus_id"]: r for r in ev["hard"]["channel_budget"]["detail"]["rows"]}
    assert chan["BUS_FMC"]["gap_mm"] < chan["BUS_FMC"]["demand_mm"]
    assert any(d["ref"] == "C9" for d in ev["hard"]["keepout"]["intrusions"])
    assert any(v["ref"] == "C3" for v in ev["hard"]["orientation"]["deviants"])
    assert len(ev["hard"]["zone_purity"]["violations"]) >= 6


def test_synth_optimize_green_within_budget(synth):
    """FB1 核心门：确定性爬山预算内翻绿 + 布局规范门全过 + 锚件零移动。"""
    ctx = synth["ctx"]
    st, skels, trace = coplace_cmd.optimize(ctx, synth["st"], max_sweeps=45)
    ev = coplace_cmd.evaluate(ctx, st)
    assert ev["hard_fail_gates"] == [], ev["hard_fail_gates"]
    assert ev["verdict"] == "pass", json.dumps(ev["soft"], ensure_ascii=False)
    assert trace["converged"] or trace["sweeps"] < 45
    assert trace["accepted_moves"] > 0
    # 布局规范门（placement §8 六门映射）全过
    for g in ev["placement_gate_map"]:
        assert ev["hard"][g["gate"]]["pass"], g
    # 锚件永不移动（红线）
    for ref in synth["anchors"]:
        assert (st[ref]["x"], st[ref]["y"], st[ref]["rot"]) == \
               (synth["st"][ref]["x"], synth["st"][ref]["y"],
                synth["st"][ref]["rot"]), ref
    # 通道预算逐条复核（FMC 翻绿后 gap ≥ 需求）
    chan = {r["bus_id"]: r for r in ev["hard"]["channel_budget"]["detail"]["rows"]}
    assert chan["BUS_FMC"]["gap_mm"] >= chan["BUS_FMC"]["demand_mm"]
    assert chan["BUS_QSPI"]["gap_mm"] >= chan["BUS_QSPI"]["demand_mm"]
    assert chan["BUS_FMC"]["intruders"] == []
    assert chan["BUS_QSPI"]["intruders"] == []


def test_synth_optimize_deterministic(synth):
    """确定性：同输入双跑（小预算）位姿 byte-exact 一致；无随机/wall-clock 影响。"""
    a = coplace_cmd.optimize(synth["ctx"], synth["st"], max_sweeps=3)
    b = coplace_cmd.optimize(synth["ctx"], synth["st"], max_sweeps=3)
    ka = hashing.canonical_json_bytes(
        {r: a[0][r] for r in sorted(a[0])})
    kb = hashing.canonical_json_bytes(
        {r: b[0][r] for r in sorted(b[0])})
    assert ka == kb
    assert hashing.canonical_json_bytes(a[1]) == hashing.canonical_json_bytes(b[1])
    assert a[2] == b[2]


def test_synth_converter_replay(synth):
    """layout→placement.csv 可重放：转换双跑 byte-exact；重导回放评估仍绿；
    锚件行保真（位置/rot 不变）。"""
    ctx = synth["ctx"]
    st, skels, trace = coplace_cmd.optimize(ctx, synth["st"], max_sweeps=45)
    ev = coplace_cmd.evaluate(ctx, st)
    placements = coplace_cmd.placements_of(ctx, st)
    layout = {"placements": placements}
    csv_a = coplace_cmd.to_placement_csv(layout)
    csv_b = coplace_cmd.to_placement_csv(layout)
    assert csv_a == csv_b
    rows = list(csv_a.decode("utf-8").split("\r\n"))
    assert rows[0] == "ref,x,y,rot,side,zone"
    by_ref = {r.split(",")[0]: r.split(",") for r in rows[1:] if r}
    for ref in synth["anchors"]:
        src = synth["st"][ref]
        assert by_ref[ref][1] == coplace_cmd.fmt_csv(coplace_cmd.uq(src["x"]))
        assert by_ref[ref][3] == str(int(src["rot"]))
    # 重导：CSV → 状态 → 评估仍绿（可重放闭环）
    import csv as _csv
    import io
    back = {r["ref"]: {"x": coplace_cmd.q(float(r["x"])),
                       "y": coplace_cmd.q(float(r["y"])),
                       "rot": int(float(r["rot"]))}
            for r in _csv.DictReader(io.StringIO(csv_a.decode("utf-8"))) }
    st2 = {ref: dict(v, **back.get(ref, {})) for ref, v in st.items()}
    ev2 = coplace_cmd.evaluate(ctx, st2)
    assert ev2["hard_fail_gates"] == []
    assert ev2["verdict"] == "pass"
    proof = coplace_cmd.conversion_proof("x" * 64, "y" * 64, "out/x")
    assert "pending_approval" in proof["execution"]
    assert proof["deterministic"] is True


def test_synth_products_hygiene(synth):
    """产物卫生：layout 无禁区键/绝对路径；geojson 非地理坐标系声明；门映射覆盖 §8。"""
    ctx = synth["ctx"]
    st, skels, trace = coplace_cmd.optimize(ctx, synth["st"], max_sweeps=3)
    ev = coplace_cmd.evaluate(ctx, st)
    layout = {
        "placements": coplace_cmd.placements_of(ctx, st),
        "skeletons": skels,
        "evidence": {"hard_gates": {k: {"pass": v["pass"],
                                        "magnitude_mm": v["magnitude_mm"]}
                                    for k, v in ev["hard"].items()}},
    }
    assert envelope.scan_forbidden_core_fields(layout) == []
    geojson = coplace_cmd._build_geojson(skels, synth["board"])
    cs = geojson["coordinate_system"]
    assert cs["not_geographic"] is True and cs["units"] == "mm"
    assert [g["gate"] for g in coplace_cmd.PLACEMENT_GATE_MAP] == [
        "channel_budget", "proximity", "body_spacing", "orientation",
        "keepout", "zone_purity"]
    assert config.CPLACE_STEPS_MM == (0.5, 1.0, 2.0)
