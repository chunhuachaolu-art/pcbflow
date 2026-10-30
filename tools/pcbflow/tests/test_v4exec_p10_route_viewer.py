"""V4-EXEC-P10 route-viewer 交互视图测试（T0–T3；纯代码，零模型 token）。

被测生产模块：pcbflow/v4_route_viewer.py（新模块；表现层皮肤，零
authority）。

覆盖（派发词 §4）：

- 纯函数确定性：同输入双跑字节一致（canonical：无 wall-clock/随机源）；
- 自包含断言：产物内零 http/https 外部引用（唯一例外=内联 SVG 根的
  xmlns 命名空间标识符，非网络资源）、零外部 src/href 资源、零网络 API；
- hash 链：HTML 根 data-board-snapshot-sha256 /
  data-route-manifest-payload-sha256 与输入 manifest 绑定；board/manifest/
  SVG 三方不一致 fail-closed（ValueError，不出视图）；
- T0/T1 逐对象可寻址：manifest 每个 route/via、board 每个 pad 在内联
  SVG 中唯一 data-*-id 寻址；过滤词表（layer/line_type/state）与 manifest
  对象集一致；
- T2 计数侧栏与 DOM↔manifest 一致性断言素材在产物内；
- T3 view-spec：normalize_view_spec canonical 化 + fail-closed（未知
  层/类型/状态/焦点、bindings 错配一律拒绝）；view_spec_sha256 确定。

夹具为代码内合成最小字典（多 state 对照能力由 vrd.enrich_geometry 标注
链提供；本文件全部 baseline 态，多 state 对照在
test_v4exec_p10_render_png_viewspec.py 的 P09 桥接测试中覆盖）。
不依赖外部文件、不访问网络。
"""

import json
import re

import pytest

from pcbflow import svg_route_package as srp
from pcbflow import v4_route_viewer as vrv
from pcbflow import v4_review_dispatch as vrd

SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")


# ---------------------------------------------------------- 合成最小夹具

def make_board():
    return {
        "schema": "v4exp.board-snapshot/1",
        "scenario_id": "SC-P10-VW", "split": "calibration",
        "family": "f1", "seed": 7, "label": "SC-P10-VW",
        "board": {"bbox_mm": [0.0, 0.0, 40.0, 30.0],
                  "layers": ["F.Cu", "B.Cu"]},
        "rules": {"grid_mm": 0.25, "clearance_mm": 0.3,
                  "width_mm": {"default": 0.3, "clock": 0.4},
                  "via": {"pad_mm": 0.6, "hole_mm": 0.3},
                  "allowed_layers": {"default": ["F.Cu", "B.Cu"],
                                     "clock": ["F.Cu"]}},
        "nets": [
            {"net_id": "n1", "net_class": "default",
             "endpoints": ["U1-1", "U2-1"]},
            {"net_id": "n2", "net_class": "clock",
             "endpoints": ["U3-1", "U4-1"]},
            {"net_id": "n3", "net_class": "bus",
             "endpoints": ["J1-1", "J2-1"]},
            {"net_id": "n4", "net_class": "bus",
             "endpoints": ["J3-1", "J4-1"]}],
        "pads": [
            {"pad_id": "U1-1", "net_id": "n1", "x_mm": 5.0, "y_mm": 5.0,
             "w_mm": 1.2, "h_mm": 1.2, "layer": "F.Cu"},
            {"pad_id": "U2-1", "net_id": "n1", "x_mm": 35.0, "y_mm": 5.0,
             "w_mm": 1.2, "h_mm": 1.2, "layer": "F.Cu"},
            {"pad_id": "U3-1", "net_id": "n2", "x_mm": 5.0, "y_mm": 15.0,
             "w_mm": 1.2, "h_mm": 1.2, "layer": "F.Cu"},
            {"pad_id": "U4-1", "net_id": "n2", "x_mm": 35.0, "y_mm": 15.0,
             "w_mm": 1.2, "h_mm": 1.2, "layer": "F.Cu"}],
        "keepouts": [{"keepout_id": "K1",
                      "rect_mm": [18.0, 8.0, 24.0, 13.0],
                      "layers": ["F.Cu", "B.Cu"]}],
        "relations": [
            {"relation_id": "BUS-1", "relation_type": "bus",
             "members": ["n3", "n4"], "parent_id": None},
            {"relation_id": "CLK-1", "relation_type": "clock_group",
             "members": ["n2"], "parent_id": None}],
    }


