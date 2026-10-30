# -*- coding: utf-8 -*-
"""KiCad adapter 测试（P1 L0 门项）。

覆盖：
- s-expression 解析器单测（引号内括号 / 转义 / 嵌套 / 截断输入 fail-closed）；
- 端点极值确定性单测（最远两点 / 平手字典序 / 退化单点）；
- ptype 确定性映射、网名净化单测；
- 合成板转换（坐标旋转 / workspace 精确包围盒 / report 计数 / 新旧格式宽容）；
- 非法输入 AdapterError（未声明 net 引用 / 0 pad 网 / 未知层 / 截断 / 重复声明…）；
- C2 十板（预注册清单+冻结 hash）：source_sha256 对账 manifest、round-trip
  （板 dict → canonical 字节 → 重读 → load_board → 再序列化字节全等）、同源双跑
  同 canonical 字节。语料只读（manifest + 各板 .kicad_pcb），测试落盘仅用 tmp_path。
"""
import json
import os

import pytest

from v5 import canonical
from v5.adapters.kicad_adapter import (
    ADAPTER_NAME,
    ADAPTER_NAME_V050,
    WORKSPACE_MARGIN_MM,
    AdapterError,
    classify_ptype,
    convert_bytes,
    convert_bytes_with_report,
    convert_file,
    convert_file_with_report,
    farthest_endpoints,
    parse_sexpr,
    sanitize_net_id,
)
from v5.board import compute_board_sha256, load_board

# --------------------------------------------------------------- 语料（只读）

CORPUS_MANIFEST = "E:/ZCodeData/.zcode/workspace/default/tools/pcbflow/datasets/corpus-r2-r1/manifest.json"

# C2 层十板预注册清单（board_id, board_file_sha256 冻结值；与 DISPATCH-LOG 登记一致）。
C2_BOARDS = [
    ("vga-panel-breakout",
     "e12714cf8d52124cc18e4816c02cb30c3d832259454f258c9d09ea9b17ca1b39"),
    ("si-simulation-test-board",
     "ad22910fb65d87b9506a860a2fc9a6ad8ddb0af7743be3a9df40e4edd2c2a318"),
    ("alvium-flex-csi-100mm-double-same-side",
     "7270c9edc647ed75caa524c80244157f0c9535668f8b9f218e343a34db774338"),
    ("anavi-fume-extractor",
     "cf95579b182d4b2175d1fb53ac21bb4d8d19a6476db8b03816eb0c2f76484993"),
    ("ice40hx1k-evb-rev-b",
     "18407352cb5c31bc5c93804af764220f158017b8d2e7f2da5585a5155d188ca1"),
    ("esp32-devkit-lipo-rev-c",
     "3e7cd18fe5abcb4a93fd3e95934a74b7d396bcf0992da7861c70d9e87191558e"),
    ("badge-pcb",
     "d4a4936142d30e9c20bbbab5cb8cc681a43c16c159f6de3d9abfdfde4849aa32"),
    ("torxhat",
     "fb6097880a515424c7ac67c56330dfecece8eb70b79d21047e2516ec33e14aca"),
    ("anthc",
     "dce441d386f04de0619e9acfc655dff28db38fa8bc990c96664e0de382962d1b"),
    ("teres-pcb1-a64-main-rev-c",
     "7ba40451dc452f0bc74f8b9e1414a06b9174c18a39acc8b4c211567def7b9eae"),
]
C2_IDS = [b[0] for b in C2_BOARDS]

# --------------------------------------------------------------- 合成夹具

# 旧格式（KiCad 5，version 20171130）：module/pad、90° 旋转、引号串含括号。
MINI_V5 = """(kicad_pcb (version 20171130) (host pcbnew "(5.1.0)-1")
  (general (thickness 1.6))
  (layers (0 F.Cu signal) (31 B.Cu signal))
  (net 0 "")
  (net 1 GND)
  (net 2 SIG)
  (module M:FP (layer F.Cu) (at 10 10 90)
    (pad 1 thru_hole circle (at 1 0) (size 2 2) (drill 1) (layers *.Cu *.Mask) (net 1 GND))
    (pad 2 thru_hole circle (at -1 0) (size 2 2) (drill 1) (layers *.Cu *.Mask) (net 2 SIG))
    (pad 3 thru_hole circle (at -5 0) (size 2 2) (drill 1) (layers *.Cu *.Mask) (net 2 SIG))
  )
  (segment (start 10 10) (end 20 10) (width 0.25) (layer F.Cu) (net 2))
  (via (at 11 10) (size 0.8) (drill 0.4) (layers F.Cu B.Cu) (net 1))
  (gr_rect (start 0 0) (end 30 30) (layer Edge.Cuts) (width 0.05))
  (fp_text reference REF (at 0 -2) (layer F.SilkS) (effects (font (size 1 1))))
  (zone (net 1) (net_name GND) (layer F.Cu)
    (polygon (pts (xy 0 0) (xy 0 20) (xy 20 20) (xy 20 0))))
)
"""

