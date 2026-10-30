"""铜箔闭环 P1b —— 真实板 → SVG/manifest 输入适配层测试。

被测模块：`pcbflow/board_svg_adapter.py`（新建）+ `pcbflow/svg_route_package.py`
的唯一放宽（via.parent_id 允许 None = 独立过孔）。

覆盖：
- 正向：合成板文本 + 合成注册表 → build_inputs → svg_route_package.build →
  verify_consistency 返回 []（带/不带 snapshot）；篡改任一处后非空；
- 身份：route_id/via_id = copper key；pad_id = REF.PIN（重复时确定性加后缀
  并上报）；板级字段（sha256/copper_sha256/bbox/layers/keepouts）；
- 映射表：electrical_role → line_type（含"角色查不到 → signal + 上报"）、
  relation kind → RELATION_TYPES（含"无法映射 → 不硬塞 + 上报"）；
- fail-closed：未解析 net 的 pad/segment/via（不编造 net_id）、缺 size/drill
  的 via、身份键重复（注入 copper）、形状非法入参、不可解析板文本；
- 读板铁律：文本读入必须 newline=""（保留 CRLF）——用
  sha256_text(读入文本) == sha256_file(文件) 证明未被行尾归一化；
- 真实板（只读抽样）：`config.REVC_BOARD` + `out/revc-a3/net-registry.json`，
  不写任何板文件、不调 kicad-cli。
"""

import json
import os
import re
import xml.etree.ElementTree as ET

import pytest

from pcbflow import board_svg_adapter as ba
from pcbflow import config, geo, hashing, svg_route_package as s4

SVG_NS = "http://www.w3.org/2000/svg"

# --------------------------------------------------------------- 合成夹具

# 手写小合成板（CRLF：读板铁律的观测点）
BOARD = (
    '(kicad_pcb (version 20260206) (generator "pcbnew")\r\n'
    '\t(layers\r\n'
    '\t\t(0 "F.Cu" signal)\r\n'
    '\t\t(2 "B.Cu" signal)\r\n'
    '\t)\r\n'
    '\t(footprint "SYNTH:R" (at 10 10)\r\n'
    '\t\t(property "Reference" "U1")\r\n'
    '\t\t(pad "1" smd (at 0 0) (size 0.6 0.4) (layers "F.Cu" "F.Mask")'
    ' (net "DP_A"))\r\n'
    '\t\t(pad "2" smd (at 1 0) (size 0.6 0.4) (layers "F.Cu" "F.Mask")'
    ' (net "GND"))\r\n'
    '\t\t(pad "3" thru_hole (at 2 0) (size 0.9 0.9) (layers "*.Cu" "*.Mask")'
    ' (net "NC_X"))\r\n'
    '\t\t(pad "4" smd (at 3 0) (size 0.6 0.4) (layers "F.Paste")'
    ' (net "DP_A"))\r\n'
    '\t\t(pad "5" smd (at 3 1) (size 0.6 0.4) (layers "F.Cu" "F.Mask")'
    ' (net "SWCLK"))\r\n'
    '\t)\r\n'
    '\t(segment (start 10 10) (end 10 20) (width 0.25) (layer "F.Cu")'
    ' (net "DP_A")\r\n'
    '\t\t(uuid "aaaaaaaa-1111-1111-1111-111111111111"))\r\n'
    '\t(segment (start 10 20) (end 12 20) (width 0.25) (layer "F.Cu")'
    ' (net "DP_A")\r\n'
    '\t\t(uuid "bbbbbbbb-2222-2222-2222-222222222222"))\r\n'
    '\t(via (at 10 20) (size 0.7) (drill 0.4) (layers "F.Cu" "B.Cu")'
    ' (net "GND")\r\n'
    '\t\t(uuid "cccccccc-3333-3333-3333-333333333333"))\r\n'
    '\t(zone (net "GND") (layer "B.Cu")\r\n'
    '\t\t(uuid "dddddddd-4444-4444-4444-444444444444")\r\n'
    '\t\t(polygon (pts (xy 0 0) (xy 30 0) (xy 30 40) (xy 0 40)))\r\n'
    '\t)\r\n'
    ')\r\n'
)

A_UUID = "aaaaaaaa-1111-1111-1111-111111111111"
B_UUID = "bbbbbbbb-2222-2222-2222-222222222222"
V_UUID = "cccccccc-3333-3333-3333-333333333333"
Z_UUID = "dddddddd-4444-4444-4444-444444444444"

