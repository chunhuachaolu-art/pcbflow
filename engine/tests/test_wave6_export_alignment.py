# -*- coding: utf-8 -*-
"""P5⑥ 出口对齐测试（合同 V5-P5-WAVE6-EXPORT-ALIGNMENT-2026-09-16 §2，
A 包 D6-1+D6-2，纯导出侧；v5.kicad_export 0.4.0；版本钉已由 V5-R1
ED-X 修复批翻新至 0.5.0，见 test_version_incremented 披露）。

钉死：
- **D6-1 SMD 焊盘=单层画法**（显式层列表 → ``(pad 1 smd …)``，正/背面由声明
  层定——正面 F.Cu/反面 B.Cu 逐字 pin 行，module 层随焊盘面）；
- **D6-1 通孔焊盘=真实通孔层跨**（layers=="all"=adapter 的 *.Cu 通孔标记 →
  ``(pad 1 thru_hole … (drill D) (layers "*.Cu"))``，KiCad 通孔规范形、
  D=via_model 孔径（板值/缺省 0.3 双钉）；⑥前的「all→全部信号层按 smd 画」
  兜底画法不再出现（padstack 根因关闭）；
- **D6-1 fail-closed**：layers 缺失/非法（非 "all" 字符串、空表、未知层、
  非列表）→ ExportError 带 pad_terminals 键路径，无 "all" 回退；
- **D6-2 端点扎铜几何**：align_endpoint_into_pad 单元钉值（圆/矩形、界内
  原样含边界、界外确定性扎入=铜边界与焊盘心中点）+ 导出集成（正面/反面、
  首/末点、换层衔接点不动、无焊盘参照不动）+ **no-op 纪律**（端点已在焊盘
  心 → 导出段与 routes 逐段转录逐位一致=现网数据零扰动）；
- 确定性：双跑字节等；board 只读。

零 kicad-cli、零网络、零 out/ 接触（断言全走 kicad_pcb_bytes 内存 bytes）。
"""
import copy
import os
import re
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from v5 import canonical  # noqa: E402
from v5.adapters.kicad_adapter import parse_sexpr  # noqa: E402
from v5.board import compute_board_sha256, load_board  # noqa: E402
from v5.kicad_export import (  # noqa: E402
    VERSION,
    ExportError,
    align_endpoint_into_pad,
    kicad_pcb_bytes,
)

# ---------------------------------------------------------------- 夹具板构造

SIG2 = [{"id": "F.Cu", "kind": "signal", "preferred_direction": "any",
         "available": True},
        {"id": "B.Cu", "kind": "signal", "preferred_direction": "any",
         "available": True}]
SIG_PLANE = [{"id": "F.Cu", "kind": "signal", "preferred_direction": "any",
              "available": True},
             {"id": "In1.Cu", "kind": "signal", "preferred_direction": "any",
              "available": True},
             {"id": "In2.Cu", "kind": "plane", "preferred_direction": "any",
              "available": False},
             {"id": "B.Cu", "kind": "signal", "preferred_direction": "any",
              "available": True}]
WS = {"x_min": 0.0, "y_min": 0.0, "x_max": 40.0, "y_max": 30.0}


def make_board(board_id, partitions, nets, stackup=None, via_model=None,
               validate=True):
    """自造合法板（synthetic provenance；load_board 落链）。

    validate=False：跳过 L0 schema 校验（只算 board_sha256）——供构造「绕过
    载入面的裸 dict」测导出层自身的 fail-closed 防线（L0 之下还有一道）。
    """
    board = {
        "schema_version": "v5.board.v1",
        "board_id": board_id,
        "stackup": stackup or SIG2,
        "workspace": dict(WS),
        "zones": [],
        "partitions": partitions,
        "nets": nets,
        "hard_rules": {
            "R1": {"k_a": 0.4, "floor_mm": 0.3},
            "R2": {"min_distance_mm": 3.0, "max_parallel_mm": 5.0},
            "R3": {"unsplittable": True},
            "R4": {"return_via_required": True, "max_distance_mm": 2.0},
            "R5": {"min_clearance_mm": 0.5},
            "R6": {"plane_forbidden": True, "keepout_zones_forbidden": True},
        },
        "principle_registry": [],
        "provenance": {"source_type": "synthetic",
                       "source_uri": "tests/test_wave6_export_alignment.py",
                       "source_sha256": "0" * 64, "adapter": "hand"},
    }
    if via_model is not None:
        board["via_model"] = via_model
    board["provenance"]["board_sha256"] = compute_board_sha256(board)
    if validate:
        load_board(board)
    return board


