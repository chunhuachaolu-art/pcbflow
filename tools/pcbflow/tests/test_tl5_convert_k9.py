"""TL-5 S18：KiCad 8.99–10.99 demo 板转换器扩展（corpus_convert k9 路径）测试。

覆盖：版本门显式正负向（含 KiCad5 互斥）、真实 demo fixture 解析（拷贝自
datasets/kicad-demos-r1/raw，byte 口径 sha256 对账=拷贝只读）、20260206+
net-by-name 推导（net_id 结构性缺失如实）、退化板（constraints 0 net/
0 footprint）、规范化板确定性 byte-exact、drill oval 形态、坏文件
fail-closed、k9 graph/conversion-log 构件、multichannel 双态 audit 诚实
fail、既有 KiCad5 路径行为零改动。
"""

from __future__ import annotations

import hashlib
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from pcbflow import corpus_convert as cc
from pcbflow.sexpr_min import SexprError

FIX = os.path.join("tests", "fixtures", "kicad_demos")

#: 真实 fixture（拷贝自 datasets/kicad-demos-r1/raw；sha256 在测试内对账）
REAL_FIXTURES = {
    "ecc83-pp.kicad_pcb":
        "0ab45f4f8c90ac877e3313a1888d875107f2be3fc2b2f40cfb7927873b35260c",
    "constraints.kicad_pcb":
        "edbb888d918401098fe87af52d79df770b43203c4429b28810dc5f0cce4b8648",
    "pic_programmer.kicad_pcb":
        "1ca70b620506818eb0227e2863bbd573d1fec1672072dc43d0dbe8475e69c8fb",
}


def _fix(name: str) -> str:
    with open(os.path.join(FIX, name), "rb") as f:
        raw = f.read()
    assert hashlib.sha256(raw).hexdigest() == REAL_FIXTURES[name], \
        f"fixture byte drift: {name}"
    return raw.decode("utf-8")


def _read_dataset(name: str) -> bytes:
    rel = {"ecc83-pp.kicad_pcb": "ecc83/ecc83-pp.kicad_pcb",
           "constraints.kicad_pcb": "constraints/constraints.kicad_pcb",
           "pic_programmer.kicad_pcb":
               "pic_programmer/pic_programmer.kicad_pcb"}[name]
    with open(os.path.join("datasets", "kicad-demos-r1", "raw", rel),
              "rb") as f:
        return f.read()


# ---------------------------------------------------------------------------
# 版本门（显式、互斥）
# ---------------------------------------------------------------------------

def test_version_gate_supported_tokens():
    assert cc.K9_SUPPORTED_VERSIONS == ("20210424", "20211014", "20221018",
                                        "20241030", "20241229",
                                        "20260206", "20260624")


@pytest.mark.parametrize("token", list(cc.K9_SUPPORTED_VERSIONS))
def test_version_gate_accepts_supported(token):
    text = (f'(kicad_pcb (version {token}) (generator "pcbnew")\n'
            f'  (generator_version "9.0")\n'
            f'  (general (thickness 1.6) (legacy_teardrops no))\n'
            f'  (layers (0 "F.Cu" signal) (2 "B.Cu" signal))\n'
            f')')
    model = cc.parse_kicad9_board(text)
    assert model["board_version"] == token
    assert model["host"] == "pcbnew 9.0"


def test_version_gate_rejects_kicad5_token():
    """KiCad5 20171130 不进 k9 门；k9 门也不吃 20171130（两门互斥）。"""
    k5_text = '(kicad_pcb (version 20171130) (host pcbnew "5.1.4")\n)'
    with pytest.raises(ValueError, match="outside k9 path gate"):
        cc.parse_kicad9_board(k5_text)
    k9_text = _fix("ecc83-pp.kicad_pcb")
    with pytest.raises(ValueError, match="expect board version 20171130"):
        cc.parse_kicad5_board(k9_text)


def test_version_gate_rejects_unknown_and_future():
    for token in ("20171130", "20240101", "20270101", "garbage"):
        text = f'(kicad_pcb (version {token})\n)'
        with pytest.raises(ValueError, match="outside k9 path gate"):
            cc.parse_kicad9_board(text)


# ---------------------------------------------------------------------------
# 真实 fixture 解析（拷贝=只读：与 datasets 逐字节对账）
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("name", sorted(REAL_FIXTURES))
def test_fixture_byte_identical_to_dataset(name):
    with open(os.path.join(FIX, name), "rb") as f:
        assert f.read() == _read_dataset(name)


