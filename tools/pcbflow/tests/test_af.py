"""AF 表转写与 pin-swap 候选（AF 会话 = 第 13 会话）。

覆盖：identify_net 识别规则、互惠同组候选枚举（含排除项/排序/schema）、
真实 AF 表完整性（skipif 产物缺失）、audit --af-table opt-in 集成、
默认路径对冻结 a3 核心产物零字节扰动（回归 pin）、红线字段扫描。
"""

import os

import pytest

from pcbflow import af_table, audit_cmd, config, envelope, hashing

AF_TABLE = os.path.join(config.PCBFLOW_ROOT, "out", "revc-af",
                        "mcu-af-table-full.json")
A3_DIR = os.path.join(config.PCBFLOW_ROOT, "out", "revc-a3")


def _pin(pos, name, sigs):
    return {"position": pos, "name": name, "type": "I/O",
            "signals": [{"signal": s, "af": af} for s, af in sigs]}


def _table(pins):
    return {"schema_version": "1.0",
            "artifact_kind": af_table.AF_TABLE_KIND,
            "mcu": {"pin_count": len(pins)}, "pins": pins}


# ---- identify_net 识别规则 ----------------------------------------------------
def _pa1_pin():
    return _pin(1, "PA1", [("SPI1_SCK", 5), ("USART1_TX", 7),
                           ("GPIO", None), ("EVENTOUT", 15)])


def test_identify_exact_punct_norm():
    r = af_table.identify_net("SPI1_SCK", _pa1_pin())
    assert (r["kind"], r["signal"]) == ("exact", "SPI1_SCK")
    r = af_table.identify_net("USART_1TX", _pa1_pin())
    assert (r["kind"], r["signal"]) == ("punct_norm", "USART1_TX")


def test_identify_gpio_locked_and_mismatch():
    r = af_table.identify_net("GPIO_PA1", _pa1_pin())
    assert (r["kind"], r["signal"]) == ("gpio_locked", None)
    r = af_table.identify_net("GPIO_PB1", _pa1_pin())
    assert r["kind"] == "gpio_mismatch" and "PB1" in r["detail"]


def test_identify_unconnected_power_unidentified():
    r = af_table.identify_net("unconnected-(U1-PA1-Pad1)", _pa1_pin())
    assert r["kind"] == "unconnected" and r["detail"] == "PA1"
    assert af_table.identify_net("3V3", _pa1_pin())["kind"] == "power_special"
    r = af_table.identify_net("QSPI_CLK", _pa1_pin())
    assert r["kind"] == "unidentified" and r["signal"] is None


# ---- 互惠同组候选枚举 ----------------------------------------------------------
def _synth_table():
    return _table([
        _pin(1, "PA1", [("SPI1_SCK", 5), ("USART1_TX", 7), ("EVENTOUT", 15)]),
        _pin(2, "PA2", [("SPI1_SCK", 5), ("USART1_TX", 7)]),
        _pin(3, "PA3", [("USART1_TX", 7), ("SPI1_MISO", 6)]),
        _pin(4, "PA4", [("SPI1_MISO", 6)]),
    ])


SWAP_KEYS = {"candidate_id", "signal_or_bus", "from_ref", "from_pin",
             "from_net", "to_ref", "to_pin", "to_net", "allowed_by_source",
             "source_refs", "requires_schematic_edit", "requires_firmware_edit",
             "requires_pair_update", "affected_constraints", "delta_metrics",
             "cost_vector", "evidence", "af_numbers", "approval", "status"}


def test_enumerate_mutual_swap_schema():
    pins = [{"num": 1, "net": "SPI1_SCK"}, {"num": 2, "net": "USART1_TX"}]
    rows, ident = af_table.enumerate_swap_candidates(_synth_table(), pins)
    assert len(rows) == 1
    r = rows[0]
    assert set(r.keys()) == SWAP_KEYS
    assert (r["candidate_id"], r["from_pin"], r["from_net"],
            r["to_pin"], r["to_net"]) == ("SW-0001", "PA1", "SPI1_SCK",
                                          "PA2", "USART1_TX")
    assert r["allowed_by_source"] is True
    assert r["status"] == "proposal_only" and r["approval"] == "pending"
    assert r["requires_schematic_edit"] and r["requires_firmware_edit"]
    assert set(r["cost_vector"]) == {"schematic_edit", "firmware_mux",
                                     "external_connector", "length_timing",
                                     "escape", "via", "congestion",
                                     "review_risk"}
    assert r["af_numbers"]["cross"] == {"p1_has_s2_af": 7, "p2_has_s1_af": 5}