def part(pid, a, b, pads=None, ptype="MISC"):
    geo = {"endpoints": [list(a), list(b)]}
    if pads is not None:
        geo["pad_terminals"] = pads
    return {"partition_id": pid, "ptype": ptype, "layer_policy": "any",
            "width_prior": {"w_min": 0.2, "w_max": 0.4}, "current_a": 0,
            "speed_class": "unknown", "geometry": geo}


def net(nid, pids):
    return {"net_id": nid, "net_class": "MISC", "partitions": list(pids)}


def routes_doc(board, entries):
    sha = board["provenance"]["board_sha256"]
    return {"schema_version": "v5.routes.v1", "board_id": board["board_id"],
            "board_sha256": sha, "routes": entries, "negotiation_log": [],
            "provenance": {"generator": "v5.executor/0.4.0",
                           "board_sha256": sha}}


def entry(pid, nid, layer, pts, width=0.2, tv=None, rv=None):
    return {"partition_id": pid, "net_id": nid, "layer": layer,
            "polyline": [list(p) for p in pts], "width": width,
            "transition_vias": [list(v) for v in (tv or [])],
            "return_vias": [list(v) for v in (rv or [])]}


def pad_lines(txt):
    """导出件中的 (pad 1 …) 行（含缩进去除）。"""
    return [l.strip() for l in txt.splitlines() if "(pad 1" in l]


_SEG_HEAD = re.compile(r"^\(segment \(start (\S+) (\S+)\) \(end (\S+) (\S+)\)")


def segment_tokens(txt):
    """(segment …) 行的 (start/end) 四个数值 token（repr 逐位还原）。"""
    out = []
    for l in txt.splitlines():
        m = _SEG_HEAD.match(l.strip())
        if m:
            out.append(m.groups())
    return out


def _seg_head(ax, ay, bx, by):
    return (repr(float(ax)), repr(float(ay)), repr(float(bx)), repr(float(by)))


def _expected_segment_heads(routes):
    """routes 逐段转录的期望 (start/end) token（repr 逐位）。"""
    out = []
    for r in routes["routes"]:
        pts = r["polyline"]
        for a, b in zip(pts[:-1], pts[1:]):
            out.append(_seg_head(a[0], a[1], b[0], b[1]))
    return out


# ---------------------------------------------------------------- D6-1 SMD

def test_smd_pad_front_face_single_layer():
    """显式层列表 [F.Cu] = SMD 正面焊盘：smd 单层画法逐字 pin（module 面=F）。"""
    board = make_board("w6-smd-f",
                       [part("P1", (2.0, 5.0), (18.0, 5.0),
                             pads=[{"endpoint": 0, "shape": "rect",
                                    "size_mm": [2.0, 1.0], "layers": ["F.Cu"]},
                                   {"endpoint": 1, "shape": "rect",
                                    "size_mm": [2.0, 1.0],
                                    "layers": ["F.Cu"]}])],
                       [net("N1", ["P1"])])
    doc = routes_doc(board, [entry("P1", "N1", "F.Cu",
                                   [[2.0, 5.0], [18.0, 5.0]])])
    txt = kicad_pcb_bytes(board, doc).decode("utf-8")
    pads = pad_lines(txt)
    assert len(pads) == 2
    for l in pads:
        assert l == ('(pad 1 smd rect (at 0 0) (size 2.0 1.0) (layers "F.Cu")'
                     ' (net 1 "N1")))')
    assert '(module "V5-anchor-P1-a" (layer "F.Cu") (at 2.0 5.0)' in txt


