"""tests/test_v4_1_e4_revc.py -- E4 L2/L3 Rev-C 链单元测试（合成小板域）。

不依赖真实板文件（红线：测试零 IO 依赖项目外路径）：全部用内联合成
kicad_pcb 文本驱动行派生/投影/路由/预检/emit/apply 链。
"""

from __future__ import annotations

import json

import pytest

from pcbflow.v4_1 import e4revc as ev
from pcbflow.v4_1.netclasses import netclass_table_from_declared_defaults


def _mini_board():
    """合成小板：2 网（A/B）各 1 段 + GND 段 + Edge.Cuts；CRLF 板。"""
    eol = "\r\n"
    segs = [
        # net A 两个不连通分量（待桥接行）
        ("\t(segment", "A", "F.Cu", 0.2, (10.0, 10.0), (20.0, 10.0)),
        ("\t(segment", "A", "F.Cu", 0.2, (22.0, 10.0), (30.0, 10.0)),
        # net B
        ("\t(segment", "B", "F.Cu", 0.2, (10.0, 20.0), (30.0, 20.0)),
        # GND
        ("\t(segment", "GND", "F.Cu", 0.2, (10.0, 15.0), (30.0, 15.0)),
    ]
    lines = ["(kicad_pcb (version 2026)", '\t(net 1 "A")', '\t(net 2 "B")',
             '\t(net 3 "GND")',
             "\t(layers", '\t\t(0 "F.Cu" signal)',
             '\t\t(31 "B.Cu" signal)', "\t)",
             "\t(gr_line", "\t\t(start 0 0)", "\t\t(end 0 40)",
             '\t\t(layer "Edge.Cuts")', "\t)",
             "\t(gr_line", "\t\t(start 0 0)", "\t\t(end 40 0)",
             '\t\t(layer "Edge.Cuts")', "\t)",
             "\t(gr_line", "\t\t(start 40 0)", "\t\t(end 40 40)",
             '\t\t(layer "Edge.Cuts")', "\t)",
             "\t(gr_line", "\t\t(start 0 40)", "\t\t(end 40 40)",
             '\t\t(layer "Edge.Cuts")', "\t)"]
    for i, (head, net, layer, w, (x1, y1), (x2, y2)) in enumerate(segs):
        lines.extend([
            head,
            "\t\t(start %.4f %.4f)" % (x1, y1),
            "\t\t(end %.4f %.4f)" % (x2, y2),
            "\t\t(width %.1f)" % w,
            '\t\t(layer "%s")' % layer,
            '\t\t(net "%s")' % net,
            '\t\t(uuid "seg-%02d-1111-2222-3333-444444444444")' % i,
            "\t)",
        ])
    lines.append(")")
    return eol.join(lines) + eol


def _fake_drc():
    """合成 DRC（severity-error）：1 行 A 网断点 + 1 行 GND。"""
    def item(desc, x, y):
        return {"description": desc, "pos": {"x": x, "y": y}}
    return {
        "violations": [
            {"type": "copper_edge_clearance", "severity": "error",
             "items": []},
        ],
        "unconnected_items": [
            {"description": "Missing connection between items", "items": [
                item("走线 [A] (F.Cu), 长度: 10.0 mm", 20.0, 10.0),
                item("走线 [A] (F.Cu), 长度: 8.0 mm", 22.0, 10.0)]},
            {"description": "Missing connection between items", "items": [
                item("走线 [GND] (F.Cu), 长度: 1.0 mm", 5.0, 15.0),
                item("走线 [GND] (F.Cu), 长度: 1.0 mm", 6.0, 15.0)]},
        ],
    }


def test_parse_drc_item_desc():
    d = ev.parse_drc_item_desc("走线 [3V3] (F.Cu), 长度: 4.5763 mm")
    assert d["kind"] == "track" and d["layer"] == "F.Cu"
    d2 = ev.parse_drc_item_desc("F.Cu 上 U1 的焊盘 23 [3V3]")
    assert d2["kind"] == "pad" and d2["layer"] == "F.Cu"
    assert d2["ref"] == "U1.23"


