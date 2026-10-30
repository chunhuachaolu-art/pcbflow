# -*- coding: utf-8 -*-
"""v5.view P4 三视图（L7 布线图 / 爆炸分解 / L6 候选对比，§3.7）单元测试。

纪律（沿 tests/test_view.py 口径）：
- 基板一律用真实 demo 板 boards/d/demo-01-v2-corridor.board.v1.json（只读）；
- routes / candidates 为手工构造夹具（v5.routes.v1 与 planner 候选合同形状；
  ⑤执行器未交付，不 import executor）；
- 确定性：每视图同输入双跑字节等断言；手拼 SVG 可被 stdlib XML 解析器整段解析；
- 非法输入 fail-closed：断言 ValueError 且报文含键路径；
- 不写盘（落盘测试 monkeypatch sidecar.ALLOWED_ROOTS → tmp_path）。
"""
import json
import os
import xml.etree.ElementTree as ET

import pytest

from v5 import sidecar, view


# ---------------------------------------------------------------- 夹具

def _demo_board():
    """真实 demo 板（只读）；不在场则 skip（与 test_view.py 冒烟口径一致）。"""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(root, "boards", "d", "demo-01-v2-corridor.board.v1.json")
    if not os.path.isfile(path):
        pytest.skip("demo-01 板不在场")
    with open(path, encoding="utf-8") as f:
        return json.load(f)          # 只读，不回写


def _routes_doc(board, routes=None):
    """手工 v5.routes.v1 夹具：跨层网（F.Cu→In1.Cu，transition via 成对）+ 单层
    B.Cu 网带 return via。坐标落在 demo 工作区 [0,50]×[0,40] 内。"""
    if routes is None:
        routes = [
            {"partition_id": "P2", "net_id": "CLK-200M", "layer": "F.Cu",
             "polyline": [[5.0, 10.0], [30.0, 10.0], [45.0, 10.0]],
             "width": 0.15, "transition_vias": [[45.0, 10.0]], "return_vias": []},
            {"partition_id": "P2", "net_id": "CLK-200M", "layer": "In1.Cu",
             "polyline": [[45.0, 10.0], [45.0, 30.0]],
             "width": 0.15, "transition_vias": [[45.0, 10.0]],
             "return_vias": [[45.0, 20.0]]},
            {"partition_id": "P6", "net_id": "MISC2", "layer": "B.Cu",
             "polyline": [[46.0, 32.0], [46.0, 38.0]],
             "width": 0.2, "transition_vias": [], "return_vias": [[46.0, 35.0]]},
        ]
    sha = board["provenance"]["board_sha256"]
    return {"schema_version": "v5.routes.v1",
            "board_id": board["board_id"], "board_sha256": sha,
            "routes": routes, "negotiation_log": [],
            "provenance": {"generator": "v5.executor/0.1.0", "board_sha256": sha}}


_ORDER = ["P2", "P3", "P4", "P1", "P5", "P6", "P7", "P8", "P9"]


def _candidates(board, count=3):
    """手工候选夹具（planner 消费合同形状；polylines=板级分区端点直线）。"""
    ends = {p["partition_id"]: [list(pt) for pt in p["geometry"]["endpoints"]]
            for p in board["partitions"]}

    def mk(cid, arm, assign):
        return {"candidate_id": cid, "arm": arm,
                "provenance": {"generator": "v5.planner/0.1.0",
                               "rules_consumed": [],
                               "compiled_sha256": "a" * 64},
                "route_order": list(_ORDER),
                "layer_assignment": dict(assign),
                "polylines": {pid: [list(pt) for pt in ends[pid]] for pid in _ORDER},
                "generation_trace": []}

    base = {pid: "F.Cu" for pid in _ORDER}
    arms = [
        ("C-001", "principle", dict(base, P3="In1.Cu", P4="B.Cu")),
        ("C-002", "no-principle", dict(base, P6="B.Cu")),
        ("C-003", "shadow-b", dict(base, P4="In1.Cu", P5="In1.Cu")),
    ]
    return [mk(cid, arm, assign) for cid, arm, assign in arms[:count]]


# ---------------------------------------------------------------- 解析小工具