def test_parse_real_ecc83_top_level_nets():
    model = cc.parse_kicad9_board(_fix("ecc83-pp.kicad_pcb"))
    d = cc.board_denominators(model)
    assert model["board_version"] == "20241229"
    assert model["net_declaration_source"] == "top_level"
    assert model["host"] == "pcbnew 9.0"
    assert d["net_count"] == 14 and d["named_net_count"] == 13
    assert d["module_count"] == 15 and d["pad_count"] == 33
    # copper 层判定=type=="signal"（k9 层编号重排，不能用 0..31 过滤）
    assert d["copper_layer_count"] == 2
    assert [l["name"] for l in model["copper_layers"]] == ["F.Cu", "B.Cu"]
    assert model["zone_count"] == 1
    assert model["segment_count"] == 59
    assert model["parse_warnings"] == []
    refs = [m["ref"] for m in model["modules"]]
    assert "C1" in refs  # property "Reference" 提取（盘上实测锚）
    assert all(not r.startswith("__NOREF__") for r in refs)
    # pad net 形态=(net N "name")
    pad = model["modules"][0]["pads"][0]
    assert pad["net"] is None or set(pad["net"]) == {"net_id", "name"}


def test_parse_pic_programmer_net_by_name():
    model = cc.parse_kicad9_board(_fix("pic_programmer.kicad_pcb"))
    d = cc.board_denominators(model)
    assert model["board_version"] == "20260206"
    assert model["net_declaration_source"] == "pad_derived"
    assert d["net_count"] == 111 and d["module_count"] == 63
    # net_id 结构性不可得——如实 None，不虚构
    assert all(n["net_id"] is None for n in model["nets"])
    names = {n["name"] for n in model["nets"]}
    assert "VCC" in names and "GND" in names
    assert model["nets"] == sorted(model["nets"], key=lambda x: x["name"])
    # pad net 形态=(net "name")
    named = [p["net"] for m in model["modules"] for p in m["pads"]
             if p["net"]]
    assert any(x == {"net_id": None, "name": "VCC"} for x in named)
    # drill 形态保留源字面量（pic_programmer 盘上实测=单值圆钻）
    drills = [tuple(p["drill"]) for m in model["modules"] for p in m["pads"]
              if p["drill"]]
    assert ("1.2",) in drills
    # oval 钻形态（demo 库其他板实测形态）由合成文本覆盖
    oval = cc.parse_kicad9_board(
        '(kicad_pcb (version 20241229) (generator "pcbnew")\n'
        '  (generator_version "9.0") (general (thickness 1.6))\n'
        '  (layers (0 "F.Cu" signal))\n'
        '  (footprint "L:X" (layer "F.Cu") (at 0 0)\n'
        '    (pad "1" thru_hole oval (at 0 0) (size 2 3)\n'
        '      (drill oval 1.02 2.03) (layers "*.Cu") (net "A"))\n'
        '  )\n'
        ')')
    assert oval["modules"][0]["pads"][0]["drill"] == ["oval", "1.02", "2.03"]


def test_parse_constraints_degenerate_board():
    model = cc.parse_kicad9_board(_fix("constraints.kicad_pcb"))
    d = cc.board_denominators(model)
    assert model["board_version"] == "20260624"
    assert d["net_count"] == 0 and d["module_count"] == 0
    assert d["pad_count"] == 0
    assert model["segment_count"] == 0
    # 退化板仍可走完整构件链（如实零值，不抛不凑）
    crit = cc.derive_critical_nets(model)
    assert crit["power_rails"] == [] and crit["diff_pairs"] == []
    norm = cc.normalized_k9_board_text(
        model, source_path="x.kicad_pcb", source_sha256="0" * 64)
    assert "(nets 0)" in norm


def test_footprint_without_reference_falls_back_and_warns():
    text = ('(kicad_pcb (version 20241229) (generator "pcbnew")\n'
            '  (generator_version "9.0")\n'
            '  (general (thickness 1.6))\n'
            '  (layers (0 "F.Cu" signal))\n'
            '  (footprint "Lib:NoRef" (layer "F.Cu") (at 0 0)\n'
            '    (pad "1" smd rect (at 0 0) (size 1 1)\n'
            '      (layers "F.Cu") (net "A"))\n'
            '  )\n'
            '  (footprint "Lib:Ok" (layer "F.Cu") (at 1 1)\n'
            '    (property "Reference" "R1" (at 0 0) (layer "F.SilkS"))\n'
            '  )\n'
            ')')
    model = cc.parse_kicad9_board(text)
    assert model["parse_warnings"] == ["footprint_without_reference:Lib:NoRef"]
    # modules 按 ref 排序："R1"(0x52) < "__NOREF__000"(0x5F)
    refs = [m["ref"] for m in model["modules"]]
    assert refs == ["R1", "__NOREF__000"]


