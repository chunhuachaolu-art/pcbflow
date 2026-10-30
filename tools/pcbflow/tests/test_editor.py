"""FB2 E 简版骨架编辑器测试。

覆盖（SPEC v1.3 §15 A2 顺延位 + HANDOFF §2 FB2 门）：
- html 双跑 byte-exact（确定性）与离线纯净（无外部资源/网络调用）；
- bundle 与 ③ layout 同源一致（锚件标记/总线/端点/常量=config）；
- 提案校验器全负例：锚件禁动/身份不增删/side·zone·端点不可变/量化/旋转步进/
  拐点间距与角度/板内包含/changes 对账/base 六 hash 过期/畸形输入；
- 编辑器契约：零写板（board_write=false）、核心产物禁区扫描、CLI exit-code 契约。
"""

import json
import math

import pytest

from pcbflow import cli, config, coplace_cmd, editor_cmd, envelope

OUT_REL = "out/revc-b2"


@pytest.fixture(scope="module")
def products():
    return editor_cmd.build_products(OUT_REL)


@pytest.fixture(scope="module")
def bundle(products):
    return products["bundle"]["obj"]


@pytest.fixture(scope="module")
def html_text(products):
    return products["html"]["bytes"].decode(config.ENCODING)


# ---- 确定性与离线纯净 -----------------------------------------------------------
def test_html_double_run_byte_exact():
    a = editor_cmd.build_products(OUT_REL)["html"]["bytes"]
    b = editor_cmd.build_products(OUT_REL)["html"]["bytes"]
    assert a == b


def test_html_offline_purity(html_text):
    """自包含离线：仅允许的 URL=SVG 命名空间（svg 元素+createElementNS 各一次）；
    无脚本外链/网络调用。"""
    assert html_text.count("http://") == 2
    assert html_text.count("http://www.w3.org/2000/svg") == 2
    for bad in ("https://", "fetch(", "XMLHttpRequest", "<script src",
                "<link", "WebSocket", "EventSource", "import("):
        assert bad not in html_text, bad
    assert '<script type="application/json" id="pcbflow-bundle">' in html_text


def test_bundle_no_forbidden_core_fields(bundle):
    assert envelope.scan_forbidden_core_fields(bundle) == []


def test_bundle_no_board_write(products):
    env = products["envelope"]["obj"]
    assert env["data"]["board_write"] is False
    assert env["data"]["command_status"] == "implemented"
    assert env["command"] == "editor" and env["command_kind"] == "core"
    assert env["schema_version"] == "1.3"


# ---- bundle 与 ③ layout 同源 ----------------------------------------------------
def test_bundle_matches_layout(bundle):
    cop = coplace_cmd.build_products(OUT_REL)
    layout = cop["layout"]["obj"]
    assert len(bundle["placements"]) == 72
    assert sum(1 for p in bundle["placements"] if p["anchor"]) == 10
    assert len(bundle["skeletons"]) == 7
    lp = {p["ref"]: p for p in layout["placements"]}
    for row in bundle["placements"]:
        src = lp[row["ref"]]
        assert (row["x"], row["y"], row["rot"]) == (src["x"], src["y"], src["rot"])
        assert row["anchor"] == (src["role"] == "anchor_locked")
        assert row["side"] == src["side"] and row["zone"] == src["zone"]
    for s, ls in zip(bundle["skeletons"], layout["skeletons"]):
        assert s["bus_id"] == ls["bus_id"]
        for seg, lseg in zip(s["segments"], ls["segments"]):
            assert seg["polyline"] == lseg["polyline"]
            assert seg["from_ref"] == lseg["from_ref"]
    assert bundle["base"]["layout_sha256"] == cop["layout"]["sha256"]
    assert bundle["constants"]["quant_mm"] == config.CPLACE_QUANT
    assert bundle["constants"]["min_bend_spacing_mm"] == config.CPLACE_MIN_BEND_SPACING_MM
    assert bundle["constants"]["rot_step_deg"] == config.CPLACE_ROT_STEP