# 新格式（KiCad 6+ 语风）：footprint/property、引号层名、多行 via、+前缀网名、含空格网名。
MINI_V6 = """(kicad_pcb
\t(version 20241229)
\t(generator "pcbnew")
\t(generator_version "9.0")
\t(layers
\t\t(0 "F.Cu" signal)
\t\t(2 "B.Cu" signal)
\t)
\t(net 0 "")
\t(net 1 "GND")
\t(net 2 "+3.3V")
\t(net 3 "SIG A")
\t(footprint "Conn:TagConnect" (layer "F.Cu") (uuid "aaaaaaaa-0000-0000-0000-000000000001")
\t\t(at 20 30 180)
\t\t(property "Reference" "J1" (at 0 -3 0) (layer "F.SilkS") (uuid "b"))
\t\t(pad "1" smd roundrect (at 1.905 0) (size 1.0 1.6)
\t\t\t(layers "F.Cu" "F.Paste" "F.Mask") (net 2 "+3.3V"))
\t\t(pad "2" smd roundrect (at -1.905 0) (size 1.0 1.6)
\t\t\t(layers "F.Cu" "F.Paste" "F.Mask") (net 1 "GND"))
\t\t(pad "3" smd roundrect (at 0 3.81) (size 1.0 1.6)
\t\t\t(layers "F.Cu" "F.Paste" "F.Mask") (net 3 "SIG A"))
\t)
\t(via
\t\t(at 18 30)
\t\t(size 0.6)
\t\t(drill 0.3)
\t\t(layers "F.Cu" "B.Cu")
\t\t(net 2 "+3.3V")
\t)
\t(segment
\t\t(start 19.5 30)
\t\t(end 21.905 30)
\t\t(width 0.2)
\t\t(layer "F.Cu")
\t\t(net 2 "+3.3V")
\t)
)
"""

# 弧段（KiCad 6+ track arc）+ 4 层乱序层号（anthc 语风：B.Cu=2/In1=4/In2=6）。
MINI_ARC = """(kicad_pcb
  (version 20211014)
  (layers (2 B.Cu power) (4 In1.Cu signal) (0 F.Cu signal) (6 In2.Cu signal))
  (net 0 "")
  (net 1 GND)
  (module M:X (layer F.Cu) (at 0 0)
    (pad 1 thru_hole circle (at 0 0) (size 1 1) (drill 0.5) (layers *.Cu) (net 1 GND)))
  (arc (start 0 0) (mid 5 1) (end 10 0) (width 0.2) (layer F.Cu) (net 1))
)
"""


def _mini_bytes(text=MINI_V5):
    return text.encode("utf-8")


# --------------------------------------------------------------- 解析器单测

def test_parse_quoted_string_with_parens():
    root = parse_sexpr('(kicad_pcb (host pcbnew "(5.1.0)-1") (net 1 "A (B) C"))')
    assert root[0] == "kicad_pcb"
    host = root[1]
    assert host[0] == "host" and host[1] == "pcbnew" and host[2] == "(5.1.0)-1"
    net = root[2]
    assert net[0] == "net" and net[1] == "1" and net[2] == "A (B) C"


def test_parse_escapes():
    root = parse_sexpr(r'(kicad_pcb (name "a\"b\\c\nd\te"))')
    name = root[1]
    assert name[1] == 'a"b\\c\nd\te'


def test_parse_nesting():
    root = parse_sexpr("(kicad_pcb (a (b (c 1 2) (d \"x\")) 3))")
    a = root[1]
    assert a[0] == "a" and a[2] == "3"
    b = a[1]
    assert b[0] == "b"
    assert b[1] == ["c", "1", "2"]
    assert b[2] == ["d", "x"]


