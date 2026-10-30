"""pcbflow.v4_1.netclasses 单元测试（net class 载入 + 逐网 clearance 矩阵）。"""

from __future__ import annotations

from pathlib import Path

import pytest

from pcbflow.v4_1.netclasses import (NetClass, NetClassError,
                                     NetClassNotAvailable, NetClassTable,
                                     load_netclasses,
                                     netclass_table_from_board_text,
                                     netclass_table_from_kicad_pro)

REPO = Path(__file__).resolve().parent.parent
PRO = (REPO.parent.parent / "design/coreboard/kicad/"
       "stm32h743-coreboard-revc/stm32h743-coreboard-revc.kicad_pro")

BOARD_WITH_CLASSES = """(kicad_pcb (version 20200110)
  (layers (0 "F.Cu" signal) (31 "B.Cu" signal))
  (net_class "Default" (clearance 0.2) (trace_width 0.25)
    (via_dia 1.0) (via_dri 0.6) (net "A") (net "B"))
  (net_class "PWR" (clearance 0.4) (trace_width 1.0)
    (via_dia 1.2) (via_dri 0.7) (net "VBIG"))
)
"""

BOARD_WITHOUT_CLASSES = """(kicad_pcb (version 20260206)
  (layers (0 "F.Cu" signal) (31 "B.Cu" signal))
  (segment (start 0 0) (end 1 1) (width 0.2) (layer "F.Cu") (net "A")
    (uuid "u1"))
)
"""

PRO_OBJ = {
    "net_settings": {
        "classes": [
            {"name": "Default", "clearance": 0.2, "track_width": 0.15},
            {"name": "PWR", "clearance": 0.5, "track_width": 1.0},
            {"name": "SIG", "clearance": 0.25, "track_width": 0.2},
        ],
        "netclass_assignments": {"NET_X": "SIG"},
        "netclass_patterns": [
            {"netclass": "PWR", "pattern": "PWR*"},
            {"netclass": "SIG", "pattern": "SIG_*"},
        ],
    }
}


def test_board_text_netclass_nodes():
    t = netclass_table_from_board_text(BOARD_WITH_CLASSES)
    assert t.source == "board_net_class_nodes"
    assert t.resolve("A").name == "Default"
    assert t.resolve("VBIG").name == "PWR"
    assert t.resolve("UNKNOWN").name == "Default"
    assert t.required_clearance("A", "VBIG") == pytest.approx(0.4)
    assert t.required_clearance("A", "B") == pytest.approx(0.2)


def test_board_text_without_classes_returns_none_then_fail_closed():
    assert netclass_table_from_board_text(BOARD_WITHOUT_CLASSES) is None
    with pytest.raises(NetClassNotAvailable):
        load_netclasses(board_text=BOARD_WITHOUT_CLASSES)
    err = None
    try:
        load_netclasses(board_text=BOARD_WITHOUT_CLASSES)
    except NetClassNotAvailable as exc:
        err = str(exc)
    assert "not_available" in err


def test_kicad_pro_netclass_resolution():
    t = netclass_table_from_kicad_pro(PRO_OBJ)
    assert t.source == "kicad_pro_net_settings"
    assert t.resolve("NET_X").name == "SIG"          # 精确指派
    assert t.resolve("PWR_5V").name == "PWR"         # 模式
    assert t.resolve("SIG_CLK").name == "SIG"
    assert t.resolve("whatever").name == "Default"   # 缺省
    # max 口径
    assert t.required_clearance("PWR_5V", "whatever") == pytest.approx(0.5)
    assert t.required_clearance("NET_X", "SIG_CLK") == pytest.approx(0.25)


def test_kicad_pro_without_net_settings_returns_none():
    assert netclass_table_from_kicad_pro({"board": {}}) is None


def test_declared_defaults_source():
    t = load_netclasses(declared_defaults=(0.2, 0.15))
    assert t.source == "declared_defaults"
    assert t.required_clearance("A", "B") == pytest.approx(0.2)


def test_ambiguous_multi_source_fail_closed():
    with pytest.raises(NetClassError) as ei:
        load_netclasses(board_text=BOARD_WITH_CLASSES,
                        kicad_pro_obj=PRO_OBJ)
    assert "ambiguous_source" in str(ei.value)


def test_validation_fail_closed():
    with pytest.raises(NetClassError):   # 缺 Default
        NetClassTable({"PWR": NetClass("PWR", 0.4)}, {}, [], "x")
    with pytest.raises(NetClassError):   # 模式引用未定义类
        NetClassTable({"Default": NetClass("Default", 0.2)}, {},
                      [("NOPE", "*")], "x")
    with pytest.raises(NetClassError):   # 负 clearance
        NetClass("D", -0.1)
    with pytest.raises(NetClassError):   # NaN
        NetClass("D", float("nan"))
    with pytest.raises(NetClassError):   # 精确指派引用未定义类
        NetClassTable({"Default": NetClass("Default", 0.2)},
                      {"N": "GHOST"}, [], "x")
    with pytest.raises(NetClassError):   # declared_defaults 形状错
        load_netclasses(declared_defaults=(0.2,))
    with pytest.raises(NetClassError):   # pro classes 项缺 name
        netclass_table_from_kicad_pro(
            {"net_settings": {"classes": [{"clearance": 0.2}]}})


def test_matrix_and_status_dict():
    t = netclass_table_from_kicad_pro(PRO_OBJ)
    m = t.matrix(["NET_X", "PWR_5V", "OTHER"])
    assert m["NET_X"] == {"class": "SIG", "clearance_mm": 0.25,
                          "track_width_mm": 0.2}
    assert m["OTHER"]["class"] == "Default"
    s = t.status_dict()
    assert s["class_count"] == 3 and s["status"] == "ok"


@pytest.mark.skipif(not PRO.is_file(), reason="Rev-C kicad_pro absent")
def test_real_revc_pro_load():
    import json
    t = netclass_table_from_kicad_pro(
        json.loads(PRO.read_text(encoding="utf-8")))
    assert t.source == "kicad_pro_net_settings"
    assert len(t.classes) == 18
    # G1.1 网对：LTDC_R7 无模式命中（R5-R7 未列入 LTDC 类）-> Default；
    # FMC_BA1 -> FMC_ADDR；required = max(0.2, 0.2) = 0.2（与 kicad-cli 判决
    # “间距 0.2000mm”一致）
    assert t.resolve("LTDC_R7").name == "Default"
    assert t.resolve("FMC_BA1").name == "FMC_ADDR"
    assert t.required_clearance("LTDC_R7", "FMC_BA1") == pytest.approx(0.2)