# ---- 提案构造辅助（与浏览器 buildProposal 同式） --------------------------------
def make_proposal(bundle, pl_edits=None, vtx_edits=None, base=None):
    """从 bundle 合成提案；pl_edits: {ref: (x,y,rot)}；vtx_edits:
    {(bus,seg,vi): (x,y)}；base 可覆写（负例：过期绑定）。"""
    pl_edits = pl_edits or {}
    vtx_edits = vtx_edits or {}
    pc, vc = [], []
    placements = []
    for p in sorted(bundle["placements"], key=lambda r: r["ref"]):
        x, y, rot = pl_edits.get(p["ref"], (p["x"], p["y"], p["rot"]))
        if (x, y, rot) != (p["x"], p["y"], p["rot"]):
            pc.append({"ref": p["ref"], "from": [p["x"], p["y"], p["rot"]],
                       "to": [round(x, 3), round(y, 3), rot]})
        placements.append({"ref": p["ref"], "x": round(x, 3), "y": round(y, 3),
                           "rot": rot, "side": p["side"], "zone": p["zone"]})
    skeletons = []
    for s in bundle["skeletons"]:
        segs = []
        for gi, seg in enumerate(s["segments"]):
            pts = [list(pt) for pt in seg["polyline"]]
            for (bus, seg_i, vi), (nx, ny) in vtx_edits.items():
                if bus == s["bus_id"] and seg_i == gi:
                    if (round(nx, 3), round(ny, 3)) != (pts[vi][0], pts[vi][1]):
                        vc.append({"bus_id": bus, "segment_index": gi,
                                   "vertex_index": vi,
                                   "from": [pts[vi][0], pts[vi][1]],
                                   "to": [round(nx, 3), round(ny, 3)]})
                    pts[vi] = [round(nx, 3), round(ny, 3)]
            segs.append({"from_ref": seg["from_ref"], "to_ref": seg["to_ref"],
                         "polyline": pts})
        skeletons.append({"bus_id": s["bus_id"], "segments": segs})
    vc.sort(key=lambda r: (r["bus_id"], r["segment_index"], r["vertex_index"]))
    return {
        "schema_version": "1.3", "artifact_kind": "editor_proposal",
        "tool": "pcbflow-editor", "tool_version": config.TOOL_VERSION,
        "mode": "manual_skeleton_edit", "project": bundle["project"],
        "base": base if base is not None else dict(bundle["base"]),
        "placements": placements, "skeletons": skeletons,
        "changes": {"placement_changes": pc, "vertex_changes": vc},
        "notes": bundle["notes"],
    }


@pytest.fixture(scope="module")
def movable_ref(bundle):
    """一个非锚件 ref（移动后远离板缘，正例用）。"""
    edge = bundle["board"]["edge_rect_mm"]
    cands = [p for p in bundle["placements"] if not p["anchor"]
             and edge[0] + 2 < p["x"] < edge[2] - 2
             and edge[1] + 2 < p["y"] < edge[3] - 2]
    assert cands, "无非锚件且离板缘 ≥2mm 的 ref"
    return cands[0]["ref"]


def _pick_bend_target(bundle, kind):
    """选一个拐点编辑目标（返回 (bus, seg_i, vi, 新坐标)）。
    对角拐点（L 形另一角）量化到 0.05 网格，两腿均 ≥1.5mm（间距守卫余量）。"""
    for s in bundle["skeletons"]:
        for gi, seg in enumerate(s["segments"]):
            (x0, y0), (x1, y1), (x2, y2) = seg["polyline"][0], \
                seg["polyline"][1], seg["polyline"][2]
            raw = ((x2, y0) if (x1, y1) == (x0, y2) else (x0, y2))
            other = (round(round(raw[0] / 0.05) * 0.05, 3),
                     round(round(raw[1] / 0.05) * 0.05, 3))
            legs = (math.hypot(other[0] - x0, other[1] - y0),
                    math.hypot(other[0] - x2, other[1] - y2))
            if min(legs) >= 1.5 and other != (round(x1, 3), round(y1, 3)):
                return s["bus_id"], gi, 1, other
    raise AssertionError("无可用的拐点编辑目标")


def _write(tmp_path, obj, name="p.json"):
    path = tmp_path / name
    if isinstance(obj, str):
        path.write_text(obj, encoding="utf-8")
    else:
        path.write_text(json.dumps(obj, ensure_ascii=False, indent=1),
                        encoding="utf-8")
    return str(path)


def _validate(tmp_path, proposal):
    env, report = editor_cmd.validate_proposal(_write(tmp_path, proposal),
                                               out_dir_rel=OUT_REL)
    return env, report


# ---- 正例 ------------------------------------------------------------------------
def test_validate_identity_proposal(tmp_path, bundle):
    env, report = _validate(tmp_path, make_proposal(bundle))
    assert env["status"] == "ok" and env["verdict"] == "pass"
    assert report["summary"]["all_pass"] is True
    assert report["summary"]["placement_change_count"] == 0
    assert report["summary"]["vertex_change_count"] == 0


def test_validate_moved_part_and_bend(tmp_path, bundle, movable_ref):
    p = next(x for x in bundle["placements"] if x["ref"] == movable_ref)
    bus, gi, vi, new_bend = _pick_bend_target(bundle, "valid")
    prop = make_proposal(
        bundle,
        pl_edits={movable_ref: (p["x"] - 0.5, p["y"] - 0.5, p["rot"])},
        vtx_edits={(bus, gi, vi): new_bend})
    env, report = _validate(tmp_path, prop)
    assert env["status"] == "ok" and env["verdict"] == "pass", \
        json.dumps(report["summary"], ensure_ascii=False)
    assert report["summary"]["placement_change_count"] == 1
    assert report["summary"]["vertex_change_count"] == 1


