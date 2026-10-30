"""V4-EXEC-P10 render_png view-spec 扩展 + P09 viewer 桥接测试。

被测生产模块：pcbflow/svg_route_package.py（render_png 向后兼容扩展）与
pcbflow/v4_review_dispatch.py（追加式 viewer 桥接；既有签名/行为零改动）。

覆盖（派发词 §4）：

- **向后兼容钉死**：view_spec=None（默认）时 render_png 输出字节与返回
  键集与扩展前完全一致（golden hash 于 2026-09-11 扩展实施前对同夹具
  捕获，扩展后复验一致后写入；任何默认路径行为漂移即红）；
- view-spec → PNG：确定性（双跑逐字节）、过滤有效性（≠默认投影）、
  分辨率以 spec.resolution_px 为准、返回附 view_spec_sha256；
- fail-closed：非法 spec（未知层/焦点/schema）经 render_png 入口同样
  ValueError；
- P09 桥接：review_viewer_files 产出 baseline/diff 双 viewer HTML（多
  state 对照由真实 build_review_package 生成）；build_review_bundle 的
  viewer_files_by_case 可选参数——不传时输出与历史逐字节一致（对照
  legacy 四键 case 形态）、传入时仅追加 viewer_files 键且校验通过；
  键集不完整 fail-closed。

夹具为代码内合成最小字典，不依赖外部文件、不访问网络。
"""

import copy
import hashlib
import json

import pytest

from pcbflow import hashing
from pcbflow import svg_route_package as srp
from pcbflow import v4_review_dispatch as vrd
from pcbflow import v4_route_viewer as vrv

from test_v4exec_p10_route_viewer import make_board, make_geom

# 扩展实施前（2026-09-11）对同夹具捕获的 golden（见模块 docstring）
GOLDEN_DEFAULT_1600x900 = ("6d22059f28f5e4b05b8cf4734cfc95fb"
                           "b421e63a01dcddcffe7f03e18ad3fd49")
GOLDEN_DEFAULT_1200x675 = ("42b36941ea2dfcf8436fb36cabecacd56"
                            "b74616ce56bdaeb6f9caf767a1559dc")
GOLDEN_FOCUSED_BCU_1200x675 = ("fb8da979d3947f285a052843aefd71bd"
                               "6137821c3b5e6d2c69583749f521c7bc")


@pytest.fixture(scope="module")
def built():
    board = make_board()
    geom = vrd.enrich_geometry(board, make_geom(),
                               state="baseline", source="baseline")
    svg_text, man = srp.build(board, geom)
    return {"board": board, "svg": svg_text, "manifest": man}


# ----------------------------------------------------- 向后兼容（钉死）

def test_render_png_default_path_golden_bytes(built):
    """无 view-spec = 现行为字节不变：golden 逐字节比对 + 键集不变。"""
    r = srp.render_png(built["board"], built["manifest"])
    assert r["available"] is True
    assert sorted(r) == ["available", "height", "png_bytes", "width"]
    assert hashlib.sha256(r["png_bytes"]).hexdigest() == \
        GOLDEN_DEFAULT_1600x900
    r2 = srp.render_png(built["board"], built["manifest"],
                        width=1200, height=675)
    assert hashlib.sha256(r2["png_bytes"]).hexdigest() == \
        GOLDEN_DEFAULT_1200x675


def test_render_png_default_still_deterministic(built):
    a = srp.render_png(built["board"], built["manifest"])
    b = srp.render_png(built["board"], built["manifest"])
    assert a["png_bytes"] == b["png_bytes"]


# ----------------------------------------------------- view-spec → PNG

def test_render_png_viewspec_deterministic_and_filtered(built):
    spec = {"schema": vrv.VIEW_SPEC_SCHEMA, "layers": ["B.Cu"],
            "resolution_px": [1200, 675]}
    r1 = srp.render_png(built["board"], built["manifest"], view_spec=spec)
    r2 = srp.render_png(built["board"], built["manifest"], view_spec=spec)
    assert r1["available"] is True
    assert r1["png_bytes"] == r2["png_bytes"]           # 确定性
    assert (r1["width"], r1["height"]) == (1200, 675)   # spec 分辨率优先
    assert "view_spec_sha256" in r1
    assert r1["view_spec_sha256"] == vrv.view_spec_sha256(
        vrv.normalize_view_spec(spec, built["manifest"], built["board"]))
    # 过滤真实生效：单层投影 ≠ 全量投影（同分辨率）
    full = srp.render_png(built["board"], built["manifest"],
                          width=1200, height=675)
    assert r1["png_bytes"] != full["png_bytes"]
    assert hashlib.sha256(r1["png_bytes"]).hexdigest() == \
        GOLDEN_FOCUSED_BCU_1200x675
    # 默认路径键集不被污染（向后兼容：无 spec 无新键）
    assert "view_spec_sha256" not in full


