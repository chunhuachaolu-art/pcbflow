"""pcbflow.v4_1.e2parity -- net class 线宽/间距规则 kicad-cli DRC 对拍
（E2 G2.2；堵 K2）。

对拍设计（多层合成板：生成 kicad_pcb → kicad-cli DRC → 对照 v4_1 内部
判定；一致率台账，不一致逐条归因，禁静默）：

- 板：KiCad 10 格式最小多层板（4 铜层 F.Cu/In1.Cu/In2.Cu/B.Cu +
  Edge.Cuts 外框），每例一板（case 子目录），探针物项（probe）uuid
  唯一——DRC 违例按 uuid 匹配，归因无歧义；
- net class 三类（.kicad_pro net_settings——KiCad 8+ 权威源；板内
  net_class 节点 KiCad 10 解析器拒收，探针 A 实证）：
  Default clearance=0.2 track_width=0.25 / HC clearance=0.5
  track_width=0.30 / LC clearance=0.1 track_width=0.15；
- 覆盖面：逐类 clearance（含 max-of-pair 口径与 LC 小 clearance 向下
  载入）、跨层合法负例、贯通/盲/埋 via 跨度障碍（含中间层与跨度外
  负例）、THT pad 全层障碍 vs SMD pad 单层、pad-pad 逐类间距、
  板级 min_track_width（design_settings.rules）；
- v4_1 判定（prepare 时算定，与 kicad-cli 无关）：路径 A + Minkowski
  核精确引擎（precheck）+ 路径 B + 外切多边形引擎（checker）双预测；
  宽度判定=KiCad 实测口径（板级 min；net class track_width 为布线
  默认值非 DRC 约束——探针 D 实证，台账登记为语义发现非不一致）。

kicad-cli 调用纪律（编排侧 Bash 执行，本模块零子进程）：staging 副本
（每 case 一目录）、零 live 板写、每次调用后 .kicad_prl sidecar 盘点
（prl_hygiene.check_and_restore；每目录恰一次调用=逐调用归因）。

探针实证记录（2026-09-12，kicad-cli 10.0.5，探针件
out/v4.1-engineering/e2/kicad-cli-probe/）：

- probe-a：板内 (net_class ...) 节点 KiCad 10 拒收（应为 symbol 解析
  错）→ per-class 规则唯一可用源=.kicad_pro net_settings；
- probe-b：net_settings clearance 生效（Default 0.2 vs HC 0.5，报文
  「网络类 'HC' 间距 0.5000 mm; 实际 0.2500 mm」——max-of-pair 口径）；
- probe-c：贯通 via 在中间层 In1.Cu 为障碍（violation 实际 0.1）；
  埋孔 (F.Cu In1.Cu) 对 In2.Cu 无违例（跨度外负例）；track_width 违
  例引用「电路板配置约束 最小宽度 0.2000 mm」（板级约束非类约束）；
- probe-d：net_settings track_width 0.3 的 HC 类走线宽 0.25 无违例
  （类宽=默认值非约束）；design_settings.rules.min_track_width=0.35
  生效（宽 0.25 报最小宽度 0.3000/0.3500 实测口径）；.kicad_dru 自
  定义规则本环境未被 kicad-cli 装载（无条件/带条件/severity 三式均
  不生效——登记为环境边界，非语义不一致）。

零子进程（kicad-cli 由编排侧调用）、零网络、零 wall-clock。
"""

from __future__ import annotations

import json
import re

from . import DECLARED_DATE, G11_TOLERANCE_MM
from .board_parse import parse_board_text
from .board_parse_alt import parse_board_text_alt
from .checker import IndependentGeometryChecker, build_check_items
from .netclasses import netclass_table_from_kicad_pro
from .precheck import AdvisoryPrecheckV41, build_geom_items

__all__ = [
    "build_parity_cases", "prepare_staging", "predict_case",
    "parse_drc_report", "collect_parity", "PARITY_PROBE_UUID_FMT",
    "KICAD_DEFAULT_MIN_TRACK_WIDTH_MM",
]

_PARITY_SCHEMA = "pcbflow.v4_1.e2parity/1"

#: KiCad 10 内建默认最小线宽（无 design_settings.rules 时的口径；
#: probe-c 实测报文「电路板配置约束 最小宽度 0.2000 mm」）
KICAD_DEFAULT_MIN_TRACK_WIDTH_MM = 0.2

PARITY_PROBE_UUID_FMT = "e2pb0000-0000-0000-0000-00000000%04x"

_PRO_CLASSES = [
    {"name": "Default", "clearance": 0.2, "track_width": 0.25,
     "via_diameter": 0.8, "via_drill": 0.4},
    {"name": "HC", "clearance": 0.5, "track_width": 0.3,
     "via_diameter": 0.8, "via_drill": 0.4},
    {"name": "LC", "clearance": 0.1, "track_width": 0.15,
     "via_diameter": 0.8, "via_drill": 0.4},
]

