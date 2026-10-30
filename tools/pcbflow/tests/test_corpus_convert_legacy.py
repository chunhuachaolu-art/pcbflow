"""corpus_convert_legacy 单测：合成 fixture + corpus-r2-r1 两真实板 smoke。

真实板只读（datasets/ 零写入）。计数断言口径（2026-09-12 实测）：
  - segments/vias/zones/footprints 与 metadata.json evidence 逐一相等；
  - copper 层数：teres 6==metadata.layers；ice40 文件实测 4，metadata
    layers=2 是入库工具正则少计带引号自定义层名（"In1(GND).Cu"）——
    按文件事实断言 4，并 pin 住 metadata 侧数字，差异不硬凑；
  - 网声明数：解析器 475/97 == 板内 (general (nets ...)) 自声明；
    metadata.net_count 285/17 是"只数带引号网名"的入库正则口径——
    同样 pin 两侧数字如实登记差异。
"""

from __future__ import annotations

import functools
import json
import pathlib

import pytest

from pcbflow import corpus_convert_legacy as legacy
from pcbflow import sexpr_min

REPO = pathlib.Path(__file__).resolve().parents[1]
RAW = REPO / "datasets" / "corpus-r2-r1" / "raw"

BOARD_PATHS = {
    "teres": RAW / "OLIMEX__teres-pcb1-a64-main-rev-c"
    / "TERES_PCB1-A64-MAIN_Rev.C.kicad_pcb",
    "ice40": RAW / "OLIMEX__ice40hx1k-evb-rev-b"
    / "iCE40HX1K-EVB_Rev_B.kicad_pcb",
}

# ---------------------------------------------------------------------------
# 合成 fixture（最小 legacy 文本；形态取自两真实板实测）
# ---------------------------------------------------------------------------

FIX_20171114 = """\
(kicad_pcb (version 20171114) (host pcbnew "(2017-11-22 revision 78366f8f0)-master")

  (general
    (thickness 1.2)
    (tracks 0)
    (modules 2)
    (nets 3)
  )

  (page A2)
  (layers
    (0 F.Cu mixed)
    (1 In1.Cu power)
    (31 B.Cu mixed)
    (32 B.Adhes user hide)
    (44 Edge.Cuts user)
  )

  (setup
    (last_trace_width 0.127)
    (trace_clearance 0.127)
    (via_size 0.327)
  )

  (net 0 "")
  (net 1 +5V)
  (net 2 "Net-(C1-Pad2)")

  (module OLIMEX_RLC-FP:C_0603 locked (layer F.Cu) (tedit 58CA8E1C)
    (at 10 20 90)
    (fp_text reference C1 (at 0 -1) (layer F.SilkS))
    (fp_text value 100n (at 0 1) (layer F.Fab))
    (pad 1 smd rect (at -0.5 0 90) (size 0.5 0.5) (layers F.Cu F.Paste F.Mask)
      (net 1 +5V))
    (pad 2 smd rect (at 0.5 0 90) (size 0.5 0.5) (layers F.Cu F.Paste F.Mask)
      (net 2 "Net-(C1-Pad2)"))
    (pad 3 thru_hole circle (at 0 0) (size 1 1) (drill oval 1 4)
      (layers *.Cu *.Mask))
  )

  (module OLIMEX_IC-FP:U1 (layer B.Cu)
    (at 30 40)
    (fp_text reference U1 (at 0 0) (layer B.SilkS))
    (pad A1 smd rect (at 0 0) (size 0.25 1.2) (layers B.Cu B.Paste B.Mask)
      (net 2 "Net-(C1-Pad2)"))
    (pad A2 thru_hole rect (at 2 0) (size 1.5 1.5) (drill 0.6)
      (layers *.Cu *.Mask)
      (net 0 ""))
  )

  (segment (start 10 20) (end 11 21) (width 0.254) (layer F.Cu) (net 1))
  (segment (start 11 21) (end 12 22) (width 0.254) (layer F.Cu) (net 1))
  (via (at 11 21) (size 0.327) (drill 0.2) (layers F.Cu B.Cu) (net 1))
  (arc (start 0 0) (end 1 1) (angle 90) (layer Edge.Cuts) (width 0.1))
  (zone (net 0) (net_name "") (layer F.Cu) (hatch edge 0.5)
    (connect_pads (clearance 0.127))
    (min_thickness 0.2)
    (fill yes (thermal_gap 0.4))
    (polygon (pts (xy 0 0) (xy 5 0) (xy 5 5) (xy 0 5))))
  (zone (net 1) (net_name +5V) (layer B.Cu) (hatch edge 0.5)
    (min_thickness 0.2)
    (fill yes)
    (polygon (pts (xy 1 1) (xy 6 1) (xy 6 6) (xy 1 6))))
)
"""