def test_parse_empty_and_whitespace_only():
    for text in ("", "   \n\t "):
        with pytest.raises(AdapterError):
            parse_sexpr(text)


def test_parse_truncated_fail_closed():
    cases = [
        "(kicad_pcb (version 20171130)",      # EOF 括号未闭合
        '(kicad_pcb (net 1 "abc)',            # 引号未闭合（截断）
        '(net 1 "abc" ) )',                   # 多余右括号
        "(kicad_pcb) (kicad_pcb)",            # 顶层两个表
        "(foo 1)",                            # 根不是 kicad_pcb
        '(kicad_pcb "尾随孤立引号)',           # 字符串吞掉结构后括号失衡
    ]
    for text in cases:
        with pytest.raises(AdapterError):
            parse_sexpr(text)


def test_convert_invalid_utf8_fail_closed():
    with pytest.raises(AdapterError) as ei:
        convert_bytes(b"(kicad_pcb \xff\xfe)", "x", "mem")
    assert "UTF-8" in str(ei.value)


# --------------------------------------------------------------- 端点极值确定性

def test_farthest_pair_clear_max():
    a, b = farthest_endpoints([(0.0, 0.0), (10.0, 0.0), (1.0, 1.0)])
    assert (a, b) == ((0.0, 0.0), (10.0, 0.0))


def test_farthest_pair_tie_lexicographic():
    # 正方形四角全对同距 → 平手取字典序最小的一对 ((0,0),(1,1))。
    a, b = farthest_endpoints([(1.0, 1.0), (0.0, 0.0), (0.0, 1.0), (1.0, 0.0)])
    assert (a, b) == ((0.0, 0.0), (1.0, 1.0))


def test_farthest_pair_single_point_degenerate():
    a, b = farthest_endpoints([(3.0, 4.0)])
    assert (a, b) == ((3.0, 4.0), (3.0, 4.0))


def test_farthest_pair_empty_fails():
    with pytest.raises(AdapterError):
        farthest_endpoints([])


# --------------------------------------------------------------- ptype / 净化映射

def test_ptype_mapping_table():
    pwr = ["+3V3", "+12V", "+BATT", "GND", "GND1", "GNDA", "VCC", "VDD", "VSS",
           "AGND", "DGND", "MOTOR_PWR", "POWER_IN", "pwr_enable", "power"]
    misc = ["SIG", "Net-(J1-Pad4)", "/clk", "SDA", "usb_dp", "BUTTON"]
    for name in pwr:
        assert classify_ptype(name) == "PWR", name
    for name in misc:
        assert classify_ptype(name) == "MISC", name


def test_sanitize_net_id():
    assert sanitize_net_id("+3.3V") == "_3.3V"
    assert sanitize_net_id("Net-(J1-Pad4)") == "Net-_J1-Pad4_"
    assert sanitize_net_id("SIG A") == "SIG_A"
    assert sanitize_net_id("") == "_"
    assert sanitize_net_id("///") == "___"


# --------------------------------------------------------------- 合成板转换

def test_mini_v5_converts_and_loads():
    board = convert_bytes(_mini_bytes(), "mini-v5", "synthetic://mini-v5")
    assert load_board(board)["board_id"] == "mini-v5"
    assert board["schema_version"] == "v5.board.v1"
    assert board["zones"] == []
    assert board["principle_registry"] == []
    assert [l["id"] for l in board["stackup"]] == ["F.Cu", "B.Cu"]
    for layer in board["stackup"]:
        assert layer["kind"] == "signal"
        assert layer["preferred_direction"] == "any"
        assert layer["available"] is True
    assert board["hard_rules"]["R5"] == {"min_clearance_mm": 0.5}
    prov = board["provenance"]
    assert prov["source_type"] == "kicad_pcb"
    # V5-R1 翻转披露（2026-09-25）：adapter v0.3.0→v0.4.0（全 pad 质心集+topology）
    # V5-R7 翻转披露（2026-10-04）：adapter v0.4.0→v0.5.0（net class 双源+
    # Edge_Cuts 真实板轮廓；夹具 gr_line→gr_rect=Edge_Cuts 开口轮廓自本批起
    # fail-closed，R8 F1 先例同步）
    # adapter-fix-r1（2026-10-23）双版本串：纯现代夹具（无方言路径激活）落
    # ADAPTER_NAME_V050=v0.5.0 原串（存量板逐字节零漂移合同）；v0.6.0 仅在
    # FA-5a/b/c/d 方言路径激活的板出现（方言夹具测试=
    # out/adapter-fix-r1/tests/test_dialect_fixes.py）。
    assert prov["adapter"] == ADAPTER_NAME_V050 == "kicad-adapter v0.5.0"
    assert prov["source_uri"] == "synthetic://mini-v5"
    assert prov["source_sha256"] == canonical.sha256_bytes(_mini_bytes())
    assert prov["board_sha256"] == compute_board_sha256(board)