# 合成注册表：差分正极网（含别名）/ 地网 / 调试网 / 无角色网 + 四类 relation
REGISTRY = {
    "schema_version": "1.0",
    "nets": [
        {"net_id": "N0001", "net_name": "DP_A", "aliases": ["DP_A_ALIAS"],
         "electrical_role": {"value": "differential_positive",
                             "status": "inferred"},
         "endpoints": ["U1.1"]},
        {"net_id": "N0002", "net_name": "GND", "aliases": [],
         "electrical_role": {"value": "ground_return", "status": "inferred"},
         "endpoints": ["U1.2"]},
        {"net_id": "N0003", "net_name": "SWCLK", "aliases": [],
         "electrical_role": {"value": "test_or_configuration",
                             "status": "source_declared"},
         "endpoints": ["U1.5"]},
        {"net_id": "N0004", "net_name": "ROLELESS", "aliases": [],
         "electrical_role": {"value": None, "status": "unclassified"},
         "endpoints": []},
    ],
    "excluded_nets": [
        {"net_name": "NC_X", "reason": "unconnected-(...) NC 焊盘网，显式列账"}],
    "relations": {
        "RDP-USB": {"relation_id": "RDP-USB", "kind": "differential_pair",
                    "members": ["N0001", "N0002"]},
        "RLG-G_FMC_D": {"relation_id": "RLG-G_FMC_D", "kind": "length_group",
                        "members": ["N0001"]},
        "RSYM-usb": {"relation_id": "RSYM-usb", "kind": "symmetry_class",
                     "members": ["N0002"]},
        "RBOGUS": {"relation_id": "RBOGUS", "kind": "mystery_kind",
                   "members": ["N0002"]},
    },
}

SCENARIO = "SC-P1B-SYNTH"


def write_board(tmp_path, text=BOARD, name="synth.kicad_pcb"):
    """落盘合成板（newline="" 写，保留 CRLF）；返回路径。"""
    p = tmp_path / name
    with open(p, "w", encoding="utf-8", newline="") as f:
        f.write(text)
    return str(p)


def reg(**over):
    """注册表深拷贝（可选顶层覆盖）。"""
    out = json.loads(json.dumps(REGISTRY))
    out.update(over)
    return out


def find_by_id(root, el_id):
    for el in root.iter():
        if isinstance(el.tag, str) and el.attrib.get("id") == el_id:
            return el
    raise AssertionError(f"SVG 中找不到 id={el_id!r}")


@pytest.fixture(scope="module")
def package(tmp_path_factory):
    """合成板 + 注册表 → (board, ref, svg, manifest, board_path)。"""
    d = tmp_path_factory.mktemp("p1b")
    path = write_board(d)
    board, ref = ba.build_inputs(path, REGISTRY, scenario_id=SCENARIO)
    svg, manifest = s4.build(board, ref)
    return board, ref, svg, manifest, path


# ------------------------------------------------------------------ 正向

class TestCleanRoundtrip:
    def test_verify_consistency_clean(self, package):
        board, _ref, svg, manifest, _p = package
        assert s4.verify_consistency(svg, manifest) == []
        assert s4.verify_consistency(svg, manifest, snapshot=board) == []

    def test_board_and_ref_shapes(self, package):
        board, ref, _s, _m, _p = package
        assert board["scenario_id"] == ref["scenario_id"] == SCENARIO
        b = board["board"]
        assert isinstance(b["bbox_mm"], list) and len(b["bbox_mm"]) == 4
        assert b["layers"] == ["F.Cu", "B.Cu"]
        assert b["layers_basis"] == ba.LAYERS_BASIS_BOARD
        assert b["bbox_basis"] == ba.BBOX_BASIS
        assert re.fullmatch(r"[0-9a-f]{64}", b["source_board_sha256"])
        assert b["identity_basis"] == "kicad_uuid"
        assert board["keepouts"] == []  # 本阶段显式为空（docstring 声明）
        assert len(ref["routes"]) == 2  # 1 个 segment 节点 ↔ 1 条 route
        assert {r["route_id"] for r in ref["routes"]} == {A_UUID, B_UUID}

    def test_route_fields_are_real_copper_facts(self, package):
        _b, ref, _s, manifest, _p = package
        for r in ref["routes"]:
            assert r["state"] == "baseline" and r["source"] == "baseline"
            assert r["constraint_refs"] == []
            assert r["parent_id"] is None
            assert r["endpoint_ids"] == ["@%.6f,%.6f" % (x, y)
                                         for x, y in r["polyline_mm"]]
        mr = [r for r in manifest["routes"]
              if r["route_id"] == A_UUID][0]
        assert mr["width_mm"] == 0.25
        assert mr["polyline_mm"] == [[10.0, 10.0], [10.0, 20.0]]

    def test_pads_mapped_with_registry_ids_and_layers(self, package):
        board, _r, _s, _m, _p = package
        pads = {p["pad_id"]: p for p in board["pads"]}
        assert pads["U1.1"]["net_id"] == "N0001"
        assert pads["U1.2"]["net_id"] == "N0002"
        assert pads["U1.5"]["net_id"] == "N0003"
        # 层由板文本焊盘 (layers ...) 判定：SMD→F.Cu、通孔→*.Cu
        assert pads["U1.1"]["layer"] == "F.Cu"
        assert pads["U1.3"]["layer"] == "*.Cu"
        assert pads["U1.1"]["x_mm"] == 10.0 and pads["U1.1"]["y_mm"] == 10.0

    def test_determinism_byte_exact(self, tmp_path):
        p = write_board(tmp_path)
        b1, r1 = ba.build_inputs(p, REGISTRY, scenario_id=SCENARIO)
        b2, r2 = ba.build_inputs(p, REGISTRY, scenario_id=SCENARIO)
        assert json.dumps(b1, sort_keys=True) == json.dumps(b2, sort_keys=True)
        assert json.dumps(r1, sort_keys=True) == json.dumps(r2, sort_keys=True)
        assert s4.build(b1, r1)[0] == s4.build(b2, r2)[0]

    def test_board_and_copper_sha_are_bound(self, package):
        board, _r, _s, _m, p = package
        assert board["board"]["source_board_sha256"] == hashing.sha256_file(p)
        copper = ba.copper_model.parse_copper_file(p)
        assert board["board"]["copper_sha256"] == copper["copper_sha256"]
        assert board["adapter_notes"]["copper_sha256"] == \
            copper["copper_sha256"]

    def test_bbox_covers_pads_and_copper(self, package):
        board, _r, _s, _m, _p = package
        x0, y0, x1, y1 = board["board"]["bbox_mm"]
        for p in board["pads"]:  # 焊盘外沿必须在 bbox 内
            assert x0 <= p["x_mm"] - p["w_mm"] / 2
            assert p["x_mm"] + p["w_mm"] / 2 <= x1
            assert y0 <= p["y_mm"] - p["h_mm"] / 2
            assert p["y_mm"] + p["h_mm"] / 2 <= y1
        assert x0 <= 10.0 and y0 <= 10.0 and x1 >= 12.0 and y1 >= 20.0