def _blocks(svg, marker, closer="</g>"):
    """按组开标记切片（marker 后到第一个 closer）——只适用于无嵌套组的标记。"""
    return [chunk.split(closer)[0] for chunk in svg.split(marker)[1:]]


def _segments(svg, marker, stop=None):
    """按 marker 切段：第 i 段 = marker i 之后到 marker i+1（或 stop/文档尾）。
    适用于含嵌套组的容器（如爆炸面板组）。"""
    parts = svg.split(marker)[1:]
    out = []
    for part in parts:
        for stopper in [s for s in (stop,) if s] + ["</svg>"]:
            idx = part.find(stopper)
            part = part[:idx] if idx != -1 else part
        out.append(part)
    return out


def _attr(text, name):
    return text.split('%s="' % name)[1].split('"')[0]


# ---------------------------------------------------------------- L7：确定性

def test_l7_wellformed_and_double_run():
    board = _demo_board()
    doc = _routes_doc(board)
    a = view.render_l7_view(board, doc, "all")
    b = view.render_l7_view(board, doc, "all")
    assert a == b and a.encode("utf-8") == b.encode("utf-8")   # 双跑字节等
    root = ET.fromstring(a)                                    # 手拼串不破良构性
    assert root.tag.endswith("svg")
    assert root.get("id") == "v5-l7-view" and root.get("data-v5") == "l7-routes"
    assert root.get("data-board-sha256") == board["provenance"]["board_sha256"]


def test_l7_route_line_style_and_width():
    """按层着色 + 线宽=width（视图投影原样，不钳制）+ 透明 0.75 + 按层线型。"""
    board = _demo_board()
    svg = view.render_l7_view(board, _routes_doc(board), "all")
    route_blocks = _blocks(svg, '<g class="v5-route"')
    assert len(route_blocks) == 3
    by_layer = {_attr(blk, "data-layer"): blk for blk in route_blocks}
    f = by_layer["F.Cu"]
    assert 'stroke="%s"' % view.LAYER_BASE_COLORS["F"] in f      # F.Cu 红
    assert 'stroke-width="1.545"' in f                           # 0.15mm × 投影 10.3
    assert 'stroke-opacity="0.75"' in f                          # §3.7 走线透明
    assert "stroke-dasharray" not in f                           # F.Cu=实线
    b = by_layer["B.Cu"]
    assert 'stroke="%s"' % view.LAYER_BASE_COLORS["B"] in b      # B.Cu 蓝
    assert 'stroke-width="2.060"' in b                           # 0.2mm × 10.3
    assert 'stroke-dasharray="2,4"' in b                         # 栈序 3 → 点线
    # 折线投影：ox=142.5、scale=10.3（工作区 50×40mm → 地图区 708×412px）
    assert 'points="194.000,149.000 451.500,149.000 606.000,149.000"' in f


def test_l7_via_double_ring_symbols():
    """transition=实心双环（内芯层色实心）/ return=空心双环（内环白底）；
    同一过孔在两条路线条目各画一组（合同逐条目携带过孔，视图照画）。"""
    board = _demo_board()
    svg = view.render_l7_view(board, _routes_doc(board), "all")
    vias = _blocks(svg, '<g class="v5-via"')
    assert len(vias) == 4                        # 2 transition + 2 return
    kinds = [_attr(blk, "data-via-kind") for blk in vias]
    assert kinds.count("transition") == 2 and kinds.count("return") == 2
    for blk in vias:                             # 双环：每组恰两圆，外环白底
        circles = [ln for ln in blk.split("\n") if ln.startswith("<circle")]
        assert len(circles) == 2
        assert 'r="%s"' % view.VIA_R_OUT in circles[0]
        assert 'fill="#ffffff"' in circles[0]
    trans = [blk for blk in vias if 'data-via-kind="transition"' in blk]
    # 实心芯=所属路线层色（绘制序自底向上：按 data-layer 匹配）
    trans_by_layer = {_attr(blk, "data-layer"): blk for blk in trans}
    assert 'fill="%s"' % view.LAYER_BASE_COLORS["F"] in trans_by_layer["F.Cu"]
    assert 'fill="%s"' % view.LAYER_BASE_COLORS["In1"] in trans_by_layer["In1.Cu"]
    assert all('r="%s"' % view.VIA_R_IN in blk for blk in trans)
    ret = [blk for blk in vias if 'data-via-kind="return"' in blk]
    for blk in ret:                              # 空心：内环白底只描边
        inner = [ln for ln in blk.split("\n") if 'r="%s"' % view.VIA_R_IN in ln][0]
        assert 'fill="#ffffff"' in inner


