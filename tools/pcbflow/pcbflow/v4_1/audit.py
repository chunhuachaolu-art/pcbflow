"""pcbflow.v4_1.audit -- G1.2 构造对拍集 + 漏报审计 + 误报台账。

构造对拍集（任务书 §3 E1：三类形状×典型相对位置，含已知违例与已知合
法两侧）：

- 形状：round（圆）/ oval（椭圆胶囊）/ rect+roundrect（矩形族）；
- 位置：长轴/短轴逼近、角区逼近（G1.1 同构）、旋转焊盘、跨层（THT
  *.Cu 全层障碍）、via、pad-pad、track-track；
- 每例 expected_clearance 由测试侧独立闭式公式给出（轴对齐手推式，
  与被测引擎的一般化实现结构性不同——非循环验证）；
- 两侧：违例侧 expected < required；合法侧 expected >= required +
  保守带；另设带内边界例 [required, required+band)（真值=合法，预检
  按保守方向判违例 -> 计入误报台账，不计漏报）。

判定口径：

- 漏报（false negative）= 真值违例（expected < required）而引擎 clean；
  G1.2 门：漏报率=0；
- 误报（false positive）= 真值合法而引擎判违例——逐条描述性登记，
  不设门；
- 预检/checker 交叉不一致 -> cross_disagreements 登记（blocked 语义，
  不静默取其一）。

零 IO（除 --out 写产物）、零子进程、零网络、零 wall-clock。
"""

from __future__ import annotations

import math

from . import CONSERVATIVE_BAND_MM, DECLARED_DATE
from .board_parse import parse_board_text
from .board_parse_alt import parse_board_text_alt
from .checker import IndependentGeometryChecker, build_check_items
from .netclasses import NetClass, NetClassTable
from .precheck import AdvisoryPrecheckV41, build_geom_items

__all__ = ["build_case_board_text", "construct_cases", "run_audit",
           "main"]

_AUDIT_SCHEMA = "pcbflow.v4_1.false-negative-audit/1"
REQUIRED_MM = 0.2


class CaseBoard:
    """单用例板上下文（每例独立小板文本，避免例间串扰）。"""

    def __init__(self, case_id, segments, pads, vias):
        self.case_id = case_id
        self.segments = segments
        self.pads = pads
        self.vias = vias

    def board_text(self):
        seg_lines = []
        for (i, s) in enumerate(self.segments):
            seg_lines.append(
                '  (segment (start %s %s) (end %s %s) (width %s) '
                '(layer "%s") (net "%s") (uuid "seg-%s-%d"))'
                % (_f(s["x1"]), _f(s["y1"]), _f(s["x2"]), _f(s["y2"]),
                   _f(s["w"]), s["layer"], s["net"], self.case_id, i))
        pad_lines = []
        for (i, p) in enumerate(self.pads):
            rr = ' (roundrect_rratio %s)' % _f(p["rratio"]) \
                if p.get("rratio") is not None else ""
            rot = ' %s' % _f(p["pad_rot"]) if p.get("pad_rot") else ""
            pad_lines.append(
                '  (footprint "FP-%s-%d" (layer "F.Cu") (at %s %s%s)\n'
                '    (property "Reference" "F%d" (at 0 0) '
                '(layer "F.SilkS"))\n'
                '    (pad "1" smd %s (at %s %s%s) (size %s %s) '
                '(layers %s)%s (net "%s") (uuid "pad-%s-%d"))\n  )'
                % (self.case_id, i, _f(p["fp_x"]), _f(p["fp_y"]),
                   (" " + _f(p["fp_rot"])) if p.get("fp_rot") else "",
                   i, p["shape"], _f(p["x"]), _f(p["y"]), rot,
                   _f(p["w"]), _f(p["h"]), p["layers"], rr, p["net"],
                   self.case_id, i))
        via_lines = []
        for (i, v) in enumerate(self.vias):
            via_lines.append(
                '  (via (at %s %s) (size %s) (drill 0.3) '
                '(layers "F.Cu" "B.Cu") (net "%s") (uuid "via-%s-%d"))'
                % (_f(v["x"]), _f(v["y"]), _f(v["size"]), v["net"],
                   self.case_id, i))
        return ("(kicad_pcb (version 20260206)\n"
                '  (layers (0 "F.Cu" signal) (1 "In1.Cu" signal) '
                '(31 "B.Cu" signal))\n'
                + "\n".join(pad_lines + seg_lines + via_lines) + "\n)\n")