# ------------------------------------------------------------ 篡改（负向）

class TestTamperDetected:
    def test_tampered_svg_coordinate(self, package):
        _b, _r, svg, manifest, _p = package
        assert "M 10.000000 10.000000" in svg
        bad = svg.replace("M 10.000000 10.000000", "M 10.000001 10.000000", 1)
        assert bad != svg
        assert s4.verify_consistency(bad, manifest) != []

    def test_tampered_manifest_field(self, package):
        _b, _r, svg, manifest, _p = package
        dup = json.loads(json.dumps(manifest))
        dup["routes"][0]["width_mm"] = 0.5
        assert s4.verify_consistency(svg, dup) != []

    def test_tampered_svg_viewbox(self, package):
        """篡改 SVG viewBox（bbox 合同点）→ 必报违规。"""
        _b, _r, svg, manifest, _p = package
        bad = re.sub(r'viewBox="[^"]*"',
                     'viewBox="0.000000 0.000000 1.000000 1.000000"', svg, 1)
        assert bad != svg
        assert s4.verify_consistency(bad, manifest) != []

    def test_tampered_via_parent_to_missing_route(self, package):
        board, _r, _s, manifest, _p = package
        dup = json.loads(json.dumps(manifest))
        dup["vias"][0]["parent_id"] = "no-such-route"
        dup["manifest_payload_sha256"] = s4._sha256_of(dup)
        out = s4.verify_consistency(s4.build_svg(board, dup), dup)
        assert any("不指向存在的 route" in x for x in out)

    def test_tampered_relation_member_not_registered(self, package):
        board, ref, _s, _m, _p = package
        bad_board = json.loads(json.dumps(board))
        for rel in bad_board["relations"]:
            if rel["relation_id"] == "RDP-USB":
                rel["members"] = ["N0001", "N9999"]
        svg2, man2 = s4.build(bad_board, ref)
        out = s4.verify_consistency(svg2, man2)
        assert any("N9999" in x and "不是已注册 net" in x for x in out)


# --------------------------------------------------- 合同放宽（独立过孔）

class TestIndependentViaRelaxation:
    def test_adapter_vias_are_independent_and_clean(self, package):
        board, ref, svg, manifest, _p = package
        assert [v["parent_id"] for v in ref["vias"]] == [None]
        assert [v["parent_id"] for v in manifest["vias"]] == [None]
        el = find_by_id(ET.fromstring(svg), f"via-{ref['vias'][0]['via_id']}")
        assert el.get("data-object-kind") == "via"
        assert el.get("data-parent-id") == ""  # 与 route 的既有约定一致
        # 独立过孔不产生任何一致性违规
        assert s4.verify_consistency(svg, manifest) == []
        assert [v["via_id"] for v in ref["vias"]] == [V_UUID]

    def test_parented_via_behavior_unchanged(self):
        board = {"scenario_id": "S", "board": {"bbox_mm": [0, 0, 10, 10]},
                 "pads": [], "keepouts": [], "relations": []}
        route = {"route_id": "R1", "net_id": "N1", "relation_ids": [],
                 "line_type": "signal", "parent_id": None, "layer": "F.Cu",
                 "width_mm": 0.25, "polyline_mm": [[0, 0], [5, 5]],
                 "endpoint_ids": ["A", "B"], "constraint_refs": [],
                 "state": "baseline", "source": "baseline"}
        via_ok = {"via_id": "V1", "net_id": "N1", "parent_id": "R1",
                  "from_layer": "F.Cu", "to_layer": "B.Cu",
                  "center_mm": [1, 2], "drill_mm": 0.4,
                  "annular_ring_mm": 0.15}
        svg, man = s4.build(board, {"scenario_id": "S", "routes": [route],
                                    "vias": [via_ok]})
        assert s4.verify_consistency(svg, man) == []
        assert find_by_id(ET.fromstring(svg), "via-V1").get(
            "data-parent-id") == "R1"
        # 给了 parent_id 时既有校验逐字不变：不存在 / 空串都拒绝
        for bad_pid in ("no-such-route", ""):
            with pytest.raises(ValueError):
                s4.build(board, {"scenario_id": "S", "routes": [route],
                                 "vias": [dict(via_ok, parent_id=bad_pid)]})