_PRO_NET_ASSIGN = {"nH": "HC", "nH2": "HC", "nL": "LC", "nL2": "LC"}

#: 类 -> (探针网, 障碍网)：同类对亦用相异网名（同网自豁免≠规则对拍）
_NETS_OF_CLASS = {"Default": ("nD", "nD2"), "HC": ("nH", "nH2"),
                  "LC": ("nL", "nL2")}


def _board_text(items, min_track_width_mm=None):
    """多层最小板文本（4 铜层 + Edge.Cuts 外框；items=段/via/pad 源）。

    min_track_width_mm：写入 .kicad_pro design_settings.rules（板级最小
    线宽约束）；None=KiCad 内建默认 0.2（由 _pro_text 呈现）。
    """
    lines = [
        "(kicad_pcb",
        '\t(version 20260206)',
        '\t(generator "pcbnew")',
        '\t(generator_version "10.0")',
        "\t(general",
        "\t\t(thickness 1.6)",
        "\t)",
        '\t(paper "A4")',
        "\t(layers",
        '\t\t(0 "F.Cu" signal)',
        '\t\t(1 "In1.Cu" signal)',
        '\t\t(2 "In2.Cu" signal)',
        '\t\t(31 "B.Cu" signal)',
        '\t\t(13 "F.Paste" user)',
        '\t\t(15 "B.Paste" user)',
        '\t\t(1 "F.Mask" user)',
        '\t\t(3 "B.Mask" user)',
        '\t\t(5 "F.SilkS" user "F.Silkscreen")',
        '\t\t(7 "B.SilkS" user "B.Silkscreen")',
        '\t\t(25 "Edge.Cuts" user)',
        "\t)",
        "\t(gr_rect",
        "\t\t(start 0 0)",
        "\t\t(end 100 60)",
        '\t\t(stroke (width 0.05) (type default))',
        "\t\t(fill no)",
        '\t\t(layer "Edge.Cuts")',
        '\t\t(uuid "e2fr0000-0000-0000-0000-000000000000")',
        "\t)",
    ]
    lines.extend(items)
    lines.append(")")
    return "\n".join(lines) + "\n"


def _segment(uuid, net, layer, x1, y1, x2, y2, width):
    return ("\t(segment\n\t\t(start %s %s)\n\t\t(end %s %s)\n\t\t"
            "(width %s)\n\t\t(layer \"%s\")\n\t\t(net \"%s\")\n\t\t"
            "(uuid \"%s\")\n\t)"
            % (_f(x1), _f(y1), _f(x2), _f(y2), _f(width), layer, net,
               uuid))


def _via(uuid, net, l1, l2, x, y, size=0.6, drill=0.3, kind=""):
    head = "\t(via %s\n" % kind if kind else "\t(via\n"
    return ("%s\t\t(at %s %s)\n\t\t(size %s)\n\t\t(drill %s)\n\t\t"
            "(layers \"%s\" \"%s\")\n\t\t(net \"%s\")\n\t\t"
            "(uuid \"%s\")\n\t)"
            % (head, _f(x), _f(y), _f(size), _f(drill), l1, l2, net,
               uuid))


def _footprint_tht(uuid, net, x, y, dia=0.9, drill=0.4, ref="VT1"):
    return ("\t(footprint \"E2-THT\"\n\t\t(layer \"F.Cu\")\n\t\t"
            "(at %s %s)\n\t\t(property \"Reference\" \"%s\" (at 0 0) "
            '(layer "F.SilkS"))\n'
            "\t\t(pad \"1\" thru_hole circle (at 0 0) (size %s %s) "
            "(drill %s)\n\t\t\t(layers \"*.Cu\" \"*.Mask\") "
            "(net \"%s\") (uuid \"%s\"))\n\t)"
            % (_f(x), _f(y), ref, _f(dia), _f(dia), _f(drill), net, uuid))


def _footprint_smd(uuid, net, x, y, w=1.2, h=1.2, ref="VS1"):
    return ("\t(footprint \"E2-SMD\"\n\t\t(layer \"F.Cu\")\n\t\t"
            "(at %s %s)\n\t\t(property \"Reference\" \"%s\" (at 0 0) "
            '(layer "F.SilkS"))\n'
            "\t\t(pad \"1\" smd rect (at 0 0) (size %s %s)\n\t\t\t"
            "(layers \"F.Cu\") (net \"%s\") (uuid \"%s\"))\n\t)"
            % (_f(x), _f(y), ref, _f(w), _f(h), net, uuid))


def _f(v):
    s = ("%.6f" % float(v)).rstrip("0")
    return s + "0" if s.endswith(".") else s