# ---------------------------------------------------------------------------
# 规范化板（确定性 byte-exact）与构件
# ---------------------------------------------------------------------------

def test_normalized_board_deterministic_byte_exact():
    text = _fix("ecc83-pp.kicad_pcb")
    sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
    model = cc.parse_kicad9_board(text)
    kw = {"source_path": "datasets/kicad-demos-r1/raw/ecc83/ecc83-pp.kicad_pcb",
          "source_sha256": sha}
    a = cc.normalized_k9_board_text(model, **kw)
    b = cc.normalized_k9_board_text(cc.parse_kicad9_board(text), **kw)
    assert a == b
    assert f'(sha256 "{sha}")' in a
    assert '(version 20241229)' in a
    assert cc.K9_GENERATOR in a
    # net 行保留 id+name 源形态
    assert '(net 0 "")' in a
    with pytest.raises(ValueError, match="source_sha256 required"):
        cc.normalized_k9_board_text(model, source_path="x", source_sha256="z"*63)


def test_normalized_board_net_by_name_form():
    model = cc.parse_kicad9_board(_fix("pic_programmer.kicad_pcb"))
    norm = cc.normalized_k9_board_text(
        model, source_path="p.kicad_pcb", source_sha256="0" * 64)
    assert '(net "VCC")' in norm
    assert "(net 0 " not in norm  # pad_derived 板不虚构 id


def test_artifact_chain_ecc83_honest_missingness():
    text = _fix("ecc83-pp.kicad_pcb")
    model = cc.parse_kicad9_board(text)
    crit = cc.derive_critical_nets(model)
    sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
    st = cc.build_stackup_obj(model, board_id="ecc83/ecc83-pp",
                              source={"path": "s", "sha256": sha})
    assert st["thickness_mm"] == 1.6
    # k9 setup 无 KiCad5 最小值键——如实 null（不虚构）
    assert set(st["setup_mins"]) == {"trace_min_mm", "trace_clearance_mm",
                                     "via_size_mm", "via_drill_mm",
                                     "via_min_size_mm", "via_min_drill_mm"}
    assert all(v is None for v in st["setup_mins"].values())
    prof = cc.build_profile_obj(model, profile_id="kicaddemo-ecc83-ecc83-pp",
                                project_id="ecc83/ecc83-pp", crit=crit)
    assert prof["thresholds"] == {}  # 缺项整键不生成（值域禁 null）
    assert [l["name"] for l in prof["layers"]] == ["F.Cu", "B.Cu"]
    nr = cc.build_net_registry_obj(model, board_id="ecc83/ecc83-pp",
                                   crit=crit)
    assert nr["net_count"] == 14
    cls = {n["name"]: n["classification"] for n in nr["nets"]}
    assert cls["GND"] == "power_rail"
    topo = cc.topology_group_id(model, crit)
    assert topo.startswith("cu2-")


# ---------------------------------------------------------------------------
# k9 graph / conversion log 构件
# ---------------------------------------------------------------------------

def test_k9_graph_spec_audit_flag():
    fh = {"inputs/board.kicad_pcb": "0" * 64,
          "inputs/stackup.json": "0" * 64,
          "inputs/constraints.json": "0" * 64,
          "derived/net-registry.json": "0" * 64,
          "derived/feedforward-plan.json": "0" * 64}
    g = cc.build_k9_graph_spec(project_id="b", profile_id="p",
                               revision="r1", file_hashes=fh,
                               has_audit=False)
    kinds = [n["artifact_id"] for n in g["nodes"]]
    assert "audit_report" not in kinds
    assert g["deviations"] and "不虚构" in g["deviations"][0]
    assert g["converter_path"] == cc.K9_CONVERTER_VERSION
    fh2 = dict(fh, **{"derived/audit.json": "1" * 64})
    g2 = cc.build_k9_graph_spec(project_id="b", profile_id="p",
                                revision="r1", file_hashes=fh2,
                                has_audit=True)
    kinds2 = [n["artifact_id"] for n in g2["nodes"]]
    assert "audit_report" in kinds2 and g2["deviations"] == []
    ff = next(n for n in g2["nodes"]
              if n["artifact_id"] == "feedforward_plan")
    assert ff["inputs"] == ["net_registry", "audit_report"]