def test_l7_via_legend():
    board = _demo_board()
    svg = view.render_l7_view(board, _routes_doc(board), "all")
    assert '<g id="via-legend" data-kind="via-legend">' in svg
    assert "transition 换层（实心双环）" in svg
    assert "return 回流（空心双环）" in svg


def test_l7_base_map_l1_conventions():
    """禁布/敏感/走廊照 L1 口径（斜线禁布/橙敏感/蓝走廊+capacity 文本）+ 板级分区底图。"""
    board = _demo_board()
    svg = view.render_l7_view(board, _routes_doc(board), "all")
    assert 'url(#v5-hatch-keepout)' in svg            # K1/K2 红斜线
    assert view.ZONE_STYLES["sensitive"]["stroke"] in svg   # ANA 橙
    assert view.ZONE_STYLES["corridor"]["stroke"] in svg    # C1 蓝
    assert "capacity=4.300" in svg                    # 引擎值写死（C1=4.3）
    assert 'id="workspace-frame"' in svg
    assert 'id="v5-part-P1"' in svg                   # 板级分区底图在场
    assert 'data-partition-id="P9"' in svg


def test_l7_single_layer_mode_filters_routes():
    board = _demo_board()
    doc = _routes_doc(board)
    svg = view.render_l7_view(board, doc, "In1.Cu")
    assert 'data-mode="In1.Cu"' in svg
    routes = _blocks(svg, '<g class="v5-route"')
    assert len(routes) == 1                           # 只有 In1.Cu 条目在场
    assert 'data-layer="In1.Cu"' in routes[0]
    assert all('data-layer="B.Cu"' not in blk for blk in routes)
    assert 'data-net-id="MISC2"' not in routes[0]
    assert 'id="v5-part-P1"' not in svg               # 底图分区 policy=F.Cu → 滤除
    with pytest.raises(ValueError):                   # 非法 mode fail-closed
        view.render_l7_view(board, doc, "In9")
    for bad in ("", "ALL"):
        with pytest.raises(ValueError):
            view.render_l7_view(board, doc, bad)


# ---------------------------------------------------------------- L7：合同 fail-closed

def test_l7_routes_doc_level_failclosed():
    board = _demo_board()
    doc = _routes_doc(board)
    cases = [
        dict(doc, schema_version="v4.routes.v0"),
        dict(doc, board_id="other-board"),
        dict(doc, board_sha256="f" * 64),
        dict(doc, routes=None),
        dict(doc, negotiation_log="not-a-list"),
        dict(doc, provenance={"generator": "", "board_sha256":
                              board["provenance"]["board_sha256"]}),
        dict(doc, provenance={"generator": "v5.executor/0.1.0",
                              "board_sha256": "f" * 64}),
        dict(doc, routes=[dict(doc["routes"][0], partition_id="NOPE")]),
        dict(doc, routes=[dict(doc["routes"][0], net_id="NOPE")]),
        # 分区×净交叉对账：P1 不属于 CLK-200M
        dict(doc, routes=[dict(doc["routes"][0], partition_id="P1")]),
        dict(doc, routes=[dict(doc["routes"][0], layer="In2.Cu")]),   # 平面层
        dict(doc, routes=[dict(doc["routes"][0], layer="In9")]),      # 未定层
        dict(doc, routes=[dict(doc["routes"][0], polyline=[[1.0, 1.0]])]),
        dict(doc, routes=[dict(doc["routes"][0], width=0.0)]),
        dict(doc, routes=[dict(doc["routes"][0], width=-0.2)]),
        dict(doc, routes=[dict(doc["routes"][0], transition_vias=[[1.0]])]),
    ]
    for bad in cases:
        with pytest.raises(ValueError) as ei:
            view.render_l7_view(board, bad, "all")
        assert "routes" in str(ei.value)              # 报文带键路径
    with pytest.raises(ValueError):                   # routes 整体非 dict
        view.render_l7_view(board, [doc["routes"][0]], "all")
    with pytest.raises(ValueError):
        view.render_exploded_view(board, dict(doc, schema_version="x"))