def _f(v):
    return ("%.6f" % float(v)).rstrip("0").rstrip(".") or "0"


# ---------------------------------------------------------------- 用例集

def construct_cases():
    """构造对拍集（确定性；expected=独立闭式公式手推值）。

    记号：required=0.2（Default 类）；hw=候选走线半宽；保守带 band=0.01。
    expected 公式按轴对齐几何手推（见各 case comment）。
    """
    cases = []
    band = CONSERVATIVE_BAND_MM

    def add(cid, desc, seg, pads, vias, expected, nets, candidate=None,
            board_segments_extra=None):
        cases.append({
            "case_id": cid, "description": desc,
            "candidate_segment": seg,
            "candidate": candidate or {"type": "segment"},
            "pads": pads, "vias": vias,
            "expected_clearance_mm": round(expected, 6),
            "expected_truth": "violation" if expected < REQUIRED_MM
            else ("conservative_band" if expected < REQUIRED_MM + band
                  else "legal"),
            "nets": nets,
            "board_segments_extra": board_segments_extra or [],
        })

    # ---- 族 1：round（圆）× 走线（水平正下方通过；投影在跨内）
    # expected = dy - r_pad - hw
    for (dy, cid_suffix) in ((0.65, "viol"), (0.805, "edge_band"),
                             (0.85, "legal"), (1.2, "legal_far")):
        dy = 10.0 - (10.0 - dy)  # keep literal
        exp = dy - 0.5 - 0.1
        add("round_track_%s" % cid_suffix,
            "圆 pad d=1.0 @ (10,10)；水平走线正下方 hw=0.1；"
            "expected=dy-0.5-0.1",
            {"x1": 8.5, "y1": 10 + dy, "x2": 11.5, "y2": 10 + dy,
             "w": 0.2, "layer": "F.Cu", "net": "NET_T"},
            [{"fp_x": 10, "fp_y": 10, "x": 0, "y": 0, "w": 1.0, "h": 1.0,
              "shape": "circle", "net": "NET_P", "layers": '"F.Cu"'}],
            [], exp, ["NET_T", "NET_P"])

    # ---- 族 2：oval（椭圆胶囊 1.6x0.6）× 走线（长轴端逼近）
    # expected = dx - (w-h)/2 - r - hw，r=min/2=0.3，半核长=0.5
    for (dx, suffix) in ((1.0, "viol"), (1.08, "edge_band"),
                         (1.25, "legal")):
        exp = dx - 0.5 - 0.3 - 0.075
        add("oval_track_%s" % suffix,
            "oval pad 1.6x0.6 @ (10,20)；走线自长轴端水平逼近 hw=0.075；"
            "expected=dx-0.5-0.3-0.075",
            {"x1": 10 + dx, "y1": 20.0, "x2": 10 + dx + 1.2,
             "y2": 20.0, "w": 0.15, "layer": "F.Cu", "net": "NET_T"},
            [{"fp_x": 10, "fp_y": 20, "x": 0, "y": 0, "w": 1.6, "h": 0.6,
              "shape": "oval", "net": "NET_P", "layers": '"F.Cu"'}],
            [], exp, ["NET_T", "NET_P"])

    # ---- 族 3：oval 短轴侧逼近：expected = dy - 0.3 - hw
    add("oval_track_side_viol",
        "oval pad 1.6x0.6 @ (10,26)；走线短轴侧下方；expected=dy-0.3-hw",
        {"x1": 8.8, "y1": 26.47, "x2": 11.2, "y2": 26.47, "w": 0.15,
         "layer": "F.Cu", "net": "NET_T"},
        [{"fp_x": 10, "fp_y": 26, "x": 0, "y": 0, "w": 1.6, "h": 0.6,
          "shape": "oval", "net": "NET_P", "layers": '"F.Cu"'}],
        [], 0.47 - 0.3 - 0.075, ["NET_T", "NET_P"])

    # ---- 族 4：roundrect（1.5x0.3 rratio 0.25，r=0.075）× 直边侧逼近
    # expected = dy - 0.15 - hw（投影在直边跨内 [x0+r, x1-r]）
    for (dy, suffix) in ((0.32, "viol"), (0.43, "edge_band"),
                         (0.45, "legal")):
        exp = dy - 0.15 - 0.075
        add("roundrect_track_%s" % suffix,
            "roundrect 1.5x0.3 r=0.075 @ (10,30)；水平走线正下方 hw=0.075；"
            "expected=dy-0.15-0.075",
            {"x1": 9.6, "y1": 30 + dy, "x2": 10.4, "y2": 30 + dy,
             "w": 0.15, "layer": "F.Cu", "net": "NET_T"},
            [{"fp_x": 10, "fp_y": 30, "x": 0, "y": 0, "w": 1.5, "h": 0.3,
              "shape": "roundrect", "rratio": 0.25, "net": "NET_P",
              "layers": '"F.Cu"'}],
            [], exp, ["NET_T", "NET_P"])

    # ---- 族 5：roundrect 角区 45° 逼近（G1.1 同构，独立手推公式）
    # 右下角弧心 C=(cx+0.675, cy-0.075)（canvas y-down：走线在焊盘下方）
    # expected = dist(走线, C) - 0.075 - hw（闭式线段-点距）
    seg5 = (10.85, 29.65, 11.35, 29.9)
    c5 = (10 + 0.675, 30 - 0.075)
    d5 = _seg_point_dist(c5[0], c5[1], seg5[0], seg5[1], seg5[2], seg5[3])
    add("roundrect_corner45_g11_like",
        "roundrect 1.5x0.3 @ (10,30)；45° 走线逼近右下外角弧（G1.1 同构）；"
        "expected=dist(seg,arc_center)-0.075-0.075（闭式）",
        {"x1": seg5[0], "y1": seg5[1], "x2": seg5[2], "y2": seg5[3],
         "w": 0.15, "layer": "F.Cu", "net": "NET_T"},
        [{"fp_x": 10, "fp_y": 30, "x": 0, "y": 0, "w": 1.5, "h": 0.3,
          "shape": "roundrect", "rratio": 0.25, "net": "NET_P",
          "layers": '"F.Cu"'}],
        [], d5 - 0.075 - 0.075, ["NET_T", "NET_P"])
    seg5b = (13.0, 29.6, 13.55, 29.875)
    d5b = _seg_point_dist(c5[0], c5[1], seg5b[0], seg5b[1], seg5b[2],
                          seg5b[3])
    add("roundrect_corner45_far_legal",
        "同上角区几何但走线远离；expected=dist(seg,arc_center)-0.15（合法侧）",
        {"x1": seg5b[0], "y1": seg5b[1], "x2": seg5b[2], "y2": seg5b[3],
         "w": 0.15, "layer": "F.Cu", "net": "NET_T"},
        [{"fp_x": 10, "fp_y": 30, "x": 0, "y": 0, "w": 1.5, "h": 0.3,
          "shape": "roundrect", "rratio": 0.25, "net": "NET_P",
          "layers": '"F.Cu"'}],
        [], d5b - 0.075 - 0.075, ["NET_T", "NET_P"])

    # ---- 族 6：rect（0.8x1.6）× 走线（旋转 90° 焊盘：fp_rot=90）
    # 焊盘局部 0.8x1.6 旋转 90° -> 板上等效 1.6 宽 x 0.8 高
    # expected = dx - 0.8 - hw（走线自右侧逼近等效宽边）
    for (dx, suffix) in ((0.95, "viol"), (1.15, "legal")):
        exp = dx - 0.8 - 0.1
        add("rect_rot90_track_%s" % suffix,
            "rect 0.8x1.6 fp_rot=90 @ (10,40)（板上等效 1.6x0.8）；"
            "走线右侧水平逼近 hw=0.1；expected=dx-0.8-0.1",
            {"x1": 10 + dx, "y1": 40.0, "x2": 10 + dx + 1.0,
             "y2": 40.0, "w": 0.2, "layer": "F.Cu", "net": "NET_T"},
            [{"fp_x": 10, "fp_y": 40, "fp_rot": 90, "x": 0, "y": 0,
              "w": 0.8, "h": 1.6, "shape": "rect", "net": "NET_P",
              "layers": '"F.Cu"'}],
            [], exp, ["NET_T", "NET_P"])

    # ---- 族 7：pad 自旋（pad_rot=90，rect 1.2x0.4 -> 等效 0.4x1.2）
    # expected = dy - 0.6 - hw（走线下方，投影在直边跨内）
    add("rect_padrot_viol",
        "rect 1.2x0.4 pad_rot=90 @ (10,50)（板上等效 0.4x1.2）；"
        "走线正下方 hw=0.1；expected=dy-0.6-0.1",
        {"x1": 9.7, "y1": 50.82, "x2": 10.3, "y2": 50.82, "w": 0.2,
         "layer": "F.Cu", "net": "NET_T"},
        [{"fp_x": 10, "fp_y": 50, "x": 0, "y": 0, "w": 1.2, "h": 0.4,
          "shape": "rect", "pad_rot": 90, "net": "NET_P",
          "layers": '"F.Cu"'}],
        [], 0.82 - 0.6 - 0.1, ["NET_T", "NET_P"])

    # ---- 族 8：THT 圆 pad（*.Cu）跨层障碍（In1.Cu 走线）
    # expected = dy - 0.45 - hw（全铜层索引验证）
    add("tht_pad_cross_layer_viol",
        "THT 圆 pad d=0.9 layers=*.Cu @ (10,60)；In1.Cu 走线正下方；"
        "expected=dy-0.45-0.075（*.Cu 须在 In1.Cu 生效）",
        {"x1": 9.0, "y1": 60.62, "x2": 11.0, "y2": 60.62, "w": 0.15,
         "layer": "In1.Cu", "net": "NET_T"},
        [{"fp_x": 10, "fp_y": 60, "x": 0, "y": 0, "w": 0.9, "h": 0.9,
          "shape": "circle", "net": "NET_P", "layers": '"*.Cu"'}],
        [], 0.62 - 0.45 - 0.075, ["NET_T", "NET_P"])

    # ---- 族 9：via × pad：expected = d - r_via - r_pad（via 为候选）
    add("via_pad_viol",
        "via size 0.6 @ (10.35,70) vs 圆 pad d=1.0 @ (10,70)；"
        "expected=d-0.3-0.5（重叠=负）",
        {"x1": 8.0, "y1": 71.5, "x2": 12.0, "y2": 71.5, "w": 0.2,
         "layer": "F.Cu", "net": "NET_T"},
        [{"fp_x": 10, "fp_y": 70, "x": 0, "y": 0, "w": 1.0, "h": 1.0,
          "shape": "circle", "net": "NET_P", "layers": '"F.Cu"'}],
        [{"x": 10.35, "y": 70.0, "size": 0.6, "net": "NET_V"}],
        0.35 - 0.3 - 0.5, ["NET_V", "NET_P"],
        candidate={"type": "via", "via_index": 0})
    add("via_pad_legal",
        "via size 0.6 @ (11.1,70) vs 圆 pad d=1.0 @ (10,70)；"
        "expected=1.1-0.3-0.5=0.3（合法侧）",
        {"x1": 8.0, "y1": 71.5, "x2": 12.0, "y2": 71.5, "w": 0.2,
         "layer": "F.Cu", "net": "NET_T"},
        [{"fp_x": 10, "fp_y": 70, "x": 0, "y": 0, "w": 1.0, "h": 1.0,
          "shape": "circle", "net": "NET_P", "layers": '"F.Cu"'}],
        [{"x": 11.1, "y": 70.0, "size": 0.6, "net": "NET_V"}],
        1.1 - 0.3 - 0.5, ["NET_V", "NET_P"],
        candidate={"type": "via", "via_index": 0})

    # ---- 族 10：pad-pad（roundrect vs 圆，水平）：expected = dx - 0.75 - 0.2
    for (dx, suffix) in ((0.98, "viol"), (1.18, "legal")):
        exp = dx - 0.75 - 0.2
        add("padpad_roundrect_circle_%s" % suffix,
            "roundrect 1.5x0.3 @ (10,80) vs 圆 d=0.4 @ (10+dx,80)；"
            "pad-pad 检验（圆 pad 为候选）；expected=dx-0.75-0.2",
            {"x1": 13.5, "y1": 81.2, "x2": 14.5, "y2": 81.2, "w": 0.2,
             "layer": "F.Cu", "net": "NET_T"},
            [{"fp_x": 10, "fp_y": 80, "x": 0, "y": 0, "w": 1.5, "h": 0.3,
              "shape": "roundrect", "rratio": 0.25, "net": "NET_P",
              "layers": '"F.Cu"'},
             {"fp_x": 10 + dx, "fp_y": 80, "x": 0, "y": 0, "w": 0.4,
              "h": 0.4, "shape": "circle", "net": "NET_Q",
              "layers": '"F.Cu"'}],
            [], exp, ["NET_Q", "NET_P"],
            candidate={"type": "pad", "pad_index": 1})

    # ---- 族 11：oval-oval 对角：核段均为水平 [cx-0.5, cx+0.5]，x 跨不叠
    # → 核距=端点距 hypot(dx_gap, dy)，expected = hypot(dx_gap,dy) - 0.6
    add("oval_oval_diag_viol",
        "oval 1.6x0.6 @ (10,90) 与 @ (11.3,90.3)；expected="
        "hypot(0.3,0.3)-0.6（重叠=负；第二 pad 为候选）",
        {"x1": 13.0, "y1": 91.5, "x2": 14.0, "y2": 91.5, "w": 0.2,
         "layer": "F.Cu", "net": "NET_T"},
        [{"fp_x": 10, "fp_y": 90, "x": 0, "y": 0, "w": 1.6, "h": 0.6,
          "shape": "oval", "net": "NET_P", "layers": '"F.Cu"'},
         {"fp_x": 11.3, "fp_y": 90.3, "x": 0, "y": 0, "w": 1.6, "h": 0.6,
          "shape": "oval", "net": "NET_Q", "layers": '"F.Cu"'}],
        [], math.hypot(0.3, 0.3) - 0.6, ["NET_Q", "NET_P"],
        candidate={"type": "pad", "pad_index": 1})
    add("oval_oval_diag_legal",
        "同族 11 几何但拉开到 (12.2,90.3)；expected=hypot(1.2,0.3)-0.6"
        "（合法侧）",
        {"x1": 14.0, "y1": 91.5, "x2": 15.0, "y2": 91.5, "w": 0.2,
         "layer": "F.Cu", "net": "NET_T"},
        [{"fp_x": 10, "fp_y": 90, "x": 0, "y": 0, "w": 1.6, "h": 0.6,
          "shape": "oval", "net": "NET_P", "layers": '"F.Cu"'},
         {"fp_x": 12.2, "fp_y": 90.3, "x": 0, "y": 0, "w": 1.6, "h": 0.6,
          "shape": "oval", "net": "NET_Q", "layers": '"F.Cu"'}],
        [], math.hypot(1.2, 0.3) - 0.6, ["NET_Q", "NET_P"],
        candidate={"type": "pad", "pad_index": 1})

    # ---- 族 12：track-track：expected = 中心距 - hw1 - hw2
    add("track_track_viol",
        "两平行走线 w=0.15 中心距 0.34 @ y=100；expected=0.34-0.075-0.075"
        "=0.19",
        {"x1": 8.0, "y1": 100.34, "x2": 12.0, "y2": 100.34, "w": 0.15,
         "layer": "F.Cu", "net": "NET_T"},
        [],
        [{"x": 10.0, "y": 99.0, "size": 0.6, "net": "NET_F"}],
        0.34 - 0.15, ["NET_T", "NET_F"],
        board_segments_extra=[
            {"x1": 8.0, "y1": 100.0, "x2": 12.0, "y2": 100.0, "w": 0.15,
             "layer": "F.Cu", "net": "NET_F"}])
    add("track_track_legal",
        "两平行走线 w=0.15 中心距 0.5；expected=0.5-0.15=0.35（合法侧）",
        {"x1": 8.0, "y1": 100.5, "x2": 12.0, "y2": 100.5, "w": 0.15,
         "layer": "F.Cu", "net": "NET_T"},
        [],
        [{"x": 10.0, "y": 99.0, "size": 0.6, "net": "NET_F"}],
        0.5 - 0.15, ["NET_T", "NET_F"],
        board_segments_extra=[
            {"x1": 8.0, "y1": 100.0, "x2": 12.0, "y2": 100.0, "w": 0.15,
             "layer": "F.Cu", "net": "NET_F"}])

    # ---- 族 13：合法远距对照（各形状同板）
    add("far_legal_mixed",
        "圆/oval/roundrect/rect 各一，候选走线远距（min clearance 0.225）；"
        "全部合法侧",
        {"x1": 8.0, "y1": 110.8, "x2": 12.0, "y2": 110.8, "w": 0.15,
         "layer": "F.Cu", "net": "NET_T"},
        [{"fp_x": 9.0, "fp_y": 110, "x": 0, "y": 0, "w": 1.0, "h": 1.0,
          "shape": "circle", "net": "NET_P1", "layers": '"F.Cu"'},
         {"fp_x": 10.2, "fp_y": 110, "x": 0, "y": 0, "w": 1.6, "h": 0.6,
          "shape": "oval", "net": "NET_P2", "layers": '"F.Cu"'},
         {"fp_x": 11.8, "fp_y": 110, "x": 0, "y": 0, "w": 1.5, "h": 0.3,
          "shape": "roundrect", "rratio": 0.25, "net": "NET_P3",
          "layers": '"F.Cu"'},
         {"fp_x": 13.2, "fp_y": 110, "x": 0, "y": 0, "w": 0.8, "h": 0.8,
          "shape": "rect", "net": "NET_P4", "layers": '"F.Cu"'}],
        [], 0.8 - 0.5 - 0.075, ["NET_T", "NET_P1", "NET_P2", "NET_P3",
                                "NET_P4"])

    # ---- 族 14：旧模型盲区负对照（oval 长轴逼近距中心远、距边缘近）
    # 旧模型 min(w,h)/2=0.3：中心距=1.0+0.5=1.5 -> need=0.575 -> pass（漏）
    # 新精确：expected=dx-0.5-0.3-0.075=0.125（violation）
    add("old_model_blindspot_oval",
        "oval 长轴端距中心 1.5（旧口径 need=0.575 放行）但距真实边界 "
        "0.125 -> 新模型必须拦截（P3 根因同构）",
        {"x1": 11.0, "y1": 20.0 + 5.0, "x2": 12.2, "y2": 20.0 + 5.0,
         "w": 0.15, "layer": "F.Cu", "net": "NET_T2"},
        [{"fp_x": 10, "fp_y": 25, "x": 0, "y": 0, "w": 1.6, "h": 0.6,
          "shape": "oval", "net": "NET_P5", "layers": '"F.Cu"'}],
        [], 1.0 - 0.5 - 0.3 - 0.075, ["NET_T2", "NET_P5"])

    return cases