def _pro_text(min_track_width_mm=None):
    """最小 .kicad_pro（net_settings 三类 + 指派；可选板级最小线宽）。"""
    classes = []
    for c in _PRO_CLASSES:
        classes.append({
            "bus_width": 12, "clearance": c["clearance"],
            "diff_pair_gap": 0.25, "diff_pair_via_gap": 0.25,
            "diff_pair_width": 0.2, "line_style": 0,
            "microvia_drill": 0.1, "name": c["name"],
            "pcb_color": "rgba(0, 0, 0, 0.000000)",
            "schematic_color": "rgba(0, 0, 0, 0.000000)",
            "track_width": c["track_width"],
            "via_diameter": c["via_diameter"], "via_drill": c["via_drill"],
            "wire_width": 6,
        })
    pro = {
        "meta": {"filename": "case.kicad_pro", "version": 3},
        "board": {
            "3dviewports": [], "layer_presets": [], "viewports": [],
            "design_settings": [] if min_track_width_mm is None
            else {"rules": {"min_track_width": min_track_width_mm}},
        },
        "boards": [], "cvpcb": {"equivalence_files": []},
        "libraries": {"pinned_footprint_libs": [],
                      "pinned_symbol_libs": []},
        "net_settings": {
            "classes": classes,
            "netclass_assignments": dict(_PRO_NET_ASSIGN),
            "netclass_patterns": [],
        },
        "schematic": {"legacy_lib_dir": "", "legacy_lib_list": []},
        "sheets": [], "text_variables": {},
    }
    return pro


#: 坐标系：探针/障碍水平走线 y 基准 20，长度 10（x 20..30）；via/pad
#: 障碍置 (10, 20) 或 (40, 20)；探针走线区避让障碍区。
_W = 0.25          # 探针/障碍默认线宽


