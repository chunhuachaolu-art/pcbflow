"""G 线 r2 包 G2b（actual 侧扩档+对齐器）测试。

覆盖（任务书 5 项对应）：
- actual_ext 版本门扩档（追加 20210424/20211014/20221018 id 档 + legacy
  20171114/"4" module 档；铜层判据按档三口径与 corpus_convert.K9_MODERN_
  COPPER_TYPES 单一事实源同判；既有五档行为零改动——档外仍拒/绑定档错
  配仍拒/既有档 4 板教训 fail-closed 不豁免/zone 嵌套弧防御与 r1 口径
  一致）；
- U-R2-5 双形态 pad 账源（parse_routed_geometry_dual_form：k5 module/
  k9 footprint 双形态 pad 账，账本与 check_stage.parse_routed_geometry
  同构；4 板型 ActualExtError 回退路径留给编排层的 fail-closed 演示）；
- observation_align_ext 对齐器两口径（A 口径 per-pad 2×2+summary 守恒
  +convention 逐字；LC demand 贴合度同判据网集复算+actual 求值+对称差
  如实+E/e 语义）；
- r1 回归钉：rows-r1 54 板 actual 侧关键输出（R6② padload 面+via 计数
  面）重算逐值相等断言——扩档零改既有行为的字节级/逐值级证明。

探针级用例只读 datasets/corpus-r2-r1/ 与 out/v3-obs/rows-r1/（零写入）。
convention 逐字锚硬编码自 ACTUAL-SIDE-ALIGNMENT-PROPOSAL.md §2.3/§3.2
原文（测试内比对，防止常量漂移）。
"""

from __future__ import annotations

import json
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from pcbflow import actual_ext as ae
from pcbflow import check_stage, config, corpus_convert as cc
from pcbflow import corpus_convert_ext as cce
from pcbflow import observation_align_ext as oae

ROOT = os.path.join(os.path.dirname(__file__), "..")
ROWS_R1 = os.path.join(ROOT, "out", "v3-obs", "rows-r1")
CORPUS_R2 = os.path.join(ROOT, "datasets", "corpus-r2-r1")

#: r2 扩档桶（提案 §2.2 权威口径：20210424×1+20211014×5+20221018×9+
#: legacy 20171114×1+"4"×1 = 17 板）
R2_NEW_VERSION_TOKENS = ("20210424", "20211014", "20221018",
                         "20171114", "4")

#: 17 板版本门实测锚（G2b 动工批实测；usb-gigabit/kria mixed/power 白
#: 名单非零铜层实证 + 计数锚，防回归）
ANCHOR_17 = {
    "usb-gigabit-rev-e": {"v": "20221018", "cu": 4, "vias": 75, "pads": 186},
    "kria-k26-devboard": {"v": "20221018", "cu": 8, "vias": 1901,
                          "pads": 2681},
    "teres-pcb1-a64-main-rev-c": {"v": "20171114", "cu": 6, "vias": 1594,
                                  "pads": 2018, "form": "module"},
    "stm32-ds2480-emu": {"v": "20210424", "cu": 2, "vias": 20, "pads": 83},
    "ice40hx1k-evb-rev-b": {"v": "4", "cu": 4, "vias": 279, "pads": 341,
                            "form": "module"},
}


# ---------------------------------------------------------------------------
# 合成夹具
# ---------------------------------------------------------------------------