def test_mini_v5_partitions_endpoints_and_policy():
    board = convert_bytes(_mini_bytes(), "mini-v5", "synthetic://mini-v5")
    parts = dict((p["partition_id"], p) for p in board["partitions"])
    # pad 绝对坐标 = footprint(10,10,90°) + R(90)·局部：pad1(1,0)→(10,9)；90° 用精确三角值。
    gnd = parts["PT-GND"]
    assert gnd["ptype"] == "PWR"
    assert gnd["geometry"]["endpoints"] == [[10.0, 9.0], [10.0, 9.0]]
    assert gnd["note"] == "adapter: 1 pad abstracted to 2 coincident endpoints (degenerate)"
    sig = parts["PT-SIG"]
    assert sig["ptype"] == "MISC"
    assert sig["geometry"]["endpoints"] == [[10.0, 11.0], [10.0, 15.0]]
    assert sig["note"] == "adapter: 2 pads -> 2 terminal nodes (R1 explicit topology)"
    for p in parts.values():
        assert p["layer_policy"] == "any"
        assert p["width_prior"] == {"w_min": 0.3, "w_max": 1.0}
        assert p["current_a"] == 0
        assert p["speed_class"] == "unknown"
    nets = dict((n["net_id"], n) for n in board["nets"])
    assert set(nets) == {"GND", "SIG"}
    assert nets["GND"]["partitions"] == ["PT-GND"]
    assert nets["SIG"]["partitions"] == ["PT-SIG"]


def test_mini_v5_workspace_exact_bbox_with_margin():
    board = convert_bytes(_mini_bytes(), "mini-v5", "synthetic://mini-v5")
    ws = board["workspace"]
    # pad: x[9,11]∪{pad3 y 到 16}；segment: x[9.875,20.125]；via r=0.4；全部含于
    # 铜包围盒 x[9,20.125]、y[8,16]，外扩 WORKSPACE_MARGIN_MM=1.0（精确浮点）。
    assert ws == {"x_min": 8.0, "y_min": 7.0, "x_max": 21.125, "y_max": 17.0}
    assert WORKSPACE_MARGIN_MM == 1.0


def test_mini_v5_report_counts():
    board, report = convert_bytes_with_report(_mini_bytes(), "mini-v5", "synthetic://mini-v5")
    assert report["kicad_version"] == "20171130"
    assert report["net_count"] == 2
    assert report["footprint_count"] == 1
    assert report["pad_count"] == 3
    assert report["netted_pad_count"] == 3
    assert report["segment_count"] == 1
    assert report["arc_count"] == 0
    assert report["via_count"] == 1
    assert report["ignored_zones"] == 1
    assert report["ignored_drawings"] == 1  # fp_text（装饰性跳过；V5-R7 起
    # Edge_Cuts 图元入 outline_mm 不再计装饰——原 gr_line@Edge.Cuts 夹具换 gr_rect）


def test_mini_v6_new_format_tolerated():
    data = MINI_V6.encode("utf-8")
    board = convert_bytes(data, "mini-v6", "synthetic://mini-v6")
    load_board(board)
    assert [l["id"] for l in board["stackup"]] == ["F.Cu", "B.Cu"]
    parts = dict((p["partition_id"], p) for p in board["partitions"])
    # 180° 精确旋转：pad(1.905,0) → (20-1.905, 30)。
    assert parts["PT-_3.3V"]["geometry"]["endpoints"] == [[18.095, 30.0], [18.095, 30.0]]
    assert parts["PT-_3.3V"]["ptype"] == "PWR"  # '+' 前缀
    assert parts["PT-GND"]["ptype"] == "PWR"
    assert "PT-SIG_A" in parts  # 含空格网名净化
    nets = dict((n["net_id"], n) for n in board["nets"])
    assert set(nets) == {"GND", "+3.3V", "SIG A"}