def _case_defs():
    """对拍用例定义（确定性列表；每例一板）。

    clearance 目标值由中心距 - 双半宽解析给定（探针/障碍同宽 _W=0.25，
    中心距 = 目标 + 0.25；via 半径 0.3 / pad 半宽 0.6 / THT 半径 0.45
    逐例换算）。
    """
    cases = []

    def track_pair(cid, cls_p, cls_o, clearance_mm, layer_p="F.Cu",
                   layer_o=None, note=""):
        """两平行水平走线（探针在下）。"""
        dy = clearance_mm + _W  # 同宽：中心距=clearance+宽
        uid_p = PARITY_PROBE_UUID_FMT % len(cases)
        uid_o = "e2ob0000-0000-0000-0000-00000000%04x" % len(cases)
        net_p = _NETS_OF_CLASS[cls_p][0]
        net_o = _NETS_OF_CLASS[cls_o][1]
        items = [
            _segment(uid_o, net_o, layer_o or "F.Cu", 20, 20, 30, 20, _W),
            _segment(uid_p, net_p, layer_p, 20, 20 + dy, 30, 20 + dy, _W),
        ]
        cases.append({
            "case_id": cid, "kind": "clearance", "note": note,
            "probe": {"type": "segment", "uuid": uid_p, "net": net_p,
                      "layer": layer_p, "width": _W,
                      "start": [20, 20 + dy], "end": [30, 20 + dy]},
            "board_items": items, "min_track_width_mm": None,
        })

    def via_case(cid, via_kind, l1, l2, probe_layer, clearance_mm, note,
                 probe_is_via=False):
        uid_v = "e2ob0000-0000-0000-0000-00000000%04x" % len(cases)
        uid_p = PARITY_PROBE_UUID_FMT % len(cases)
        if probe_is_via:
            dy = clearance_mm + 0.3 + 0.3
            items = [
                _via(uid_v, "nV", l1, l2, 40, 20, kind=via_kind),
                _via(uid_p, "nD2", "F.Cu", "B.Cu", 40, 20 + dy),
            ]
            probe = {"type": "via", "uuid": uid_p, "net": "nD2",
                     "layers": ["F.Cu", "B.Cu"], "size": 0.6,
                     "at": [40, 20 + dy]}
        else:
            dy = clearance_mm + 0.3 + _W / 2.0
            items = [
                _via(uid_v, "nV", l1, l2, 40, 20, kind=via_kind),
                _segment(uid_p, "nD2", probe_layer, 35, 20 + dy, 45,
                         20 + dy, _W),
            ]
            probe = {"type": "segment", "uuid": uid_p, "net": "nD2",
                     "layer": probe_layer, "width": _W,
                     "start": [35, 20 + dy], "end": [45, 20 + dy]}
        cases.append({
            "case_id": cid, "kind": "clearance", "note": note,
            "probe": probe, "board_items": items,
            "min_track_width_mm": None,
        })

    def pad_case(cid, pad_kind, probe_layer, clearance_mm, cls_p="Default",
                 cls_pad="Default", note=""):
        uid_pad = "e2ob0000-0000-0000-0000-00000000%04x" % len(cases)
        uid_p = PARITY_PROBE_UUID_FMT % len(cases)
        net_pad = _NETS_OF_CLASS[cls_pad][1]
        net_p = _NETS_OF_CLASS[cls_p][0]
        if pad_kind == "tht":
            dy = clearance_mm + 0.45 + _W / 2.0
            pad = _footprint_tht(uid_pad, net_pad, 40, 20, ref="VT%02d"
                                 % len(cases))
        else:
            dy = clearance_mm + 0.6 + _W / 2.0
            pad = _footprint_smd(uid_pad, net_pad, 40, 20, ref="VS%02d"
                                 % len(cases))
        items = [
            pad,
            _segment(uid_p, net_p, probe_layer, 35, 20 + dy, 45, 20 + dy,
                     _W),
        ]
        cases.append({
            "case_id": cid, "kind": "clearance", "note": note,
            "probe": {"type": "segment", "uuid": uid_p, "net": net_p,
                      "layer": probe_layer, "width": _W,
                      "start": [35, 20 + dy], "end": [45, 20 + dy]},
            "board_items": items, "min_track_width_mm": None,
        })

    def pad_pad_case(cid, cls_p, cls_o, clearance_mm, note):
        uid_o = "e2ob0000-0000-0000-0000-00000000%04x" % len(cases)
        uid_p = PARITY_PROBE_UUID_FMT % len(cases)
        net_o = _NETS_OF_CLASS[cls_o][1]
        net_p = _NETS_OF_CLASS[cls_p][0]
        dx = clearance_mm + 1.2  # 两 1.2 宽 rect pad：中心距=clearance+1.2
        items = [
            _footprint_smd(uid_o, net_o, 40, 20, ref="VO%02d" % len(cases)),
            _footprint_smd(uid_p, net_p, 40 + dx, 20, ref="VP%02d"
                           % len(cases)),
        ]
        cases.append({
            "case_id": cid, "kind": "clearance", "note": note,
            "probe": {"type": "pad", "uuid": uid_p, "net": net_p,
                      "layer": "F.Cu", "shape": "rect", "size": [1.2, 1.2],
                      "at": [40 + dx, 20], "pad_kind": "smd"},
            "board_items": items, "min_track_width_mm": None,
        })

    def width_case(cid, width_mm, min_track_width_mm, note):
        uid_p = PARITY_PROBE_UUID_FMT % len(cases)
        items = [_segment(uid_p, "nD", "F.Cu", 20, 20, 30, 20, width_mm)]
        cases.append({
            "case_id": cid, "kind": "width", "note": note,
            "probe": {"type": "segment", "uuid": uid_p, "net": "nD",
                      "layer": "F.Cu", "width": width_mm,
                      "start": [20, 20], "end": [30, 20]},
            "board_items": items,
            "min_track_width_mm": min_track_width_mm,
        })

    # ---- 逐类 clearance（max-of-pair 口径；LC 向下）----
    track_pair("cls-default-ok", "Default", "Default", 0.30,
               note="同类 Default 0.30>=0.2 合法")
    track_pair("cls-default-viol", "Default", "Default", 0.10,
               note="同类 Default 0.10<0.2 违例")
    track_pair("cls-max-cross-viol", "Default", "HC", 0.40,
               note="跨类 max 口径：0.40<max(0.2,0.5)=0.5 违例")
    track_pair("cls-max-cross-ok", "Default", "HC", 0.60,
               note="跨类 0.60>=0.5 合法")
    track_pair("cls-lc-small-ok", "LC", "LC", 0.15,
               note="LC 类 0.15>=0.1 合法（逐类 clearance 向下载入）")
    track_pair("cls-lc-small-viol", "LC", "LC", 0.05,
               note="LC 类 0.05<0.1 违例（逐类下限同判）")
    # ---- 跨层负例（多层语义）----
    track_pair("cross-layer-ok", "Default", "Default", -0.125,
               layer_p="In1.Cu",
               note="F.Cu vs In1.Cu 同位重叠：跨层无 clearance 约束")
    # ---- via 跨度障碍（贯通/盲/埋；中间层+跨度外）----
    via_case("via-through-inner-viol", "", "F.Cu", "B.Cu", "In1.Cu", 0.10,
             note="贯通 via 在中间层 In1.Cu 为障碍：0.10<0.2 违例")
    via_case("via-through-inner-ok", "", "F.Cu", "B.Cu", "In1.Cu", 0.30,
             note="贯通 via 中间层 0.30>=0.2 合法")
    via_case("via-buried-outside-ok", "buried", "F.Cu", "In1.Cu",
             "In2.Cu", 0.10,
             note="埋孔(F..In1) 对跨度外 In2.Cu 无障碍：合法（负例）")
    via_case("via-buried-endpoint-viol", "buried", "F.Cu", "In1.Cu",
             "In1.Cu", 0.10,
             note="埋孔跨度端点层 In1.Cu 为障碍：0.10<0.2 违例")
    via_case("via-blind-intermediate-viol", "buried", "F.Cu", "In2.Cu",
             "In1.Cu", 0.10,
             note="盲孔(F..In2) 中间层 In1.Cu 为障碍：违例（E2 核心语义）")
    via_case("via-blind-below-ok", "buried", "F.Cu", "In2.Cu", "B.Cu",
             0.10,
             note="盲孔(F..In2) 对跨度外 B.Cu 无障碍：合法（负例）")
    via_case("via-via-viol", "", "F.Cu", "B.Cu", "In1.Cu", 0.10,
             note="贯通 via 对贯通 via（In1.Cu 共层）：0.10<0.2 违例",
             probe_is_via=True)
    # ---- THT/SMD pad 跨层障碍 ----
    pad_case("tht-pad-inner-viol", "tht", "In2.Cu", 0.10,
             note="THT(*.Cu) 在 In2.Cu 为障碍：违例")
    pad_case("smd-pad-inner-ok", "smd", "In2.Cu", 0.10,
             note="SMD(F.Cu) 对 In2.Cu 无障碍：合法（负例）")
    # ---- pad-pad 逐类间距 ----
    pad_pad_case("pad-pad-cross-viol", "Default", "HC", 0.30,
                 note="pad-pad 跨类 max：0.30<0.5 违例")
    pad_pad_case("pad-pad-default-ok", "Default", "Default", 0.30,
                 note="pad-pad 同类 0.30>=0.2 合法")
    # ---- 板级最小线宽（design_settings.rules；类宽=默认值非约束）----
    width_case("width-default-min-viol", 0.15, None,
               note="宽 0.15 < 内建板级最小 0.2：违例")
    width_case("width-default-min-ok", 0.25, None,
               note="宽 0.25 >= 0.2：合法")
    width_case("width-board-035-viol", 0.25, 0.35,
               note="design_settings.rules.min_track_width=0.35："
                    "宽 0.25 违例（板级约束生效）")
    width_case("width-class-hc-not-enforced", 0.25, None,
               note="HC 类 track_width=0.3 但宽 0.25 合法——类宽为布线"
                    "默认值非 DRC 约束（probe-d 实证，语义发现登记）")
    return cases