@pytest.mark.parametrize("spec,expect_focus", [
    ({"schema": vrv.VIEW_SPEC_SCHEMA,
      "focus": {"kind": "net", "id": "n1"}}, "net"),
    ({"schema": vrv.VIEW_SPEC_SCHEMA,
      "focus": {"kind": "route", "id": "n1-S01"}}, "route"),
    ({"schema": vrv.VIEW_SPEC_SCHEMA,
      "focus": {"kind": "relation", "id": "CLK-1"}}, "relation"),
    ({"schema": vrv.VIEW_SPEC_SCHEMA,
      "focus": {"kind": "parent", "id": "BUS-1"}}, "parent"),
])
def test_render_png_viewspec_focus_kinds(built, spec, expect_focus):
    r = srp.render_png(built["board"], built["manifest"], view_spec=spec)
    assert r["available"] is True
    again = srp.render_png(built["board"], built["manifest"],
                           view_spec=spec)
    assert r["png_bytes"] == again["png_bytes"]
    full = srp.render_png(built["board"], built["manifest"],
                          width=r["width"], height=r["height"])
    assert r["png_bytes"] != full["png_bytes"]


def test_render_png_viewspec_toggles(built):
    """show_pads/show_keepouts/states/line_types 过滤改变投影字节。"""
    base = {"schema": vrv.VIEW_SPEC_SCHEMA, "resolution_px": [1200, 675]}
    r_all = srp.render_png(built["board"], built["manifest"],
                           view_spec=dict(base))
    r_nopads = srp.render_png(
        built["board"], built["manifest"],
        view_spec=dict(base, show_pads=False))
    r_noko = srp.render_png(
        built["board"], built["manifest"],
        view_spec=dict(base, show_keepouts=False))
    r_clock = srp.render_png(
        built["board"], built["manifest"],
        view_spec=dict(base, line_types=["clock"]))
    r_prop = srp.render_png(
        built["board"], built["manifest"],
        view_spec=dict(base, states=["proposed"]))
    for r in (r_nopads, r_noko, r_clock):
        assert r["png_bytes"] != r_all["png_bytes"]
        assert r["available"] is True
    # states=["proposed"]：本夹具无该态对象 → 投影只剩板框（仍有 PNG）
    assert r_prop["available"] is True


@pytest.mark.parametrize("bad", [
    {"schema": "nope/1"},
    {"schema": vrv.VIEW_SPEC_SCHEMA, "layers": ["X.Cu"]},
    {"schema": vrv.VIEW_SPEC_SCHEMA, "focus": {"kind": "net", "id": "nX"}},
    {"schema": vrv.VIEW_SPEC_SCHEMA,
     "bindings": {"board_snapshot_sha256": "0" * 64,
                  "route_manifest_payload_sha256": "0" * 64}},
])
def test_render_png_viewspec_fail_closed(built, bad):
    with pytest.raises(ValueError):
        srp.render_png(built["board"], built["manifest"], view_spec=bad)


# ----------------------------------------------------- P09 桥接

@pytest.fixture(scope="module")
def review_pkg(built):
    """真实 build_review_package：candidate 改 n1 一条走线 → diff 视图
    多 state 对照（baseline + candidate 并存）。"""
    board = built["board"]
    base_ref = vrd.enrich_geometry(board, {
        "routes": [dict(r) for r in built["manifest"]["routes"]],
        "vias": [dict(v) for v in built["manifest"]["vias"]]},
        state="baseline", source="baseline")
    svg_text, man = srp.build(board, base_ref)
    baseline_pkg = {"svg_text": svg_text, "manifest": man}
    cand_routes = [dict(r) for r in built["manifest"]["routes"]]
    for r in cand_routes:
        if r["route_id"] == "n1-S01":
            r["polyline_mm"] = [[5.0, 5.0], [35.0, 5.0]]
    cand = {"routes": cand_routes,
            "vias": [dict(v) for v in built["manifest"]["vias"]]}
    pkg = vrd.build_review_package(board, baseline_pkg, cand,
                                   case_id="RC-P10-T01")
    states = {r["state"] for r in pkg["diff_view"]["manifest"]["routes"]}
    assert states == {"baseline", "candidate"}   # 多 state 对照前提
    return {"board": board, "pkg": pkg}