#: A 口径 2×2 合成板（id 档 20211014 白名单档、footprint 形态）。
#: 每网两 pad 各自独立封装（transit 带判定按封装 pad-bbox，独立封装使
#: 「远/近」可控）。预期（见 test_pad_escape_agreement_synthetic）：
#:   (T,T)=U1/U2、(T,F)=U3/U4、(F,T)=U5/U6、(F,F)=U7/U8；
#:   GND U9/U10 → pred 未定义 actual_only；(net 5) 无联名 U12 →
#:   actual_only；无 net 子节点 U11 → 两侧皆未定义。
SYNTH_AGGREEMENT = """(kicad_pcb (version 20211014) (generator pcbnew)

  (layers
    (0 "F.Cu" signal)
    (31 "B.Cu" mixed)
  )

  (net 0 "")
  (net 1 SIG)
  (net 2 GND)
  (net 3 SIG3)
  (net 4 SIG4)

  (footprint "Lib:U" (layer "F.Cu")
    (at 10.0 20.0)
    (property "Reference" "U1" (at 0 0 0) (layer "F.SilkS"))
    (pad "1" smd rect (at 0.0 0.0) (size 0.4 0.4) (layers "F.Cu")
      (net 1 SIG))
  )
  (footprint "Lib:U" (layer "F.Cu")
    (at 30.0 20.0)
    (property "Reference" "U2" (at 0 0 0) (layer "F.SilkS"))
    (pad "1" smd rect (at 0.0 0.0) (size 0.4 0.4) (layers "F.Cu")
      (net 1 SIG))
  )
  (footprint "Lib:U" (layer "F.Cu")
    (at 50.0 20.0)
    (property "Reference" "U3" (at 0 0 0) (layer "F.SilkS"))
    (pad "1" smd rect (at 0.0 0.0) (size 0.4 0.4) (layers "F.Cu")
      (net 5 SIG2))
  )
  (footprint "Lib:U" (layer "F.Cu")
    (at 70.0 20.0)
    (property "Reference" "U4" (at 0 0 0) (layer "F.SilkS"))
    (pad "1" smd rect (at 0.0 0.0) (size 0.4 0.4) (layers "F.Cu")
      (net 5 SIG2))
  )
  (footprint "Lib:U" (layer "F.Cu")
    (at 90.0 20.0)
    (property "Reference" "U5" (at 0 0 0) (layer "F.SilkS"))
    (pad "1" smd rect (at 0.0 0.0) (size 0.4 0.4) (layers "F.Cu")
      (net 3 SIG3))
  )
  (footprint "Lib:U" (layer "F.Cu")
    (at 91.5 20.0)
    (property "Reference" "U6" (at 0 0 0) (layer "F.SilkS"))
    (pad "1" smd rect (at 0.0 0.0) (size 0.4 0.4) (layers "F.Cu")
      (net 3 SIG3))
  )
  (footprint "Lib:U" (layer "F.Cu")
    (at 110.0 20.0)
    (property "Reference" "U7" (at 0 0 0) (layer "F.SilkS"))
    (pad "1" smd rect (at 0.0 0.0) (size 0.4 0.4) (layers "F.Cu")
      (net 4 SIG4))
  )
  (footprint "Lib:U" (layer "F.Cu")
    (at 111.5 20.0)
    (property "Reference" "U8" (at 0 0 0) (layer "F.SilkS"))
    (pad "1" smd rect (at 0.0 0.0) (size 0.4 0.4) (layers "F.Cu")
      (net 4 SIG4))
  )
  (footprint "Lib:U" (layer "F.Cu")
    (at 130.0 20.0)
    (property "Reference" "U9" (at 0 0 0) (layer "F.SilkS"))
    (pad "1" smd rect (at 0.0 0.0) (size 0.4 0.4) (layers "F.Cu")
      (net 2 GND))
  )
  (footprint "Lib:U" (layer "F.Cu")
    (at 131.0 20.0)
    (property "Reference" "U10" (at 0 0 0) (layer "F.SilkS"))
    (pad "1" smd rect (at 0.0 0.0) (size 0.4 0.4) (layers "F.Cu")
      (net 2 GND))
  )
  (footprint "Lib:U" (layer "F.Cu")
    (at 150.0 20.0)
    (property "Reference" "U11" (at 0 0 0) (layer "F.SilkS"))
    (pad "1" smd rect (at 0.0 0.0) (size 0.4 0.4) (layers "F.Cu"))
  )
  (footprint "Lib:U" (layer "F.Cu")
    (at 170.0 20.0)
    (property "Reference" "U12" (at 0 0 0) (layer "F.SilkS"))
    (pad "1" smd rect (at 0.0 0.0) (size 0.4 0.4) (layers "F.Cu")
      (net 6))
  )

  (segment (start 10.0 20.0) (end 30.0 20.0) (width 0.25) (layer "F.Cu")
    (net 1))
  (via (at 10.0 20.0) (size 0.8) (drill 0.4) (layers "F.Cu" "B.Cu")
    (net 1))
  (segment (start 90.0 20.0) (end 91.5 20.0) (width 0.25) (layer "F.Cu")
    (net 3))
  (segment (start 130.0 20.0) (end 131.0 20.0) (width 0.25) (layer "F.Cu")
    (net 2))
)
"""

#: legacy 两档合成板（20171114：module/fp_text + 裸 token + angle 形态
#: arc + (net N NAME) 无引号联名）。angle=90、chord=2 → R=√2、
#: len=R·θ=√2·π/2。
SYNTH_LEGACY = """(kicad_pcb (version 20171114) (host pcbnew "(4.0.7)")

  (layers
    (0 F.Cu signal)
    (31 B.Cu mixed)
  )

  (net 0 "")
  (net 1 SIG)
  (net 2 GND)

  (module Lib:A (layer F.Cu) (tedit 0)
    (at 0.0 0.0)
    (fp_text reference U1 (at 0 -2.0) (layer F.SilkS))
    (pad 1 smd rect (at 0.0 0.0) (size 0.4 0.4) (layers F.Cu)
      (net 1 SIG))
    (pad 2 smd rect (at 0.0 2.0) (size 0.4 0.4) (layers F.Cu)
      (net 2 GND))
  )

  (segment (start 0.0 0.0) (end 0.0 0.0) (width 0.2) (layer F.Cu)
    (net 1))
  (arc (start 0.0 0.0) (end 2.0 0.0) (angle 90) (width 0.2) (layer F.Cu)
    (net 1))
  (via (at 0.0 0.0) (size 0.8) (drill 0.4) (layers F.Cu B.Cu) (net 1))
  (zone (net 2) (net_name GND) (layer B.Cu)
    (polygon (pts (xy 0 0) (xy 5 5))))
)
"""

#: 既有档（20241229）jumper 型铜层 segment：signal-only 判据下非铜层
#: 声明层 → r1 4 板教训 fail-closed（新档不豁免的对偶：既有档口径不动）
SYNTH_K9_JUMPER_LAYER = """(kicad_pcb (version 20241229) (generator "pcbnew") (generator_version "9.0")

  (layers
    (0 "F.Cu" signal)
    (2 "In4.Cu" jumper)
  )

  (footprint "Lib:C" (layer "F.Cu")
    (at 5.0 5.0)
    (property "Reference" "C1" (at 0 0 0) (layer "F.SilkS"))
    (pad "1" smd rect (at 0.0 0.0) (size 0.4 0.4) (layers "F.Cu")
      (net 2 "Net-(P3-P1)"))
  )

  (segment (start 5.0 5.0) (end 6.0 5.0) (width 0.2) (layer "In4.Cu")
    (net 2))
)
"""

#: zone 嵌套填充弧无 layer token（r1 royalblue54l 型防御面）
SYNTH_ZONE_NESTED_ARC = """(kicad_pcb (version 20211014) (generator pcbnew)

  (layers
    (0 "F.Cu" mixed)
  )

  (footprint "Lib:U" (layer "F.Cu")
    (at 0.0 0.0)
    (property "Reference" "U1" (at 0 0 0) (layer "F.SilkS"))
    (pad "1" smd rect (at 0.0 0.0) (size 0.4 0.4) (layers "F.Cu")
      (net 1 SIG))
  )

  (zone (net 1) (net_name SIG) (layer "F.Cu")
    (polygon (pts (xy 0 0) (xy 5 5)))
    (filled_polygon
      (pts (xy 0 0) (xy 5 5))
      (arc (start 0.0 0.0) (mid 1.0 1.0) (end 2.0 0.0)))
  )
)
"""