FIX_V4 = """\
(kicad_pcb (version 4) (host pcbnew 4.0.2+dfsg1-stable)

  (general
    (links 3)
    (no_connects 0)
    (area 9.9 9.9 40.1 40.1)
    (thickness 1.5)
    (drawings 0)
    (tracks 0)
    (zones 0)
    (modules 1)
    (nets 3)
  )

  (page A4)
  (layers
    (0 F.Cu signal)
    (1 "In1(GND).Cu" signal hide)
    (2 "In2(PWR).Cu" signal hide)
    (31 B.Cu signal hide)
    (44 Edge.Cuts user)
  )

  (setup
    (last_trace_width 0.2032)
    (via_size 0.45)
    (pcbplotparams
      (layerselection 0x0000000000000000)
    )
  )

  (net 0 "")
  (net 1 GND)
  (net 2 /BUT1)

  (module OLIMEX_IC-FP:VQFP100 (layer F.Cu) (tedit 56B1B30F) (tstamp 56BB24F3)
    (at 25 25)
    (attr smd)
    (fp_text reference U1 (at -7.6 8.9) (layer F.SilkS))
    (pad 1 smd rect (at -6 7.8 180) (size 0.25 1.2) (layers F.Cu F.Paste F.Mask)
      (net 2 /BUT1))
    (pad 2 thru_hole circle (at 0 0) (size 1.5 1.5) (drill 0.6)
      (layers *.Cu *.Mask) (net 1 GND))
    (pad 3 smd rect (at 6 -7.8) (size 0.25 1.2) (layers F.Cu F.Paste F.Mask))
  )

  (segment (start 25 25) (end 26 26) (width 0.2032) (layer F.Cu) (net 1))
  (via (at 26 26) (size 0.45) (drill 0.3) (layers F.Cu B.Cu) (net 1))
)
"""

# 无名编号网 / 无名焊盘网（推测形态；两真实板实测 0 例——行为要 pin 住）
FIX_NAMELESS = """\
(kicad_pcb (version 20171114) (host pcbnew x)
  (layers (0 F.Cu signal) (31 B.Cu signal))
  (net 0 "")
  (net 1 GND)
  (net 2)
  (module L:M (layer F.Cu)
    (at 0 0)
    (fp_text reference X1 (at 0 0) (layer F.SilkS))
    (pad 1 thru_hole circle (at 0 0) (size 1 1) (drill 0.6)
      (layers *.Cu *.Mask) (net 3))
  )
)
"""


# ---------------------------------------------------------------------------
# 合成 fixture 单测
# ---------------------------------------------------------------------------

def test_contract_keys_and_version_20171114():
    m = legacy.parse_legacy_board(FIX_20171114)
    assert all(k in m for k in legacy.CONTRACT_KEYS)
    assert m["board_version"] == "20171114"
    assert m["host"] == 'pcbnew (2017-11-22 revision 78366f8f0)-master'


def test_layers_20171114_mixed_type_and_flags():
    m = legacy.parse_legacy_board(FIX_20171114)
    assert [(l["index"], l["name"], l["type"]) for l in m["layers"]] == [
        (0, "F.Cu", "mixed"), (1, "In1.Cu", "power"), (31, "B.Cu", "mixed"),
        (32, "B.Adhes", "user"), (44, "Edge.Cuts", "user")]
    # copper 判定沿用 0..31 编号（KiCad4/5 口径）
    assert [l["index"] for l in m["copper_layers"]] == [0, 1, 31]
    assert m["layer_entry_flags"] == {32: ["hide"]}


def test_nets_sorted_with_net0_empty_20171114():
    m = legacy.parse_legacy_board(FIX_20171114)
    assert m["nets"] == [
        {"net_id": 0, "name": ""},
        {"net_id": 1, "name": "+5V"},
        {"net_id": 2, "name": "Net-(C1-Pad2)"},
    ]
    assert m["net_declaration_source"] == "top_level"


def test_modules_locked_refs_and_pads():
    m = legacy.parse_legacy_board(FIX_20171114)
    assert [x["ref"] for x in m["modules"]] == ["C1", "U1"]
    assert m["module_locked_count"] == 1
    c1 = m["modules"][0]
    assert c1["lib"] == "OLIMEX_RLC-FP:C_0603"
    assert c1["layer"] == "F.Cu"
    assert c1["at"] == ["10", "20", "90"]
    p1, p2, p3 = c1["pads"]
    assert p1["net"] == {"net_id": 1, "name": "+5V"}
    # 网名引号可选：quoted 与 unquoted 同样取值
    assert p2["net"] == {"net_id": 2, "name": "Net-(C1-Pad2)"}
    # oval drill 多 token 如实保留
    assert p3["drill"] == ["oval", "1", "4"]
    assert p3["net"] is None
    assert p3["layers"] == ["*.Cu", "*.Mask"]
    u1 = m["modules"][1]
    assert u1["pads"][1]["net"] == {"net_id": 0, "name": ""}