def _seg_point_dist(px, py, ax, ay, bx, by):
    vx, vy = bx - ax, by - ay
    l2 = vx * vx + vy * vy
    if l2 <= 1e-18:
        return math.hypot(px - ax, py - ay)
    t = ((px - ax) * vx + (py - ay) * vy) / l2
    t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)
    return math.hypot(px - (ax + t * vx), py - (ay + t * vy))


def build_case_board_text(case):
    """用例 -> 板文本（含候选段? 否——候选段仅作 query，不入板）。"""
    segs = list(case.get("board_segments_extra") or [])
    cb = CaseBoard(case["case_id"], segs, case["pads"], case["vias"])
    return cb.board_text()


def _audit_table():
    return NetClassTable({"Default": NetClass("Default", REQUIRED_MM, 0.15)},
                         {}, [], "declared_defaults:G1.2 构造集（Default "
                                 "0.2mm，对齐 Rev-C 全类实测 0.2）")


def run_audit(cases=None):
    """G1.2 审计主入口 -> canonical-ready dict（含漏报/误报/交叉台账）。"""
    from .geometry import PadGeom
    cases = cases if cases is not None else construct_cases()
    table = _audit_table()
    case_rows = []
    fn_pre, fn_chk = [], []
    fp_pre, fp_chk = [], []
    cross = []
    for case in cases:
        text = build_case_board_text(case)
        parsed_a = parse_board_text(text)
        parsed_b = parse_board_text_alt(text)
        pre = AdvisoryPrecheckV41(build_geom_items(parsed_a), table)
        chk = IndependentGeometryChecker(build_check_items(parsed_b), table)
        cand = case.get("candidate") or {"type": "segment"}
        ctype = cand.get("type", "segment")
        if ctype == "segment":
            s = case["candidate_segment"]
            r_pre = pre.check_segment(s["net"], s["layer"], s["w"],
                                      s["x1"], s["y1"], s["x2"], s["y2"])
            r_chk = chk.check_segment(s["net"], s["layer"], s["w"],
                                      s["x1"], s["y1"], s["x2"], s["y2"])
        elif ctype == "via":
            v = case["vias"][cand["via_index"]]
            r_pre = pre.check_via(v["net"], ["F.Cu", "B.Cu"], v["size"],
                                  v["x"], v["y"])
            r_chk = chk.check_via(v["net"], ["F.Cu", "B.Cu"], v["size"],
                                  v["x"], v["y"])
        elif ctype == "pad":
            pa_rec = parsed_a["pads"][cand["pad_index"]]
            pad_a = PadGeom(pa_rec["shape"], pa_rec["x_mm"], pa_rec["y_mm"],
                            pa_rec["w_mm"], pa_rec["h_mm"],
                            pa_rec["rotation_deg"],
                            radius=pa_rec["corner_radius_mm"],
                            pad_id=pa_rec["pad_id"], net_id=pa_rec["net_id"],
                            layers=pa_rec["layers"])
            r_pre = pre.check_pad(pad_a, pa_rec["layers"])
            r_chk = chk.check_pad(parsed_b["pads"][cand["pad_index"]],
                                  parsed_b["copper_layers"])
        else:
            raise ValueError("未知候选类型（fail-closed）: %r" % (ctype,))
        v_pre = r_pre["verdict"]
        v_chk = r_chk["verdict"]
        truth = case["expected_truth"]
        row = {
            "case_id": case["case_id"],
            "description": case["description"],
            "expected_clearance_mm": case["expected_clearance_mm"],
            "truth": truth,
            "precheck": {
                "verdict": v_pre,
                "min_foreign_clearance_mm":
                    r_pre["min_foreign_clearance_mm"],
            },
            "checker": {
                "verdict": v_chk,
                "min_foreign_clearance_mm":
                    r_chk["min_foreign_clearance_mm"],
            },
        }
        case_rows.append(row)
        if truth == "violation":
            if v_pre != "violation":
                fn_pre.append(dict(row))
            if v_chk != "violation":
                fn_chk.append(dict(row))
        else:
            # legal / conservative_band：引擎判违例=误报（band 例为设计内
            # 保守行为；legal 例为真实模型偏差——均逐条登记不设门）
            if v_pre == "violation":
                fp_pre.append({
                    "case_id": case["case_id"],
                    "truth": truth,
                    "expected_clearance_mm": case["expected_clearance_mm"],
                    "engine": r_pre["engine"],
                    "kind": "conservative_band_by_design"
                    if truth == "conservative_band"
                    else "model_discrepancy",
                    "detail": r_pre["violations"],
                })
            if v_chk == "violation":
                fp_chk.append({
                    "case_id": case["case_id"],
                    "truth": truth,
                    "expected_clearance_mm": case["expected_clearance_mm"],
                    "engine": r_chk["engine"],
                    "kind": "conservative_band_by_design"
                    if truth == "conservative_band"
                    else "model_discrepancy",
                    "detail": r_chk["violations"],
                })
        if v_pre != v_chk:
            cross.append({
                "case_id": case["case_id"],
                "precheck": v_pre,
                "checker": v_chk,
                "status": "blocked",
                "note": "预检/checker 交叉不一致（对拍纪律：不静默取其一）",
            })
    viol_n = sum(1 for c in cases if c["expected_truth"] == "violation")
    legal_n = sum(1 for c in cases if c["expected_truth"] == "legal")
    band_n = sum(1 for c in cases
                 if c["expected_truth"] == "conservative_band")
    fn_rate_pre = (len(fn_pre) / viol_n) if viol_n else 0.0
    fn_rate_chk = (len(fn_chk) / viol_n) if viol_n else 0.0
    return {
        "schema": _AUDIT_SCHEMA,
        "declared_date": DECLARED_DATE,
        "gate": "G1.2",
        "required_clearance_mm": REQUIRED_MM,
        "conservative_band_mm": CONSERVATIVE_BAND_MM,
        "case_count": len(cases),
        "truth_counts": {"violation": viol_n, "legal": legal_n,
                         "conservative_band": band_n},
        "false_negatives": {
            "precheck": {"count": len(fn_pre),
                         "rate": round(fn_rate_pre, 6), "detail": fn_pre},
            "checker": {"count": len(fn_chk),
                        "rate": round(fn_rate_chk, 6), "detail": fn_chk},
            "gate_rule": "漏报率=0（真值违例而引擎 clean 即漏报）",
        },
        "false_positives": {
            "gate_rule": "描述性登记不设门（G1.3 台账）",
            "precheck": fp_pre,
            "checker": fp_chk,
        },
        "cross_disagreements": cross,
        "cases": case_rows,
    }


def main(argv=None):
    """CLI：python -m pcbflow.v4_1.audit --out <dir>"""
    import argparse
    from pathlib import Path
    from .canonical import write_canonical_json
    ap = argparse.ArgumentParser(prog="pcbflow.v4_1.audit")
    ap.add_argument("--out", required=True)
    ns = ap.parse_args(argv)
    audit = run_audit()
    out = Path(ns.out)
    out.mkdir(parents=True, exist_ok=True)
    target = out / "false-negative-audit.json"
    write_canonical_json(target, audit)
    print("false_negatives precheck=%d checker=%d (violation_truth=%d)"
          % (audit["false_negatives"]["precheck"]["count"],
             audit["false_negatives"]["checker"]["count"],
             audit["truth_counts"]["violation"]))
    print("false_positives precheck=%d checker=%d cross_disagreements=%d"
          % (len(audit["false_positives"]["precheck"]),
             len(audit["false_positives"]["checker"]),
             len(audit["cross_disagreements"])))
    print("written: %s" % target)
    return 0 if (audit["false_negatives"]["precheck"]["count"] == 0
                 and audit["false_negatives"]["checker"]["count"] == 0
                 and not audit["cross_disagreements"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