def make_geom():
    return {
        "routes": [
            {"route_id": "n1-S01", "net_id": "n1", "relation_ids": [],
             "line_type": "signal", "parent_id": None, "layer": "F.Cu",
             "width_mm": 0.3,
             "polyline_mm": [[5.0, 5.0], [17.0, 5.0], [17.0, 7.0],
                             [35.0, 7.0], [35.0, 5.0]],
             "endpoint_ids": ["U1-1", "U2-1"],
             "constraint_refs": ["C-clearance-030", "C-width-030"]},
            {"route_id": "n2-S01", "net_id": "n2", "relation_ids": ["CLK-1"],
             "line_type": "clock", "parent_id": None, "layer": "F.Cu",
             "width_mm": 0.4,
             "polyline_mm": [[5.0, 15.0], [16.0, 15.0], [16.0, 17.0],
                             [35.0, 17.0], [35.0, 15.0]],
             "endpoint_ids": ["U3-1", "U4-1"],
             "constraint_refs": ["C-clearance-030", "C-width-040"]},
            {"route_id": "n3-S01", "net_id": "n3", "relation_ids": ["BUS-1"],
             "line_type": "bus_member", "parent_id": "BUS-1",
             "layer": "F.Cu", "width_mm": 0.3,
             "polyline_mm": [[3.0, 25.0], [20.0, 25.0]],
             "endpoint_ids": ["J1-1", "J2-1"],
             "constraint_refs": ["C-clearance-030", "C-width-030"]},
            {"route_id": "n3-S02", "net_id": "n3", "relation_ids": ["BUS-1"],
             "line_type": "bus_trunk", "parent_id": "BUS-1",
             "layer": "B.Cu", "width_mm": 0.3,
             "polyline_mm": [[20.0, 25.0], [20.0, 27.0], [37.0, 27.0]],
             "endpoint_ids": ["J2-1", "x"],
             "constraint_refs": ["C-clearance-030", "C-width-030"]},
            {"route_id": "n4-S01", "net_id": "n4", "relation_ids": ["BUS-1"],
             "line_type": "bus_member", "parent_id": "BUS-1",
             "layer": "F.Cu", "width_mm": 0.3,
             "polyline_mm": [[3.0, 28.0], [37.0, 28.0]],
             "endpoint_ids": ["J3-1", "J4-1"],
             "constraint_refs": ["C-clearance-030", "C-width-030"]}],
        "vias": [{"via_id": "V1", "net_id": "n3", "parent_id": "n3-S01",
                  "from_layer": "F.Cu", "to_layer": "B.Cu",
                  "center_mm": [20.0, 25.0], "drill_mm": 0.3,
                  "annular_ring_mm": 0.15}],
    }


@pytest.fixture(scope="module")
def built():
    board = make_board()
    geom = vrd.enrich_geometry(board, make_geom(),
                               state="baseline", source="baseline")
    svg_text, man = srp.build(board, geom)
    html = vrv.build_route_viewer(board, man, svg_text)
    return {"board": board, "svg": svg_text, "manifest": man, "html": html}


# ----------------------------------------------------- 确定性与自包含

def test_double_run_byte_identical(built):
    """同输入双跑字节一致（canonical：无 wall-clock/主机路径/随机）。"""
    again = vrv.build_route_viewer(built["board"], built["manifest"],
                                   built["svg"])
    assert again == built["html"]
    assert vrv.build_route_viewer(
        built["board"], built["manifest"], built["svg"]) == again


def test_self_contained_zero_external_refs(built):
    """自包含：零 http/https（唯一例外=SVG xmlns 命名空间标识符）、
    零外部资源引用、零网络 API——file:// 可开、离线可用。"""
    html = built["html"]
    urls = set(re.findall(r"https?://[^\s\"'<>]+", html))
    # xmlns 是 XML 命名空间标识符（非网络资源、不发起任何请求）
    assert urls <= {"http://www.w3.org/2000/svg"}
    for forbidden in ('<script src=', "<link ", "<img ", "url(http",
                      "fetch(", "XMLHttpRequest", "import(", "@import"):
        assert forbidden not in html, forbidden
    assert "<script type=\"application/json\" id=\"viewer-bundle\">" in html
    # 产物不含主机绝对路径（canonical；正斜杠/反斜杠盘符都挡）
    assert not re.search(r"[A-Za-z]:[/\\](Users|Windows|home)/", html)


# ----------------------------------------------------- hash 链绑定

def test_hash_chain_binding_on_html_root(built):
    html = built["html"]
    man = built["manifest"]
    bsha = re.search(r'data-board-snapshot-sha256="([0-9a-f]{64})"',
                     html).group(1)
    msha = re.search(r'data-route-manifest-payload-sha256="([0-9a-f]{64})"',
                     html).group(1)
    assert bsha == man["board_snapshot_sha256"]
    assert msha == man["manifest_payload_sha256"]
    assert f'data-pcbflow-viewer="{vrv.VIEWER_SCHEMA}"' in html