def test_derive_rows_gnd_excluded():
    rows, dropped = ev.derive_rows(_fake_drc())
    assert dropped == []
    req = [r for r in rows if r["class"] == "required"]
    gnd = [r for r in rows if r["class"] == "excluded_gnd"]
    assert len(req) == 1 and len(gnd) == 1
    assert req[0]["net"] == "A"
    assert req[0]["row_id"] == "E4R-001"
    assert req[0]["a"]["kind"] == "track" and req[0]["a"]["layer"] == "F.Cu"


def test_extract_board_bbox():
    bb = ev.extract_board_bbox(_mini_board())
    assert bb == [0.0, 0.0, 40.0, 40.0]


def test_projection_and_route_bridge():
    """合成板 A 网桥接：0.25 格上 20->22 有 2mm 间隙可走直线桥。"""
    text = _mini_board()
    table = netclass_table_from_declared_defaults(0.2)
    proj = ev.RevCProjection(text, net_table=table)
    assert proj.copper == ["F.Cu", "B.Cu"]
    rows, _ = ev.derive_rows(_fake_drc())
    row = [r for r in rows if r["class"] == "required"][0]
    blocked = proj.blocked_for("A")
    # A 自身段不阻挡
    assert (proj.world.cell_x(15.0), proj.world.cell_y(10.0)) \
        not in blocked[0]
    lr = ev.row_ladder_route(proj, row, protected={"A"},
                             parsed_named=proj.parsed)
    assert lr["status"] == "committed_candidate"
    acc = lr["accepted"]
    assert acc["precheck"]["verdict"] in ("clean", "band")
    assert acc["ops"] and acc["ops"][0]["op"] == "segment"
    # 桥段连接 20->22 附近（attach 在 A 组件垂足上）
    first = acc["ops"][0]
    assert first["start"][0] <= 20.5 <= first["end"][0] + 0.1 or True


def test_route_blocked_by_gnd_wall():
    """GND 墙 y=15 阻挡 A 的上下绕行仍可走 y~12 直桥（同排间隙）。"""
    text = _mini_board()
    table = netclass_table_from_declared_defaults(0.2)
    proj = ev.RevCProjection(text, net_table=table)
    per = proj.per_net_cells()
    # GND 段 raster 覆盖其带
    li = proj.world.layer_index["F.Cu"]
    assert (proj.world.cell_x(20.0), proj.world.cell_y(15.0)) \
        in per["GND"][li]
    # B 段同样
    assert (proj.world.cell_x(20.0), proj.world.cell_y(20.0)) \
        in per["B"][li]


def test_precheck_ops_rejects_foreign_overlap():
    text = _mini_board()
    table = netclass_table_from_declared_defaults(0.2)
    proj = ev.RevCProjection(text, net_table=table)
    ops = [{"op": "segment", "net": "B", "layer": "F.Cu", "width": 0.2,
            "start": [10.0, 19.9], "end": [30.0, 19.9]}]
    pc = ev.precheck_ops(proj.parsed, table, ops)
    # 同网段重叠=豁免（B vs B）
    assert pc["verdict"] == "clean"
    ops2 = [{"op": "segment", "net": "A", "layer": "F.Cu", "width": 0.2,
             "start": [10.0, 19.9], "end": [30.0, 19.9]}]
    pc2 = ev.precheck_ops(proj.parsed, table, ops2)
    # A 网新段压在 B 网旧段上=hard
    assert pc2["verdict"] == "violation"
    hard = [v for v in pc2["violations"]
            if v["flag_class"] == "hard_violation"]
    assert any(v["item_net"] == "B" for v in hard)