#: 白名单档 footprint 形态合成板（20221018 mixed 层 segment 入账）
SYNTH_MODERN_FP = """(kicad_pcb (version 20221018) (generator pcbnew)

  (layers
    (0 "F.Cu" mixed)
    (31 "B.Cu" power)
  )

  (net 0 "")
  (net 1 SIG)

  (footprint "Lib:R" (layer "F.Cu")
    (at 1.0 1.0)
    (property "Reference" "R1" (at 0 0 0) (layer "F.SilkS"))
    (pad "1" smd rect (at 0.0 0.0) (size 0.4 0.4) (layers "F.Cu")
      (net 1 SIG))
    (pad "2" smd rect (at 3.0 0.0) (size 0.4 0.4) (layers "F.Cu")
      (net 1 SIG))
  )

  (segment (start 1.0 1.0) (end 4.0 1.0) (width 0.25) (layer "F.Cu")
    (net 1))
  (via (at 4.0 1.0) (size 0.8) (drill 0.4) (layers "F.Cu" "B.Cu")
    (net 1))
  (zone (net 1) (net_name SIG) (layer "B.Cu")
    (polygon (pts (xy 0 0) (xy 5 5))))
)
"""


def _corpus_board_path(board_id: str) -> str:
    man = json.load(open(os.path.join(CORPUS_R2, "manifest.json"),
                         encoding="utf-8"))
    for b in man["boards"]:
        if b["board_id"] == board_id:
            kicad = [f for f in b["files"] if f.endswith(".kicad_pcb")]
            assert len(kicad) == 1, (board_id, kicad)
            return os.path.join(CORPUS_R2, b["dir"], kicad[0])
    raise AssertionError(f"board not in corpus-r2 manifest: {board_id}")


def _rows_r1_boards():
    summary = json.load(open(os.path.join(ROWS_R1, "batch-summary.json"),
                             encoding="utf-8"))
    boards = summary["boards"]
    assert len(boards) == 54
    return summary, boards


# ---------------------------------------------------------------------------
# 1. actual_ext 版本门扩档：常量锚与档门
# ---------------------------------------------------------------------------

def test_constants_anchored_to_single_source():
    """档集合与 corpus_convert_ext 同值（同批同判）；铜层白名单=单一事实
    源引用 corpus_convert.K9_MODERN_COPPER_TYPES（非复抄）。"""
    assert ae.ID_BOUND_VERSIONS == cce.ID_BOUND_VERSIONS
    assert ae.NET_NAME_BOUND_VERSIONS == cce.NET_NAME_BOUND_VERSIONS
    assert ae.K5_MODULE_VERSIONS == cce.K5_MODULE_VERSIONS
    assert (ae.EXT_MODERN_COPPER_VERSIONS
            == cce.EXT_MODERN_COPPER_VERSIONS)
    # 单一事实源：actual_ext 经 import corpus_convert 消费白名单常量
    assert ae.cc is cc
    assert cc.K9_MODERN_COPPER_TYPES == ("signal", "mixed", "power",
                                         "jumper")
    # 既有五档顺序保留（追加式）
    assert ae.ID_BOUND_VERSIONS[:1] == ("20171130",)
    assert ae.ID_BOUND_VERSIONS[4:6] == ("20241030", "20241229")
    assert ae.ID_BOUND_VERSIONS[6:8] == ("20171114", "4")


@pytest.mark.parametrize("tok", ["20230408", "1", "2026"])
def test_version_gate_out_of_set_rejected(tok):
    text = ('(kicad_pcb (version "%s") (layers (0 "F.Cu" signal)))'
            % tok)
    with pytest.raises(ae.ActualExtError, match="不在 binding"):
        ae.extract_routed_elements(text, binding=ae.BINDING_ID)
    with pytest.raises(cce.CorpusExtError, match="不在十档全集"):
        cce.detect_binding(text)


def test_version_gate_missing_version_rejected():
    with pytest.raises(ae.ActualExtError):
        ae.extract_routed_elements('(kicad_pcb (layers (0 "F.Cu" signal)))',
                                   binding=ae.BINDING_ID)


def test_binding_mismatch_and_illegal_enum_rejected():
    with pytest.raises(ae.ActualExtError, match="binding 非法"):
        ae.extract_routed_elements(SYNTH_MODERN_FP, binding="guess")
    # 名档板传 id 档 → 版本门拒（fail-closed 换档提示）
    name_bound = ('(kicad_pcb (version 20260206) (layers (0 "F.Cu" '
                  'signal)))')
    with pytest.raises(ae.ActualExtError, match="不在 binding"):
        ae.extract_routed_elements(name_bound, binding=ae.BINDING_ID)
    # dual_form 只收 id 档（名档指路 R7 函数）
    with pytest.raises(ae.ActualExtError, match="parse_routed_geometry_"
                                                "by_net_name"):
        ae.parse_routed_geometry_dual_form(name_bound,
                                           binding=ae.BINDING_NAME)


def test_copper_criteria_three_way_same_layer_table():
    """同一 mixed/power 层表：20211014 白名单全收 / 20241229 signal-only
    1 层 / legacy index 判据全收（按档三口径；既有档零改动）。"""
    layer_table = ('(layers (0 "F.Cu" mixed) (1 "In1.Cu" power) '
                   '(31 "B.Cu" signal))')
    for tok, version_literal in (
            ("20211014", '"20211014"'),
            ("20171114", "20171114"),   # legacy 裸 token
            ("4", '"4"')):              # 短 token 带引号（禁字符串序比较）
        root = ae.sexpr_min.parse(
            '(kicad_pcb (version %s) %s)' % (version_literal, layer_table))
        layers = ae._parse_copper_layers(root[0], tok)
        assert [l["name"] for l in layers] == ["F.Cu", "In1.Cu", "B.Cu"]
    root = ae.sexpr_min.parse(
        '(kicad_pcb (version 20241229) %s)' % layer_table)
    layers = ae._parse_copper_layers(root[0], "20241229")
    assert [l["name"] for l in layers] == ["B.Cu"]  # signal-only 零改动