# ------------------------------------------------------------ 映射表（真值）

class TestMappingTables:
    def test_role_to_line_type_table(self, package):
        _b, ref, _s, _m, _p = package
        by_id = {r["route_id"]: r for r in ref["routes"]}
        assert by_id[A_UUID]["line_type"] == "diff_p"
        for role, lt in ba.ELECTRICAL_ROLE_TO_LINE_TYPE.items():
            assert lt in s4.LINE_TYPES, (role, lt)
        expect = {
            "power_rail": "power", "power_switch_node": "power",
            "power_feedback": "power", "power_enable": "power",
            "ground_return": "ground", "ground_return_analog": "ground",
            "differential_positive": "diff_p",
            "differential_negative": "diff_n",
            "clock": "clock", "crystal_node": "clock",
            "ordinary_gpio": "signal", "ordinary_control": "signal",
            "ordinary_signal": "signal", "test_or_configuration": "signal",
            "reset": "signal", "analog_sensitive": "signal",
        }
        for role, lt in expect.items():
            assert ba.ELECTRICAL_ROLE_TO_LINE_TYPE[role] == lt
        assert ba.DEFAULT_LINE_TYPE == "signal"

    def test_unknown_role_defaults_to_signal_and_is_reported(self, tmp_path):
        # GND 网的角色被抹掉 → 该网的 route 给 signal 且必须上报
        text = BOARD.replace('(net "DP_A")\r\n\t\t(uuid "aaaa',
                             '(net "GND")\r\n\t\t(uuid "aaaa')
        p = write_board(tmp_path, text)
        registry = reg()
        for n in registry["nets"]:
            if n["net_id"] == "N0002":
                n["electrical_role"] = {"value": None, "status": "unclassified"}
        board, ref = ba.build_inputs(p, registry, scenario_id=SCENARIO)
        by_id = {r["route_id"]: r for r in ref["routes"]}
        assert by_id[A_UUID]["line_type"] == "signal"
        rep = ba.build_inputs_report(p, registry, scenario_id=SCENARIO)
        assert [d["net_id"] for d in rep["line_type_defaulted"]] == ["N0002"]
        assert rep["line_type_defaulted"][0]["line_type"] == "signal"
        assert rep["counts"]["line_type_defaulted_nets"] == 1
        # 上报不改产物自洽性
        svg, man = s4.build(board, ref)
        assert s4.verify_consistency(svg, man) == []

    def test_relation_kind_table_and_no_force_fit(self, package):
        board, _ref, _s, _m, p = package
        types = {r["relation_id"]: r["relation_type"]
                 for r in board["relations"]}
        assert types == {"RDP-USB": "differential_pair",
                         "RLG-G_FMC_D": "bus",
                         "RSYM-usb": "bus"}
        for t in types.values():
            assert t in s4.RELATION_TYPES
        for kind, t in ba.RELATION_KIND_TO_TYPE.items():
            assert t in s4.RELATION_TYPES, (kind, t)
        # 映射表外的 kind 不得硬塞：不进 relations，显式上报
        rep = ba.build_inputs_report(p, REGISTRY, scenario_id=SCENARIO)
        unmapped = rep["unmapped_relation_kinds"]
        assert [u["relation_id"] for u in unmapped] == ["RBOGUS"]
        assert unmapped[0]["kind"] == "mystery_kind"
        assert rep["counts"]["relations_unmapped_kind"] == 1

    def test_route_relation_ids_only_reference_emitted_relations(self, package):
        board, ref, _s, _m, _p = package
        emitted = {r["relation_id"] for r in board["relations"]}
        for r in ref["routes"]:
            assert set(r["relation_ids"]) <= emitted
        by_id = {r["route_id"]: r for r in ref["routes"]}
        assert by_id[A_UUID]["relation_ids"] == ["RDP-USB", "RLG-G_FMC_D"]

    def test_relations_sorted_and_members_sorted(self, package):
        board, _r, _s, _m, _p = package
        ids = [r["relation_id"] for r in board["relations"]]
        assert ids == sorted(ids)
        for r in board["relations"]:
            assert r["members"] == sorted(r["members"]) and r["members"]
            assert r["parent_id"] is None


# ------------------------------------------------------- fail-closed 上报