def test_smd_pad_back_face_single_layer():
    """显式层列表 [B.Cu] = SMD 反面焊盘：module 面=B、pad 层=B（背面扎铜面）。"""
    board = make_board("w6-smd-b",
                       [part("P1", (2.0, 5.0), (18.0, 5.0),
                             pads=[{"endpoint": 0, "shape": "circle",
                                    "size_mm": [1.2], "layers": ["B.Cu"]},
                                   {"endpoint": 1, "shape": "circle",
                                    "size_mm": [1.2], "layers": ["B.Cu"]}])],
                       [net("N1", ["P1"])])
    doc = routes_doc(board, [entry("P1", "N1", "B.Cu",
                                   [[2.0, 5.0], [18.0, 5.0]])])
    txt = kicad_pcb_bytes(board, doc).decode("utf-8")
    pads = pad_lines(txt)
    assert len(pads) == 2
    for l in pads:
        assert l == ('(pad 1 smd circle (at 0 0) (size 1.2 1.2) (layers "B.Cu")'
                     ' (net 1 "N1")))')
    assert '(module "V5-anchor-P1-a" (layer "B.Cu") (at 2.0 5.0)' in txt


# ---------------------------------------------------------------- D6-1 通孔

def test_thru_hole_pad_real_span_default_drill():
    """layers=="all" = 通孔：thru_hole + (layers "*.Cu") + 缺省 drill 0.3
    （via_model 文档化常量）；⑥前的 smd 全信号层画法不再出现。"""
    board = make_board("w6-th",
                       [part("P1", (2.0, 5.0), (18.0, 5.0),
                             pads=[{"endpoint": 0, "shape": "rect",
                                    "size_mm": [1.6, 1.6], "layers": "all"},
                                   {"endpoint": 1, "shape": "circle",
                                    "size_mm": [1.6], "layers": "all"}])],
                       [net("N1", ["P1"])])
    doc = routes_doc(board, [entry("P1", "N1", "F.Cu",
                                   [[2.0, 5.0], [18.0, 5.0]])])
    txt = kicad_pcb_bytes(board, doc).decode("utf-8")
    pads = pad_lines(txt)
    assert len(pads) == 2
    assert '(pad 1 thru_hole rect (at 0 0) (size 1.6 1.6) (drill 0.3) ' \
        '(layers "*.Cu") (net 1 "N1")))' in pads
    assert '(pad 1 thru_hole circle (at 0 0) (size 1.6 1.6) (drill 0.3) ' \
        '(layers "*.Cu") (net 1 "N1")))' in pads
    assert not any(" smd " in l for l in pads)          # 兜底画法废除
    assert not any('"F.Cu" "B.Cu"' in l for l in pads)  # 不再展开信号层


def test_thru_hole_drill_from_board_via_model():
    """drill 走板 via_model（孔几何唯一推导口）：drill_mm=0.45 → (drill 0.45)。"""
    board = make_board("w6-th-vm",
                       [part("P1", (2.0, 5.0), (18.0, 5.0),
                             pads=[{"endpoint": 0, "shape": "circle",
                                    "size_mm": [1.6], "layers": "all"},
                                   {"endpoint": 1, "shape": "circle",
                                    "size_mm": [1.6], "layers": "all"}])],
                       [net("N1", ["P1"])],
                       via_model={"drill_mm": 0.45, "annular_mm": 0.2})
    doc = routes_doc(board, [entry("P1", "N1", "F.Cu",
                                   [[2.0, 5.0], [18.0, 5.0]])])
    txt = kicad_pcb_bytes(board, doc).decode("utf-8")
    assert all("(drill 0.45)" in l for l in pad_lines(txt))


def test_thru_hole_span_independent_of_signal_subset():
    """跨层画法与信号层子集无关：含 plane 层的 4 层叠层上通孔仍= *.Cu 全铜层跨
    （KiCad 按板 (layers) 表解析），module 面=stackup 首铜层。"""
    board = make_board("w6-th-4l",
                       [part("P1", (2.0, 5.0), (18.0, 5.0),
                             pads=[{"endpoint": 0, "shape": "rect",
                                    "size_mm": [1.6, 1.6], "layers": "all"},
                                   {"endpoint": 1, "shape": "rect",
                                    "size_mm": [1.6, 1.6], "layers": "all"}])],
                       [net("N1", ["P1"])], stackup=SIG_PLANE)
    doc = routes_doc(board, [entry("P1", "N1", "F.Cu",
                                   [[2.0, 5.0], [18.0, 5.0]])])
    txt = kicad_pcb_bytes(board, doc).decode("utf-8")
    pads = pad_lines(txt)
    assert len(pads) == 2
    for l in pads:
        assert l.startswith("(pad 1 thru_hole rect ") and \
            '(layers "*.Cu")' in l
    assert '(module "V5-anchor-P1-a" (layer "F.Cu") (at 2.0 5.0)' in txt