def test_review_viewer_files_deterministic(review_pkg):
    out1 = vrd.review_viewer_files(review_pkg["board"], review_pkg["pkg"])
    out2 = vrd.review_viewer_files(review_pkg["board"], review_pkg["pkg"])
    assert sorted(out1) == ["baseline_view", "diff_view"]
    for view, rec in out1.items():
        assert rec["html_text"] == out2[view]["html_text"]  # 双跑一致
        assert rec["html_sha256"] == hashing.sha256_bytes(
            rec["html_text"].encode("utf-8"))
        # diff viewer 确实是多 state 对照视图
        states = {r["state"] for r
                  in review_pkg["pkg"][view]["manifest"]["routes"]}
        for s in states:
            assert f'data-filter="state" value="{s}"' in rec["html_text"]


def test_review_viewer_files_fail_closed_on_pkg_shape(review_pkg):
    pkg = copy.deepcopy(review_pkg["pkg"])
    del pkg["diff_view"]["svg_text"]
    with pytest.raises(ValueError, match="diff_view"):
        vrd.review_viewer_files(review_pkg["board"], pkg)


def _bundle_case(pkg):
    return [{"case_id": pkg["case_id"],
             "review_package_sha256": pkg["review_package_sha256"],
             "three_bind": pkg["three_bind"],
             "files": {role: {"file_rel": f"x/{role}", "sha256": "a" * 64}
                       for role in ("diff_svg", "diff_png", "baseline_png",
                                    "summary")}}]


def test_bundle_default_path_unchanged(review_pkg):
    """不传 viewer_files_by_case：case 形态=legacy 四键，输出逐字节可复
    现（与既有行为零差异）。"""
    b1 = vrd.build_review_bundle(run_id="r5", cases=_bundle_case(
        review_pkg["pkg"]), approval_sha256="b" * 64)
    b2 = vrd.build_review_bundle(run_id="r5", cases=_bundle_case(
        review_pkg["pkg"]), approval_sha256="b" * 64)
    assert json.dumps(b1, sort_keys=True) == json.dumps(b2, sort_keys=True)
    for c in b1["cases"]:
        assert sorted(c) == ["case_id", "files",
                             "review_package_sha256", "three_bind"]
        assert "viewer_files" not in c
    vrd.validate_review_bundle(b1)


def test_bundle_with_viewer_files(review_pkg):
    vf = vrd.review_viewer_files(review_pkg["board"], review_pkg["pkg"])
    by_case = {review_pkg["pkg"]["case_id"]: {
        "baseline_viewer_html": {
            "file_rel": "v/baseline.html",
            "sha256": vf["baseline_view"]["html_sha256"]},
        "diff_viewer_html": {
            "file_rel": "v/diff.html",
            "sha256": vf["diff_view"]["html_sha256"]}}}
    b0 = vrd.build_review_bundle(run_id="r5", cases=_bundle_case(
        review_pkg["pkg"]), approval_sha256="b" * 64)
    b1 = vrd.build_review_bundle(run_id="r5", cases=_bundle_case(
        review_pkg["pkg"]), approval_sha256="b" * 64,
        viewer_files_by_case=by_case)
    for c in b1["cases"]:
        assert sorted(c) == ["case_id", "files",
                             "review_package_sha256", "three_bind",
                             "viewer_files"]
        assert c["viewer_files"]["diff_viewer_html"]["sha256"] == \
            vf["diff_view"]["html_sha256"]
    # 其余字段零改动：剥掉 viewer_files 后与不传时逐字段一致
    stripped = copy.deepcopy(b1)
    for c in stripped["cases"]:
        c.pop("viewer_files")
    assert json.dumps(stripped, sort_keys=True) == \
        json.dumps(b0, sort_keys=True)
    # 新产物新文件：bundle canonical hash 变化；校验仍通过
    assert vrd.review_bundle_sha256(b0) != vrd.review_bundle_sha256(b1)
    vrd.validate_review_bundle(b1)


def test_bundle_viewer_files_fail_closed(review_pkg):
    with pytest.raises(ValueError, match="viewer_files 键集不符"):
        vrd.build_review_bundle(
            run_id="r5", cases=_bundle_case(review_pkg["pkg"]),
            approval_sha256="b" * 64,
            viewer_files_by_case={review_pkg["pkg"]["case_id"]: {
                "diff_viewer_html": {"file_rel": "a", "sha256": "c" * 64}}})
    with pytest.raises(ValueError, match="viewer_files.diff_viewer_html"):
        vrd.build_review_bundle(
            run_id="r5", cases=_bundle_case(review_pkg["pkg"]),
            approval_sha256="b" * 64,
            viewer_files_by_case={review_pkg["pkg"]["case_id"]: {
                "baseline_viewer_html": {"file_rel": "a",
                                         "sha256": "c" * 64},
                "diff_viewer_html": {"file_rel": "a",
                                     "sha256": "not-hex"}}})