def test_l7_routes_entry_keypath_in_message():
    board = _demo_board()
    base_routes = _routes_doc(board)["routes"]
    mutated = dict(base_routes[2], transition_vias=[[None, 1.0]])
    doc = _routes_doc(board, [base_routes[0], base_routes[1], mutated])
    with pytest.raises(ValueError) as ei:
        view.render_l7_view(board, doc, "all")
    assert "routes[2].transition_vias[0]" in str(ei.value)


# ---------------------------------------------------------------- 爆炸分解

def test_exploded_wellformed_double_run_and_panels():
    board = _demo_board()
    doc = _routes_doc(board)
    a = view.render_exploded_view(board, doc)
    b = view.render_exploded_view(board, doc)
    assert a == b and a.encode("utf-8") == b.encode("utf-8")   # 双跑字节等
    root = ET.fromstring(a)
    assert root.tag.endswith("svg")
    assert root.get("id") == "v5-exploded-view" and root.get("data-v5") == "l7-exploded"
    panels = _blocks(a, '<g class="v5-expanel"')
    assert len(panels) == 3                           # 3 信号层（F/In1/B），平面层无面板
    assert [ _attr(p, "data-layer") for p in panels ] == ["F.Cu", "In1.Cu", "B.Cu"]
    assert "In2.Cu" not in a                          # 平面层 In2.Cu 不出面板
    titles = [ln for ln in a.split("\n")
              if 'class="v5-expanel-title"' in ln]
    assert [t.split(">")[1].split("<")[0] for t in titles] == ["F.Cu", "In1.Cu", "B.Cu"]


def test_exploded_cross_panel_connector_shared_x():
    """transition via 跨面板连线：同 x（x1==x2 逐位相同=共享 x 轴）、跨面板 y、
    每对只画一条、连线色=所属层色；return via 不产生连线。"""
    board = _demo_board()
    svg = view.render_exploded_view(board, _routes_doc(board))
    links = [ln for ln in svg.split("\n") if 'class="v5-exvia-link"' in ln]
    assert len(links) == 1                            # 1 个换层过孔对（去重后）
    ln = links[0]
    assert _attr(ln, "x1") == _attr(ln, "x2")         # 同 x 位置
    assert _attr(ln, "y1") != _attr(ln, "y2")         # 跨面板
    assert 'stroke="%s"' % view.LAYER_BASE_COLORS["F"] in ln   # F.Cu 条目色
    assert 'data-net-id="CLK-200M"' in ln
    dots = [l for l in svg.split("\n")
            if l.startswith("<circle") and 'r="2"' in l]
    assert len(dots) == 2                             # 连线两端点标记
    # return via（2 个）只在面板内画空心环，无跨面板连线（count==1 已证）


def test_exploded_orphan_transition_via_failclosed():
    board = _demo_board()
    # 孤儿点取线中顶点 [30,10]（非分区端点）：端点上的过渡孔按焊盘逃逸孔合法
    # （view 决定 4b），fail-closed 只管既无 entry 配对又不在端点上的真孤儿。
    lone = dict(_routes_doc(board)["routes"][0],
                transition_vias=[[30.0, 10.0]], return_vias=[])
    doc = _routes_doc(board, [lone])                  # transition via 无异层配对
    with pytest.raises(ValueError) as ei:
        view.render_exploded_view(board, doc)
    msg = str(ei.value)
    assert "routes[0].transition_vias" in msg and "孤儿" in msg