@pytest.mark.parametrize("tamper", ["board", "manifest", "svg"])
def test_fail_closed_on_hash_mismatch(built, tamper):
    """board/manifest/SVG 三方任一不符 → ValueError，不出视图。"""
    if tamper == "board":
        board = json.loads(json.dumps(built["board"]))
        board["pads"][0]["x_mm"] = 9.9
        with pytest.raises(ValueError, match="board_snapshot_sha256"):
            vrv.build_route_viewer(board, built["manifest"], built["svg"])
    elif tamper == "manifest":
        man = json.loads(json.dumps(built["manifest"]))
        man["routes"][0]["width_mm"] = 0.5
        with pytest.raises(ValueError, match="manifest_payload_sha256"):
            vrv.build_route_viewer(built["board"], man, built["svg"])
    else:
        svg = built["svg"].replace('data-route-manifest-sha256="',
                                   'data-route-manifest-sha256="0', 1)
        with pytest.raises(ValueError, match="data-route-manifest-sha256"):
            vrv.build_route_viewer(built["board"], built["manifest"], svg)


def test_fail_closed_on_missing_object(built):
    """manifest 对象在 SVG 不可寻址 → ValueError（过滤/高亮可达性前提）。"""
    man = json.loads(json.dumps(built["manifest"]))
    man["routes"][0]["route_id"] = "n1-S99"
    man["manifest_payload_sha256"] = vrv._payload_sha256(man)
    svg = built["svg"].replace(
        f'data-route-id="{man["routes"][0]["route_id"][:-3]}"',
        'data-route-id="zzz"', 1)  # svg 与 manifest 同步换名后重绑
    svg = re.sub(r'data-route-manifest-sha256="([0-9a-f]*)"',
                 f'data-route-manifest-sha256="{man["manifest_payload_sha256"]}"',
                 svg, count=1)
    with pytest.raises(ValueError, match="未在 SVG"):
        vrv.build_route_viewer(built["board"], man, svg)


# ----------------------------------------------------- T0/T1 可寻址性

def test_every_manifest_object_uniquely_addressable(built):
    """逐对象可寻址断言：manifest 每个 route/via、board 每个 pad 在产物
    内恰好出现一次 data-*-id（CSS 选择器唯一选中）。"""
    html = built["html"]
    for r in built["manifest"]["routes"]:
        assert html.count(f'data-route-id="{r["route_id"]}"') == 1
    for v in built["manifest"]["vias"]:
        assert html.count(f'data-via-id="{v["via_id"]}"') == 1
    for p in built["board"]["pads"]:
        assert html.count(f'data-pad-id="{p["pad_id"]}"') == 1


def test_filter_vocabularies_match_manifest(built):
    """T0 过滤词表与 manifest 对象集一致：每个出现的层/line_type/state
    都有对应复选框；计数与 manifest 重算一致。"""
    html = built["html"]
    man = built["manifest"]
    layers = {r["layer"] for r in man["routes"]}
    layers |= {v["from_layer"] for v in man["vias"]}
    layers |= {v["to_layer"] for v in man["vias"]}
    for layer in layers:
        assert f'data-filter="layer" value="{layer}"' in html
    for r in man["routes"]:
        assert f'data-filter="line-type" value="{r["line_type"]}"' in html
        assert f'data-filter="state" value="{r["state"]}"' in html
    # T1 组高亮词表：relation 与 parent
    for rel in built["board"]["relations"]:
        assert f'data-group-kind="relation" data-group-id="{rel["relation_id"]}"' \
            in html
    assert 'data-group-kind="parent" data-group-id="BUS-1"' in html


def test_embedded_bundle_consistency(built):
    """内嵌 viewer bundle：manifest 全量在包；侧栏计数与 manifest 重算
    一致（DOM↔manifest 一致性徽章的数据前提）。"""
    m = re.search(
        r'<script type="application/json" id="viewer-bundle">'
        r'(.*?)</script>', built["html"], re.S).group(1)
    bundle = json.loads(m)
    assert bundle["manifest"]["manifest_payload_sha256"] == \
        built["manifest"]["manifest_payload_sha256"]
    v = bundle["viewer"]
    man = built["manifest"]
    assert v["counts"]["routes"] == len(man["routes"])
    assert v["counts"]["vias"] == len(man["vias"])
    assert v["counts"]["pads"] == len(built["board"]["pads"])
    assert sum(v["routes_by_state"].values()) == len(man["routes"])
    assert sum(v["routes_by_line_type"].values()) == len(man["routes"])
    assert set(v["route_ids"]) == {r["route_id"] for r in man["routes"]}
    assert set(v["net_ids"]) == {r["net_id"] for r in man["routes"]}