def test_implicit_anchor_stays_smd_route_layer():
    """隐式 anchor（无 pad_terminals）⑥画法零改写：smd rect 1.0、层随 route。"""
    board = make_board("w6-implicit",
                       [part("P1", (2.0, 5.0), (18.0, 5.0))],
                       [net("N1", ["P1"])])
    doc = routes_doc(board, [entry("P1", "N1", "B.Cu",
                                   [[2.0, 5.0], [18.0, 5.0]])])
    txt = kicad_pcb_bytes(board, doc).decode("utf-8")
    pads = pad_lines(txt)
    assert pads == [
        '(pad 1 smd rect (at 0 0) (size 1.0 1.0) (layers "B.Cu")'
        ' (net 1 "N1")))',
        '(pad 1 smd rect (at 0 0) (size 1.0 1.0) (layers "B.Cu")'
        ' (net 1 "N1")))',
    ]


# ---------------------------------------------------------------- D6-1 fail

@pytest.mark.parametrize("layers_mut, tag", [
    ("__missing__", "missing"),
    ("top", "str-non-all"),
    ([], "empty-list"),
    (["Nope.Cu"], "unknown-layer"),
    (42, "non-list"),
    (["F.Cu", "Nope.Cu"], "partial-unknown"),
])
def test_pad_layers_field_fail_closed_no_all_fallback(layers_mut, tag):
    """layers 字段缺失/非法 → ExportError 带 pad_terminals 键路径；禁止回退
    "all"（fail-closed 纪律，D6-1）。schema 能拦的形态（空表/非列表）在 L0
    即拒——本测以裸 dict（validate=False）钉导出层自身的防线：任何到达
    导出器的非法 layers 一律抛错，无 "all" 回退。"""
    item = {"endpoint": 0, "shape": "rect", "size_mm": [2.0, 1.0]}
    if layers_mut != "__missing__":
        item["layers"] = layers_mut
    board = make_board("w6-bad-" + tag,
                       [part("P1", (2.0, 5.0), (18.0, 5.0), pads=[item])],
                       [net("N1", ["P1"])], validate=False)
    doc = routes_doc(board, [entry("P1", "N1", "F.Cu",
                                   [[2.0, 5.0], [18.0, 5.0]])])
    with pytest.raises(ExportError) as ei:
        kicad_pcb_bytes(board, doc)
    assert "pad_terminals[0].layers" in str(ei.value)


# ---------------------------------------------------------------- D6-2 几何

def test_align_endpoint_inside_pad_unchanged():
    """界内（含边界）原样返回：圆心/矩形内/圆边界/矩形边界均逐位原点。"""
    assert align_endpoint_into_pad([2.0, 5.0], (2.0, 5.0), "rect",
                                   [1.0, 1.4]) == [2.0, 5.0]
    assert align_endpoint_into_pad([2.4, 5.6], (2.0, 5.0), "rect",
                                   [1.0, 1.4]) == [2.4, 5.6]   # 界内
    assert align_endpoint_into_pad([2.5, 5.0], (2.0, 5.0), "rect",
                                   [1.0, 1.4]) == [2.5, 5.0]   # 矩形右边界
    assert align_endpoint_into_pad([2.0, 5.0], (2.0, 5.0), "circle",
                                   [1.6]) == [2.0, 5.0]        # 圆心
    assert align_endpoint_into_pad([2.8, 5.0], (2.0, 5.0), "circle",
                                   [1.6]) == [2.8, 5.0]        # 圆边界（d=r）