def test_legacy_module_form_full_chain_and_arc_length():
    """legacy 档（20171114）module 形态全链：元素视图 + angle 形态弧长
    （R=chord/(2·sin(θ/2))=√2，len=R·θ）+ escape 归因 + dual_form 账。"""
    el = ae.extract_routed_elements(SYNTH_LEGACY, binding=ae.BINDING_ID)
    assert el["board_version"] == "20171114"
    assert [l["name"] for l in el["copper_layers"]] == ["F.Cu", "B.Cu"]
    assert len(el["pads"]) == 2 and len(el["segments"]) == 1
    assert len(el["arcs"]) == 1 and len(el["vias"]) == 1
    arc = el["arcs"][0]
    assert arc["angle_deg"] == 90.0 and arc["mid"] is None
    length = ae._arc_length_mm(arc, "20171114", "arc[0]")
    assert math.isclose(length, math.sqrt(2.0) * math.pi / 2.0,
                        rel_tol=1e-9)
    # escape 归因（U1.P1 与 via/segment 同位 → via 优先）
    att = ae.attribute_pad_escapes(SYNTH_LEGACY, binding=ae.BINDING_ID)
    kinds = {(r["ref"], r["pad"]): r["escape_kind"] for r in att["pads"]}
    assert kinds == {("U1", "1"): "via", ("U1", "2"): "none"}
    # dual_form：module 形态 pad 账非零
    acc = ae.parse_routed_geometry_dual_form(SYNTH_LEGACY,
                                             binding=ae.BINDING_ID)
    assert acc["pad_account_form"] == "module"
    assert acc["net_count"] == 3 and acc["named_net_count"] == 2
    per_net = {n["net_id"]: n for n in acc["per_net"]}
    assert per_net[1]["pad_count"] == 1
    assert per_net[2]["pad_count"] == 1
    assert per_net[0]["pad_count"] == 0  # (net 0 "") 声明在、无 pad
    assert acc["geometry_counts"] == {"segments": 1, "arcs": 1, "vias": 1,
                                      "zones": 1}


def test_dual_form_footprint_pad_account_nonzero_modern():
    """U-R2-5 核心语义：footprint 形态板（20221018 白名单档）pad 账非零
    （check_stage 只扫 module 的恒 0 缺口修复）。"""
    acc = ae.parse_routed_geometry_dual_form(SYNTH_MODERN_FP,
                                             binding=ae.BINDING_ID)
    assert acc["pad_account_form"] == "footprint"
    per_net = {n["net_id"]: n for n in acc["per_net"]}
    assert per_net[1]["pad_count"] == 2
    assert acc["geometry_counts"] == {"segments": 1, "arcs": 0, "vias": 1,
                                      "zones": 1}
    # 与 check_stage 同板对照：pad 账恒 0 的缺口被修复
    cs = check_stage.parse_routed_geometry(SYNTH_MODERN_FP)
    assert sum(n["pad_count"] for n in cs["per_net"]) == 0
    assert sum(n["pad_count"] for n in acc["per_net"]) == 2
    assert cs["geometry_counts"] == acc["geometry_counts"]


def test_dual_form_key_surface_matches_check_stage():
    """id 档账本同构：合成 20171130 板除 pad 账形态外与 check_stage 逐键
    相等；net id 0 口径差异（KiCad 无绑定语义不入账）显式断言。"""
    board = """(kicad_pcb (version 20171130) (host pcbnew "(5.1.4)")

  (layers
    (0 F.Cu signal)
    (31 B.Cu signal)
  )

  (net 0 "")
  (net 1 SIG)
  (net 2 GND)

  (module Lib:A (layer F.Cu) (tedit 0)
    (at 10.0 20.0)
    (fp_text reference U1 (at 0 -2.0) (layer F.SilkS))
    (pad 1 smd rect (at 0.0 0.0) (size 0.3 0.6) (layers F.Cu)
      (net 1 SIG))
    (pad 2 smd rect (at 2.0 0.0) (size 0.3 0.6) (layers B.Cu)
      (net 2 GND))
  )

  (segment (start 10.0 20.0) (end 13.0 20.0) (width 0.2) (layer F.Cu)
    (net 1))
  (segment (start 0.0 0.0) (end 1.0 0.0) (width 0.2) (layer F.Cu)
    (net 0))
  (via (at 13.0 20.0) (size 0.8) (drill 0.4) (layers F.Cu B.Cu)
    (net 1))
  (zone (net 0) (layer B.Cu) (polygon (pts (xy 0 0) (xy 5 5))))
)
"""
    cs = check_stage.parse_routed_geometry(board)
    acc = ae.parse_routed_geometry_dual_form(board, binding=ae.BINDING_ID)
    assert acc["net_count"] == cs["net_count"] == 3
    assert acc["named_net_count"] == cs["named_net_count"]
    assert acc["actual_min"] == cs["actual_min"]
    assert acc["setup"] == cs["setup"]
    assert acc["vias_without_drill_token"] == \
        cs["vias_without_drill_token"] == 0
    # 口径差异（convention_note 声明）：(net 0) segment/zone——check_stage
    # 入 net 0 账（id 0 在声明表）；dual_form 按 KiCad 无绑定语义入
    # items_bound_outside_declared_nets
    assert cs["geometry_counts"] == {"segments": 2, "arcs": 0, "vias": 1,
                                     "zones": 1}
    assert acc["geometry_counts"] == {"segments": 1, "arcs": 0, "vias": 1,
                                      "zones": 0}
    assert cs["items_bound_outside_declared_nets"] == 0
    assert acc["items_bound_outside_declared_nets"] == 2
    per_cs = {n["net_id"]: n for n in cs["per_net"]}
    per_acc = {n["net_id"]: n for n in acc["per_net"]}
    assert per_acc[1]["pad_count"] == per_cs[1]["pad_count"] == 1
    assert per_acc[2]["pad_count"] == per_cs[2]["pad_count"] == 1
    assert per_acc[1]["segment_count"] == per_cs[1]["segment_count"] == 1
    assert per_acc[1]["via_count"] == per_cs[1]["via_count"] == 1