class TestFailClosedReporting:
    def test_pad_with_unregistered_net_gets_no_fabricated_id(self, package):
        board, _ref, _s, _m, _p = package
        pads = {p["pad_id"]: p for p in board["pads"]}
        assert pads["U1.3"]["net_id"] == ""      # NC_X 不在注册表 → 不编造
        rep = board["adapter_notes"]
        entry = [e for e in rep["unmapped_nets"]
                 if e["net_name"] == "NC_X"][0]
        assert entry["registry_excluded"] is True
        assert entry["occurrences"]["pads"] == 1
        assert entry["subjects"]["pads"] == ["U1.3"]
        assert rep["counts"]["pads_without_registered_net"] == 1

    def test_pad_without_any_net_is_reported(self, tmp_path):
        p = write_board(tmp_path, BOARD.replace(' (net "NC_X")', ""))
        board, _ref = ba.build_inputs(p, REGISTRY, scenario_id=SCENARIO)
        pads = {x["pad_id"]: x for x in board["pads"]}
        assert pads["U1.3"]["net_id"] == ""
        e = board["adapter_notes"]["unmapped_nets"][0]
        assert e["net_name"] is None and e["registry_excluded"] is False

    def test_pad_layer_fallback_is_reported(self, package):
        board, _ref, _s, _m, _p = package
        pads = {p["pad_id"]: p for p in board["pads"]}
        assert pads["U1.4"]["layer"] == "F.Cu"   # 仅 F.Paste（无铜层声明）
        fb = board["adapter_notes"]["pad_layer_fallback"]
        assert fb["count"] == 1 and fb["pads"] == ["U1.4"]
        assert fb["kind"] == "pad_layer_fallback"   # 记录的是产物 pad_id

    def test_alias_resolution_is_registry_sanctioned(self, tmp_path):
        text = BOARD.replace('(net "DP_A")', '(net "DP_A_ALIAS")')
        p = write_board(tmp_path, text)
        board, ref = ba.build_inputs(p, REGISTRY, scenario_id=SCENARIO)
        assert {r["net_id"] for r in ref["routes"]} == {"N0001"}
        assert board["adapter_notes"]["alias_resolved_net_names"] == 1
        assert {x["net_id"] for x in board["pads"] if x["net_id"]} == {
            "N0001", "N0002", "N0003"}

    def test_unmapped_copper_net_drops_route_and_reports(self, tmp_path):
        text = BOARD.replace('(net "DP_A")\r\n\t\t(uuid "aaaa',
                             '(net "GHOST")\r\n\t\t(uuid "aaaa')
        p = write_board(tmp_path, text)
        board, ref = ba.build_inputs(p, REGISTRY, scenario_id=SCENARIO)
        assert A_UUID not in {r["route_id"] for r in ref["routes"]}
        rep = board["adapter_notes"]
        e = [x for x in rep["unmapped_nets"] if x["net_name"] == "GHOST"][0]
        assert e["occurrences"]["segments"] == 1
        assert e["subjects"]["segments"] == [A_UUID]
        assert rep["counts"]["routes_dropped_unmapped_net"] == 1
        svg, man = s4.build(board, ref)   # 丢弃后产物仍自洽
        assert s4.verify_consistency(svg, man) == []

    def test_unmapped_via_net_drops_via_and_reports(self, tmp_path):
        text = BOARD.replace('(net "GND")\r\n\t\t(uuid "cccc',
                             '(net "GHOST")\r\n\t\t(uuid "cccc')
        p = write_board(tmp_path, text)
        board, ref = ba.build_inputs(p, REGISTRY, scenario_id=SCENARIO)
        assert ref["vias"] == []
        rep = board["adapter_notes"]
        e = [x for x in rep["unmapped_nets"] if x["net_name"] == "GHOST"][0]
        assert e["occurrences"]["vias"] == 1
        assert e["subjects"]["vias"] == [V_UUID]
        assert rep["counts"]["vias_dropped"] == 1

    def test_injected_copper_missing_size_and_drill(self, tmp_path):
        p = write_board(tmp_path)
        copper = ba.copper_model.parse_copper_file(p)
        copper["vias"] = [
            dict(copper["vias"][0], key="V-NOSIZE", size=None),
            dict(copper["vias"][0], key="V-NODRILL", drill=None),
            dict(copper["vias"][0], key="V-BADLAYERS", layers=["F.Cu"]),
        ]
        board, ref = ba.build_inputs(p, REGISTRY, scenario_id=SCENARIO,
                                     copper=copper)
        by_id = {v["via_id"]: v for v in ref["vias"]}
        assert by_id["V-NOSIZE"]["annular_ring_mm"] == 0.0  # size 缺失 → 0
        assert set(by_id) == {"V-NOSIZE"}                  # 另两个无法表达
        notes = board["adapter_notes"]["vias_missing_size_or_drill"]
        kinds = {n["via_key"]: n["kind"] for n in notes}
        assert kinds == {"V-NOSIZE": "via_missing_size",
                         "V-NODRILL": "via_unrepresentable",
                         "V-BADLAYERS": "via_unrepresentable"}
        assert board["adapter_notes"]["counts"]["vias_dropped"] == 2
        svg, man = s4.build(board, ref)
        assert s4.verify_consistency(svg, man) == []

    def test_injected_segment_unrepresentable(self, tmp_path):
        p = write_board(tmp_path)
        copper = ba.copper_model.parse_copper_file(p)
        copper["segments"] = copper["segments"] + [
            dict(copper["segments"][0], key="S-BADWIDTH", width=0)]
        board, ref = ba.build_inputs(p, REGISTRY, scenario_id=SCENARIO,
                                     copper=copper)
        assert "S-BADWIDTH" not in {r["route_id"] for r in ref["routes"]}
        rej = board["adapter_notes"]["segments_unrepresentable"]
        assert [x["key"] for x in rej] == ["S-BADWIDTH"]
        assert board["adapter_notes"]["counts"]["routes_dropped_unmapped_net"] \
            == 1

    def test_duplicate_copper_keys_disambiguated_and_reported(self, tmp_path):
        p = write_board(tmp_path)
        copper = ba.copper_model.parse_copper_file(p)
        copper["segments"] = [dict(s, key="SAME") for s in
                              copper["segments"]]
        copper["vias"] = [dict(copper["vias"][0], key="SAME")]
        board, ref = ba.build_inputs(p, REGISTRY, scenario_id=SCENARIO,
                                     copper=copper)
        assert sorted(r["route_id"] for r in ref["routes"]) == \
            ["SAME", "SAME#2"]
        assert [v["via_id"] for v in ref["vias"]] == ["SAME"]  # 独立命名空间
        dups = board["adapter_notes"]["ids_disambiguated"]
        assert [d["kind"] for d in dups] == ["duplicate_copper_key"]
        assert dups[0]["base_id"] == "SAME" and dups[0]["id"] == "SAME#2"
        svg, man = s4.build(board, ref)
        assert len({r["svg_id"] for r in man["routes"]}) == 2
        assert {v["via_id"] for v in man["vias"]} == {"SAME"}
        assert s4.verify_consistency(svg, man) == []

    def test_duplicate_pad_id_disambiguated_and_reported(self, tmp_path):
        p = write_board(tmp_path, BOARD.replace('(pad "5" smd', '(pad "4" smd'))
        board, ref = ba.build_inputs(p, REGISTRY, scenario_id=SCENARIO)
        ids = sorted(x["pad_id"] for x in board["pads"])
        assert "U1.4" in ids and "U1.4#2" in ids
        dups = board["adapter_notes"]["ids_disambiguated"]
        assert [d["kind"] for d in dups] == ["duplicate_pad_id"]
        assert [d["id"] for d in dups] == ["U1.4#2"]
        svg, man = s4.build(board, ref)
        assert len({p["pad_id"] for p in board["pads"]}) == len(board["pads"])
        assert s4.verify_consistency(svg, man) == []

    def test_relation_member_absent_from_board_is_reported(self, tmp_path):
        """关系成员里出现"板上没有铜箔/焊盘"的网：关系仍如实发出（真值），
        适配层显式登记缺口，并把随之而来的 verify 违规**归属清楚**。"""
        p = write_board(tmp_path)
        registry = reg()
        registry["relations"]["RDP-USB"]["members"] = ["N0001", "N0004"]
        board, ref = ba.build_inputs(p, registry, scenario_id=SCENARIO)
        gaps = board["adapter_notes"]["relation_member_gaps"]
        assert [g["relation_id"] for g in gaps] == ["RDP-USB"]
        assert gaps[0]["members_missing"] == ["N0004"]
        svg, man = s4.build(board, ref)
        out = s4.verify_consistency(svg, man)
        # 违规恰是该成员的"不是已注册 net"（SVG 侧与 manifest 侧各一条）：
        # 生成器 verify 的 net 全集只取产物内出现的网、无注册表入参 ——
        # 已知口径，且已由 adapter_notes 显式上报（可归属）
        assert len(out) == 2
        assert all("N0004" in x and "不是已注册 net" in x for x in out)
        # 成员都在板上时 → 零违规
        registry["relations"]["RDP-USB"]["members"] = ["N0001", "N0002"]
        board2, ref2 = ba.build_inputs(p, registry, scenario_id=SCENARIO)
        assert board2["adapter_notes"]["relation_member_gaps"] == []
        assert s4.verify_consistency(*s4.build(board2, ref2)) == []

    def test_zones_are_now_represented_and_accounted(self, package):
        """P3 合同 v2：zone 只读进入镜像（1:1），未表达的部分显式列账。

        （本断言随 P3 合同扩展更新：v1 时 zone 一律未表达，故旧的
        `zones_not_represented.count == 1 / keys == [Z_UUID] / layers ==
        ["B.Cu"]` 描述的是"未表达"，现由 `zones_in_manifest` 描述"已表达"。
        会计纪律不变：任何**未**进入 manifest 的 zone 必须逐条列账。）
        """
        board, ref, _s, manifest, _p = package
        # 已表达：1 个 zone ↔ 1 个 zone 条目，事实与派生数据分开
        assert len(ref["zones"]) == 1 and len(manifest["zones"]) == 1
        z = board["adapter_notes"]["zones_in_manifest"]
        assert z["count"] == 1
        assert z["zone_ids"] == [Z_UUID]
        assert z["layers"] == ["B.Cu"]
        assert z["outline_points"] == [4]
        assert z["fill_state_counts"] == {"fresh": 0, "stale": 0, "unknown": 1}
        # 未表达：本板上为零（不再"假装未表达"，也不静默丢弃）
        nr = board["adapter_notes"]["zones_not_represented"]
        assert nr["count"] == 0 and nr["keys"] == []

    def test_unmapped_net_zone_is_dropped_and_reported(self, tmp_path):
        """未注册 net 的 zone：绝不编造 net_id，逐条列账。"""
        text = BOARD.replace('(zone (net "GND")', '(zone (net "GHOST_Z")')
        p = write_board(tmp_path, text, "ghost-zone.kicad_pcb")
        board, ref = ba.build_inputs(p, REGISTRY, scenario_id=SCENARIO)
        assert ref["zones"] == []
        e = [x for x in board["adapter_notes"]["unmapped_nets"]
             if x["net_name"] == "GHOST_Z"][0]
        assert e["occurrences"]["zones"] == 1
        assert e["subjects"]["zones"] == [Z_UUID]
        nr = board["adapter_notes"]["zones_not_represented"]
        assert nr["count"] == 1 and nr["keys"] == [Z_UUID]
        assert board["adapter_notes"]["counts"]["zones_dropped"] == 1
        svg, man = s4.build(board, ref)
        assert man["zones"] == [] and man["zones_summary"]["count"] == 0
        assert s4.verify_consistency(svg, man) == []

    def test_board_level_gaps_declared(self, package):
        board, _r, _s, _m, _p = package
        items = {g["item"]: g["status"]
                 for g in board["adapter_notes"]["board_level_gaps"]}
        assert items["board_frame_edge_cuts"] == "not_parsed"
        assert items["board_keepouts"] == "not_parsed"
        assert items["pad_rotation_bbox"] == "not_applied"
        assert "board_top_level_layers" not in items  # 本夹具层表可取

    def test_layers_fallback_paths(self, tmp_path):
        no_layers = BOARD.replace(
            '\t(layers\r\n\t\t(0 "F.Cu" signal)\r\n\t\t(2 "B.Cu" signal)\r\n'
            '\t)\r\n', "")
        assert no_layers.count('"F.Cu" signal') == 0  # 顶层层表已摘除
        assert no_layers.count('"*.Cu"') == 1         # 焊盘的 layers 仍在
        p = write_board(tmp_path, no_layers, "nolayers.kicad_pcb")
        board, _ref = ba.build_inputs(p, REGISTRY, scenario_id=SCENARIO)
        # 铜箔声明了 F.Cu/B.Cu → 按铜箔回退（并显式上报）
        assert board["board"]["layers"] == ["F.Cu", "B.Cu"]
        assert board["board"]["layers_basis"] == ba.LAYERS_BASIS_COPPER
        items = {g["item"]: g["status"]
                 for g in board["adapter_notes"]["board_level_gaps"]}
        assert items["board_top_level_layers"] == \
            "fallback_copper_declared_layers"
        # 无层表且无铜箔 → 两层级兜底（同样显式上报）
        bare = ('(kicad_pcb (version 20260206)\r\n'
                '\t(footprint "F" (at 1 1)\r\n'
                '\t\t(property "Reference" "R1")\r\n'
                '\t\t(pad "1" smd (at 0 0) (size 0.5 0.5)'
                ' (layers "F.Cu") (net "DP_A"))\r\n'
                '\t)\r\n)\r\n')
        p2 = write_board(tmp_path, bare, "bare.kicad_pcb")
        board2, _r2 = ba.build_inputs(p2, REGISTRY, scenario_id=SCENARIO)
        assert board2["board"]["layers"] == ["F.Cu", "B.Cu"]
        assert board2["board"]["layers_basis"] == ba.LAYERS_BASIS_FALLBACK
        items2 = {g["item"]: g["status"]
                  for g in board2["adapter_notes"]["board_level_gaps"]}
        assert items2["board_top_level_layers"] == "fallback_two_layer"

    def test_input_shape_fail_closed(self, tmp_path):
        p = write_board(tmp_path)
        with pytest.raises(ValueError):
            ba.build_inputs(p, ["not-a-dict"], scenario_id=SCENARIO)
        with pytest.raises(ValueError):
            ba.build_inputs(p, REGISTRY, scenario_id="")
        with pytest.raises(ValueError):
            ba.build_inputs("", REGISTRY, scenario_id=SCENARIO)
        with pytest.raises(ValueError):
            ba.build_inputs(p, REGISTRY, scenario_id=SCENARIO, copper={})
        # 形状合法但内容为空：不抛，copper_sha256 如实透传
        b, r = ba.build_inputs(p, REGISTRY, scenario_id=SCENARIO,
                               copper={"segments": [], "vias": [],
                                       "copper_sha256": "x"})
        assert r["routes"] == [] and r["vias"] == []
        assert b["board"]["copper_sha256"] == "x"

    def test_unparseable_board_raises_fail_closed(self, tmp_path):
        """板文本括号不平衡：geo/sexpr_min 抛 ValueError（无部分产物）。"""
        p = write_board(tmp_path, '(kicad_pcb (segment (start 1 2)',
                        "broken.kicad_pcb")
        with pytest.raises(ValueError):
            ba.build_inputs(p, REGISTRY, scenario_id=SCENARIO)