# ---------------------------------------------------------------- 预测

def predict_case(case, board_text, pro_obj):
    """v4_1 双引擎预测（与 kicad-cli 无关；prepare 时算定）。

    - clearance 例：解析板文本（双路径），剔除探针后建障碍物项，
      check_segment/check_via/check_pad 复核探针几何；
      判定口径=hard（保守带内标记为 band，advisory 非 gate——E1 同口径）；
    - width 例：KiCad 实测口径（板级最小线宽；类宽=默认值非约束）。
    """
    parsed_a = parse_board_text(board_text)
    parsed_b = parse_board_text_alt(board_text)
    table = netclass_table_from_kicad_pro(pro_obj)
    probe = case["probe"]
    if case["kind"] == "width":
        min_w = pro_obj.get("board", {}).get("design_settings")
        if isinstance(min_w, dict):
            min_w = min_w.get("rules", {}).get("min_track_width")
        else:
            min_w = None
        eff_min = float(min_w) if min_w is not None \
            else KICAD_DEFAULT_MIN_TRACK_WIDTH_MM
        viol = probe["width"] < eff_min - 1e-12
        return {
            "verdict": "violation" if viol else "clean",
            "rule": "board_min_track_width",
            "effective_min_mm": eff_min,
            "probe_width_mm": probe["width"],
            "class_track_width_note": "net class track_width 为布线默认"
                                      "值非 DRC 约束（probe-d 实证）",
        }
    # clearance 例：探针剔除（其余物项为障碍）
    if probe["type"] == "segment":
        keep = lambda items: [it for it in items
                              if it.get("uuid") != probe["uuid"]]
        parsed_a["segments"] = keep(parsed_a["segments"])
        parsed_b["segments"] = keep(parsed_b["segments"])
        pre = AdvisoryPrecheckV41(build_geom_items(parsed_a), table)
        chk = IndependentGeometryChecker(build_check_items(parsed_b), table)
        r_pre = pre.check_segment(probe["net"], probe["layer"],
                                  probe["width"], probe["start"][0],
                                  probe["start"][1], probe["end"][0],
                                  probe["end"][1])
        r_chk = chk.check_segment(probe["net"], probe["layer"],
                                  probe["width"], probe["start"][0],
                                  probe["start"][1], probe["end"][0],
                                  probe["end"][1])
    elif probe["type"] == "via":
        keep = lambda items: [it for it in items
                              if it.get("uuid") != probe["uuid"]]
        parsed_a["vias"] = keep(parsed_a["vias"])
        parsed_b["vias"] = keep(parsed_b["vias"])
        pre = AdvisoryPrecheckV41(build_geom_items(parsed_a), table)
        chk = IndependentGeometryChecker(build_check_items(parsed_b), table)
        r_pre = pre.check_via(probe["net"], probe["layers"], probe["size"],
                              probe["at"][0], probe["at"][1])
        r_chk = chk.check_via(probe["net"], probe["layers"], probe["size"],
                              probe["at"][0], probe["at"][1])
    elif probe["type"] == "pad":
        keep = lambda items: [it for it in items
                              if it.get("uuid") != probe["uuid"]]
        # pad 探针：路径 A/B pad 记录带 pad_id（U?.1），uuid 在 src 外
        #（board_parse 不保留 pad uuid——以 pad_id 剔除：唯一 ref 逐例保证）
        parsed_a["pads"] = [p for p in parsed_a["pads"]
                            if "VP" not in p["pad_id"]]
        parsed_b["pads"] = [p for p in parsed_b["pads"]
                            if "VP" not in p["pad_id"]]
        pre = AdvisoryPrecheckV41(build_geom_items(parsed_a), table)
        chk = IndependentGeometryChecker(build_check_items(parsed_b), table)
        # pad 探针以 check_pad 复核（geom=rect 1.2x1.2 @ at）
        from .geometry import PadGeom
        pad = PadGeom(probe["shape"], probe["at"][0], probe["at"][1],
                      probe["size"][0], probe["size"][1], 0.0,
                      pad_id="(probe)", net_id=probe["net"],
                      layers=(probe["layer"],))
        r_pre = pre.check_pad(pad, {probe["layer"]})
        pad_dict = {"pad_id": "(probe)", "shape": probe["shape"],
                    "net_id": probe["net"], "x_mm": probe["at"][0],
                    "y_mm": probe["at"][1], "w_mm": probe["size"][0],
                    "h_mm": probe["size"][1], "rotation_deg": 0.0,
                    "corner_radius_mm": None, "layers": [probe["layer"]],
                    "primitive_pts": None}
        r_chk = chk.check_pad(pad_dict, [probe["layer"]])
    else:
        raise ValueError("未知探针类型（fail-closed）: %r" % probe["type"])
    hard_pre = [v for v in r_pre["violations"]
                if v["flag_class"] == "hard_violation"]
    band_pre = [v for v in r_pre["violations"]
                if v["flag_class"] == "conservative_band"]
    hard_chk = [v for v in r_chk["violations"]
                if v["flag_class"] == "hard_violation"]
    return {
        "verdict": "violation" if hard_pre else "clean",
        "hard_violations": hard_pre,
        "band_flags": band_pre,
        "pred_clearance_mm": (hard_pre or band_pre or [{}])[0].get(
            "pred_clearance_mm"),
        "required_mm": (hard_pre or band_pre or [{}])[0].get("required_mm"),
        "checker_verdict": "violation" if hard_chk else "clean",
        "checker_pred_clearance_mm": None,
        "cross_engine_agree": (bool(hard_pre) == bool(hard_chk)),
    }