def test_dual_form_existing_board_class_still_failclosed():
    """4 板教训口径在既有档（20241030+）不豁免：jumper 型层上的 segment
    照拒（signal-only 判据零改动的对偶面）；ActualExtError 回退路径留给
    编排层（R6② 先例）——此处只断言异常形态。"""
    with pytest.raises(ae.ActualExtError,
                       match="In4.Cu.*非铜层声明层"):
        ae.parse_routed_geometry_dual_form(SYNTH_K9_JUMPER_LAYER,
                                           binding=ae.BINDING_ID)
    with pytest.raises(ae.ActualExtError,
                       match="In4.Cu.*非铜层声明层"):
        ae.extract_routed_elements(SYNTH_K9_JUMPER_LAYER,
                                   binding=ae.BINDING_ID)


def test_zone_nested_arc_no_layer_failclosed_consistent():
    """zone 嵌套填充弧缺 layer → fail-closed（r1 royalblue54l 型处置
    口径一致，扩档不放松）。"""
    with pytest.raises(ae.ActualExtError, match="arc"):
        ae.extract_routed_elements(SYNTH_ZONE_NESTED_ARC,
                                   binding=ae.BINDING_ID)


def test_neg_bad_boards_fail_closed():
    """坏板 fail-closed：缺 pad layers / 缺 at / 非有限数 / 截断 sexpr。"""
    bad_layers = SYNTH_MODERN_FP.replace('(layers "F.Cu")\n      (net 1 SIG)',
                                         '(net 1 SIG)', 1)
    with pytest.raises(ae.ActualExtError, match="缺 layers"):
        ae.extract_routed_elements(bad_layers, binding=ae.BINDING_ID)
    # 截断 s-expression：SexprError 原样上抛（本模块不捕获不降级）
    from pcbflow.sexpr_min import SexprError
    with pytest.raises(SexprError, match="unbalanced"):
        ae.extract_routed_elements("(kicad_pcb (version 20211014)",
                                   binding=ae.BINDING_ID)
    bad_xy = SYNTH_MODERN_FP.replace("(at 1.0 1.0)", "(at nan 1.0)", 1)
    with pytest.raises(ae.ActualExtError, match="非有限"):
        ae.extract_routed_elements(bad_xy, binding=ae.BINDING_ID)


# ---------------------------------------------------------------------------
# 2. 探针级：corpus-r2 17 板版本门解除实证（datasets 只读）
# ---------------------------------------------------------------------------

def test_corpus_r2_17_board_gate_release():
    """扩档桶 17 板逐板：extract_routed_elements 走通 + dual_form pad 账
    非零 + form 正确；锚定三板计数（usb-gigabit/kria mixed·power 白名单
    非零铜层实证、teres legacy module 形态）。"""
    man = json.load(open(os.path.join(CORPUS_R2, "manifest.json"),
                         encoding="utf-8"))
    targets = [b for b in man["boards"]
               if b.get("kicad_version_token") in R2_NEW_VERSION_TOKENS]
    assert len(targets) == 17, len(targets)
    ok = 0
    for b in targets:
        kicad = [f for f in b["files"] if f.endswith(".kicad_pcb")]
        path = os.path.join(CORPUS_R2, b["dir"], kicad[0])
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        binding = cce.detect_binding(text)
        assert binding == ae.BINDING_ID  # 17 板全 id 档（提案 §2.2）
        el = ae.extract_routed_elements(text, binding=binding)
        acc = ae.parse_routed_geometry_dual_form(text, binding=binding)
        assert el["board_version"] == b["kicad_version_token"]
        assert len(el["copper_layers"]) >= 1  # 零铜层虚假事实不出现
        assert acc["pad_account_form"] in ("module", "footprint")
        pad_sum = sum(n["pad_count"] for n in acc["per_net"])
        assert pad_sum > 0
        anchor = ANCHOR_17.get(b["board_id"])
        if anchor:
            assert el["board_version"] == anchor["v"]
            assert len(el["copper_layers"]) == anchor["cu"]
            assert acc["geometry_counts"]["vias"] == anchor["vias"]
            assert pad_sum == anchor["pads"]
            if "form" in anchor:
                assert acc["pad_account_form"] == anchor["form"]
        ok += 1
    assert ok == 17
    # 白名单实证：usb-gigabit 4 铜层全 mixed/power（signal-only 会得 0）
    path = _corpus_board_path("usb-gigabit-rev-e")
    with open(path, encoding="utf-8") as fh:
        el = ae.extract_routed_elements(fh.read(), binding=ae.BINDING_ID)
    types = {l["type"] for l in el["copper_layers"]}
    assert types <= set(cc.K9_MODERN_COPPER_TYPES)
    assert "signal" not in types  # 全 mixed/power → signal-only 判据=0 层


# ---------------------------------------------------------------------------
# 3. 对齐器 A 口径（evaluate_pad_escape_agreement）
# ---------------------------------------------------------------------------

PROPOSAL_PAD_VERBATIM = (
    "escape 一致性核对（附属，descriptive）：prediction=audit_cmd."
    "escape_check pad_transit[(ref,num)]（重算，同 ffext demand 生成"
    "同源同判；GND/unconnected- 前缀网模型内建跳过）；actual=actual_"
    "ext.attribute_pad_escapes escape_kind∈{via,trace}（同位容差 "
    "0.01mm、层相交含 *.Cu；无 net 绑定 pad 不参与）；两侧同为 per-pad "
    "二元标签，agreement=标签一致率；非 escape_slots 资源量配对"
    "（channels 场级供需无 actual 测量器），不入 M1–M3（沿 Q6/RC-6 "
    "附属先例）")