def test_k9_conversion_log_fields():
    text = _fix("ecc83-pp.kicad_pcb")
    model = cc.parse_kicad9_board(text)
    crit = cc.derive_critical_nets(model)
    log = cc.build_k9_conversion_log(
        board_id="ecc83/ecc83-pp", profile_id="kicaddemo-ecc83-ecc83-pp",
        module_sha256="0" * 64,
        inputs=[{"path": "s", "sha256": "0" * 64}],
        outputs=[{"path": "o", "sha256": "0" * 64}],
        model=model, model_r=None, crit=crit, topology_group="cu2-x",
        audit_result=None, route_check_status="not_executed")
    assert log["track"] == cc.TRACK_K9
    assert log["converter_version"] == cc.K9_CONVERTER_VERSION
    assert log["version_gate"]["board_version"] == "20241229"
    assert log["version_gate"]["net_declaration_source"] == "top_level"
    assert log["field_missingness"]["route_check"] == "not_executed"
    assert "not_applicable_single_state" in \
        log["field_missingness"]["audit_pair_check"]
    assert log["audit_result"] is None
    assert "net_ids_pad_derived" in log["dropped"]
    assert "constraint_tokens" in log["dropped"]


def test_multichannel_pair_audit_honest_fail():
    """-unrouted 文件自带 routed 几何（140 seg/19 via，盘上实测）——
    unrouted_state_pristine 如实 fail；同板身份 pass。"""
    text_u = ('(kicad_pcb (version 20241030) (generator "pcbnew")\n'
              '  (generator_version "8.99") (general (thickness 1.6))\n'
              '  (layers (0 "F.Cu" signal) (2 "B.Cu" signal))\n'
              '  (net 0 "") (net 1 "GND")\n'
              '  (footprint "L:C1" (layer "F.Cu") (at 0 0)\n'
              '    (property "Reference" "C1" (at 0 0) (layer "F.SilkS"))\n'
              '    (pad "1" thru_hole circle (at 0 0) (size 1 1)\n'
              '      (drill 0.5) (layers "*.Cu") (net 1 "GND"))\n'
              '  )\n'
              '  (segment (start 0 0) (end 1 0) (width 0.2) (layer "F.Cu")\n'
              '    (net 1))\n'
              ')')
    text_r = text_u.replace("(version 20241030)", "(version 20241229)")
    mu = cc.parse_kicad9_board(text_u)
    mr = cc.parse_kicad9_board(text_r)
    audit = cc.build_audit_obj(mu, mr, board_id="multichannel/multichannel_mixer")
    by_id = {c["id"]: c for c in audit["checks"]}
    assert by_id["unrouted_state_pristine"]["pass"] is False
    assert "segments=1" in by_id["unrouted_state_pristine"]["evidence"]
    assert by_id["unrouted_routed_same_board_identity"]["pass"] is True
    assert audit["result"] == "fail"


# ---------------------------------------------------------------------------
# fail-closed 与既有路径零改动
# ---------------------------------------------------------------------------

def test_malformed_board_fail_closed():
    text = _fix("ecc83-pp.kicad_pcb")
    with pytest.raises(SexprError):
        cc.parse_kicad9_board(text[:len(text) // 2])
    with pytest.raises(SexprError):
        cc.parse_kicad9_board(text + " (unbalanced")
    with pytest.raises(ValueError, match="expect exactly one kicad_pcb root"):
        cc.parse_kicad9_board("(kicad_pcb (version 20241229)) (kicad_pcb)")


def test_k5_path_behavior_unchanged():
    """既有 KiCad5 路径行为零改动（S18 红线：k9 为纯增量节）。"""
    synth = ('(kicad_pcb (version 20171130) (host pcbnew "5.1.4")\n'
             '  (general (thickness 1.6) (tracks 0))\n'
             '  (layers (0 Top signal) (31 Bottom signal))\n'
             '  (setup (trace_min 0.2))\n'
             '  (net 0 "") (net 1 GND)\n'
             '  (module Lib:A (layer Top) (at 0 0)\n'
             '    (fp_text reference U1 (at 0 0) (layer F.SilkS))\n'
             '    (pad 1 smd rect (at 0 0) (size 1 1) (layers F.Cu)\n'
             '      (net 1 GND))\n'
             '  )\n'
             ')')
    model = cc.parse_kicad5_board(synth)
    assert model["board_version"] == "20171130"
    assert model["nets"] == [{"net_id": 0, "name": ""},
                             {"net_id": 1, "name": "GND"}]
    assert model["modules"][0]["ref"] == "U1"
    assert model["modules"][0]["lib"] == "Lib:A"
    # k9 版本门对 k5 token 拒绝（互斥），k5 门对 k9 token 拒绝
    with pytest.raises(ValueError):
        cc.parse_kicad9_board(synth)
    with pytest.raises(ValueError):
        cc.parse_kicad5_board(_fix("ecc83-pp.kicad_pcb"))