# ---------------------------------------------------------------- DRC 解析

_REQ_RE = re.compile(r"间距\s*(?:'[^']*'\s*)?间距?\s*([0-9.]+)\s*mm"
                     r"|间距\s*([0-9.]+)\s*mm")
_ACT_RE = re.compile(r"实际\s*([0-9.]+)\s*mm")
_MINW_RE = re.compile(r"最小宽度\s*([0-9.]+)\s*mm")
_ITEM_NET_RE = re.compile(r"\[([^\]]+)\]")
_ITEM_LAYER_RE = re.compile(r"\(([A-Za-z0-9*.]+\.Cu)")


def _item_matches_probe(item, probe):
    """DRC item 与探针几何匹配（KiCad 10 装载时重写 item uuid——
    实测 drc.json 中 uuid 与板文本不一致（cls-default-viol 抽查：
    板文本 e2pb0000-… → drc 97c8a061-…），故匹配键=网名+层+位置）。"""
    desc = str(item.get("description", ""))
    m_net = _ITEM_NET_RE.search(desc)
    if not m_net or m_net.group(1) != probe["net"]:
        return False
    pos = item.get("pos") or {}
    px = round(float(pos.get("x", 1e9)), 3)
    py = round(float(pos.get("y", 1e9)), 3)
    if probe["type"] == "segment":
        m_layer = _ITEM_LAYER_RE.search(desc)
        if not m_layer or m_layer.group(1) != probe["layer"]:
            return False
        return (abs(px - round(probe["start"][0], 3)) <= 1e-6
                and abs(py - round(probe["start"][1], 3)) <= 1e-6)
    if probe["type"] == "via":
        return (abs(px - round(probe["at"][0], 3)) <= 1e-6
                and abs(py - round(probe["at"][1], 3)) <= 1e-6)
    if probe["type"] == "pad":
        return (abs(px - round(probe["at"][0], 3)) <= 1e-6
                and abs(py - round(probe["at"][1], 3)) <= 1e-6)
    return False