# E-3（PREREG-RESOURCE-CALIBRATION-R2-frozen §5）：提案 §3.2 原文含句末
# 「。」，库常量已按 E-3 授权补齐；期望随之更新（单字符差、语义恒同）。
PROPOSAL_LC_VERBATIM = (
    "这是「layer_capacity demand 模型对参考态布线占用的贴合度」核对"
    "（链式直连假设 vs 实际走线长度的系统性比），不是层容量校准"
    "（supply 侧无 actual，M1/M2 解锁面仅覆盖 demand 半边）；unit 两侧"
    "一致 mm²。")


def test_pad_escape_agreement_synthetic_2x2_and_conservation():
    r = oae.evaluate_pad_escape_agreement(SYNTH_AGGREEMENT,
                                          binding=ae.BINDING_ID)
    assert r["binding"] == ae.BINDING_ID
    assert r["board_version"] == "20211014"
    rows = {(x["ref"], x["pad"]): x for x in r["pads"]}
    # 2×2 四格（per-pad 语义见夹具注释）
    assert rows[("U1", "1")]["agreement"] is True  # (T,T) via
    assert rows[("U1", "1")]["pred_transit"] is True
    assert rows[("U1", "1")]["actual_escape_kind"] == "via"
    assert rows[("U2", "1")]["agreement"] is True  # (T,T) trace
    assert rows[("U3", "1")]["agreement"] is False  # (T,F)
    assert rows[("U4", "1")]["agreement"] is False  # (T,F)
    assert rows[("U5", "1")]["agreement"] is False  # (F,T)
    assert rows[("U7", "1")]["agreement"] is True   # (F,F)
    assert rows[("U8", "1")]["agreement"] is True   # (F,F)
    # GND：pred 未定义（模型内建跳过）、actual 有定义 → actual_only
    assert rows[("U9", "1")]["pred_transit"] is None
    assert rows[("U9", "1")]["actual_escape_kind"] == "trace"
    assert rows[("U9", "1")]["agreement"] is None
    # 无联名 id pad（两 token (net 6)）：pred None、actual kind=none
    assert rows[("U12", "1")]["pred_transit"] is None
    assert rows[("U12", "1")]["actual_escape_kind"] == "none"
    assert rows[("U12", "1")]["net_key"] == 6
    # 无 net 子节点 pad：两侧皆 None
    assert rows[("U11", "1")]["pred_transit"] is None
    assert rows[("U11", "1")]["actual_escape_kind"] is None
    s = r["summary"]
    assert s["pads_both_defined"] == 8
    assert s["agree"] == 4 and s["disagree"] == 4
    assert s["pads_pred_only"] == 0
    assert s["pads_actual_only"] == 3  # GND×2 + 无联名×1
    assert s["pads_undefined_both"] == 1
    assert s["pads_total"] == len(r["pads"]) == 12
    # 守恒：四类合计 == pad 总数
    assert (s["pads_both_defined"] + s["pads_pred_only"]
            + s["pads_actual_only"] + s["pads_undefined_both"]
            == s["pads_total"])
    assert s["contingency"] == {
        "pred_true_actual_true": 2, "pred_true_actual_false": 2,
        "pred_false_actual_true": 2, "pred_false_actual_false": 2}
    assert s["agreement_rate"] == 0.5
    assert r["convention_verbatim"] == PROPOSAL_PAD_VERBATIM
    assert r["r2_pending"] is True and r["r2_pending_note"]
    assert any("attribute_pad_escapes" in b for b in r["basis"])
    assert any("escape_check" in b for b in r["basis"])


def test_pad_escape_agreement_empty_board_zero_defined():
    """零 defined 板（仅无网 pad）：守恒仍成立、agreement_rate=None 不
    虚构（沿 §0.3）。"""
    text = """(kicad_pcb (version 20211014) (generator pcbnew)
  (layers (0 "F.Cu" signal))
  (footprint "Lib:U" (layer "F.Cu")
    (at 0.0 0.0)
    (property "Reference" "U1" (at 0 0 0) (layer "F.SilkS"))
    (pad "1" smd rect (at 0.0 0.0) (size 0.4 0.4) (layers "F.Cu"))
  )
)
"""
    r = oae.evaluate_pad_escape_agreement(text, binding=ae.BINDING_ID)
    s = r["summary"]
    assert s["pads_total"] == 1 and s["pads_both_defined"] == 0
    assert s["pads_undefined_both"] == 1
    assert s["agreement_rate"] is None


def test_pad_escape_agreement_convention_verbatim():
    assert (oae.CONVENTION_VERBATIM_PAD_ESCAPE
            == PROPOSAL_PAD_VERBATIM)
    # 提案原文逐字（md 反引号块内字符串，剥去包裹引号）
    with open(os.path.join(ROOT, "out", "v3-obs-proposal",
                           "ACTUAL-SIDE-ALIGNMENT-PROPOSAL.md"),
              encoding="utf-8") as f:
        text = f.read()
    i = text.find("escape 一致性核对")
    k = text.find("`", i)
    assert text[i:k].rstrip('"') == oae.CONVENTION_VERBATIM_PAD_ESCAPE