def test_mini_arc_and_layer_order_by_name():
    data = MINI_ARC.encode("utf-8")
    board = convert_bytes(data, "mini-arc", "synthetic://mini-arc")
    load_board(board)
    # 层号乱序（B.Cu=2/In1=4/In2=6）仍按栈名排序：F → In1 → In2 → B。
    assert [l["id"] for l in board["stackup"]] == ["F.Cu", "In1.Cu", "In2.Cu", "B.Cu"]
    # 弧控制点 (0,0)/(5,1)/(10,0)（外接圆心 (5,-12)、r=13）；弧段 + pad 都必须被工作区包含。
    ws = board["workspace"]
    assert ws["x_min"] <= -0.5 - WORKSPACE_MARGIN_MM + 1e-9
    assert ws["x_max"] >= 10.1 + WORKSPACE_MARGIN_MM - 1e-9
    assert ws["y_max"] >= 1.1 + WORKSPACE_MARGIN_MM - 1e-9
    _board, report = convert_bytes_with_report(data, "mini-arc", "synthetic://mini-arc")
    assert report["arc_count"] == 1


def test_arc_axis_extreme_beyond_control_points():
    # 圆心 (5,0) r=5 的弧，扫掠 [200°,340°]，跨 270° 轴向极值 (5,-5)；
    # 三个控制点最低 y=-4.698，极值点必须在包围盒内（检验轴向极值分支，非控制点兜底）。
    arc = """(kicad_pcb
  (layers (0 F.Cu signal))
  (net 0 "")
  (net 1 GND)
  (module M:X (layer F.Cu) (at 100 100)
    (pad 1 thru_hole circle (at 0 0) (size 1 1) (drill 0.5) (layers *.Cu) (net 1 GND)))
  (arc (start 0.301537 -1.710101) (mid 3.289899 -4.698463) (end 9.698463 -1.710101)
    (width 0.2) (layer F.Cu) (net 1))
)
"""
    board = convert_bytes(arc.encode("utf-8"), "arc-extreme", "synthetic://arc-extreme")
    ws = board["workspace"]
    # 极值 y = -5，半宽 0.1，余量 1.0 → y_min ≈ -6.1（允许外接圆心求解的末位浮点差）。
    assert -6.2 < ws["y_min"] <= -6.0


def test_convert_file_matches_convert_bytes(tmp_path):
    p = tmp_path / "mini.kicad_pcb"
    p.write_bytes(_mini_bytes())
    board_f = convert_file(str(p), "mini-file")
    uri = board_f["provenance"]["source_uri"]
    assert os.path.isabs(uri)
    assert uri.replace("\\", "/").endswith("mini.kicad_pcb")
    # 同 bytes + 同 source_uri ⇒ 两条入口产出逐字节相同的板（source_uri 进哈希链，
    # 故必须以相同 uri 对喂 convert_bytes 才可比较全等）。
    with open(str(p), "rb") as f:
        data = f.read()
    board_b = convert_bytes(data, "mini-file", uri)
    assert canonical.canonical_json(board_f) == canonical.canonical_json(board_b)


def test_duplicate_partition_id_gets_deterministic_suffix():
    # 两个不同网名 "A B" 与 "A/B" 净化后同为 "A_B" → 网号升序追加 "_2" 后缀，全程确定性。
    # （同名网在 _declared_nets 已 fail-closed 拒绝，故冲突只能来自净化碰撞。）
    conflict = MINI_V5.replace("(net 1 GND)", '(net 1 "A B")').replace(
        "(net 2 SIG)", '(net 2 "A/B")')
    board = convert_bytes(conflict.encode("utf-8"), "dup-net", "synthetic://dup")
    pids = [p["partition_id"] for p in board["partitions"]]
    assert sorted(pids) == ["PT-A_B", "PT-A_B_2"]


# --------------------------------------------------------------- 非法输入 fail-closed

def _convert_or_error(text):
    return convert_bytes(text.encode("utf-8"), "bad", "synthetic://bad")


