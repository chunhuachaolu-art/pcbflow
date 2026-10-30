"""observation 线 actual 侧扩展（扩展实施批·包 a；ADJUDICATION R6/R7）测试。

覆盖：R7 20260206+ net 名绑定并行解析器（真实 pic_programmer fixture
sha 对账+合成板正向/负向；与 check_stage.parse_routed_geometry 并列、
既有路径行为零改动）、R6① 逐铜层 segment/arc 长度求值（两种 arc 源
形态精确值）、R6② 逐铜层 pad 计数（与 FF-CORPUS signal_layer_pad_load
口径逐层一致）、R6③ per-pad escape 归因（via>trace>none 优先级、旋转
折算、层相交）、负向四类（缺字段/非法枚举/非有限数/未知格式——含
版本门双向、绑定档错配、非法弧几何）、确定性 byte-exact。
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from pcbflow import actual_ext as ae
from pcbflow import hashing
from pcbflow.sexpr_min import SexprError

FIX = os.path.join("tests", "fixtures", "kicad_demos")

#: 真实 fixture（拷贝自 datasets/kicad-demos-r1/raw；sha256 在测试内对账，
#: 锚与 test_tl5_convert_k9.py 同源）
PIC_PROGRAMMER_SHA256 = (
    "1ca70b620506818eb0227e2863bbd573d1fec1672072dc43d0dbe8475e69c8fb")


def _pic_programmer_text() -> str:
    with open(os.path.join(FIX, "pic_programmer.kicad_pcb"), "rb") as f:
        raw = f.read()
    assert hashlib.sha256(raw).hexdigest() == PIC_PROGRAMMER_SHA256, \
        "fixture byte drift: pic_programmer.kicad_pcb"
    return raw.decode("utf-8")


def _json(obj) -> str:
    return hashing.json_dumps(obj)


# ---------------------------------------------------------------------------
# 合成板：名绑定档（20260206）
# ---------------------------------------------------------------------------

#: 名绑定档合成板：VCC（1 pad+1 seg+1 via）、GND（2 pad+1 seg+1 arc+
#: 1 zone）、1 个无绑定 pad（unbound 靶）；U1 rot=90（escape 折算靶）
SYNTH_NAME_BOUND = """(kicad_pcb (version 20260206) (generator "pcbnew") (generator_version "10.0")

  (layers
    (0 "F.Cu" signal)
    (2 "B.Cu" signal)
  )

  (footprint "Lib:A" (layer "F.Cu")
    (at 10.0 20.0 90)
    (property "Reference" "U1" (at 0 0 0) (layer "F.SilkS"))
    (pad "1" smd rect (at 0.0 0.0) (size 0.3 0.6) (layers "F.Cu") (net "VCC"))
    (pad "2" thru_hole circle (at 2.0 0.0) (size 0.5 0.5) (drill 0.3)
      (layers "*.Cu" "*.Mask") (net "GND"))
  )

  (footprint "Lib:B" (layer "B.Cu")
    (at 0.0 0.0)
    (property "Reference" "R1" (at 0 0 0) (layer "B.SilkS"))
    (pad "1" smd rect (at 1.0 1.0) (size 0.4 0.4) (layers "B.Cu") (net "GND"))
    (pad "2" smd rect (at 3.0 1.0) (size 0.4 0.4) (layers "B.Cu"))
  )

  (segment (start 10.0 20.0) (end 12.0 20.0) (width 0.25) (layer "F.Cu")
    (net "VCC"))
  (segment (start 1.0 1.0) (end 4.0 1.0) (width 0.3) (layer "B.Cu")
    (net "GND"))
  (arc (start 0.0 0.0) (mid 1.414213562373 0.585786437627) (end 2.0 2.0)
    (width 0.3) (layer "B.Cu") (net "GND"))
  (via (at 10.0 20.0) (size 0.8) (drill 0.4) (layers "F.Cu" "B.Cu")
    (net "VCC"))
  (zone (net "GND") (layer "B.Cu") (polygon (pts (xy 0 0) (xy 5 5))))
)
"""

#: id 绑定档合成板（KiCad5 20171130）：fp_text reference + angle 形态 arc
SYNTH_ID_BOUND = """(kicad_pcb (version 20171130) (host pcbnew "(5.1.4)")

  (layers
    (0 F.Cu signal)
    (31 B.Cu signal)
  )

  (net 0 "")
  (net 1 GND)
  (net 2 SIG)

  (module Lib:A (layer F.Cu) (tedit 0)
    (at 10.0 20.0)
    (fp_text reference U1 (at 0 -2.0) (layer F.SilkS))
    (pad 1 smd rect (at 0.0 0.0) (size 0.3 0.6) (layers F.Cu) (net 1 GND))
    (pad 2 smd rect (at 2.0 0.0) (size 0.3 0.6) (layers B.Cu) (net 2 SIG))
  )

  (segment (start 10.0 20.0) (end 13.0 20.0) (width 0.2) (layer F.Cu)
    (net 1))
  (arc (start 0.0 0.0) (end 2.0 0.0) (angle 90) (width 0.2) (layer F.Cu)
    (net 1))
  (via (at 13.0 20.0) (size 0.8) (drill 0.4) (layers F.Cu B.Cu) (net 1))
  (zone (net 1) (net_name GND) (layer B.Cu)
    (polygon (pts (xy 0 0) (xy 5 5))))
)
"""

#: id 绑定档 k9 早期形态（20241229）：footprint+property Reference、
#: (net 2) 两 token 元素、zone (net 1)(net_name "GND")
SYNTH_ID_BOUND_K9 = """(kicad_pcb (version 20241229) (generator "pcbnew") (generator_version "9.0")

  (layers
    (0 "F.Cu" signal)
    (2 "B.Cu" signal)
  )

  (footprint "Lib:C" (layer "F.Cu")
    (at 5.0 5.0)
    (property "Reference" "C1" (at 0 0 0) (layer "F.SilkS"))
    (pad "1" smd rect (at 0.0 0.0) (size 0.4 0.4) (layers "F.Cu")
      (net 2 "Net-(P3-P1)"))
  )

  (segment (start 5.0 5.0) (end 6.0 5.0) (width 0.2) (layer "F.Cu")
    (net 2))
  (zone (net 1) (net_name "GND") (layer "B.Cu")
    (polygon (pts (xy 0 0) (xy 5 5))))
)
"""


def _per_net(g: dict, name: str) -> dict:
    return next(n for n in g["per_net"] if n["name"] == name)


def _layer_entry(result: dict, layer: str) -> dict:
    return next(e for e in result["per_layer"] if e["layer"] == layer)


# ---------------------------------------------------------------------------
# R7：名绑定并行解析器（合成板正向）
# ---------------------------------------------------------------------------

def test_r7_name_bound_synth_counts_and_per_net():
    g = ae.parse_routed_geometry_by_net_name(SYNTH_NAME_BOUND)
    assert g["binding"] == ae.BINDING_NAME
    assert g["board_version"] == "20260206"
    assert g["net_declaration_source"] == "pad_derived"
    assert g["net_count"] == 2 and g["named_net_count"] == 2
    assert [n["name"] for n in g["per_net"]] == ["GND", "VCC"]
    gnd, vcc = _per_net(g, "GND"), _per_net(g, "VCC")
    assert gnd["net_id"] is None  # pad_derived：不虚构 id（k9 路径同口径）
    assert (gnd["pad_count"], gnd["segment_count"], gnd["arc_count"],
            gnd["via_count"], gnd["zone_count"]) == (2, 1, 1, 0, 1)
    assert gnd["copper_item_count"] == 3
    assert (vcc["pad_count"], vcc["segment_count"], vcc["via_count"],
            vcc["zone_count"]) == (1, 1, 1, 0)
    assert g["geometry_counts"] == {"segments": 2, "arcs": 1, "vias": 1,
                                    "zones": 1}
    # R1.2 pad 无 net 不计 unbound（沿 id 路径先例，pad_count 账自然不含）
    assert g["items_bound_outside_declared_nets"] == 0
    assert g["actual_min"] == {"track_width_mm": 0.25, "via_size_mm": 0.8,
                               "via_drill_mm": 0.4}
    assert g["vias_without_drill_token"] == 0


def test_r7_name_bound_unbound_counting():
    """无绑定 segment（无 net 子节点）→ unbound 计数；空名 pad (net "")
    不入 net 集（与 id 路径『无 net 子节点→unbound / pad 不计』同构）。"""
    text = SYNTH_NAME_BOUND.replace(
        '(layers "*.Cu" "*.Mask") (net "GND"))',
        '(layers "*.Cu" "*.Mask") (net ""))')
    # 追加一个无 net 的 segment（unbound 靶）
    text = text.replace("(zone (net \"GND\")",
                        "(segment (start 0.0 0.0) (end 1.0 0.0)"
                        " (width 0.2) (layer \"F.Cu\"))\n"
                        "  (zone (net \"GND\")")
    g = ae.parse_routed_geometry_by_net_name(text)
    # 空名 pad：U1.2 退账 → GND pad 只剩 R1.1；net 集 GND+VCC 均在
    assert g["net_count"] == 2
    assert _per_net(g, "GND")["pad_count"] == 1
    # 无 net segment → unbound=1（pad 无绑定不计；unbound 几何不入
    # geometry_counts——与 id 路径同构）
    assert g["items_bound_outside_declared_nets"] == 1
    assert g["geometry_counts"]["segments"] == 2


def test_r7_determinism_byte_exact():
    a = _json(ae.parse_routed_geometry_by_net_name(SYNTH_NAME_BOUND))
    b = _json(ae.parse_routed_geometry_by_net_name(SYNTH_NAME_BOUND))
    assert a == b


# ---------------------------------------------------------------------------
# R7：真实 pic_programmer fixture（1 via + 2 rails 解锁验证面）
# ---------------------------------------------------------------------------

def test_r7_pic_programmer_unlock_counts():
    g = ae.parse_routed_geometry_by_net_name(_pic_programmer_text())
    assert g["board_version"] == "20260206"
    assert g["net_declaration_source"] == "pad_derived"
    # 计数类 actual 面板级账：1 via 行（board 级 via 计数）
    assert g["geometry_counts"] == {"segments": 370, "arcs": 0, "vias": 6,
                                    "zones": 1}
    assert g["items_bound_outside_declared_nets"] == 0
    assert g["actual_min"] == {"track_width_mm": 0.35, "via_size_mm": 1.6,
                               "via_drill_mm": 0.6}
    assert g["vias_without_drill_token"] == 0
    # 2 rails 行（GND/VCC）：actual=板文件 pad 元素按 net 绑定计数
    assert _per_net(g, "GND")["pad_count"] == 40
    assert _per_net(g, "VCC")["pad_count"] == 12
    # via 全部绑在两信号网上（逐网明细留 features 层）
    via_rows = [(n["name"], n["via_count"]) for n in g["per_net"]
                if n["via_count"]]
    assert sorted(via_rows) == [("/CLOCK-RB6", 3), ("/DATA-RB7", 3)]
    assert g["net_count"] == 111


def test_r7_pic_programmer_rails_names_pairable_with_ff_plan():
    """2 rails 行的配对可行性：FF 计划 rail net 名与名绑定账本名集可
    全等匹配（M4 口径：net 名原样全等匹配）；pad_count 两口径差异
    （计划侧 member_refs 含重复引用 vs actual 侧 pad 元素计数）=被测
    对象，此处只断言可配对与 actual 侧字面值。"""
    with open(os.path.join(
            "profiles", "kicaddemo-pic_programmer-pic_programmer",
            "derived", "feedforward-plan.json"), encoding="utf-8") as f:
        plan = json.load(f)
    g = ae.parse_routed_geometry_by_net_name(_pic_programmer_text())
    names = {n["name"] for n in g["per_net"]}
    for rail in plan["rails"]:
        assert rail["net"] in names  # net 名原样全等可配对
    actual = {r["name"]: r["pad_count"] for r in g["per_net"]}
    assert actual["GND"] == 40 and actual["VCC"] == 12
    # 计划侧账本字面值（含重复引用实例）与 actual 元素计数的差异如实
    # 不等——两口径差异本身=rails 忠实性行的被测对象（M4）
    for rail in plan["rails"]:
        assert rail["pad_count"] != actual[rail["net"]]


# ---------------------------------------------------------------------------
# R6①：逐铜层长度求值
# ---------------------------------------------------------------------------

def test_r6_1_name_bound_layer_lengths():
    r = ae.evaluate_layer_track_length_mm(SYNTH_NAME_BOUND,
                                          binding=ae.BINDING_NAME)
    assert r["board_version"] == "20260206"
    fcu, bcu = _layer_entry(r, "F.Cu"), _layer_entry(r, "B.Cu")
    assert fcu["segment_length_mm"] == 2.0 and fcu["segment_count"] == 1
    assert fcu["arc_length_mm"] == 0.0
    # 弧：r=2、θ=π/2 → len=π（mid 形态三点定圆）
    assert bcu["segment_length_mm"] == 3.0
    assert bcu["arc_length_mm"] == pytest.approx(math.pi, abs=1e-9)
    assert bcu["total_length_mm"] == pytest.approx(3.0 + math.pi, abs=1e-9)
    assert r["board_totals"]["total_length_mm"] == pytest.approx(
        2.0 + 3.0 + math.pi, abs=1e-9)
    assert r["board_totals"]["segment_count"] == 2
    assert r["board_totals"]["arc_count"] == 1


def test_r6_1_kicad5_angle_form_arc():
    r = ae.evaluate_layer_track_length_mm(SYNTH_ID_BOUND,
                                          binding=ae.BINDING_ID)
    fcu = _layer_entry(r, "F.Cu")
    assert fcu["segment_length_mm"] == 3.0
    # angle 形态：chord=2、θ=90° → R=√2、len=√2·π/2
    assert fcu["arc_length_mm"] == pytest.approx(math.sqrt(2) * math.pi / 2,
                                                 abs=1e-9)
    assert r["board_totals"]["arc_count"] == 1


def test_r6_1_zero_length_layers_retained():
    r = ae.evaluate_layer_track_length_mm(SYNTH_ID_BOUND,
                                          binding=ae.BINDING_ID)
    bcu = _layer_entry(r, "B.Cu")  # 无走线铜层保留零长度条目（分母完整）
    assert bcu["total_length_mm"] == 0.0
    assert bcu["segment_count"] == 0 and bcu["arc_count"] == 0


def test_r6_1_reverse_sweep_arc():
    """mid 在反向侧：θ=3π/2 → len=3π（方向判定由 mid 位置决定）。"""
    text = SYNTH_NAME_BOUND.replace(
        "(mid 1.414213562373 0.585786437627)",
        "(mid -1.414213562373 3.414213562373)")
    r = ae.evaluate_layer_track_length_mm(text, binding=ae.BINDING_NAME)
    bcu = _layer_entry(r, "B.Cu")
    assert bcu["arc_length_mm"] == pytest.approx(3.0 * math.pi, abs=1e-9)


def test_r6_1_mid_off_original_arc_is_just_another_arc():
    """mid 偏离原四分之一弧位置：任意不共线三点恒共圆，求值出另一条
    合法弧（如实求长，无『非共圆』失败路径——半径检查仅防字面量噪声
    级不自洽）。"""
    text = SYNTH_NAME_BOUND.replace(
        "(mid 1.414213562373 0.585786437627)", "(mid 1.0 2.9)")
    r = ae.evaluate_layer_track_length_mm(text, binding=ae.BINDING_NAME)
    bcu = _layer_entry(r, "B.Cu")
    assert bcu["arc_length_mm"] > 0.0
    assert bcu["arc_count"] == 1


# ---------------------------------------------------------------------------
# R6②：逐铜层 pad 计数（口径对齐 signal_layer_pad_load）
# ---------------------------------------------------------------------------

def test_r6_2_synth_counts_with_wildcard():
    r = ae.count_pads_per_layer(SYNTH_NAME_BOUND, binding=ae.BINDING_NAME)
    assert _layer_entry(r, "F.Cu")["pad_count"] == 2  # U1.1 + U1.2(*.Cu)
    assert _layer_entry(r, "B.Cu")["pad_count"] == 3  # U1.2(*.Cu)+R1.1+R1.2
    # R6② 为纯几何层计数：无 net 绑定的 R1.2 依其 layers 如实计入
    assert r["pad_total"] == 4
    assert r["wildcard_cu_pad_count"] == 1
    # 口径事实：sum(per_layer)−pad_total=通配 pad 重复计数
    assert sum(e["pad_count"] for e in r["per_layer"]) - r["pad_total"] == 1


def test_r6_2_pic_programmer_matches_ff_plan_layer_load():
    """R8 依赖面：actual 侧逐层 pad 计数与 FF-CORPUS 预测侧
    signal_layer_pad_load 逐层相等（146 条层声明配对口径核验）。"""
    with open(os.path.join(
            "profiles", "kicaddemo-pic_programmer-pic_programmer",
            "derived", "feedforward-plan.json"), encoding="utf-8") as f:
        plan = json.load(f)
    r = ae.count_pads_per_layer(_pic_programmer_text(),
                                binding=ae.BINDING_NAME)
    actual = {e["layer"]: e["pad_count"] for e in r["per_layer"]}
    assert len(plan["signal_layer_pad_load"]) == len(r["per_layer"])
    for entry in plan["signal_layer_pad_load"]:
        assert actual[entry["layer"]] == entry["pad_count"]


# ---------------------------------------------------------------------------
# R6③：per-pad escape 归因
# ---------------------------------------------------------------------------

def test_r6_3_synth_attribution_priority_and_rotation():
    r = ae.attribute_pad_escapes(SYNTH_NAME_BOUND, binding=ae.BINDING_NAME)
    by_ref = {(p["ref"], p["pad"]): p for p in r["pads"]}
    # U1 at (10,20) rot=90：pad1 局部 (0,0) → abs (10,20)；同网 VCC 的
    # seg start 与 via 均同位 → kind=via（优先级高于 trace）
    u11 = by_ref[("U1", "1")]
    assert u11["abs_xy"] == [10.0, 20.0]
    assert u11["escape_kind"] == "via"
    # evidence.kind=元素类型（segment/arc 即 trace 逃逸的证据元素）
    kinds = {e["kind"] for e in u11["evidence"]}
    assert kinds == {"via", "segment"}
    # U1 pad2 局部 (2,0) rot=90 → abs (10,18)（y-down 旋转折算）：GND
    # 几何均不同位 → none
    assert by_ref[("U1", "2")]["abs_xy"] == [10.0, 18.0]
    assert by_ref[("U1", "2")]["escape_kind"] == "none"
    # R1.1 abs=(1,1)：GND seg start 同位（*.Cu 与 B.Cu 层相交）→ trace
    assert by_ref[("R1", "1")]["escape_kind"] == "trace"
    assert r["summary"]["pad_bound_count"] == 3
    assert r["summary"]["pad_without_net_count"] == 1  # R1.2 无 net
    assert r["summary"]["escape_via"] == 1
    assert r["summary"]["escape_trace"] == 1
    assert r["summary"]["escape_none"] == 1
    assert r["coord_tol_mm"] == ae.ESCAPE_COORD_TOL_MM


def test_r6_3_layer_mismatch_blocks_attribution():
    """同位但层不相交 → 不归因（VCC seg 在 F.Cu，pad 若仅 B.Cu 则
    trace 不成立）。"""
    text = SYNTH_NAME_BOUND.replace(
        '(pad "1" smd rect (at 0.0 0.0) (size 0.3 0.6) (layers "F.Cu")'
        ' (net "VCC"))',
        '(pad "1" smd rect (at 0.0 0.0) (size 0.3 0.6) (layers "B.Cu")'
        ' (net "VCC"))')
    r = ae.attribute_pad_escapes(text, binding=ae.BINDING_NAME)
    by_ref = {(p["ref"], p["pad"]): p for p in r["pads"]}
    # via layers F.Cu+B.Cu 与 pad B.Cu 相交 → via 仍归因；F.Cu seg 被
    # 层门挡掉（evidence 无 trace 项）
    u11 = by_ref[("U1", "1")]
    assert u11["escape_kind"] == "via"
    assert {e["kind"] for e in u11["evidence"]} == {"via"}


def test_r6_3_pic_programmer_attribution_inventory():
    """真实板归因账面（fixture sha 锚定下的如实计数；advisory 口径）。"""
    r = ae.attribute_pad_escapes(_pic_programmer_text(),
                                 binding=ae.BINDING_NAME)
    assert r["board_version"] == "20260206"
    assert r["summary"]["pad_bound_count"] == 236
    assert r["summary"]["pad_without_net_count"] == 11
    assert r["summary"]["escape_via"] == 0
    assert r["summary"]["escape_trace"] == 106
    assert r["summary"]["escape_none"] == 130
    assert r["summary"]["parse_warnings"] == []


# ---------------------------------------------------------------------------
# 元素视图（id 档两形态；R6①②③ 共同输入层）
# ---------------------------------------------------------------------------

def test_extract_id_bound_kicad5_forms():
    el = ae.extract_routed_elements(SYNTH_ID_BOUND, binding=ae.BINDING_ID)
    assert el["board_version"] == "20171130"
    assert [l["name"] for l in el["copper_layers"]] == ["F.Cu", "B.Cu"]
    u1 = next(p for p in el["pads"] if p["pad"] == "1")
    assert u1["ref"] == "U1" and u1["net_key"] == 1 \
        and u1["net_name"] == "GND"
    seg = el["segments"][0]
    assert seg["net_key"] == 1 and seg["net_name"] is None  # 两 token 无名
    zone = el["zones"][0]
    assert zone["net_key"] == 1 and zone["net_name"] == "GND"  # net_name 补名


def test_extract_id_bound_k9_early_forms():
    el = ae.extract_routed_elements(SYNTH_ID_BOUND_K9,
                                    binding=ae.BINDING_ID)
    assert el["board_version"] == "20241229"
    pad = el["pads"][0]
    assert pad["ref"] == "C1" and pad["net_key"] == 2 \
        and pad["net_name"] == "Net-(P3-P1)"  # (net 2 "name") 三 token
    zone = el["zones"][0]
    assert zone["net_key"] == 1 and zone["net_name"] == "GND"


def test_extract_reference_missing_degrades_explicitly():
    """reference 缺失 → __NOREF__%03d 显式降级标记（沿 corpus_convert
    先例；parse_warnings 如实登记，不静默）。"""
    text = SYNTH_NAME_BOUND.replace(
        '(property "Reference" "U1" (at 0 0 0) (layer "F.SilkS"))', "")
    el = ae.extract_routed_elements(text, binding=ae.BINDING_NAME)
    assert any(w.startswith("footprint_without_reference:__NOREF__")
               for w in el["parse_warnings"])
    assert el["pads"][0]["ref"].startswith("__NOREF__")


# ---------------------------------------------------------------------------
# 负向：缺字段（fail-closed，各公开入口）
# ---------------------------------------------------------------------------

def test_neg_missing_pad_layers():
    text = SYNTH_NAME_BOUND.replace('(layers "B.Cu") (net "GND")',
                                    '(net "GND")')
    with pytest.raises(ae.ActualExtError, match="pad 缺 layers"):
        ae.count_pads_per_layer(text, binding=ae.BINDING_NAME)


def test_neg_missing_segment_start():
    text = SYNTH_NAME_BOUND.replace("(start 1.0 1.0) (end 4.0 1.0)",
                                    "(end 4.0 1.0)")
    with pytest.raises(ae.ActualExtError, match="缺 start"):
        ae.evaluate_layer_track_length_mm(text, binding=ae.BINDING_NAME)


def test_neg_missing_footprint_at():
    text = SYNTH_NAME_BOUND.replace("    (at 10.0 20.0 90)\n", "")
    with pytest.raises(ae.ActualExtError, match="缺 at"):
        ae.extract_routed_elements(text, binding=ae.BINDING_NAME)


def test_neg_missing_arc_mid_on_name_bound():
    text = SYNTH_NAME_BOUND.replace(
        "(mid 1.414213562373 0.585786437627) ", "")
    with pytest.raises(ae.ActualExtError, match="缺 mid"):
        ae.evaluate_layer_track_length_mm(text, binding=ae.BINDING_NAME)


def test_neg_missing_pad_at():
    text = SYNTH_NAME_BOUND.replace(
        '(pad "1" smd rect (at 0.0 0.0) (size 0.3 0.6)',
        '(pad "1" smd rect (size 0.3 0.6)')
    with pytest.raises(ae.ActualExtError, match="缺 at"):
        ae.attribute_pad_escapes(text, binding=ae.BINDING_NAME)


# ---------------------------------------------------------------------------
# 负向：非法枚举（binding 档）
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("binding", ["by_name", "netid", "", "NET_NAME_BOUND"])
def test_neg_illegal_binding_enum(binding):
    for fn in (ae.evaluate_layer_track_length_mm, ae.count_pads_per_layer,
               ae.attribute_pad_escapes):
        with pytest.raises(ae.ActualExtError, match="binding 非法"):
            fn(SYNTH_NAME_BOUND, binding=binding)
    with pytest.raises(ae.ActualExtError, match="binding 非法"):
        ae.extract_routed_elements(SYNTH_NAME_BOUND, binding=binding)


# ---------------------------------------------------------------------------
# 负向：非有限数 / 不可解析数值 token
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("bad", ["nan", "inf", "-inf", "abc"])
def test_neg_non_finite_coordinates(bad):
    text = SYNTH_NAME_BOUND.replace("(start 1.0 1.0) (end 4.0 1.0)",
                                    f"(start {bad} 1.0) (end 4.0 1.0)")
    with pytest.raises(ae.ActualExtError, match="非有限数|不可解析"):
        ae.evaluate_layer_track_length_mm(text, binding=ae.BINDING_NAME)


def test_neg_non_finite_width_token():
    text = SYNTH_NAME_BOUND.replace("(width 0.3) (layer \"B.Cu\")\n"
                                    "    (net \"GND\"))\n  (arc",
                                    "(width inf) (layer \"B.Cu\")\n"
                                    "    (net \"GND\"))\n  (arc")
    with pytest.raises(ae.ActualExtError, match="非有限数"):
        ae.parse_routed_geometry_by_net_name(text)


# ---------------------------------------------------------------------------
# 负向：未知格式（版本门双向 + 绑定档错配 + 非法弧几何 + 根唯一性）
# ---------------------------------------------------------------------------

def test_neg_version_gate_name_bound_rejects_kicad5():
    with pytest.raises(ae.ActualExtError, match="不在 binding=net_name_bound"):
        ae.parse_routed_geometry_by_net_name(SYNTH_ID_BOUND)


def test_neg_version_gate_id_bound_rejects_20260206():
    with pytest.raises(ae.ActualExtError, match="不在 binding=net_id_bound"):
        ae.evaluate_layer_track_length_mm(SYNTH_NAME_BOUND,
                                          binding=ae.BINDING_ID)


def test_neg_id_form_net_token_in_name_bound():
    text = SYNTH_NAME_BOUND.replace('(net "VCC"))\n  (segment',
                                    '(net 3))\n  (segment')
    with pytest.raises(ae.ActualExtError, match="绑定档错配"):
        ae.parse_routed_geometry_by_net_name(text)


def test_neg_name_form_net_token_in_id_bound():
    text = SYNTH_ID_BOUND.replace("(net 1))\n  (arc", '(net "GND"))\n  (arc')
    with pytest.raises(ae.ActualExtError, match="绑定档错配"):
        ae.extract_routed_elements(text, binding=ae.BINDING_ID)


def test_neg_duplicate_kicad_pcb_root():
    text = SYNTH_NAME_BOUND + "\n" + "(kicad_pcb (version 20260206))"
    with pytest.raises(ae.ActualExtError, match="exactly one kicad_pcb"):
        ae.parse_routed_geometry_by_net_name(text)


def test_neg_arc_collinear_mid_points():
    text = SYNTH_NAME_BOUND.replace(
        "(mid 1.414213562373 0.585786437627)", "(mid 1.0 1.0)")
    with pytest.raises(ae.ActualExtError, match="三点共线"):
        ae.evaluate_layer_track_length_mm(text, binding=ae.BINDING_NAME)


@pytest.mark.parametrize("angle", ["0", "360", "-360"])
def test_neg_kicad5_arc_degenerate_angle(angle):
    text = SYNTH_ID_BOUND.replace("(angle 90)", f"(angle {angle})")
    with pytest.raises(ae.ActualExtError, match="退化弧"):
        ae.evaluate_layer_track_length_mm(text, binding=ae.BINDING_ID)


def test_neg_kicad5_arc_missing_angle():
    text = SYNTH_ID_BOUND.replace(" (angle 90)", "")
    with pytest.raises(ae.ActualExtError, match="缺 angle"):
        ae.evaluate_layer_track_length_mm(text, binding=ae.BINDING_ID)


def test_neg_segment_on_non_copper_layer():
    text = SYNTH_NAME_BOUND.replace('(layer "F.Cu")\n    (net "VCC"))',
                                    '(layer "F.SilkS")\n    (net "VCC"))')
    with pytest.raises(ae.ActualExtError, match="非铜层声明层"):
        ae.evaluate_layer_track_length_mm(text, binding=ae.BINDING_NAME)


def test_neg_sexpr_error_propagates():
    with pytest.raises(SexprError):
        ae.parse_routed_geometry_by_net_name("(kicad_pcb (version 20260206)")


# ---------------------------------------------------------------------------
# 与既有路径并列性：check_stage.parse_routed_geometry 行为零改动
# ---------------------------------------------------------------------------

def test_existing_id_path_function_untouched():
    """id 绑定既有解析器对 id 档板行为不变（名绑定档板仍由其 fail-closed
    上抛——既有行为原样，未因并列解析器引入而改变）。"""
    from pcbflow import check_stage as cs
    # id 档板照常解析（既有行为）
    g = cs.parse_routed_geometry(SYNTH_ID_BOUND)
    assert g["geometry_counts"]["segments"] == 1
    # 名绑定档板照旧 ValueError（int('VCC')——M2 记录的 blocked 根因原样）
    with pytest.raises(ValueError):
        cs.parse_routed_geometry(SYNTH_NAME_BOUND)