def test_neg_agreement_bad_boards_propagate():
    """A 口径 fail-closed：不捕获不降级——坏板上抛对应异常。"""
    with pytest.raises(cce.CorpusExtError, match="缺 size"):
        oae.evaluate_pad_escape_agreement(
            SYNTH_MODERN_FP.replace("(size 0.4 0.4) (layers \"F.Cu\")\n"
                                    "      (net 1 SIG)",
                                    "(size 0.4) (layers \"F.Cu\")\n"
                                    "      (net 1 SIG)", 1),
            binding=ae.BINDING_ID)
    # 联名冲突（同 net_key 两名）→ CorpusExtError
    conflict = SYNTH_MODERN_FP.replace("(net 1 SIG))\n    (pad \"2\"",
                                       "(net 1 SIGX))\n    (pad \"2\"", 1)
    with pytest.raises(cce.CorpusExtError, match="联名冲突"):
        oae.evaluate_pad_escape_agreement(conflict, binding=ae.BINDING_ID)
    # 档外版本（预测面 detect_binding 先拒）
    with pytest.raises(cce.CorpusExtError, match="不在十档全集"):
        oae.evaluate_pad_escape_agreement(
            SYNTH_MODERN_FP.replace("20221018", "20230408", 1),
            binding=ae.BINDING_ID)
    # 非法 binding 枚举
    with pytest.raises(ae.ActualExtError, match="binding 非法"):
        oae.evaluate_pad_escape_agreement(SYNTH_MODERN_FP, binding="x")


# ---------------------------------------------------------------------------
# 4. 对齐器 LC 口径（evaluate_layer_capacity_demand_fit）
# ---------------------------------------------------------------------------

def test_lc_demand_fit_synthetic_exact():
    """同判据网集复算 + actual 求值精确值：SIG routed 20mm + SIG3 routed
    1.5mm → actual=(21.5)×0.35=7.525 mm²；pred 复算=(20+20+1.5+1.5)×0.35
    =15.05 mm²；对称差={SIG2,SIG4} 如实。"""
    dem = 7.525
    r = oae.evaluate_layer_capacity_demand_fit(
        SYNTH_AGGREEMENT, ffext_layer_demand_value=dem)
    assert r["binding"] == ae.BINDING_ID
    assert r["pitch_mm"] == config.AUDIT_TRACK_PITCH_MM == 0.35
    assert r["actual"] == {"value": 7.525, "unit": "mm2"}
    assert r["E"] == 0.0 and r["e"] == 0.0
    assert r["pred_demand_value_recomputed_mm2"] == 15.05
    assert r["nets_pred"] == ["SIG", "SIG2", "SIG3", "SIG4"]
    assert r["nets_actual"] == ["SIG", "SIG3"]
    assert r["net_set_symmetric_diff"] == ["SIG2", "SIG4"]
    assert r["net_lengths_mm"] == {"SIG": 20.0, "SIG3": 1.5}
    assert r["convention_verbatim"] == PROPOSAL_LC_VERBATIM
    assert r["r2_pending"] is True
    assert any("AUDIT_TRACK_PITCH" in b for b in r["basis"])
    # GND/unconnected- 排除口径：nets_pred 不含 GND
    assert "GND" not in r["nets_pred"]


def test_lc_convention_verbatim():
    assert (oae.CONVENTION_VERBATIM_LAYER_CAPACITY
            == PROPOSAL_LC_VERBATIM)
    with open(os.path.join(ROOT, "out", "v3-obs-proposal",
                           "ACTUAL-SIDE-ALIGNMENT-PROPOSAL.md"),
              encoding="utf-8") as f:
        text = f.read()
    i = text.find("这是「layer_capacity demand")
    # E-3：截取含句末「。」（提案原文句号在位），与库常量全等
    k = text.find("；unit 两侧一致 mm²。", i) + len("；unit 两侧一致 mm²。")
    assert text[i:k].replace("**", "") \
        == oae.CONVENTION_VERBATIM_LAYER_CAPACITY


def test_lc_actual_zero_e_none_row_kept():
    """actual=0（selected 网无 routed）→ actual 行保留 0.0、e=None（沿
    §0.3），不虚构比例。"""
    text = """(kicad_pcb (version 20211014) (generator pcbnew)
  (layers (0 "F.Cu" signal))
  (net 0 "")
  (net 1 SIG)
  (footprint "Lib:U" (layer "F.Cu")
    (at 0.0 0.0)
    (property "Reference" "U1" (at 0 0 0) (layer "F.SilkS"))
    (pad "1" smd rect (at 0.0 0.0) (size 0.4 0.4) (layers "F.Cu")
      (net 1 SIG))
  )
  (footprint "Lib:U" (layer "F.Cu")
    (at 3.0 0.0)
    (property "Reference" "U2" (at 0 0 0) (layer "F.SilkS"))
    (pad "1" smd rect (at 0.0 0.0) (size 0.4 0.4) (layers "F.Cu")
      (net 1 SIG))
  )
)
"""
    r = oae.evaluate_layer_capacity_demand_fit(
        text, ffext_layer_demand_value=1.05)
    assert r["actual"] == {"value": 0.0, "unit": "mm2"}
    assert r["E"] == -1.05
    assert r["e"] is None
    assert r["nets_actual"] == []
    assert r["net_set_symmetric_diff"] == ["SIG"]


def test_lc_ffext_demand_none_row_null():
    """ffext demand=None（零封装板诚实 null）→ 整行 null+reason（不虚构
    配对面）；其余对账字段照常。"""
    r = oae.evaluate_layer_capacity_demand_fit(
        SYNTH_AGGREEMENT, ffext_layer_demand_value=None)
    assert r["actual"]["value"] is None and r["actual"]["unit"] is None
    assert "not_available_reason" in r["actual"]
    assert "demand=None" in r["actual"]["not_available_reason"]
    assert r["E"] is None and r["e"] is None