def test_enumerate_one_sided_no_candidate():
    pins = [{"num": 3, "net": "USART1_TX"}, {"num": 4, "net": "SPI1_MISO"}]
    rows, ident = af_table.enumerate_swap_candidates(_synth_table(), pins)
    assert rows == []
    assert ident["one_sided_pin_supports"] == 1


def test_enumerate_excludes_same_net_power_gpio():
    pins = [{"num": 1, "net": "SPI1_SCK"}, {"num": 2, "net": "SPI1_SCK"},
            {"num": 3, "net": "3V3"}]
    rows, ident = af_table.enumerate_swap_candidates(
        _synth_table() | {"pins": _synth_table()["pins"] +
                          [_pin(5, "PA5", [("SPI1_SCK", 5)])]},
        pins + [{"num": 5, "net": "SPI1_SCK"}])
    assert rows == []
    assert ident["same_net_pairs_excluded"] >= 1
    assert ident["kinds"].get("power_special") == 1


def test_enumerate_connector_cost():
    pins = [{"num": 1, "net": "SPI1_SCK"}, {"num": 2, "net": "USART1_TX"}]
    rows, _ = af_table.enumerate_swap_candidates(_synth_table(), pins,
                                                 connector_nets={"SPI1_SCK"})
    assert rows[0]["cost_vector"]["external_connector"] == 1
    rows, _ = af_table.enumerate_swap_candidates(_synth_table(), pins)
    assert rows[0]["cost_vector"]["external_connector"] == 0


def test_enumerate_evidence_ranking_deterministic():
    table = _table([
        _pin(1, "PA1", [("SPI1_SCK", 5), ("USART1_TX", 7)]),
        _pin(2, "PA2", [("SPI1_SCK", 5), ("USART1_TX", 7)]),
        _pin(3, "PA3", [("SPI1_MISO", 6), ("USART1_RX", 8)]),
        _pin(4, "PA4", [("SPI1_MISO", 6), ("USART1_RX", 8)]),
    ])
    pins = [{"num": 1, "net": "SPI1_SCK"}, {"num": 2, "net": "USART1_TX"},
            {"num": 3, "net": "SPI1_MISO"}, {"num": 4, "net": "USART1_RX"}]
    ev = {"SPI1_MISO": ["f3_failed", "opens_predicted"]}
    rows, _ = af_table.enumerate_swap_candidates(table, pins, evidence=ev)
    assert [r["candidate_id"] for r in rows] == ["SW-0001", "SW-0002"]
    assert rows[0]["evidence"]["from_net_flags"] == ["f3_failed",
                                                     "opens_predicted"]
    rows2, _ = af_table.enumerate_swap_candidates(table, pins, evidence=ev)
    assert rows == rows2


# ---- 真实 AF 表（本会话产物；缺失则跳过） --------------------------------------
@pytest.mark.skipif(not os.path.exists(AF_TABLE),
                    reason="out/revc-af/mcu-af-table-full.json 不存在")
def test_real_table_anchors_and_eventout():
    table = af_table.load_af_table(AF_TABLE)
    assert table["mcu"]["pin_count"] == 176
    by_pos = af_table.pins_by_position(table)
    assert by_pos[1]["name"] == "PE2"
    af1 = {s["signal"]: s["af"] for s in by_pos[1]["signals"]}
    assert af1["QUADSPI_BK1_IO2"] == 9 and af1["EVENTOUT"] == 15
    af24 = {s["signal"]: s["af"] for s in by_pos[24]["signals"]}
    assert af24["QUADSPI_BK1_IO3"] == 9
    assert by_pos[24]["name"] == "PF6" and by_pos[26]["name"] == "PF8"