def test_route_counts_20171114():
    m = legacy.parse_legacy_board(FIX_20171114)
    assert (m["segment_count"], m["via_count"], m["arc_count"],
            m["zone_count"]) == (2, 1, 1, 2)
    assert m["parse_warnings"] == []


def test_v4_quoted_custom_layer_names_and_general():
    m = legacy.parse_legacy_board(FIX_V4)
    assert m["board_version"] == "4"
    assert m["host"] == "pcbnew 4.0.2+dfsg1-stable"
    # v4 板层名可带引号自定义裸名；hide 旗标入 layer_entry_flags
    assert [(l["index"], l["name"], l["type"]) for l in m["layers"]] == [
        (0, "F.Cu", "signal"), (1, "In1(GND).Cu", "signal"),
        (2, "In2(PWR).Cu", "signal"), (31, "B.Cu", "signal"),
        (44, "Edge.Cuts", "user")]
    assert m["layer_entry_flags"] == {
        1: ["hide"], 2: ["hide"], 31: ["hide"]}
    assert [l["name"] for l in m["copper_layers"]] == [
        "F.Cu", "In1(GND).Cu", "In2(PWR).Cu", "B.Cu"]
    # general 标量子键规则与 kicad5 同构：len==2 才收（(area ...) 5 项跳过）
    assert m["general"] == {"links": "3", "no_connects": "0",
                            "thickness": "1.5", "drawings": "0",
                            "tracks": "0", "zones": "0", "modules": "1",
                            "nets": "3"}
    assert m["setup"] == {"last_trace_width": "0.2032", "via_size": "0.45"}


def test_v4_pads_oval_drill_and_unbound():
    m = legacy.parse_legacy_board(FIX_V4)
    pads = m["modules"][0]["pads"]
    assert pads[0]["net"] == {"net_id": 2, "name": "/BUT1"}
    assert pads[1]["drill"] == ["0.6"]
    assert pads[1]["net"] == {"net_id": 1, "name": "GND"}
    assert pads[2]["net"] is None
    assert (m["segment_count"], m["via_count"], m["arc_count"],
            m["zone_count"]) == (1, 1, 0, 0)


def test_nested_nets_block_direct_child_only():
    text = """\
(kicad_pcb (version 20171114) (host pcbnew x)
  (general (nets 2))
  (layers (0 F.Cu signal) (31 B.Cu signal))
  (nets (net 1 GND) (net 2 VCC))
)"""
    m = legacy.parse_legacy_board(text)
    # 判据=直接子节点：(general (nets 2)) 标量块不得触发 nested_block
    assert m["net_declaration_source"] == "nested_block"
    assert m["nets"] == [{"net_id": 1, "name": "GND"},
                         {"net_id": 2, "name": "VCC"}]


def test_nested_nets_block_unknown_entry_fails_closed():
    text = """\
(kicad_pcb (version 4) (host pcbnew x)
  (layers (0 F.Cu signal))
  (nets (net (ordinal 1) (name GND)))
)"""
    with pytest.raises(ValueError, match="not parseable"):
        legacy.parse_legacy_board(text)


def test_nameless_numbered_nets_recorded_not_invented():
    m = legacy.parse_legacy_board(FIX_NAMELESS)
    assert {"net_id": 2, "name": ""} in m["nets"]
    assert "net_declaration_without_name:2" in m["parse_warnings"]
    # 焊盘 (net 3) 无名：不造名，net 置 None + warning
    pad = m["modules"][0]["pads"][0]
    assert pad["net"] is None
    assert "pad_net_without_name:X1.1" in m["parse_warnings"]


def test_version_gate_mutually_exclusive():
    with pytest.raises(ValueError, match="outside legacy gate"):
        legacy.parse_legacy_board(
            '(kicad_pcb (version 20171130) (host pcbnew 5.1.4))')
    with pytest.raises(ValueError, match="outside legacy gate"):
        legacy.parse_legacy_board('(kicad_pcb (version 20260624))')
    with pytest.raises(ValueError, match="outside legacy gate"):
        legacy.parse_legacy_board('(kicad_pcb)')


def test_fail_closed_on_broken_text_and_two_roots():
    with pytest.raises(sexpr_min.SexprError):
        legacy.parse_legacy_board('(kicad_pcb (version 4)')
    with pytest.raises(ValueError, match="exactly one kicad_pcb root"):
        legacy.parse_legacy_board('(kicad_pcb (version 4)) '
                                  '(kicad_pcb (version 4))')


def test_pure_function_determinism():
    a = legacy.parse_legacy_board(FIX_V4)
    b = legacy.parse_legacy_board(FIX_V4)
    assert a == b