def test_align_endpoint_outside_rect_sinks_to_boundary_center_midpoint():
    """矩形外：沿 pt→心方向移到「铜边界交点-焊盘心」中点（s=s_max/2）。
    参照例：心 (2,5)、size [1.0,1.4]、pt (2.6,5)——s_max=hw/|dx|=0.5/0.6，
    扎入点 x = 2 + (0.5/0.6)/2·0.6，且 |x−2| < hw（严格在铜内）。"""
    got = align_endpoint_into_pad([2.6, 5.0], (2.0, 5.0), "rect", [1.0, 1.4])
    assert got == [2.0 + (0.5 / 0.6) / 2.0 * 0.6, 5.0]   # 公式逐位钉值
    assert abs(got[0] - 2.0) < 0.5                        # 严格界内
    # 斜向：s_max=min(hw/|dx|, hh/|dy|)，y 向先到界
    got2 = align_endpoint_into_pad([2.6, 6.2], (2.0, 5.0), "rect", [1.0, 1.4])
    assert got2 == [2.0 + (0.7 / 1.2) / 2.0 * 0.6,
                    5.0 + (0.7 / 1.2) / 2.0 * 1.2]
    assert abs(got2[0] - 2.0) < 0.5 and abs(got2[1] - 5.0) < 0.7


def test_align_endpoint_outside_circle_sinks_to_boundary_center_midpoint():
    """圆外：d>r → 扎入点=圆边界与圆心中点。参照例：r=0.8、pt (3.0,5)、
    心 (2,5) → 扎入点 x=2.4（=边界 2.8 与圆心 2.0 的中点，逐位精确）。"""
    got = align_endpoint_into_pad([3.0, 5.0], (2.0, 5.0), "circle", [1.6])
    assert got == [2.4, 5.0]
    assert (got[0] - 2.0) ** 2 + (got[1] - 5.0) ** 2 < 0.64   # 严格界内


def test_align_endpoint_deterministic():
    """同输入双跑逐位相等（确定性纪律）。"""
    a = align_endpoint_into_pad([2.6, 6.2], (2.0, 5.0), "rect", [1.0, 1.4])
    b = align_endpoint_into_pad([2.6, 6.2], (2.0, 5.0), "rect", [1.0, 1.4])
    assert a == b and repr(a) == repr(b)


# ------------------------------------------------------ D6-2 导出集成

def _smd_board():
    """正面 F.Cu rect（半宽 0.5）+ 反面 B.Cu circle（r=0.6）双焊盘板。"""
    return make_board("w6-align",
                      [part("P1", (2.0, 5.0), (18.0, 5.0),
                            pads=[{"endpoint": 0, "shape": "rect",
                                   "size_mm": [1.0, 1.4], "layers": ["F.Cu"]},
                                  {"endpoint": 1, "shape": "circle",
                                   "size_mm": [1.2], "layers": ["B.Cu"]}])],
                      [net("N1", ["P1"])])


def test_export_sinks_short_head_front_face():
    """正面扎铜：首点离 F.Cu 焊盘心 0.6（界外 0.1）→ 导出首段起点=扎入点
    （与 align_endpoint_into_pad 输出 repr 逐位一致），其余段不动。"""
    board = _smd_board()
    doc = routes_doc(board, [entry("P1", "N1", "F.Cu",
                                   [[2.6, 5.0], [10.0, 5.0], [18.0, 5.0]])])
    txt = kicad_pcb_bytes(board, doc).decode("utf-8")
    heads = segment_tokens(txt)
    want = align_endpoint_into_pad([2.6, 5.0], (2.0, 5.0), "rect", [1.0, 1.4])
    assert len(heads) == 2
    assert heads[0] == (repr(want[0]), repr(want[1]),
                        repr(10.0), repr(5.0))
    # 末点=反面焊盘心（界内）→ 原样
    assert heads[-1] == _seg_head(10.0, 5.0, 18.0, 5.0)


def test_export_sinks_short_tail_back_face():
    """反面扎铜：末点离 B.Cu 圆焊盘（r=0.5）心 1.0（界外）→ 导出末段终点=
    扎入点（二进制精确值 18.25：边界 18.5 与焊盘心 18.0 的中点）。"""
    board = make_board("w6-align-b",
                       [part("P1", (2.0, 5.0), (18.0, 5.0),
                             pads=[{"endpoint": 0, "shape": "rect",
                                    "size_mm": [1.0, 1.4], "layers": ["F.Cu"]},
                                   {"endpoint": 1, "shape": "circle",
                                    "size_mm": [1.0], "layers": ["B.Cu"]}])],
                       [net("N1", ["P1"])])
    doc = routes_doc(board, [entry("P1", "N1", "B.Cu",
                                   [[2.0, 5.0], [10.0, 5.0], [19.0, 5.0]])])
    txt = kicad_pcb_bytes(board, doc).decode("utf-8")
    heads = segment_tokens(txt)
    assert len(heads) == 2
    # 首点=正面焊盘心（界内）→ 原样
    assert heads[0] == _seg_head(2.0, 5.0, 10.0, 5.0)
    # 末点扎入（r=0.5、d=1.0 → s_max=0.5、s=0.25 → x=18.25，全二进制精确）
    assert heads[-1] == _seg_head(10.0, 5.0, 18.25, 5.0)