@pytest.mark.skipif(not os.path.exists(AF_TABLE),
                    reason="out/revc-af/mcu-af-table-full.json 不存在")
def test_real_table_identify_anchor_pads():
    table = af_table.load_af_table(AF_TABLE)
    by_pos = af_table.pins_by_position(table)
    assert af_table.identify_net("GPIO_PE2", by_pos[1])["kind"] == "gpio_locked"
    assert af_table.identify_net("unconnected-(U1-PG10-Pad153)",
                                 by_pos[153])["kind"] == "unconnected"


# ---- audit opt-in 集成与默认路径零扰动 ----------------------------------------
def test_pinmux_legacy_zero_candidates_unchanged():
    pmx = audit_cmd.pinmux_check()
    assert set(pmx.keys()) == {"candidates", "missing_sources", "mechanism"}
    assert pmx["candidates"] == []
    assert pmx["missing_sources"][0]["source"] == "mcu_alternate_function_table"


@pytest.mark.skipif(not os.path.exists(os.path.join(A3_DIR, "audit.json")),
                    reason="out/revc-a3 冻结件不在")
def test_flag_off_core_products_match_frozen_a3():
    """默认路径（无 --af-table）核心产物必须与冻结 a3 逐字节一致。"""
    products = audit_cmd.build_products()
    for name, fname in (("audit", "audit.json"),
                        ("pin_swap", "pin-swap.json"),
                        ("skeleton_seed", "skeleton-seed.json")):
        assert products[name]["sha256"] == hashing.sha256_file(
            os.path.join(A3_DIR, fname)), name


@pytest.mark.skipif(not os.path.exists(AF_TABLE),
                    reason="out/revc-af/mcu-af-table-full.json 不存在")
def test_af_mode_audit_consumes_table():
    products = audit_cmd.build_products(af_table_path=AF_TABLE,
                                        out_dir_rel="out/revc-af")
    a = products["audit"]["obj"]
    c1 = next(c for c in a["checks"] if c["check_id"] == "C1_pin_mux_swap")
    assert c1["metrics"]["candidates"] == 0 and c1["verdict"] == "pass"
    assert c1["blockers"] == []
    ps = products["pin_swap"]["obj"]
    assert ps["status"] == "proposal_only"
    assert ps["af_table_basis"]["sha256"] == hashing.sha256_file(AF_TABLE)
    assert ps["identification"]["kinds"]["exact"] == 89
    assert ps["identification"]["mismatches"] == []
    assert ps["candidate_count"] == len(ps["candidates"]) == 0
    env = products["envelope"]["obj"]
    assert any(d["id"] == "af_table_consumed" for d in env["diagnostics"])
    assert any(i["path"].endswith("mcu-af-table-full.json")
               for i in env["inputs"])
    assert env["metrics"]["pin_swap_candidates"] == 0


@pytest.mark.skipif(not os.path.exists(AF_TABLE),
                    reason="out/revc-af/mcu-af-table-full.json 不存在")
def test_af_mode_products_deterministic_and_clean():
    p1 = audit_cmd.build_products(af_table_path=AF_TABLE,
                                  out_dir_rel="out/revc-af")
    p2 = audit_cmd.build_products(af_table_path=AF_TABLE,
                                  out_dir_rel="out/revc-af")
    for name in ("audit", "pin_swap", "skeleton_seed", "envelope"):
        assert p1[name]["sha256"] == p2[name]["sha256"], name
        assert envelope.scan_forbidden_core_fields(p1[name]["obj"]) == []


@pytest.mark.skipif(not os.path.exists(AF_TABLE),
                    reason="out/revc-af/mcu-af-table-full.json 不存在")
def test_cli_audit_af_wiring():
    from pcbflow import cli
    rc = cli.main(["audit", "--select", "summary", "--out-dir", "out/revc-af",
                   "--af-table", AF_TABLE])
    assert rc == config.EXIT_OK
