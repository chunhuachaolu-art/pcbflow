"""合成留出集（SPEC §5/§6：不参与 Rev-C 调参的独立测试集）。

自包含合成板：14 封装 / 26 网。构造真值：
  - 种子故障 1：轨网 RAIL 在两侧引脚场全被电容排围死（≥4 transit 焊盘全堵）
    → 逃逸检查必须判网级致命；
  - 种子故障 2：窄走廊 BUS_C（6 网过 1mm 净空）→ C-0053 预算缺口 → 成员网致命；
  - 健康网：GPIO 长/短网、充裕走廊 BUS_B → 不得被标架构致命（留出集 FP=0）。
本文件断言的是模型对构造真值的正确行为，阈值改动必须先改真值认知再改这里。
"""

import pytest

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
    """双排芯片 + 两端 GND 填充列：北排焊盘单侧 [N]（自包含复制，见 test_audit_units）。"""
    nn = ["GND"] + list(north_nets) + ["GND"]
    ss = ["GND"] + list(south_nets) + ["GND"]
    n = _row("t", nn, x0 - dx, y_north, dx)["pads"]
    s = _row("t", ss, x0 - dx, y_south, dx)["pads"]
    for p in s:
        p["num"] = str(100 + int(p["num"]))
    return _mk_from_pads(ref, n + s)


@pytest.fixture(scope="module")
def holdout():
    """合成板：U1(西，东排+南排) + J1(东) + J2(南) + U2/U1N(北) + 电容排。"""
    bus_b = [f"B{i}" for i in range(8)]        # U1 E → J1 W（充裕走廊 ~8.5mm）
    bus_c = [f"C{i}" for i in range(6)]        # U1 S → J2 N（~0.4mm 窄缝）
    gpio = [f"GPIO_{i}" for i in range(6)]     # U1 S → J2（跨窄缝的非总线网）
    rail = ["RAIL"] * 5
    u1_e_pads = _row("t", bus_b, 12.0, 16.0, 0.5)["pads"]        # U1 东排
    u1_s_pads = _row("t", bus_c + gpio, 4.0, 24.0, 0.5)["pads"]  # U1 南排
    for p in u1_s_pads:                     # 南排编号 +100（(ref,num) 键禁撞号）
        p["num"] = str(100 + int(p["num"]))
    footprints = {
        "U1": _mk_from_pads("U1", u1_e_pads + u1_s_pads),
        "J1": _row("J1", bus_b, 24.0, 16.0, 0.5),           # 东，距 U1 东排 ~8.5mm
        "J2": _row("J2", bus_c + gpio, 4.0, 25.0, 0.5),     # 南，距 U1 南排 ~0.4mm
        # U2：双排芯片，北排=Rail×5（bbox 北缘→单侧 [N]），南排 GND 填充
        "U2": _two_row_chip("U2", rail, ["GND"] * 5, 10.0, 6.0, 16.0),
        # 远端 RAIL 端点：距 U2 北向带外（4.5mm > 3mm 带深）→ U2 RAIL 焊盘为 transit
        "U1N": _row("U1N", rail, 4.0, 10.5, 0.5),
        # CAPN 盖住 U2 北排信号焊盘 x=10..14（7 只 9.2..15.2）
        "CAPN": _row("CAPN", ["GND"] * 7, 9.2, 4.0, 1.0),
        "CAPS": _row("CAPS", ["GND"] * 5, 4.2, 26.0, 0.5),  # 压 U1 南排上侧
    }
    board = geo.finalize_board(footprints)
    # nets 字典仅 BUS_B 需要（escape/corridor 检查从板焊盘自取连接性）
    nets = {n: [{"ref": "U1", "pin": str(i + 1)}, {"ref": "J1", "pin": str(i + 1)}]
            for i, n in enumerate(bus_b)}
    structures = {"buses": [
        {"bus_id": "BUS_B", "members": bus_b, "member_count": 8,
         "endpoint_refs": ["U1", "J1"]},
        {"bus_id": "BUS_C", "members": bus_c, "member_count": 6,
         "endpoint_refs": ["U1", "J2"]},
    ]}
    return {"board": board, "nets": nets, "bus_b": bus_b, "bus_c": bus_c,
            "gpio": gpio, "structures": structures}


def test_holdout_seeded_rail_escape_fatal(holdout):
    esc = audit_cmd.escape_check(holdout["board"], lambda n: None)
    assert "RAIL" in esc["escape_fatal_nets"]


def test_holdout_seeded_corridor_deficit_fatal(holdout):
    corb = audit_cmd.corridor_budget_check(holdout["board"], holdout["structures"])
    by = {c["bus_id"]: c for c in corb["corridors"]}
    assert by["BUS_C"]["deficit"] and by["BUS_C"]["fatal"]
    assert not by["BUS_B"]["fatal"]
    assert set(corb["fatal_nets"]) == set(holdout["bus_c"])


def test_holdout_healthy_nets_not_fatal(holdout):
    """留出集 FP=0：健康 GPIO/充裕总线网不得标架构致命。"""
    esc = audit_cmd.escape_check(holdout["board"], lambda n: None)
    corb = audit_cmd.corridor_budget_check(holdout["board"], holdout["structures"])
    fatal = set(esc["escape_fatal_nets"]) | set(corb["fatal_nets"])
    healthy = set(holdout["gpio"]) | set(holdout["bus_b"])
    assert not fatal & healthy, sorted(fatal & healthy)


def test_holdout_deficit_certificate_content(holdout):
    """证书形态：被围死的场给出 demand/supply 型证据（X 网需逃逸 Y 通道）。"""
    esc = audit_cmd.escape_check(holdout["board"], lambda n: None)
    assert esc["fields"]["U2|N"]["has_deficit"]
    f = esc["fields"]["U2|N"]
    assert f["demand_transit_nets"] == 1 and f["supply_clear_channels"] == 0