def test_export_endpoints_at_pad_centers_untouched_noop():
    """no-op 纪律：端点=焊盘心（现网数据形态）→ 导出段与 routes 逐段转录
    逐位一致（v5 routes 本体不动 + 现网导出零扰动）。"""
    board = _smd_board()
    doc = routes_doc(board, [entry("P1", "N1", "F.Cu",
                                   [[2.0, 5.0], [10.0, 5.0], [18.0, 5.0]])])
    txt = kicad_pcb_bytes(board, doc).decode("utf-8")
    assert segment_tokens(txt) == _expected_segment_heads(doc)


def test_export_midroute_joint_untouched_only_true_ends_aligned():
    """换层衔接点不吸附：两 entry（F→B，衔接点 (10,5) 无焊盘）——衔接点
    原样；真端点短入时只有首/末段动。"""
    board = _smd_board()
    doc = routes_doc(board, [
        entry("P1", "N1", "F.Cu", [[2.6, 5.0], [10.0, 5.0]], tv=[[10.0, 5.0]]),
        entry("P1", "N1", "B.Cu", [[10.0, 5.0], [18.0, 5.0]], tv=[[10.0, 5.0]]),
    ])
    txt = kicad_pcb_bytes(board, doc).decode("utf-8")
    heads = segment_tokens(txt)
    want = align_endpoint_into_pad([2.6, 5.0], (2.0, 5.0), "rect", [1.0, 1.4])
    assert len(heads) == 2
    assert heads[0] == (repr(want[0]), repr(want[1]),
                        repr(10.0), repr(5.0))
    # 衔接点双侧原样（(10,5) 无焊盘参照，不吸附）
    assert heads[1] == _seg_head(10.0, 5.0, 18.0, 5.0)


def test_export_endpoint_without_pad_reference_untouched():
    """无焊盘参照的端点不吸附（首末点=分区端点的链合同由 route_check 审计，
    导出不发明几何）：首点 (2.6,7.0) 无同位焊盘 → 全部段原样。"""
    board = _smd_board()
    doc = routes_doc(board, [entry("P1", "N1", "F.Cu",
                                   [[2.6, 7.0], [10.0, 5.0], [18.0, 5.0]])])
    txt = kicad_pcb_bytes(board, doc).decode("utf-8")
    assert segment_tokens(txt) == _expected_segment_heads(doc)


def test_export_alignment_thru_hole_pad_arrival_front_and_back():
    """通孔焊盘双面到达：端点在 TH 焊盘心（界内）正/反面到达均原样——
    TH 层跨=全铜层，任一层到达皆扎在铜内（padstack/悬空族关闭形态）。"""
    board = make_board("w6-align-th",
                       [part("P1", (2.0, 5.0), (18.0, 5.0),
                             pads=[{"endpoint": 0, "shape": "circle",
                                    "size_mm": [1.6], "layers": "all"},
                                   {"endpoint": 1, "shape": "circle",
                                    "size_mm": [1.6], "layers": "all"}])],
                       [net("N1", ["P1"])])
    doc = routes_doc(board, [
        entry("P1", "N1", "F.Cu", [[2.0, 5.0], [10.0, 5.0]], tv=[[10.0, 5.0]]),
        entry("P1", "N1", "B.Cu", [[10.0, 5.0], [18.0, 5.0]], tv=[[10.0, 5.0]]),
    ])
    txt = kicad_pcb_bytes(board, doc).decode("utf-8")
    assert segment_tokens(txt) == _expected_segment_heads(doc)
    for l in pad_lines(txt):
        assert l.startswith("(pad 1 thru_hole circle ") and \
            '(layers "*.Cu")' in l