def test_validate_rotation(tmp_path, bundle, movable_ref):
    p = next(x for x in bundle["placements"] if x["ref"] == movable_ref)
    env, report = _validate(tmp_path, make_proposal(
        bundle, pl_edits={movable_ref: (p["x"], p["y"],
                                        (p["rot"] + 90) % 360)}))
    assert env["status"] == "ok"
    assert report["summary"]["placement_change_count"] == 1


# ---- 负例（逐守卫） ---------------------------------------------------------------
def _expect_blocked(env, report, cid):
    assert env["status"] == "blocked" and env["verdict"] == "red", (
        json.dumps(report["summary"], ensure_ascii=False))
    assert cid in report["summary"]["failed"], cid


def test_validate_anchor_move_blocked(tmp_path, bundle):
    anchor = next(p for p in bundle["placements"] if p["anchor"])
    env, report = _validate(tmp_path, make_proposal(
        bundle, pl_edits={anchor["ref"]: (anchor["x"] + 0.5, anchor["y"],
                                          anchor["rot"])}))
    _expect_blocked(env, report, "anchor_lock")


def test_validate_off_grid_blocked(tmp_path, bundle, movable_ref):
    p = next(x for x in bundle["placements"] if x["ref"] == movable_ref)
    env, report = _validate(tmp_path, make_proposal(
        bundle, pl_edits={movable_ref: (p["x"] + 0.07, p["y"], p["rot"])}))
    _expect_blocked(env, report, "pose_quant")


def test_validate_rot45_blocked(tmp_path, bundle, movable_ref):
    p = next(x for x in bundle["placements"] if x["ref"] == movable_ref)
    env, report = _validate(tmp_path, make_proposal(
        bundle, pl_edits={movable_ref: (p["x"], p["y"], 45)}))
    _expect_blocked(env, report, "pose_quant")


def test_validate_side_change_blocked(tmp_path, bundle, movable_ref):
    prop = make_proposal(bundle)
    for row in prop["placements"]:
        if row["ref"] == movable_ref:
            row["side"] = "B" if row["side"] == "F" else "F"
    env, report = _validate(tmp_path, prop)
    _expect_blocked(env, report, "immutables_side_zone")


def test_validate_ref_dropped_blocked(tmp_path, bundle):
    prop = make_proposal(bundle)
    prop["placements"] = prop["placements"][1:]
    env, report = _validate(tmp_path, prop)
    _expect_blocked(env, report, "identity_refs")


def test_validate_bus_dropped_blocked(tmp_path, bundle):
    prop = make_proposal(bundle)
    prop["skeletons"] = prop["skeletons"][:-1]
    env, report = _validate(tmp_path, prop)
    _expect_blocked(env, report, "identity_refs")


def test_validate_endpoint_move_blocked(tmp_path, bundle):
    s = bundle["skeletons"][0]
    e = s["segments"][0]["polyline"][0]
    env, report = _validate(tmp_path, make_proposal(
        bundle, vtx_edits={(s["bus_id"], 0, 0): (e[0] + 0.5, e[1])}))
    _expect_blocked(env, report, "skeleton_endpoints")


def test_validate_bend_spacing_blocked(tmp_path, bundle):
    """拐点移到距端点 0.5mm（沿原段方向，角度不犯规）→ 间距 <1.0 违例。"""
    for s in bundle["skeletons"]:
        for gi, seg in enumerate(s["segments"]):
            (x0, y0), (x1, y1) = seg["polyline"][0], seg["polyline"][1]
            dx, dy = x1 - x0, y1 - y0
            n = max(abs(dx), abs(dy))
            if n == 0:
                continue
            near = (x0 + dx / n * 0.5, y0 + dy / n * 0.5)
            near = (round(round(near[0] / 0.05) * 0.05, 3),
                    round(round(near[1] / 0.05) * 0.05, 3))
            if (near[0], near[1]) != (x0, y0):
                env, report = _validate(tmp_path, make_proposal(
                    bundle, vtx_edits={(s["bus_id"], gi, 1): near}))
                _expect_blocked(env, report, "vertex_rules")
                return
    raise AssertionError("未构造出间距违例")