# ------------------------------------------------------------ 读板铁律

class TestReadNewlinePreserved:
    def test_text_read_keeps_crlf(self, tmp_path):
        p = write_board(tmp_path)
        text = ba._read_board_text(p)
        assert "\r\n" in text
        # 关键证明：文本读入未被行尾归一化（归一化会改变 sha256）
        assert hashing.sha256_text(text) == hashing.sha256_file(p)


# --------------------------------------------------------- 真实板（只读）

REGISTRY_PATH = os.path.join(config.OUT_DIR, "revc-a3", "net-registry.json")
REAL_SCENARIO = "revc-a3-svg-p1b"

needs_board = pytest.mark.skipif(
    not os.path.exists(config.REVC_BOARD), reason="Rev-C board missing")


def load_registry():
    with open(REGISTRY_PATH, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def real_registry():
    if not os.path.exists(REGISTRY_PATH):
        pytest.skip("net-registry.json missing")
    return load_registry()


@pytest.fixture(scope="module")
def real_run(real_registry):
    """真实板整套产物（模块级 fixture，供 TestRealRevCBoard 复用）。"""
    if not os.path.exists(config.REVC_BOARD):
        pytest.skip("Rev-C board missing")
    board, ref = ba.build_inputs(config.REVC_BOARD, real_registry,
                                 scenario_id=REAL_SCENARIO)
    svg, manifest = s4.build(board, ref)
    return board, ref, svg, manifest


@needs_board
class TestRealRevCBoard:

    def test_verify_consistency_is_clean(self, real_run):
        board, _ref, svg, manifest = real_run
        assert s4.verify_consistency(svg, manifest) == []
        assert s4.verify_consistency(svg, manifest, snapshot=board) == []

    def test_counts_match_copper_and_geo_facts(self, real_run):
        board, ref, _svg, manifest = real_run
        copper = ba.copper_model.parse_copper_file(config.REVC_BOARD)
        parsed = geo.parse_board(config.REVC_BOARD)
        rep = board["adapter_notes"]
        assert len(board["pads"]) == len(parsed["pads"])
        assert len(ref["routes"]) + rep["counts"]["routes_dropped_unmapped_net"] \
            == copper["counts"]["segments"]
        assert len(ref["vias"]) + rep["counts"]["vias_dropped"] == \
            copper["counts"]["vias"]
        assert len(manifest["routes"]) == len(ref["routes"])
        assert len(manifest["vias"]) == len(ref["vias"])
        assert len(board["relations"]) == 12

    def test_independent_vias_and_unique_ids(self, real_run):
        board, ref, svg, manifest = real_run
        assert ref["vias"] and all(v["parent_id"] is None for v in ref["vias"])
        assert all(v["parent_id"] is None for v in manifest["vias"])
        assert len({v["via_id"] for v in ref["vias"]}) == len(ref["vias"])
        assert len({r["route_id"] for r in ref["routes"]}) == \
            len(ref["routes"])
        assert len({p["pad_id"] for p in board["pads"]}) == len(board["pads"])
        root = ET.fromstring(svg)
        ids = [el.attrib["id"] for el in root.iter()
               if isinstance(el.tag, str) and "id" in el.attrib]
        assert len(ids) == len(set(ids))

    def test_every_net_id_comes_from_registry(self, real_run):
        board, ref, _svg, _man = real_run
        net_ids = {n["net_id"] for n in load_registry()["nets"]}
        for r in ref["routes"]:
            assert r["net_id"] in net_ids
            assert r["line_type"] in s4.LINE_TYPES
            assert set(r["relation_ids"]) <= {
                x["relation_id"] for x in board["relations"]}
        for v in ref["vias"]:
            assert v["net_id"] in net_ids
        for p in board["pads"]:
            assert p["net_id"] in net_ids or p["net_id"] == ""

    def test_reports_are_populated_and_explicit(self, real_run):
        board, ref, _svg, _man = real_run
        rep = ba.build_inputs_report(config.REVC_BOARD, load_registry(),
                                     scenario_id=REAL_SCENARIO)
        assert rep == board["adapter_notes"]  # 报告与 board_dict 同源
        assert rep["unmapped_nets"], "真实板有未注册 net，必须显式上报"
        assert rep["board_level_gaps"]
        assert rep["layers_basis"] == ba.LAYERS_BASIS_BOARD
        assert rep["counts"]["relations_unmapped_kind"] == 0
        assert rep["counts"]["routes"] == len(ref["routes"])
        assert rep["counts"]["pads"] == len(board["pads"])

    def test_real_board_is_read_only(self, real_run):
        before = hashing.sha256_file(config.REVC_BOARD)
        ba.build_inputs(config.REVC_BOARD, load_registry(),
                        scenario_id=REAL_SCENARIO)
        assert hashing.sha256_file(config.REVC_BOARD) == before