def test_export_alignment_ribbon_band_endpoints():
    """ribbon 带段同规则：带端点=隐式 anchor 心（界内）→ 原样逐网落段；
    无吸附扰动。"""
    band = part("BS", (10.0, 2.0), (10.0, 18.0), ptype="BUS")
    band["geometry"]["copper_band"] = [9.2, 10.8]
    band["geometry"]["occupancy_mm"] = 1.6
    board = make_board("w6-align-ribbon", [band],
                       [net("B0", ["BS"]), net("B1", ["BS"])])
    doc = routes_doc(board, [entry("BS", "B0", "F.Cu",
                                   [[10.0, 2.0], [10.0, 18.0]], width=1.6)])
    txt = kicad_pcb_bytes(board, doc).decode("utf-8")
    heads = segment_tokens(txt)
    assert len(heads) == 2   # B0/B1 各一（组首网 entry 带段逐网转录）
    for h in heads:
        assert h == _seg_head(10.0, 2.0, 10.0, 18.0)


# ---------------------------------------------------------------- 纪律

def test_version_incremented():
    """kicad_export 版本号递增（合同：现值自查+1）：0.3.0 → 0.4.0。

    V5-R1 ED-X 修复批翻新披露（2026-09-27，任务书 V5-R1-EDX-EXPORT-FIX-
    2026-09-26 W-X3④，D8/R1 同式先例）：0.4.0 → 0.5.0（端点合同「恰 2」→
    「≥2 逐点」+pads 发射/_aligned 多端点化+隐式 anchor 消费侧补发；2 端
    旧域逐位不变）。首跑 failed 恰此 1 处（本函数），无其它翻新面。

    V5-R7 翻新披露（2026-10-04，判读席第 1 轮 findings 门 1：R7 升版时本钉
    漏同步致全量 1 红）：0.5.0 → 0.6.0（V5-R7 W-2 per-class 净类写出+
    netclass-mask 随件；缺类板 bytes 逐字节不变，升位理由全文见
    v5/kicad_export.py VERSION 注释链）。
    0.6.0 → 0.7.0（OPT-11，pcbflow-optimap EXEC-R1：空成员净类跳过+披露、
    TH drill 原值/机械孔分开建模；缺 holes 键合成板 bytes 逐字节不变、
    升位理由全文见 v5/kicad_export.py VERSION 注释链）。"""
    assert VERSION == "0.7.0"


def test_double_run_byte_equal_and_board_readonly():
    """同输入双跑字节等；board/routes 只读（canonical 视图零变化）。"""
    board = _smd_board()
    doc = routes_doc(board, [entry("P1", "N1", "F.Cu",
                                   [[2.6, 5.0], [10.0, 5.0], [18.0, 5.0]])])
    b_before = canonical.canonical_json(copy.deepcopy(board))
    d_before = canonical.canonical_json(copy.deepcopy(doc))
    first = kicad_pcb_bytes(board, doc)
    second = kicad_pcb_bytes(board, doc)
    assert first == second
    assert canonical.canonical_json(board) == b_before
    assert canonical.canonical_json(doc) == d_before


def test_export_parses_as_sexpr_with_thru_and_smd():
    """导出件 s-expression 可解析（adapter 读回面）：TH/SMD 行各就各位，
    网表 net 号一致。"""
    board = make_board("w6-parse",
                       [part("P1", (2.0, 5.0), (18.0, 5.0),
                             pads=[{"endpoint": 0, "shape": "circle",
                                    "size_mm": [1.6], "layers": "all"},
                                   {"endpoint": 1, "shape": "rect",
                                    "size_mm": [1.0, 2.0],
                                    "layers": ["B.Cu"]}])],
                       [net("N1", ["P1"])])
    doc = routes_doc(board, [entry("P1", "N1", "F.Cu",
                                   [[2.0, 5.0], [18.0, 5.0]])])
    data = kicad_pcb_bytes(board, doc)
    root = parse_sexpr(data.decode("utf-8"))
    assert root[0] == "kicad_pcb"
    txt = data.decode("utf-8")
    pads = pad_lines(txt)
    assert any(l.startswith("(pad 1 thru_hole circle") for l in pads)
    assert any(l.startswith("(pad 1 smd rect") and '"B.Cu"' in l
               for l in pads)