# ---------------------------------------------------------------------------
# 两真实板 smoke（datasets 只读；计数 vs metadata.json evidence）
# ---------------------------------------------------------------------------

@functools.lru_cache(maxsize=None)
def _parse_real(tag: str):
    text = BOARD_PATHS[tag].read_text(encoding="utf-8", errors="replace")
    return legacy.parse_legacy_board(text)


def _meta(tag: str) -> dict:
    return json.loads(
        (BOARD_PATHS[tag].parent / "metadata.json").read_text(
            encoding="utf-8"))


@pytest.mark.parametrize("tag", ["teres", "ice40"])
def test_real_board_smoke_evidence_counts(tag):
    m = _parse_real(tag)
    ev = _meta(tag)["evidence"]
    assert m["segment_count"] == ev["segments"]
    assert m["via_count"] == ev["vias"]
    assert m["zone_count"] == ev["zones"]
    assert len(m["modules"]) == ev["footprints"]
    assert m["parse_warnings"] == []


@pytest.mark.parametrize("tag,host_prefix", [
    ("teres", "pcbnew (2017-11-22 revision 78366f8f0)-master"),
    ("ice40", "pcbnew 4.0.2+dfsg1-stable")])
def test_real_board_smoke_version_host(tag, host_prefix):
    m = _parse_real(tag)
    assert m["board_version"] == _meta(tag)["kicad_version_token"]
    assert m["host"] == host_prefix
    assert m["net_declaration_source"] == "top_level"


def test_teres_copper_layers_match_metadata():
    m = _parse_real("teres")
    assert len(m["copper_layers"]) == 6
    assert len(m["copper_layers"]) == _meta("teres")["layers"]
    assert [l["name"] for l in m["copper_layers"]] == [
        "F.Cu", "In1.Cu", "In2.Cu", "In3.Cu", "In4.Cu", "B.Cu"]


def test_ice40_copper_layers_file_truth_metadata_agreement():
    m = _parse_real("ice40")
    # 文件层表实测 4 铜层（F.Cu / "In1(GND).Cu" / "In2(PWR).Cu" / B.Cu）。
    # 历史：metadata 曾记 2（入库正则少计带引号自定义层名），B2 工单钉住
    # 该缺口后由 2026-09-12 收口校准批修正为 4（metadata+manifest 同步）。
    # 本测试现断言两者一致；若任一侧再漂移，此处如实响铃。
    assert len(m["copper_layers"]) == 4
    assert _meta("ice40")["layers"] == 4


@pytest.mark.parametrize("tag,general_nets", [
    ("teres", 475), ("ice40", 97)])
def test_real_board_net_declarations_match_board_self_declaration(tag,
                                                                  general_nets):
    m = _parse_real(tag)
    # 解析器口径=全部顶层网声明；与板内 (general (nets N)) 自声明一致
    assert m["general"]["nets"] == str(general_nets)
    assert len(m["nets"]) == general_nets
    assert [n["net_id"] for n in m["nets"]] == list(range(general_nets))


@pytest.mark.parametrize("tag,metadata_net_count", [
    ("teres", 285), ("ice40", 17)])
def test_real_board_metadata_net_count_kanou_gap_pinned(tag, metadata_net_count):
    # metadata.net_count = 入库正则"只数带引号网名"口径（285/17）；
    # 解析器=全部声明（475/97）。两侧数字 pin 住，差异如实登记不硬凑。
    m = _parse_real(tag)
    assert _meta(tag)["net_count"] == metadata_net_count
    assert len(m["nets"]) > metadata_net_count


def test_teres_modules_refs_and_pads_spot():
    m = _parse_real("teres")
    # ref 均为 str；图形类 module（LOGO/基准点）实测 reference=""（10 例，
    # 如 Fiducial1x3_transp）——与 parse_kicad5_board 同口径：空串保留不告警
    assert all(isinstance(x["ref"], str) for x in m["modules"])
    assert sum(1 for x in m["modules"] if x["ref"] == "") == 10
    assert m["module_locked_count"] == 46
    refs = {x["ref"] for x in m["modules"]}
    assert {"U6", "eDP1", "USB3"} <= refs
    pad_total = sum(len(x["pads"]) for x in m["modules"])
    assert pad_total == 2118


def test_ice40_modules_and_custom_layer_names_spot():
    m = _parse_real("ice40")
    assert all(isinstance(x["ref"], str) for x in m["modules"])
    assert sum(1 for x in m["modules"] if x["ref"] == "") == 7
    assert m["module_locked_count"] == 1
    refs = {x["ref"] for x in m["modules"]}
    assert "U4" in refs
    pad_total = sum(len(x["pads"]) for x in m["modules"])
    assert pad_total == 348
    names = {l["name"] for l in m["layers"]}
    assert {"In1(GND).Cu", "In2(PWR).Cu"} <= names