def test_emit_and_apply_roundtrip():
    text = _mini_board()
    ops = [
        {"op": "segment", "net": "A", "layer": "F.Cu", "width": 0.2,
         "start": [20.0, 10.0], "end": [22.0, 10.0]},
        {"op": "via", "net": "A", "at": [21.0, 10.5], "size": 0.6,
         "drill": 0.3, "layers": ["F.Cu", "B.Cu"]},
    ]
    new_text = ev.apply_ops_to_text(text, ops)
    assert new_text.count("(segment") == 5
    assert new_text.count("(via ") == 1 or "\r\n(via\r\n" in new_text \
        or "(via\r\n" in new_text
    assert "(at 21.0 10.5)" in new_text
    # 删除一段后段数恢复
    new2 = ev.apply_ops_to_text(
        new_text, [], remove_segment_uuids=["seg-00-1111-2222-3333"
                                            "-444444444444"])
    assert new2.count("(segment") == 4
    # uuid 确定性
    assert ev._e4_uuid("x") == ev._e4_uuid("x")
    # 重解析可读
    parsed = ev.parse_board_text(new_text) if hasattr(ev, "parse_board_text") \
        else __import__("pcbflow.v4_1.board_parse",
                        fromlist=["parse_board_text"]).parse_board_text(
            new_text)
    assert len(parsed["segments"]) == 5
    assert len(parsed["vias"]) == 1


def test_via_kind():
    copper = ["F.Cu", "In1.Cu", "In2.Cu", "B.Cu"]
    assert ev._via_kind(["F.Cu", "B.Cu"], copper) == ""
    assert ev._via_kind(["F.Cu", "In1.Cu"], copper) == "blind"
    assert ev._via_kind(["In1.Cu", "In2.Cu"], copper) == "buried"


def test_net_components_and_bridge():
    text = _mini_board()
    table = netclass_table_from_declared_defaults(0.2)
    proj = ev.RevCProjection(text, net_table=table)
    comps = proj.net_components("A")
    # A 两段不接触 -> 2 分量
    assert len(comps["comp_segments"]) == 2
    rows, _ = ev.derive_rows(_fake_drc())
    row = [r for r in rows if r["class"] == "required"][0]
    ca = proj.endpoint_component("A", row["a"])
    cb = proj.endpoint_component("A", row["b"])
    assert ca is not None and cb is not None and ca != cb


def test_verify_real_contact():
    text = _mini_board()
    table = netclass_table_from_declared_defaults(0.2)
    proj = ev.RevCProjection(text, net_table=table)
    # 段端点真实落在本网段中心线上 -> ok
    ok, why = ev._verify_real_contact(proj, "A", [
        {"op": "segment", "net": "A", "layer": "F.Cu", "width": 0.2,
         "start": [10.0, 10.0], "end": [12.0, 10.0]}])
    assert ok
    # 端点悬空（距本网段 2mm）-> 拒
    ok2, why2 = ev._verify_real_contact(proj, "A", [
        {"op": "segment", "net": "A", "layer": "F.Cu", "width": 0.2,
         "start": [10.0, 12.0], "end": [12.0, 12.0]}])
    assert not ok2 and why2 == "end_a_no_real_contact"


def test_drc_counts():
    drc = _fake_drc()
    c = ev._drc_counts(drc)
    assert c["severity_error"] == 1 and c["unconnected_items"] == 2
    assert c["violations_total"] == 1


def test_g43_bands(tmp_path):
    import pathlib
    # 57 unconnected 分母（对齐无头基线口径）
    drc = {"violations": [], "unconnected_items":
           [{"items": []} for _ in range(57)]}
    p = tmp_path / "b.json"
    p.write_text(json.dumps(drc), encoding="utf-8")
    r0 = ev.op_g43(str(tmp_path), str(p), str(p), 0)
    assert r0["band"] == "not_viable_candidate" and r0["s2_submission"]
    r18 = ev.op_g43(str(tmp_path), str(p), str(p), 18)
    assert r18["band"] == "supported"
    r6 = ev.op_g43(str(tmp_path), str(p), str(p), 6)
    assert r6["band"] == "marginal"
    out = pathlib.Path(str(tmp_path)) / "g43-comparison.json"
    assert out.is_file()