def test_exploded_pad_escape_via_links_to_pad_panel():
    """焊盘逃逸孔（决定 4b；demo-02 PW1 实证形态）：单条异层 entry、过渡孔=本分区
    端点（焊盘在垫层面）、无 entry 配对 → 不判孤儿，跨面板连线画向垫层面板。"""
    board = _demo_board()
    esc = {"partition_id": "P6", "net_id": "MISC2", "layer": "B.Cu",
           "polyline": [[46.0, 32.0], [46.0, 38.0]],
           "width": 0.2, "transition_vias": [[46.0, 32.0]], "return_vias": []}
    svg = view.render_exploded_view(board, _routes_doc(board, [esc]))
    links = [ln for ln in svg.split("\n") if 'class="v5-exvia-link"' in ln]
    assert len(links) == 1                            # 画向垫层面板（F.Cu）
    assert _attr(links[0], "x1") == _attr(links[0], "x2")
    assert _attr(links[0], "y1") != _attr(links[0], "y2")


def test_exploded_via_pairs_same_partition_cross_net():
    """同分区异网配对（决定 4 放宽；demo-02 DF1 共端点实证形态）：DIFF 双网共用
    端点，B.Cu 网的过渡孔配到同分区 F.Cu 网折线的共享端点顶点，不判孤儿。"""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(root, "boards", "d", "demo-02-mixed-types.board.v1.json")
    if not os.path.isfile(path):
        pytest.skip("demo-02 板不在场")
    with open(path, encoding="utf-8") as f:
        board = json.load(f)
    # 共端点双网分区 = 同一 partition_id 出现在 ≥2 个 net 的 partitions 里
    # （v5.board.v1 网表侧持有映射，分区侧无网表键）。
    part_nets = {}
    for net in board.get("nets", []) or []:
        for pid in net.get("partitions") or []:
            part_nets.setdefault(str(pid), []).append(str(net.get("net_id", "")))
    duo_pid = next((pid for pid, ns in sorted(part_nets.items())
                    if len(ns) >= 2), None)
    if duo_pid is None:
        pytest.skip("demo-02 无共端点双网分区")
    duo = next(p for p in board["partitions"] if p["partition_id"] == duo_pid)
    eps = [list(pt) for pt in duo["geometry"]["endpoints"]]
    net_a, net_b = part_nets[duo_pid][0], part_nets[duo_pid][1]
    a = {"partition_id": duo_pid, "net_id": net_a, "layer": "F.Cu",
         "polyline": [eps[0], eps[1]], "width": 0.2,
         "transition_vias": [], "return_vias": []}
    b = {"partition_id": duo_pid, "net_id": net_b, "layer": "B.Cu",
         "polyline": [eps[0], eps[1]], "width": 0.2,
         "transition_vias": [eps[0]], "return_vias": []}
    svg = view.render_exploded_view(board, _routes_doc(board, [a, b]))
    links = [ln for ln in svg.split("\n") if 'class="v5-exvia-link"' in ln]
    assert len(links) == 1
    assert 'data-net-id="%s"' % net_b in links[0]


def test_exploded_panel_content_zones_and_routes():
    """每面板画本层可见 zones（zone.layers 口径）+ 本层 routes + 工作区边界；
    同一 zone 在各面板各自投影（y 不同、x 相同=共享 x 轴）。"""
    board = _demo_board()
    svg = view.render_exploded_view(board, _routes_doc(board))
    panels = _segments(svg, '<g class="v5-expanel"',
                       stop='<line class="v5-exvia-link"')
    assert len(panels) == 3
    for panel in panels:                              # K1 layers=all / ANA signal →
        assert 'data-zone-id="K1"' in panel           #   信号层面板全可见
        assert 'data-zone-id="ANA"' in panel
        assert 'id="workspace-frame-p' in panel
        assert 'class="v5-route"' in panel            # 每面板至少一条本层 route
    # 共享 x 轴：K1 包围盒 x 逐面板相同，y 逐面板不同（各面板独立 y 投影）
    def _zone_rect(panel, zid):
        blk = panel.split('data-zone-id="%s"' % zid)[1].split("</g>")[0]
        return [ln for ln in blk.split("\n") if ln.startswith("<rect")][0]

    k1_x = {_attr(_zone_rect(p, "K1"), "x") for p in panels}
    assert len(k1_x) == 1
    k1_y = [_attr(_zone_rect(p, "K1"), "y") for p in panels]
    assert len(set(k1_y)) == 3
    b_panel = panels[2]
    assert 'data-net-id="MISC2"' in b_panel           # B.Cu route 在 B 面板
    assert 'data-net-id="CLK-200M"' not in b_panel    # 跨层网条目只在各自面板