def test_t0_t3_wiring_present(built):
    """T0–T3 功能件在产物内接线（复选框/tooltip/搜索/缩放/计数/导出）。"""
    html = built["html"]
    assert html.count('data-filter="layer"') >= 2      # T0 图层叠加
    assert 'data-filter="line-type"' in html           # T0 line_type
    assert 'data-filter="state"' in html               # T0 state 对照
    assert 'id="tooltip"' in html                      # T0 tooltip
    assert 'id="search"' in html and 'id="b-search"' in html  # T1 搜索
    assert 'data-group-kind=' in html                  # T1 组高亮
    assert 'function fitView()' in html and 'mmPerPx' in html  # T2 导航
    assert 'dom-badge' in html                         # T2 一致性徽章
    assert 'id="b-spec"' in html                       # T3 导出
    assert vrv.VIEW_SPEC_SCHEMA in html                # T3 规格 schema


# ----------------------------------------------------- T3 view-spec

def test_normalize_view_spec_canonical(built):
    man, board = built["manifest"], built["board"]
    spec = {"schema": vrv.VIEW_SPEC_SCHEMA,
            "layers": ["B.Cu", "B.Cu"],
            "line_types": ["bus_trunk"],
            "states": ["baseline", "candidate"],
            "focus": {"kind": "parent", "id": "BUS-1"},
            "resolution_px": [800, 450]}
    n = vrv.normalize_view_spec(spec, man, board)
    assert n["layers"] == ["B.Cu"]          # 去重排序
    assert n["states"] == ["baseline", "candidate"]
    assert n["focus"] == {"kind": "parent", "id": "BUS-1"}
    assert n["resolution_px"] == [800, 450]
    assert n["show_pads"] is True and n["show_keepouts"] is True
    assert n["bindings"]["board_snapshot_sha256"] == \
        man["board_snapshot_sha256"]
    # 空列表 = 不过滤（全集）；bindings 自动补全
    n2 = vrv.normalize_view_spec({"schema": vrv.VIEW_SPEC_SCHEMA},
                                 man, board)
    assert n2["layers"] == [] and n2["focus"] is None
    assert n2["resolution_px"] == list(vrv.DEFAULT_SPEC_RESOLUTION)
    # canonical ⇒ hash 确定
    assert vrv.view_spec_sha256(n) == vrv.view_spec_sha256(
        vrv.normalize_view_spec(json.loads(json.dumps(spec)), man, board))


@pytest.mark.parametrize("bad", [
    {"schema": "wrong/1"},
    {"schema": vrv.VIEW_SPEC_SCHEMA, "layers": ["X.Cu"]},
    {"schema": vrv.VIEW_SPEC_SCHEMA, "line_types": ["no_such"]},
    {"schema": vrv.VIEW_SPEC_SCHEMA, "states": ["dreaming"]},
    {"schema": vrv.VIEW_SPEC_SCHEMA, "focus": {"kind": "net", "id": "nX"}},
    {"schema": vrv.VIEW_SPEC_SCHEMA, "focus": {"kind": "route", "id": "x"}},
    {"schema": vrv.VIEW_SPEC_SCHEMA, "focus": {"kind": "relation",
                                               "id": "NOPE"}},
    {"schema": vrv.VIEW_SPEC_SCHEMA, "focus": {"kind": "parent",
                                               "id": "NOPE"}},
    {"schema": vrv.VIEW_SPEC_SCHEMA, "focus": {"kind": "pad", "id": "U1-1"}},
    {"schema": vrv.VIEW_SPEC_SCHEMA, "resolution_px": [0, 100]},
    {"schema": vrv.VIEW_SPEC_SCHEMA, "resolution_px": [100]},
    {"schema": vrv.VIEW_SPEC_SCHEMA, "show_pads": "yes"},
    {"schema": vrv.VIEW_SPEC_SCHEMA,
     "bindings": {"board_snapshot_sha256": "0" * 64,
                  "route_manifest_payload_sha256": "0" * 64}},
])
def test_normalize_view_spec_fail_closed(built, bad):
    with pytest.raises(ValueError):
        vrv.normalize_view_spec(bad, built["manifest"], built["board"])


def test_view_spec_focus_members(built):
    man, board = built["manifest"], built["board"]
    n = vrv.normalize_view_spec(
        {"schema": vrv.VIEW_SPEC_SCHEMA,
         "focus": {"kind": "relation", "id": "BUS-1"}}, man, board)
    assert vrv.view_spec_focus_members(n, man, board) == \
        {"net_ids": {"n3", "n4"}}
    n2 = vrv.normalize_view_spec(
        {"schema": vrv.VIEW_SPEC_SCHEMA,
         "focus": {"kind": "route", "id": "n1-S01"}}, man, board)
    assert vrv.view_spec_focus_members(n2, man, board) == \
        {"route_ids": {"n1-S01"}}