def test_segment_undeclared_net_fail_closed():
    bad = MINI_V5.replace("(width 0.25) (layer F.Cu) (net 2)",
                          "(width 0.25) (layer F.Cu) (net 9)")
    with pytest.raises(AdapterError) as ei:
        _convert_or_error(bad)
    assert "未声明" in str(ei.value)


def test_pad_undeclared_net_fail_closed():
    bad = MINI_V5.replace("(layers *.Cu *.Mask) (net 2 SIG))",
                          "(layers *.Cu *.Mask) (net 9 SIG))", 1)
    with pytest.raises(AdapterError):
        _convert_or_error(bad)


def test_via_undeclared_net_fail_closed():
    bad = MINI_V5.replace("(layers F.Cu B.Cu) (net 1))",
                          "(layers F.Cu B.Cu) (net 9))")
    with pytest.raises(AdapterError):
        _convert_or_error(bad)


def test_net_with_zero_pads_fail_closed():
    bad = MINI_V5.replace("(net 2 SIG)", "(net 2 SIG)\n  (net 3 LONELY)")
    with pytest.raises(AdapterError) as ei:
        _convert_or_error(bad)
    assert "无任何 pad" in str(ei.value)


def test_segment_unknown_layer_fail_closed():
    bad = MINI_V5.replace("(layer F.Cu) (net 2))", "(layer In7.Cu) (net 2))")
    with pytest.raises(AdapterError) as ei:
        _convert_or_error(bad)
    assert "不在启用铜层" in str(ei.value)


def test_missing_layers_block_fail_closed():
    bad = MINI_V5.replace("(layers (0 F.Cu signal) (31 B.Cu signal))", "")
    with pytest.raises(AdapterError) as ei:
        _convert_or_error(bad)
    assert "(layers)" in str(ei.value)


def test_no_copper_geometry_fail_closed():
    bad = """(kicad_pcb (layers (0 F.Cu signal)) (net 1 GND)
  (gr_line (start 0 0) (end 5 5) (layer Edge.Cuts) (width 0.05)))
"""
    with pytest.raises(AdapterError) as ei:
        _convert_or_error(bad)
    assert "无任何" in str(ei.value)


def test_duplicate_net_names_fail_closed():
    bad = MINI_V5.replace("(net 2 SIG)", "(net 2 GND)")
    with pytest.raises(AdapterError) as ei:
        _convert_or_error(bad)
    assert "重复" in str(ei.value)


def test_duplicate_net_number_conflict_fail_closed():
    bad = MINI_V5.replace("(net 2 SIG)", "(net 2 SIG)\n  (net 2 OTHER)")
    with pytest.raises(AdapterError):
        _convert_or_error(bad)


def test_duplicate_net_number_same_name_tolerated():
    bad = MINI_V5.replace("(net 2 SIG)", "(net 2 SIG)\n  (net 2 SIG)")
    board = _convert_or_error(bad)
    assert len(board["nets"]) == 2


def test_non_numeric_field_fail_closed():
    bad = MINI_V5.replace("(at 10 10 90)", "(at abc 10 90)")
    with pytest.raises(AdapterError):
        _convert_or_error(bad)


def test_top_level_bare_token_fail_closed():
    bad = MINI_V5.replace("(general (thickness 1.6))",
                          "(general (thickness 1.6)) stray_atom")
    with pytest.raises(AdapterError) as ei:
        _convert_or_error(bad)
    assert "裸 token" in str(ei.value)