def test_validate_bend_angle_soft_not_blocking(tmp_path, bundle):
    """拐点移到 (端点+2.0, 端点+0.05)：邻段角 ≈1.43° 非 45° 步进——③ 运行时
    守卫=仅间距（_bend_candidates 轴对齐微移同产生非整 45° 段），故不阻断，
    只进 soft_angle_report（advisory_only）。"""
    s = bundle["skeletons"][0]
    seg = s["segments"][0]
    (x0, y0) = seg["polyline"][0]
    snap = lambda v: round(round(v / 0.05) * 0.05, 3)
    bend = (snap(x0 + 2.0), snap(y0 + 0.05))
    env, report = _validate(tmp_path, make_proposal(
        bundle, vtx_edits={(s["bus_id"], 0, 1): bend}))
    assert env["status"] == "ok" and env["verdict"] == "pass", \
        json.dumps(report["summary"], ensure_ascii=False)
    assert report["soft_angle_report"]["authority"] == "advisory_only"
    assert report["soft_angle_report"]["rows"], "非 45° 邻段应被软记录"


def test_validate_off_board_blocked(tmp_path, bundle, movable_ref):
    p = next(x for x in bundle["placements"] if x["ref"] == movable_ref)
    x1 = bundle["board"]["edge_rect_mm"][2]
    env, report = _validate(tmp_path, make_proposal(
        bundle, pl_edits={movable_ref: (x1 + 50.0, p["y"], p["rot"])}))
    _expect_blocked(env, report, "board_containment")


def test_validate_stale_base_blocked(tmp_path, bundle):
    bad_base = dict(bundle["base"])
    bad_base["layout_sha256"] = "0" * 64
    env, report = _validate(tmp_path, make_proposal(bundle, base=bad_base))
    _expect_blocked(env, report, "base_binding")


def test_validate_changes_log_mismatch_blocked(tmp_path, bundle, movable_ref):
    p = next(x for x in bundle["placements"] if x["ref"] == movable_ref)
    prop = make_proposal(bundle, pl_edits={movable_ref: (p["x"] - 0.5, p["y"],
                                                         p["rot"])})
    prop["changes"] = {"placement_changes": [], "vertex_changes": []}
    env, report = _validate(tmp_path, prop)
    _expect_blocked(env, report, "changes_log")


def test_validate_malformed_failed(tmp_path):
    env, report = editor_cmd.validate_proposal(
        _write(tmp_path, "{ not json"), out_dir_rel=OUT_REL)
    assert env["status"] == "failed" and env["verdict"] == "fail"
    assert report is None


# ---- 旋转几何（k×90° 与 ③ _rot90 同式） ------------------------------------------
def test_pose_box_rotation_swap():
    row = {"pad": {"ox_mm": 0.4, "oy_mm": -0.2, "hw_mm": 3.0, "hh_mm": 1.6},
           "body": {"ox_mm": 0.0, "oy_mm": 0.0, "hw_mm": 3.25, "hh_mm": 1.85},
           "base_rot": 90}
    k0 = editor_cmd._pose_box_mm(row, 10.0, 20.0, 90)
    assert k0["pad"] == (10.0 + 0.4 - 3.0, 20.0 - 0.2 - 1.6,
                         10.0 + 0.4 + 3.0, 20.0 - 0.2 + 1.6)
    k1 = editor_cmd._pose_box_mm(row, 10.0, 20.0, 180)  # Δ90：(ox,oy)→(oy,−ox)，宽高互换
    assert k1["pad"][:2] == (10.0 - 0.2 - 1.6, 20.0 - 0.4 - 3.0)
    assert k1["pad"][2:] == (10.0 - 0.2 + 1.6, 20.0 - 0.4 + 3.0)


# ---- CLI exit-code 契约 ----------------------------------------------------------
def test_cli_editor_summary_and_validate(capsys, tmp_path, bundle, movable_ref):
    rc = cli.main(["editor", "--select", "summary"])
    out = capsys.readouterr().out
    assert rc == 0
    assert '"command": "editor"' in out and '"status": "ok"' in out
    assert "E_editor_usability" in out

    good = _write(tmp_path, make_proposal(bundle))
    rc = cli.main(["editor", "--select", "validate", "--proposal", good])
    capsys.readouterr()
    assert rc == 0

    p = next(x for x in bundle["placements"] if x["ref"] == movable_ref)
    bad = _write(tmp_path, make_proposal(
        bundle, pl_edits={movable_ref: (p["x"] + 0.07, p["y"], p["rot"])}))
    rc = cli.main(["editor", "--select", "validate", "--proposal", bad])
    capsys.readouterr()
    assert rc == 2  # blocked


def test_cli_editor_validate_requires_proposal(capsys):
    rc = cli.main(["editor", "--select", "validate"])
    capsys.readouterr()
    assert rc == 1  # failed


def test_cli_editor_html_exit(capsys):
    rc = cli.main(["editor", "--select", "html"])
    out = capsys.readouterr()
    assert rc == 0
    assert out.out.startswith("<!DOCTYPE html>")