# ---------------------------------------------------------------- L6 候选对比

def test_l6_wellformed_double_run_and_panel_geometry():
    board = _demo_board()
    cands = _candidates(board)
    a = view.render_l6_view(board, cands)
    b = view.render_l6_view(board, cands)
    assert a == b and a.encode("utf-8") == b.encode("utf-8")   # 双跑字节等
    root = ET.fromstring(a)
    assert root.tag.endswith("svg")
    assert root.get("id") == "v5-l6-view" and root.get("data-v5") == "l6-candidates"
    assert root.get("data-candidate-count") == "3"
    panels = _blocks(a, '<g class="v5-l6-panel"')
    assert len(panels) == 3
    # 并排小面板：等宽 (708-2×10)/3=229.333，x=46 / 285.333 / 524.667
    assert '<rect x="46.000" y="46.000" width="229.333" height="452.000"' in a
    assert '<rect x="285.333" y="46.000" width="229.333" height="452.000"' in a
    assert '<rect x="524.667" y="46.000" width="229.333" height="452.000"' in a


def test_l6_panel_titles_and_order_labels():
    board = _demo_board()
    svg = view.render_l6_view(board, _candidates(board))
    assert "C-001（principle）" in svg                # candidate_id/arm 标题
    assert "C-002（no-principle）" in svg
    assert "C-003（shadow-b）" in svg                 # arm 原样展示不枚举判定
    assert 'data-candidate-id="C-002" data-arm="no-principle"' in svg
    routes = [blk for blk in _blocks(svg, '<g class="v5-l6-route"')
              if 'data-candidate-id="C-001"' in blk]
    assert len(routes) == 9                           # 恰为 route_order 全部分区
    orders = {int(_attr(blk, "data-order")): _attr(blk, "data-partition-id")
              for blk in routes}
    assert orders[1] == "P2" and orders[9] == "P9"    # 序号=route_order 位次
    assert ">1.P2<" in svg and ">2.P3<" in svg and ">9.P9<" in svg  # 序号标注文本


def test_l6_layer_coloring():
    """层着色/线型按 layer_assignment：F 红-实线 / In1 绿-长虚 / B 蓝-点线。"""
    board = _demo_board()
    svg = view.render_l6_view(board, _candidates(board))
    c1 = [blk for blk in _blocks(svg, '<g class="v5-l6-route"')
          if 'data-candidate-id="C-001"' in blk]
    by_pid = {_attr(blk, "data-partition-id"): blk for blk in c1}
    f = by_pid["P2"]
    assert 'stroke="#cc0000"' in f and "stroke-dasharray" not in f
    in1 = by_pid["P3"]
    assert 'stroke="#008000"' in in1 and 'stroke-dasharray="14,5"' in in1
    b = by_pid["P4"]
    assert 'stroke="#0000cc"' in b and 'stroke-dasharray="2,4"' in b
    c3 = [blk for blk in _blocks(svg, '<g class="v5-l6-route"')
          if 'data-candidate-id="C-003"' in blk]
    p5 = [blk for blk in c3 if 'data-partition-id="P5"' in blk][0]
    assert 'stroke="#008000"' in p5                   # 候选间层指派差异可见