def test_lc_legacy_arc_same_source_length():
    """arc 弧长同源（actual_ext._arc_length_mm）：legacy angle 形态弧入
    actual 求值——len=√2·π/2 × pitch；零长 segment 同入账（欧氏 0）。"""
    text = """(kicad_pcb (version 20171114) (host pcbnew "(4.0.7)")
  (layers
    (0 F.Cu signal)
  )
  (net 0 "")
  (net 1 SIG)
  (module Lib:A (layer F.Cu) (tedit 0)
    (at 0.0 0.0)
    (fp_text reference U1 (at 0 -2.0) (layer F.SilkS))
    (pad 1 smd rect (at 0.0 0.0) (size 0.4 0.4) (layers F.Cu)
      (net 1 SIG))
  )
  (module Lib:A (layer F.Cu) (tedit 0)
    (at 2.0 0.0)
    (fp_text reference U2 (at 0 -2.0) (layer F.SilkS))
    (pad 1 smd rect (at 0.0 0.0) (size 0.4 0.4) (layers F.Cu)
      (net 1 SIG))
  )
  (arc (start 0.0 0.0) (end 2.0 0.0) (angle 90) (width 0.2) (layer F.Cu)
    (net 1))
)
"""
    r = oae.evaluate_layer_capacity_demand_fit(
        text, ffext_layer_demand_value=0.7)
    expected = math.sqrt(2.0) * math.pi / 2.0 * 0.35
    assert math.isclose(r["actual"]["value"], round(expected, 3),
                        rel_tol=0, abs_tol=1e-9)
    assert r["net_lengths_mm"] == {"SIG": round(math.sqrt(2.0)
                                                * math.pi / 2.0, 9)}
    assert r["net_set_symmetric_diff"] == []


def test_lc_collinear_arc_raises():
    """arc 三点共线（退化弧）→ ActualExtError 上抛（fail-closed）。"""
    bad = SYNTH_MODERN_FP.replace(
        '(segment (start 1.0 1.0) (end 4.0 1.0) (width 0.25) (layer "F.Cu")\n'
        '    (net 1))',
        '(arc (start 1.0 1.0) (mid 2.5 1.0) (end 4.0 1.0) (width 0.25) '
        '(layer "F.Cu") (net 1))')
    with pytest.raises(ae.ActualExtError, match="共线"):
        oae.evaluate_layer_capacity_demand_fit(
            bad, ffext_layer_demand_value=1.0)


# ---------------------------------------------------------------------------
# 5. r1 回归钉：54 板 actual 侧关键输出重算（逐值相等）
# ---------------------------------------------------------------------------

_R62_REASON_PREFIX = ("actual_ext R6② 板级 fail-closed（逐 facet 独立"
                      "判定，不影响计数类行）：")
_REASON_MAX = 300


def test_r1_54_board_actual_side_regression_pin():
    """r1 语料 54 板 actual 侧关键输出重算（扩档后库代码）：
    - via 计数面（via_budget:board 行 actual）：id 档 check_stage.parse_
      routed_geometry / 名档 actual_ext.parse_routed_geometry_by_net_name
      （rows-r1 batch-build 同构路由）重算 == 盘面值；
    - padload 面（signal_layer_pad_load:* 行 actual）：actual_ext.count_
      pads_per_layer 逐层 pad_count 重算 == 盘面值；4 板教训板
      ActualExtError 消息与行 not_available_reason 逐字比对（截断口径同
      observation._REASON_MAX）。
    扩档零改既有行为的逐值级证明（54/54 全对账）。
    """
    summary, boards = _rows_r1_boards()
    assert summary["r62_failclosed_boards"] == [
        "kicaddemo-complex_hierarchy-complex_hierarchy",
        "kicaddemo-jetson-agx-thor-baseboard-jetson-agx-thor-baseboard",
        "kicaddemo-openair-max-one-air-max",
        "kicaddemo-royalblue54l_feather-royalblue54l-feather"]
    checked_via = checked_padload = checked_r62_fail = 0
    for b in boards:
        pid = b["profile_id"]
        rows = json.load(open(os.path.join(
            ROOT, "out", "v3-obs", "rows-r1", "rows", b["pool"],
            pid + ".json"), encoding="utf-8"))
        board_rel = b["board_path_rel"]
        with open(os.path.join(ROOT, board_rel), encoding="utf-8") as f:
            text = f.read()
        binding = cce.detect_binding(text)
        # via 计数面（router 与 rows-r1 batch-build 同构）
        if binding == ae.BINDING_ID:
            geo = check_stage.parse_routed_geometry(text)
        else:
            geo = ae.parse_routed_geometry_by_net_name(text)
        vias_recomputed = geo["geometry_counts"]["vias"]
        padload_recomputed = None
        r62_exc = None
        try:
            r62 = ae.count_pads_per_layer(text, binding=binding)
            padload_recomputed = {e["layer"]: e["pad_count"]
                                  for e in r62["per_layer"]}
        except ae.ActualExtError as exc:
            r62_exc = exc
        via_row = pad_rows = None
        for row in rows:
            rid = row["row_id"]
            if rid.startswith("via_budget:"):
                via_row = row
            elif rid.startswith("signal_layer_pad_load:"):
                (pad_rows := pad_rows or {})[rid.split(":", 1)[1]] = row
        assert via_row is not None, pid
        assert via_row["actual"]["value"] == vias_recomputed, pid
        checked_via += 1
        if r62_exc is not None:
            expected_reason = _R62_REASON_PREFIX + (
                f"ActualExtError: {r62_exc}")[:_REASON_MAX]
            for layer, row in pad_rows.items():
                assert row["actual"]["value"] is None, (pid, layer)
                assert row["actual"]["not_available_reason"] \
                    == expected_reason, (pid, layer)
                checked_r62_fail += 1
        else:
            for layer, row in pad_rows.items():
                assert row["actual"]["value"] \
                    == padload_recomputed[layer], (pid, layer)
                checked_padload += 1
    # 盘面对账（batch-summary row_class_totals）
    assert summary["row_class_totals"]["sixkind_via_budget"] == 54
    assert summary["row_class_totals"]["padload"] == 146
    assert checked_via == 54
    assert checked_padload + checked_r62_fail == 146
    # 4 板教训板 padload 行全 null+reason（complex_hierarchy 1 + jetson 9
    # + openair 2 + royalblue 8 = 20；重算异常消息逐字比对口径同
    # observation._REASON_MAX=300 截断）
    assert checked_r62_fail == 20