def test_truncated_board_fail_closed():
    with pytest.raises(AdapterError):
        _convert_or_error(MINI_V5[: len(MINI_V5) // 2])


# --------------------------------------------------------------- C2 十板（只读语料）

@pytest.fixture(scope="session")
def c2_converted():
    """转换 C2 十板（session 级，一次转换多处断言）。语料缺失 → skip（环境性）。"""
    if not os.path.exists(CORPUS_MANIFEST):
        pytest.skip("语料 manifest 不存在: %s" % CORPUS_MANIFEST)
    with open(CORPUS_MANIFEST, encoding="utf-8") as f:
        manifest = json.load(f)
    by_id = dict((b["board_id"], b) for b in manifest["boards"])
    root = os.path.dirname(CORPUS_MANIFEST)
    out = {"manifest": manifest, "by_id": by_id, "boards": {}, "paths": {}}
    for board_id, _sha in C2_BOARDS:
        assert board_id in by_id, "manifest 缺 C2 板登记: %s" % board_id
        pcbs = [f for f in by_id[board_id]["files"] if f.endswith(".kicad_pcb")]
        assert len(pcbs) == 1, "C2 板 %s 的 .kicad_pcb 登记不唯一" % board_id
        path = os.path.join(root, by_id[board_id]["dir"], pcbs[0])
        assert os.path.exists(path), "C2 板文件缺失（清单冻结板不许缺席）: %s" % path
        out["paths"][board_id] = path
        out["boards"][board_id] = convert_file(path, board_id)
    return out


def test_c2_manifest_hashes_match_frozen_registry(c2_converted):
    for board_id, sha in C2_BOARDS:
        assert c2_converted["by_id"][board_id]["board_file_sha256"] == sha


@pytest.mark.parametrize("board_id,sha", C2_BOARDS, ids=C2_IDS)
def test_c2_source_sha256_matches_manifest(c2_converted, board_id, sha):
    prov = c2_converted["boards"][board_id]["provenance"]
    assert prov["source_type"] == "kicad_pcb"
    # V5-R1 翻转披露（2026-09-25）：adapter v0.3.0→v0.4.0（全 pad 质心集+topology）
    # V5-R7 翻转披露（2026-10-04）：adapter v0.4.0→v0.5.0（R8 F1 先例同步）
    assert prov["adapter"] == "kicad-adapter v0.5.0"
    assert prov["source_sha256"] == sha
    assert prov["source_sha256"] == c2_converted["by_id"][board_id]["board_file_sha256"]


@pytest.mark.parametrize("board_id,sha", C2_BOARDS, ids=C2_IDS)
def test_c2_load_board_passes(c2_converted, board_id, sha):
    board = c2_converted["boards"][board_id]
    assert load_board(board)["board_id"] == board_id
    assert board["provenance"]["board_sha256"] == compute_board_sha256(board)


@pytest.mark.parametrize("board_id,sha", C2_BOARDS, ids=C2_IDS)
def test_c2_roundtrip_canonical_bytes_equal(c2_converted, board_id, sha):
    board = c2_converted["boards"][board_id]
    first = canonical.canonical_json(board)
    reloaded = load_board(json.loads(first.decode("utf-8")))
    second = canonical.canonical_json(reloaded)
    assert first == second
    assert reloaded["provenance"]["board_sha256"] == board["provenance"]["board_sha256"]


@pytest.mark.parametrize("board_id,sha", C2_BOARDS, ids=C2_IDS)
def test_c2_double_convert_same_bytes(c2_converted, board_id, sha):
    again = convert_file(c2_converted["paths"][board_id], board_id)
    assert canonical.canonical_json(again) == canonical.canonical_json(
        c2_converted["boards"][board_id])
    assert (again["provenance"]["board_sha256"]
            == c2_converted["boards"][board_id]["provenance"]["board_sha256"])


@pytest.mark.parametrize("board_id,sha", C2_BOARDS, ids=C2_IDS)
def test_c2_partition_per_net_contract(c2_converted, board_id, sha):
    board = c2_converted["boards"][board_id]
    assert len(board["partitions"]) == len(board["nets"]) >= 1
    pids = set(p["partition_id"] for p in board["partitions"])
    assert len(pids) == len(board["partitions"])
    for net in board["nets"]:
        assert len(net["partitions"]) == 1
        assert net["partitions"][0] in pids
    for part in board["partitions"]:
        assert part["ptype"] in ("PWR", "MISC")
        assert part["width_prior"] == {"w_min": 0.3, "w_max": 1.0}
        assert part["current_a"] == 0
        assert part["speed_class"] == "unknown"
        assert part["layer_policy"] == "any"
        # V5-R1：多 pad 网 note 含 terminal nodes；单 pad 退化网维持退化文案
        assert ("terminal nodes" in part["note"]
                or "coincident endpoints (degenerate)" in part["note"])


def test_c2_report_counts_consistent(c2_converted):
    path = c2_converted["paths"]["vga-panel-breakout"]
    _board, report = convert_file_with_report(path, "vga-panel-breakout")
    assert report["kicad_version"] == "20171130"
    assert report["net_count"] >= 1
    assert report["footprint_count"] >= 1
    assert report["pad_count"] >= report["netted_pad_count"] >= 1
    assert report["ignored_zones"] >= 0
    assert report["ignored_drawings"] >= 0