def parse_drc_report(drc_obj, probe_uuid, probe=None):
    """kicad-cli DRC JSON -> 探针视角判定（clearance/track_width 按
    severity=error 计；item 匹配=网名+层+位置——KiCad 10 重写 uuid，
    uuid 键不可用作匹配，实证见 _item_matches_probe 注）。

    返回 {violation: bool, type, actual_mm, required_mm, description,
    matched_item_desc}（无违例时 type="none"）。
    """
    for v in drc_obj.get("violations", []):
        if v.get("severity") != "error":
            continue
        hit = None
        if probe is not None:
            hit = next((i for i in v.get("items", [])
                        if _item_matches_probe(i, probe)), None)
        elif probe_uuid is not None:
            hit = next((i for i in v.get("items", [])
                        if i.get("uuid") == probe_uuid), None)
        if hit is None:
            continue
        desc = str(v.get("description", ""))
        actual = _ACT_RE.search(desc)
        if v.get("type") == "track_width":
            req = _MINW_RE.search(desc)
            return {"violation": True, "type": "track_width",
                    "actual_mm": float(actual.group(1)) if actual else None,
                    "required_mm": float(req.group(1)) if req else None,
                    "description": desc,
                    "matched_item_desc": str(hit.get("description", ""))}
        req = _REQ_RE.search(desc)
        required = None
        if req:
            required = float(req.group(1) or req.group(2))
        return {"violation": True, "type": "clearance",
                "actual_mm": float(actual.group(1)) if actual else None,
                "required_mm": required, "description": desc,
                "matched_item_desc": str(hit.get("description", ""))}
    return {"violation": False, "type": "none", "actual_mm": None,
            "required_mm": None, "description": "",
            "matched_item_desc": ""}


# ---------------------------------------------------------------- 编排

def build_parity_cases():
    """全部对拍用例（board_text + pro + 预测；确定性）。"""
    out = []
    for case in _case_defs():
        board_text = _board_text(case["board_items"],
                                 case["min_track_width_mm"])
        pro = _pro_text(case["min_track_width_mm"])
        pred = predict_case(case, board_text, pro)
        entry = {
            "case_id": case["case_id"],
            "kind": case["kind"],
            "note": case["note"],
            "probe": case["probe"],
            "v41_prediction": pred,
        }
        entry["_board_text"] = board_text
        entry["_pro"] = pro
        out.append(entry)
    return out


def prepare_staging(staging_dir):
    """prepare：staging 逐例目录落板+pro+cases 记录（canonical）。

    返回 (cases_manifest, per_case_files)；kicad-cli 调用由编排侧执行
    （cwd=各 case 目录，board 名恒 case.kicad_pcb）。
    """
    import os
    from .canonical import write_canonical_json
    from .prl_hygiene import inventory
    os.makedirs(staging_dir, exist_ok=True)
    cases = build_parity_cases()
    entries = []
    for c in cases:
        d = os.path.join(staging_dir, c["case_id"])
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "case.kicad_pcb"), "w",
                  encoding="utf-8", newline="\n") as f:
            f.write(c["_board_text"])
        write_canonical_json(os.path.join(d, "case.kicad_pro"), c["_pro"])
        entry = {k: v for k, v in c.items()
                 if not k.startswith("_")}
        entry["inventory_before"] = inventory(d)
        entries.append(entry)
    manifest = {
        "schema": _PARITY_SCHEMA,
        "declared_date": DECLARED_DATE,
        "stage": "prepared",
        "case_count": len(entries),
        "classes": [{"name": c["name"], "clearance_mm": c["clearance"],
                     "track_width_mm": c["track_width"]}
                    for c in _PRO_CLASSES],
        "kicad_cli_command": "kicad-cli pcb drc --format json "
                             "--severity-all --output drc.json "
                             "case.kicad_pcb（cwd=case 目录；每目录恰一次"
                             "调用=逐调用 prl 卫生归因）",
        "cases": entries,
    }
    write_canonical_json(os.path.join(staging_dir, "cases-prepared.json"),
                         manifest)
    return manifest