def test_l6_failclosed():
    board = _demo_board()
    good = _candidates(board)
    def bad_list(cand_mutations):
        return [dict(c, **m) for c, m in cand_mutations]
    with pytest.raises(ValueError):                   # 空列表
        view.render_l6_view(board, [])
    with pytest.raises(ValueError):                   # 非 list
        view.render_l6_view(board, good[0])
    with pytest.raises(ValueError) as ei:             # candidate_id 空
        view.render_l6_view(board, [dict(good[0], candidate_id="")])
    assert "candidates[0].candidate_id" in str(ei.value)
    with pytest.raises(ValueError):
        view.render_l6_view(board, [dict(good[0], arm="")])
    with pytest.raises(ValueError):
        view.render_l6_view(board, [dict(good[0], route_order=[])])
    with pytest.raises(ValueError) as ei:             # 分区未命中板
        view.render_l6_view(board, [dict(good[0], route_order=["P2", "NOPE"],
                                          layer_assignment={"P2": "F.Cu", "NOPE": "F.Cu"},
                                          polylines=dict(good[0]["polylines"],
                                                         NOPE=[[0, 0], [1, 1]]))])
    assert "NOPE" in str(ei.value)
    with pytest.raises(ValueError) as ei:             # 层=平面层
        c = dict(good[0], layer_assignment=dict(good[0]["layer_assignment"], P2="In2.Cu"))
        view.render_l6_view(board, [c])
    assert "layer_assignment[P2]" in str(ei.value)
    with pytest.raises(ValueError) as ei:             # polylines 键不恰为 route_order
        polys = dict(good[0]["polylines"])
        del polys["P9"]
        view.render_l6_view(board, [dict(good[0], polylines=polys)])
    assert "polylines" in str(ei.value)
    with pytest.raises(ValueError) as ei:             # 折线不足 2 点
        polys = dict(good[0]["polylines"], P2=[[5.0, 10.0]])
        view.render_l6_view(board, [dict(good[0], polylines=polys)])
    assert "polylines[P2]" in str(ei.value)
    with pytest.raises(ValueError):                   # route_order 含重复
        view.render_l6_view(board, [dict(good[0], route_order=["P1", "P1"])])
    assert not bad_list([])                           # （helper 自检：不改变输入）


# ---------------------------------------------------------------- 落盘与 demo 冒烟

def test_write_view_new_kinds(tmp_path, monkeypatch):
    """新 kind 令牌（l7-all / l7-exploded / l6-candidates）走既有 write_view：
    sidecar 命名 + provenance 头 + 混合树过 check_tree。"""
    monkeypatch.setattr(sidecar, "ALLOWED_ROOTS", (str(tmp_path),))
    board = _demo_board()
    sha = board["provenance"]["board_sha256"]
    out_dir = str(tmp_path / "out")
    payloads = [
        ("l7-all", view.render_l7_view(board, _routes_doc(board), "all")),
        ("l7-exploded", view.render_exploded_view(board, _routes_doc(board))),
        ("l6-candidates", view.render_l6_view(board, _candidates(board))),
    ]
    paths = [view.write_view(payload, kind, board["board_id"], sha, out_dir)
             for kind, payload in payloads]
    assert [os.path.basename(p) for p in paths] == [
        "demo-01-v2-corridor.l7-all.svg",
        "demo-01-v2-corridor.l7-exploded.svg",
        "demo-01-v2-corridor.l6-candidates.svg"]
    for path, (kind, payload) in zip(paths, payloads):
        with open(path, encoding="utf-8") as f:
            text = f.read()
        first_line = text.split("\n", 1)[0]
        assert first_line.startswith("<!--") and first_line.endswith("-->")
        assert "generator=v5.view" in first_line
        assert "generator_version=%s" % view.VERSION in first_line
        assert "board_sha256=%s" % sha in first_line
        assert "kind=%s" % kind in first_line
        assert payload in text
    assert sidecar.check_tree(str(tmp_path)) == []


def test_demo01_smoke_all_views_element_counts():
    """demo-01 实渲染自检（只读）：三视图全渲染 + SVG 元素计数断言。"""
    board = _demo_board()
    doc = _routes_doc(board)
    l7 = view.render_l7_view(board, doc, "all")
    expl = view.render_exploded_view(board, doc)
    l6 = view.render_l6_view(board, _candidates(board))
    for svg in (l7, expl, l6):
        assert ET.fromstring(svg).tag.endswith("svg")   # 全部良构
    assert l7.count('class="v5-route"') == 3
    assert l7.count('class="v5-via"') == 4
    assert l7.count('class="v5-part"') == 9             # 板级分区底图 9 分区
    assert expl.count('class="v5-expanel"') == 3
    assert expl.count('class="v5-exvia-link"') == 1
    assert l6.count('class="v5-l6-panel"') == 3
    assert l6.count('class="v5-l6-route"') == 27        # 3 候选 × 9 分区
    assert l6.count('class="v5-l6-order"') == 27