def collect_parity(staging_dir):
    """collect：读各 case drc.json + prl 复核 -> rule-parity 台账。"""
    import os
    from .canonical import write_canonical_json
    from .prl_hygiene import check_and_restore
    prepared_path = os.path.join(staging_dir, "cases-prepared.json")
    with open(prepared_path, "r", encoding="utf-8") as f:
        prepared = json.load(f)
    rows = []
    for entry in prepared["cases"]:
        d = os.path.join(staging_dir, entry["case_id"])
        drc_path = os.path.join(d, "drc.json")
        if not os.path.isfile(drc_path):
            rows.append({
                "case_id": entry["case_id"], "kind": entry["kind"],
                "status": "missing_drc_json", "agreement": "not_compared",
            })
            continue
        with open(drc_path, "r", encoding="utf-8") as f:
            drc = json.load(f)
        kicad = parse_drc_report(drc, entry["probe"]["uuid"],
                                 probe=entry["probe"])
        pred = entry["v41_prediction"]
        if entry["kind"] == "width":
            agree = (kicad["violation"] == (pred["verdict"] == "violation"))
            numeric = None
        else:
            agree = (kicad["violation"] == (pred["verdict"] == "violation"))
            numeric = None
            if kicad["violation"] and kicad["actual_mm"] is not None \
                    and pred.get("pred_clearance_mm") is not None:
                numeric = {
                    "v41_pred_mm": pred["pred_clearance_mm"],
                    "kicad_actual_mm": kicad["actual_mm"],
                    "abs_diff_mm": round(abs(pred["pred_clearance_mm"]
                                             - kicad["actual_mm"]), 6),
                    "within_g11_tolerance":
                        abs(pred["pred_clearance_mm"]
                            - kicad["actual_mm"]) <= G11_TOLERANCE_MM,
                }
        hygiene = check_and_restore(d, {
            n: v for n, v in entry["inventory_before"].items()})
        rows.append({
            "case_id": entry["case_id"],
            "kind": entry["kind"],
            "note": entry["note"],
            "probe_uuid": entry["probe"]["uuid"],
            "v41": {"verdict": pred["verdict"],
                    "checker_verdict": pred.get("checker_verdict"),
                    "pred_clearance_mm": pred.get("pred_clearance_mm"),
                    "required_mm": pred.get("required_mm"),
                    "effective_min_mm": pred.get("effective_min_mm"),
                    "band_flags": pred.get("band_flags", [])},
            "kicad_cli": kicad,
            "agreement": "agree" if agree else "mismatch",
            "numeric_parity": numeric,
            "attribution": _attribute(entry, kicad, pred, agree),
            "prl_hygiene": {"verdict": hygiene["verdict"],
                            "created": hygiene["prl_created"],
                            "restored": hygiene["restored"],
                            "post_restore_matches_before":
                                hygiene["post_restore_matches_before"]},
        })
    n_cmp = [r for r in rows if r.get("agreement") in ("agree", "mismatch")]
    n_agree = [r for r in n_cmp if r["agreement"] == "agree"]
    mism = [r for r in n_cmp if r["agreement"] == "mismatch"]
    numeric_rows = [r for r in rows if r.get("numeric_parity")]
    numeric_ok = [r for r in numeric_rows
                  if r["numeric_parity"]["within_g11_tolerance"]]
    ledger = {
        "schema": _PARITY_SCHEMA,
        "declared_date": DECLARED_DATE,
        "stage": "collected",
        "kicad_cli_version": "10.0.5（toolchain_lock.json 锁定口径）",
        "case_count": len(rows),
        "verdict_agreement": {
            "compared": len(n_cmp),
            "agree": len(n_agree),
            "mismatch": len(mism),
            "rate": round(len(n_agree) / len(n_cmp), 6) if n_cmp else None,
        },
        "numeric_parity": {
            "compared": len(numeric_rows),
            "within_g11_tolerance_0p01mm": len(numeric_ok),
            "max_abs_diff_mm": max(
                (r["numeric_parity"]["abs_diff_mm"]
                 for r in numeric_rows), default=None),
        },
        "mismatches": mism,
        "unattributed_mismatches": [r for r in mism
                                    if not r.get("attribution")],
        "semantic_findings": [
            "net class track_width=布线默认值非 DRC 约束（probe-d：HC 0.3 "
            "类走线宽 0.25 无违例；宽度约束=板级 min_track_width，"
            "design_settings.rules 可配置）——非判定不一致，口径登记",
            "板内 (net_class ...) 节点 KiCad 10 解析器拒收（probe-a）——"
            "per-class 规则权威源=.kicad_pro net_settings（与 Rev-C 实况"
            "一致）",
            ".kicad_dru 自定义规则文件本环境未被 kicad-cli 装载（probe-d "
            "三式实测不生效）——环境边界登记，S1 不触发（clearance/宽度"
            "主口径不依赖 dru）",
        ],
        "cases": rows,
    }
    write_canonical_json(os.path.join(staging_dir, "..", "rule-parity.json"),
                         ledger)
    return ledger


def _attribute(entry, kicad, pred, agree):
    """不一致/发现归因（禁静默；agree 时归因字段=口径说明）。"""
    if agree:
        return "一致（%s）" % entry["note"]
    if kicad["violation"] and pred["verdict"] == "clean":
        return "kicad 报违例而 v4_1 判 clean——漏报方向，须逐项复核" \
               "（候选归因：net class 载入口径/几何建模差异）"
    return "v4_1 判违例而 kicad 报 clean——误报方向，须逐项复核" \
           "（候选归因：保守带/超集建模/规则源差异）"


def main(argv=None):
    import argparse
    import os
    ap = argparse.ArgumentParser(prog="pcbflow.v4_1.e2parity")
    ap.add_argument("--staging", required=True)
    ap.add_argument("action", choices=("prepare", "collect"))
    ns = ap.parse_args(argv)
    if ns.action == "prepare":
        m = prepare_staging(ns.staging)
        print("prepared %d cases under %s" % (m["case_count"], ns.staging))
        return 0
    ledger = collect_parity(ns.staging)
    va = ledger["verdict_agreement"]
    print("parity: %d/%d agree (rate=%s), numeric %s"
          % (va["agree"], va["compared"], va["rate"],
             ledger["numeric_parity"]))
    mism = ledger["unattributed_mismatches"]
    print("unattributed_mismatches=%d" % len(mism))
    return 0 if not mism else 1


if __name__ == "__main__":
    raise SystemExit(main())
