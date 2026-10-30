# -*- coding: utf-8 -*-
"""v5.view（P1 视图骨架 + L1 分区图；P2 增 L2 包络图 / L3 叠加与 J 项图，§3.7）单元测试。

纪律：
- 一律内联小板 + 内联分区表（不依赖并行产出的 boards/d/demo-0*.board.v1.json）；
  board_sha256 用 v5.board.compute_board_sha256 现算回填 provenance；
- 写盘测试 monkeypatch sidecar.ALLOWED_ROOTS → tmp_path，不污染真实 out/；
- 只断言字符串/文件事实，不在前端/测试里重算任何引擎数值；
- 例外：test_demo01_real_artifacts_smoke / test_demo01_real_chain_l3_smoke 按任务令
  对 demo-01 做只读冒烟（真实板/工件作渲染输入或纯函数构建，文件缺失则 skip，
  不写回任何字节）。
"""
import json
import os
import xml.etree.ElementTree as ET

import pytest

from v5 import board as v5_board
from v5 import sidecar, view


# ---------------------------------------------------------------- 内联夹具

def _make_board():
    """内联小板（4 层栈：3 信号层 + 1 平面层），provenance 哈希现场复算回填。"""
    board = {
        "schema_version": "v5.board.v1",
        "board_id": "view-test-0",
        "stackup": [
            {"id": "F.Cu", "kind": "signal", "preferred_direction": "h", "available": True},
            {"id": "In1", "kind": "signal", "preferred_direction": "any", "available": True},
            {"id": "In2P", "kind": "plane", "preferred_direction": "any", "available": True},
            {"id": "B.Cu", "kind": "signal", "preferred_direction": "v", "available": True},
        ],
        "workspace": {"x_min": 0.0, "y_min": 0.0, "x_max": 60.0, "y_max": 40.0},
        "zones": [
            {"zone_id": "Z-KEEP", "kind": "keepout",
             "rect": {"x_min": 4.0, "y_min": 4.0, "x_max": 14.0, "y_max": 11.0},
             "layers": "all"},
            {"zone_id": "Z-SENS", "kind": "sensitive",
             "rect": {"x_min": 20.0, "y_min": 24.0, "x_max": 30.0, "y_max": 32.0},
             "layers": "signal"},
            {"zone_id": "Z-CORR", "kind": "corridor",
             "rect": {"x_min": 40.0, "y_min": 4.0, "x_max": 56.0, "y_max": 9.0},
             "layers": "all", "capacity": 3, "note": "底部贯穿走廊"},
        ],
        "partitions": [],
        "nets": [],
        "hard_rules": {
            "R1": {"k_a": 1.0, "floor_mm": 0.2},
            "R2": {"min_distance_mm": 2.0, "max_parallel_mm": 10.0},
            "R3": {"unsplittable": True},
            "R4": {"return_via_required": False, "max_distance_mm": 5.0},
            "R5": {"min_clearance_mm": 0.2},
            "R6": {"plane_forbidden": True, "keepout_zones_forbidden": True},
        },
        "principle_registry": [],
        "provenance": {
            "source_type": "synthetic", "source_uri": "inline://view-test-0",
            "source_sha256": "0" * 64, "adapter": "hand", "board_sha256": "",
        },
    }
    board["provenance"]["board_sha256"] = v5_board.compute_board_sha256(board)
    return board


# 8 种 ptype × 差异化 layer_policy：覆盖单层过滤的所有分支
_PTYPE_POLICIES = {
    "PWR": "F.Cu", "CLK": "F.Cu", "HS": "any", "BUS": "B.Cu",
    "DIFF": "F.Cu/B.Cu", "MISC": "B.Cu", "ANA": "In1", "ROUTED": "B.Cu",
}


def _make_ptable(board, partitions=None):
    if partitions is None:
        partitions = []
        for i, ptype in enumerate(view.PTYPE_ORDER):
            x = 6.0 + i * 6.0
            partitions.append({
                "partition_id": "PG-%02d" % (i + 1),
                "ptype": ptype,
                "net_ids": ["N-%s" % ptype],
                "geometry": {"endpoints": [[x, 34.0], [x + 4.0, 16.0]]},
                "layer_policy": _PTYPE_POLICIES[ptype],
                "width_prior": {"w_min": 0.25, "w_max": 0.9},
                "current_a": 0.5 + i * 0.25,
                "speed_class": "HS-fast" if ptype == "HS" else "std",
                "source_partitions": ["SP-%02d" % (i + 1)],
                "source_principles": ["PR-%02d" % (i + 1)],
                "note": "",
            })
    return {
        "artifact": "v5.partition.v1",
        "board_id": board["board_id"],
        "board_sha256": board["provenance"]["board_sha256"],
        "granularity_provenance": [{"rule": "ptype-x-adjacency",
                                    "source_principles": ["PR-01"]}],
        "partitions": partitions,
    }


# ---------------------------------------------------------------- 确定性

def test_svg_is_wellformed_xml():
    """SVG 产物可被 stdlib XML 解析器整段解析（手拼字符串不破良构性）。"""
    board = _make_board()
    ptable = _make_ptable(board)
    for mode in ("all", "F.Cu", "In2P"):
        root = ET.fromstring(view.render_l1_view(board, ptable, mode))
        assert root.tag.endswith("svg")
        assert root.get("data-mode") == mode


def test_svg_double_run_byte_equal():
    board = _make_board()
    ptable = _make_ptable(board)
    a = view.render_l1_view(board, ptable, "all")
    b = view.render_l1_view(board, ptable, "all")
    assert a == b
    assert a.encode("utf-8") == b.encode("utf-8")


def test_html_double_run_byte_equal():
    board = _make_board()
    ptable = _make_ptable(board)
    a = view.render_l1_html(board, ptable)
    b = view.render_l1_html(board, ptable)
    assert a == b
    assert a.encode("utf-8") == b.encode("utf-8")
    assert "\nDate" not in a and "Math.random" not in a  # 无时间源/随机源


# ---------------------------------------------------------------- mode 合同

def test_invalid_mode_raises():
    board = _make_board()
    ptable = _make_ptable(board)
    for bad in ("In9", "", "signal", "ALL"):
        with pytest.raises(ValueError):
            view.render_l1_view(board, ptable, bad)


def test_single_layer_mode_filters_partitions():
    board = _make_board()
    ptable = _make_ptable(board)
    all_svg = view.render_l1_view(board, ptable, "all")
    b_svg = view.render_l1_view(board, ptable, "B.Cu")
    assert all_svg != b_svg                       # 不同 mode 输出必不同
    assert 'data-mode="B.Cu"' in b_svg            # 含对应层 id
    assert 'data-partition-id="PG-04"' in b_svg   # BUS：policy=B.Cu
    assert 'data-partition-id="PG-05"' in b_svg   # DIFF：policy=F.Cu/B.Cu
    assert 'data-partition-id="PG-03"' in b_svg   # HS：policy=any 恒可见
    assert 'data-partition-id="PG-01"' not in b_svg  # PWR：policy=F.Cu 被滤除
    assert 'data-partition-id="PG-07"' not in b_svg  # ANA：policy=In1 被滤除


def test_plane_mode_filters_signal_zones():
    board = _make_board()
    ptable = _make_ptable(board)
    p_svg = view.render_l1_view(board, ptable, "In2P")  # 平面层
    assert 'data-zone-id="Z-KEEP"' in p_svg        # layers=all → 任何层都显示
    assert 'data-zone-id="Z-CORR"' in p_svg
    assert 'data-zone-id="Z-SENS"' not in p_svg    # layers=signal → 平面层滤除
    assert 'data-partition-id="PG-03"' in p_svg    # any 恒可见
    assert 'data-partition-id="PG-04"' not in p_svg  # B.Cu 分区被滤除


def test_any_policy_partition_lists_all_layers():
    board = _make_board()
    ptable = _make_ptable(board)
    svg = view.render_l1_view(board, ptable, "all")
    # HS（any）：data-layers 预计算为 all + 全部层（HTML solo 的显隐依据）
    assert 'data-layers="all F.Cu In1 In2P B.Cu"' in svg


# ---------------------------------------------------------------- 调色板与图例

def test_ptype_palette_coverage_and_legend():
    board = _make_board()
    ptable = _make_ptable(board)
    svg = view.render_l1_view(board, ptable, "all")
    assert '<g id="legend"' in svg
    assert svg.count('class="v5-legend-item"') == 8
    for ptype in view.PTYPE_ORDER:
        assert 'data-ptype="%s"' % ptype in svg
        assert view.PTYPE_COLORS[ptype] in svg    # 8 色固定映射全部在场


def test_zone_keepout_drawn():
    board = _make_board()
    ptable = _make_ptable(board)
    svg = view.render_l1_view(board, ptable, "all")
    assert 'data-kind="keepout"' in svg
    assert 'url(#v5-hatch-keepout)' in svg        # 红/斜线填充示意
    assert view.ZONE_STYLES["keepout"]["stroke"] in svg


def test_zone_sensitive_drawn():
    board = _make_board()
    ptable = _make_ptable(board)
    svg = view.render_l1_view(board, ptable, "all")
    assert 'data-kind="sensitive"' in svg
    assert view.ZONE_STYLES["sensitive"]["stroke"] in svg  # 橙


def test_zone_corridor_capacity_text():
    board = _make_board()
    ptable = _make_ptable(board)
    svg = view.render_l1_view(board, ptable, "all")
    assert 'data-kind="corridor"' in svg
    assert view.ZONE_STYLES["corridor"]["stroke"] in svg   # 蓝
    assert 'capacity=3.000' in svg                # 引擎算好的值写死进文本（%.3f）


# ---------------------------------------------------------------- 高亮钩子

def test_partition_hook_attributes():
    board = _make_board()
    ptable = _make_ptable(board)
    svg = view.render_l1_view(board, ptable, "all")
    assert 'id="v5-part-PG-01"' in svg
    # 组 + 两端点圆 + 连线 + 文本 = 每分区 ≥5 处钩子（整条高亮的锚点）
    assert svg.count('data-partition-id="PG-01"') >= 5
    assert 'data-layer="F.Cu"' in svg
    assert 'data-layers="all F.Cu"' in svg


def test_workspace_frame_drawn():
    board = _make_board()
    ptable = _make_ptable(board)
    svg = view.render_l1_view(board, ptable, "all")
    assert 'id="workspace-frame"' in svg
    assert 'stroke="#262626"' in svg


def test_layer_legend_colors_and_dashes():
    board = _make_board()
    ptable = _make_ptable(board)
    svg = view.render_l1_view(board, ptable, "all")
    assert '<g id="layer-legend"' in svg
    # KiCad 惯例层色：F.Cu 红 / In1 绿 / B.Cu 蓝
    assert view.LAYER_BASE_COLORS["F"] in svg
    assert view.LAYER_BASE_COLORS["In1"] in svg
    assert view.LAYER_BASE_COLORS["B"] in svg
    # 按层线型双编码：长虚/短虚/点线在场（F.Cu 为实线，无 dasharray）
    assert 'stroke-dasharray="14,5"' in svg
    assert 'stroke-dasharray="5,4"' in svg
    assert 'stroke-dasharray="2,4"' in svg


# ---------------------------------------------------------------- HTML 骨架

def test_html_solo_and_focus_hooks():
    board = _make_board()
    ptable = _make_ptable(board)
    html = view.render_l1_html(board, ptable)
    assert html.startswith("<!DOCTYPE html>")
    assert '<select id="v5-layer-solo"' in html          # 层 solo 下拉
    assert '<option value="all"' in html
    assert '<option value="In2P">' in html               # 各层 id 都有选项
    assert "addEventListener('change'" in html           # solo 切换钩子
    assert "addEventListener('click'" in html            # 整条高亮钩子
    assert "v5-has-focus" in html                        # 高亮压暗 CSS/JS 锚
    assert "data-partition-id" in html                   # 高亮聚合键
    assert 'id="v5-tooltip"' in html                     # 悬浮预算 tooltip
    assert "__SVG__" not in html and "__JS__" not in html \
        and "__OPTIONS__" not in html and "__CSS__" not in html  # 模板全替换
    assert 'id="v5-l1-view"' in html                     # SVG 已内嵌


# ---------------------------------------------------------------- provenance 对账

def test_partition_table_mismatch_raises():
    board = _make_board()
    ptable = _make_ptable(board)
    bad_sha = dict(ptable, board_sha256="f" * 64)
    with pytest.raises(ValueError):
        view.render_l1_view(board, bad_sha, "all")
    bad_id = dict(ptable, board_id="other-board")
    with pytest.raises(ValueError):
        view.render_l1_view(board, bad_id, "all")


# ---------------------------------------------------------------- 空表与落盘

def test_empty_partition_table_renders():
    board = _make_board()
    ptable = _make_ptable(board, partitions=[])
    svg = view.render_l1_view(board, ptable, "all")   # 不崩
    assert 'id="workspace-frame"' in svg
    assert 'data-zone-id="Z-KEEP"' in svg             # zones 照画
    assert "data-partition-id" not in svg             # 无分区元素


def test_write_view_svg_header_and_path(tmp_path, monkeypatch):
    monkeypatch.setattr(sidecar, "ALLOWED_ROOTS", (str(tmp_path),))
    board = _make_board()
    ptable = _make_ptable(board)
    svg = view.render_l1_view(board, ptable, "all")
    out_dir = os.path.join(str(tmp_path), "out")
    path = view.write_view(svg, "l1view", board["board_id"],
                           board["provenance"]["board_sha256"], out_dir)
    assert os.path.isfile(path)
    assert os.path.basename(path) == "view-test-0.l1view.svg"   # §3.5 命名
    assert os.path.dirname(os.path.abspath(path)) == os.path.abspath(out_dir)
    with open(path, encoding="utf-8") as f:
        text = f.read()
    first_line = text.split("\n", 1)[0]
    assert first_line.startswith("<!--") and first_line.endswith("-->")
    assert "generator=v5.view" in first_line
    assert "generator_version=%s" % view.VERSION in first_line
    assert "board_sha256=%s" % board["provenance"]["board_sha256"] in first_line
    assert svg in text                                # 头之后是完整 payload


def test_write_view_tree_stays_green_for_checker(tmp_path, monkeypatch):
    """SVG/HTML + json sidecar 混合树：sidecar.check_tree 与检查器口径均不报。"""
    monkeypatch.setattr(sidecar, "ALLOWED_ROOTS", (str(tmp_path),))
    board = _make_board()
    ptable = _make_ptable(board)
    out_dir = str(tmp_path / "out")
    sha = board["provenance"]["board_sha256"]
    view.write_view(view.render_l1_view(board, ptable, "all"),
                    "l1view", board["board_id"], sha, out_dir)
    html_path = view.write_view(view.render_l1_html(board, ptable),
                                "l1view-html", board["board_id"], sha, out_dir)
    assert os.path.basename(html_path) == "view-test-0.l1view-html.html"
    sidecar.write_sidecar(os.path.join(out_dir, "x.metrics.json"), {"v": 1},
                          generator="v5.test", generator_version="0.1.0",
                          board_sha256=sha)
    assert sidecar.check_tree(str(tmp_path)) == []


def test_write_view_rejects_outside_allowed_roots(tmp_path, monkeypatch):
    monkeypatch.setattr(sidecar, "ALLOWED_ROOTS", (str(tmp_path),))
    board = _make_board()
    svg = view.render_l1_view(board, _make_ptable(board), "all")
    outside = str(tmp_path.parent / "outside-run")
    with pytest.raises(sidecar.SidecarViolation):
        view.write_view(svg, "l1view", board["board_id"],
                        board["provenance"]["board_sha256"], outside)
    assert not os.path.exists(outside)                # 越界请求不落任何目录


def test_write_view_rejects_bad_payload_and_kind(tmp_path, monkeypatch):
    monkeypatch.setattr(sidecar, "ALLOWED_ROOTS", (str(tmp_path),))
    board = _make_board()
    svg = view.render_l1_view(board, _make_ptable(board), "all")
    sha = board["provenance"]["board_sha256"]
    with pytest.raises(ValueError):                   # 非 SVG/HTML payload
        view.write_view("plain text", "l1view", board["board_id"], sha, str(tmp_path))
    with pytest.raises(ValueError):                   # kind 带路径分隔符（防越界名）
        view.write_view(svg, "../evil", board["board_id"], sha, str(tmp_path))
    with pytest.raises(ValueError):                   # board_sha256 非法形态
        view.write_view(svg, "l1view", board["board_id"], "nothex", str(tmp_path))


# ================================================================= P2：L2 包络图

def _make_envelope(board, ptable):
    """内联 v5.envelope.v1 工件（夹具输入数据，非引擎复算）：包络 = 端点包围盒
    ± 0.6（视图口径 ENVELOPE_MARGIN_DEFAULT），宽度先验/optimal 直接落数。"""
    per = []
    for p in ptable["partitions"]:
        xs = sorted(pt[0] for pt in p["geometry"]["endpoints"])
        ys = sorted(pt[1] for pt in p["geometry"]["endpoints"])
        per.append({
            "partition_ref": p["partition_id"],
            "width_prior": {"w_min": p["width_prior"]["w_min"],
                            "w_max": p["width_prior"]["w_max"]},
            "optimal_width": p["width_prior"]["w_min"],
            "envelope_mm": [xs[0] - 0.6, ys[0] - 0.6, xs[-1] + 0.6, ys[-1] + 0.6],
            "margin_mm": 0.6,
            "capacity_notes": [],
        })
    return {
        "artifact": "v5.envelope.v1",
        "board_id": board["board_id"],
        "board_sha256": board["provenance"]["board_sha256"],
        "per_partition": per,
        "corridor_ledger": {},
    }


def _proj(board):
    """复算视图投影（与 v5.view._Plane 同式；这是视图几何，非引擎判定值）。"""
    ws = board["workspace"]
    map_h = view.VIEW_H - view.LEGEND_BAND
    dx = ws["x_max"] - ws["x_min"]
    dy = ws["y_max"] - ws["y_min"]
    bw = view.VIEW_W - 2 * view.MARGIN
    bh = map_h - 2 * view.MARGIN
    s = min(bw / dx, bh / dy)
    ox = view.MARGIN + (bw - dx * s) / 2.0
    oy = view.MARGIN + (bh - dy * s) / 2.0

    def f(wx, wy):
        return (ox + (wx - ws["x_min"]) * s, oy + (wy - ws["y_min"]) * s)
    return f, s


def test_l2_svg_wellformed_and_double_run():
    board = _make_board()
    ptable = _make_ptable(board)
    env = _make_envelope(board, ptable)
    a = view.render_l2_view(board, ptable, env, "all")
    b = view.render_l2_view(board, ptable, env, "all")
    assert a == b and a.encode("utf-8") == b.encode("utf-8")   # 双跑字节等
    root = ET.fromstring(a)                                    # 手拼串不破良构性
    assert root.tag.endswith("svg")
    assert root.get("id") == "v5-l2-view" and root.get("data-v5") == "l2-envelope"


def test_l2_envelope_rect_geometry_precise():
    """包络矩形坐标精确断言：PG-01 端点包围盒 [6,16,10,34] ± 0.6 → [5.4,15.4,10.6,34.6]
    经视图投影后的 SVG 像素坐标逐位相符（几何 ±0.6 口径落在渲染产物上）。"""
    board = _make_board()
    ptable = _make_ptable(board)
    svg = view.render_l2_view(board, ptable, _make_envelope(board, ptable), "all")
    f, s = _proj(board)
    x, y = f(5.4, 15.4)                     # 包络 min 角（±0.6 后）
    w = (10.6 - 5.4) * s
    h = (34.6 - 15.4) * s
    fc = view.LAYER_BASE_COLORS["F"]        # PG-01 主层 F.Cu
    expected = ('<rect x="%.3f" y="%.3f" width="%.3f" height="%.3f"'
                ' fill="%s" fill-opacity="0.18" stroke="%s"'
                % (x, y, w, h, fc, fc))
    assert expected in svg                  # 精确到 %.3f 的包络矩形
    assert 'data-margin-mm="0.600"' in svg  # 复用既有 margin 口径 0.6
    assert 'stroke-dasharray' not in [ln for ln in svg.split("\n")
                                      if 'data-partition-id="PG-01"' in ln
                                      and ln.startswith('<rect ')][0]  # F.Cu=实线


def test_l2_width_prior_text_present():
    board = _make_board()
    ptable = _make_ptable(board)
    svg = view.render_l2_view(board, ptable, _make_envelope(board, ptable), "all")
    # 宽度先验区间一行文本：数值来自 envelope_artifact.per_partition（引擎算好写死）
    assert "PG-01 w∈[0.250,0.900]→opt 0.250" in svg
    assert "PG-04 w∈[0.250,0.900]→opt 0.250" in svg
    assert 'data-opt-width="0.250"' in svg
    assert 'class="v5-envelope-width"' in svg


def test_l2_single_layer_mode_filter():
    board = _make_board()
    ptable = _make_ptable(board)
    env = _make_envelope(board, ptable)
    b_svg = view.render_l2_view(board, ptable, env, "B.Cu")
    assert 'data-mode="B.Cu"' in b_svg
    assert 'data-partition-id="PG-04"' in b_svg   # BUS：policy=B.Cu → 包络在
    assert 'data-partition-id="PG-05"' in b_svg   # DIFF：policy=F.Cu/B.Cu → 在
    assert 'data-partition-id="PG-01"' not in b_svg  # PWR：policy=F.Cu → 滤除
    assert 'data-partition-id="PG-07"' not in b_svg  # ANA：policy=In1 → 滤除


def test_l2_invalid_mode_raises():
    board = _make_board()
    ptable = _make_ptable(board)
    env = _make_envelope(board, ptable)
    for bad in ("In9", "", "ALL"):
        with pytest.raises(ValueError):
            view.render_l2_view(board, ptable, env, bad)


def test_l2_provenance_and_tag_contract():
    board = _make_board()
    ptable = _make_ptable(board)
    env = _make_envelope(board, ptable)
    with pytest.raises(ValueError):   # 包络工件 sha 与板不符（按 hash 对账失败）
        view.render_l2_view(board, ptable, dict(env, board_sha256="f" * 64), "all")
    with pytest.raises(ValueError):   # board_id 不符
        view.render_l2_view(board, ptable, dict(env, board_id="other"), "all")
    with pytest.raises(ValueError):   # artifact 标识非 v5.envelope.v1
        view.render_l2_view(board, ptable, dict(env, artifact="v4.envelope.v0"), "all")
    with pytest.raises(ValueError):   # per_partition 缺失
        bad = dict(env)
        del bad["per_partition"]
        view.render_l2_view(board, ptable, bad, "all")
    with pytest.raises(ValueError):   # 包络条目 ref 未命中分区表（fail-closed）
        orphan = dict(env, per_partition=[dict(env["per_partition"][0],
                                               partition_ref="NOPE")])
        view.render_l2_view(board, ptable, orphan, "all")


# ================================================================= P2：L3 叠加与 J 项图

def _make_conflicts(board, conflicts=None):
    """内联 v5.conflicts.v1 工件（上游合同形状；数值为夹具输入，非引擎复算）。"""
    if conflicts is None:
        conflicts = [
            {"conflict_id": "CF-001", "kind": "straight_zone_cross",
             "subjects": ["PG-01"], "zone": "Z-KEEP",
             "basis": "直线段穿越禁布区",
             "arithmetic": "occ=7.050mm>cap=3.000mm", "severity": "blocking"},
            {"conflict_id": "CF-002", "kind": "capacity_infeasible",
             "subjects": ["PG-04"], "zone": "Z-CORR",
             "basis": "走廊容量不可行",
             "arithmetic": "occ=7.050mm>cap=4.300mm", "severity": "advisory"},
            {"conflict_id": "CF-003", "kind": "envelope_overlap_diagnostic",
             "subjects": ["PG-01"], "zone": None,
             "basis": "包络重叠诊断", "arithmetic": None, "severity": "advisory"},
        ]
    return {"artifact": "v5.conflicts.v1",
            "board_id": board["board_id"],
            "board_sha256": board["provenance"]["board_sha256"],
            "conflicts": conflicts}


def test_l3_svg_wellformed_and_double_run():
    board = _make_board()
    ptable = _make_ptable(board)
    conf = _make_conflicts(board)
    stats = {"Z-CORR": {"occupancy": 7.05, "capacity": 4.3}}
    a = view.render_l3_view(board, ptable, conf, corridor_stats=stats, mode="all")
    b = view.render_l3_view(board, ptable, conf, corridor_stats=stats, mode="all")
    assert a == b and a.encode("utf-8") == b.encode("utf-8")   # 双跑字节等
    root = ET.fromstring(a)
    assert root.tag.endswith("svg")
    assert root.get("id") == "v5-l3-view" and root.get("data-v5") == "l3-overlays"


def test_l3_blocking_advisory_outline_styles():
    """blocking=红实线轮廓 / advisory=橙短虚线轮廓（字符串特征区分）。"""
    board = _make_board()
    ptable = _make_ptable(board)
    svg = view.render_l3_view(board, ptable, _make_conflicts(board), mode="all")
    lines = svg.split("\n")

    def rect_line(cid):
        hits = [ln for ln in lines
                if ln.startswith("<rect ") and 'data-conflict-id="%s"' % cid in ln]
        assert len(hits) == 1
        return hits[0]

    blocking = rect_line("CF-001")
    assert 'stroke="#cc0000"' in blocking            # 红
    assert "stroke-dasharray" not in blocking        # 实线
    advisory = rect_line("CF-002")
    assert 'stroke="#ff9900"' in advisory            # 橙
    assert 'stroke-dasharray="4,3"' in advisory      # 短虚线
    third = rect_line("CF-003")                      # CF-003 同为 advisory 样式
    assert 'stroke="#ff9900"' in third
    assert 'stroke-dasharray="4,3"' in third
    assert 'data-severity="advisory"' in third


def test_l3_conflict_hooks_and_arithmetic_text():
    board = _make_board()
    ptable = _make_ptable(board)
    svg = view.render_l3_view(board, ptable, _make_conflicts(board), mode="all")
    # 每冲突元素带三件套钩子（=整条高亮钩子）：组+轮廓+id 文本+算式文本
    assert ('class="v5-conflict" data-conflict-id="CF-001" data-severity="blocking"'
            ' data-kind="straight_zone_cross"') in svg
    assert svg.count('data-conflict-id="CF-001"') >= 4
    assert 'data-severity="advisory"' in svg
    assert 'data-kind="capacity_infeasible"' in svg
    # arithmetic 文本在场且经 XML 转义（可复算式显示，前端不重算）
    assert 'class="v5-conflict-arithmetic"' in svg
    assert "occ=7.050mm&gt;cap=3.000mm" in svg
    # arithmetic=None 的冲突（CF-003）不产算式文本：组+轮廓+id 文本恰好 3 处钩子
    assert svg.count('data-conflict-id="CF-003"') == 3


def test_l3_corridor_heat_over():
    """热区：occupancy/capacity 比值驱动填充透明度，图例文本写引擎值。"""
    board = _make_board()
    ptable = _make_ptable(board)
    svg = view.render_l3_view(board, ptable, _make_conflicts(board),
                              corridor_stats={"Z-CORR": {"occupancy": 7.05,
                                                         "capacity": 4.3}},
                              mode="all")
    assert 'fill-opacity="1.000"' in svg             # 7.05/4.3 超载 → 钳到上界
    assert "Z-CORR 7.050/4.300 OVER" in svg          # 引擎值写死进图例文本
    assert 'data-occupancy="7.050"' in svg
    assert 'data-capacity="4.300"' in svg
    assert "capacity=3.000" not in svg               # 常规 capacity 文本被热区文本取代


def test_l3_corridor_heat_ratio_below_capacity():
    board = _make_board()
    ptable = _make_ptable(board)
    svg = view.render_l3_view(board, ptable, _make_conflicts(board),
                              corridor_stats={"Z-CORR": {"occupancy": 2.0,
                                                         "capacity": 4.0}},
                              mode="all")
    assert 'fill-opacity="0.500"' in svg             # 比值 2.0/4.0 → 0.500
    assert "Z-CORR 2.000/4.000 OK" in svg


def test_l3_corridor_stats_none_keeps_regular():
    board = _make_board()
    ptable = _make_ptable(board)
    svg = view.render_l3_view(board, ptable, _make_conflicts(board),
                              corridor_stats=None, mode="all")   # 不崩
    assert 'fill-opacity="0.12"' in svg              # 走廊常规色
    assert "capacity=3.000" in svg                   # 常规 capacity 文本在场
    assert "OVER" not in svg and "OK</text>" not in svg


def test_l3_mode_filters_conflicts():
    board = _make_board()
    ptable = _make_ptable(board)
    conf = _make_conflicts(board)
    all_svg = view.render_l3_view(board, ptable, conf, mode="all")
    b_svg = view.render_l3_view(board, ptable, conf, mode="B.Cu")
    assert 'data-conflict-id="CF-003"' in all_svg    # subject PG-01(F.Cu)、无 zone
    assert 'data-conflict-id="CF-003"' not in b_svg  # B.Cu 模式滤除
    assert 'data-conflict-id="CF-002"' in b_svg      # subject PG-04(B.Cu) → 在
    assert 'data-conflict-id="CF-001"' in b_svg      # zone Z-KEEP layers=all → 恒在


def test_l3_contract_violations_raise():
    board = _make_board()
    ptable = _make_ptable(board)
    conf = _make_conflicts(board)
    with pytest.raises(ValueError):   # sha 对账失败
        view.render_l3_view(board, ptable, dict(conf, board_sha256="f" * 64), mode="all")
    with pytest.raises(ValueError):   # artifact 标识非 v5.conflicts.v1
        view.render_l3_view(board, ptable, dict(conf, artifact="v4.conflicts.v0"),
                            mode="all")
    with pytest.raises(ValueError):   # severity 枚举外 fail-closed
        bad = _make_conflicts(board, [dict(conf["conflicts"][0], severity="warn")])
        view.render_l3_view(board, ptable, bad, mode="all")
    with pytest.raises(ValueError):   # conflict_id 空
        bad = _make_conflicts(board, [dict(conf["conflicts"][0], conflict_id="")])
        view.render_l3_view(board, ptable, bad, mode="all")
    with pytest.raises(ValueError):   # subject 未命中分区表
        bad = _make_conflicts(board, [dict(conf["conflicts"][0], subjects=["NOPE"])])
        view.render_l3_view(board, ptable, bad, mode="all")
    with pytest.raises(ValueError):   # zone 未命中板 zones
        bad = _make_conflicts(board, [dict(conf["conflicts"][0], zone="NOPE")])
        view.render_l3_view(board, ptable, bad, mode="all")
    with pytest.raises(ValueError):   # 热区键未命中 corridor zone
        view.render_l3_view(board, ptable, conf,
                            corridor_stats={"NOPE": {"occupancy": 1, "capacity": 2}},
                            mode="all")
    with pytest.raises(ValueError):   # 热区条目缺 capacity
        view.render_l3_view(board, ptable, conf,
                            corridor_stats={"Z-CORR": {"occupancy": 1}}, mode="all")
    with pytest.raises(ValueError):   # 热区 capacity ≤ 0
        view.render_l3_view(board, ptable, conf,
                            corridor_stats={"Z-CORR": {"occupancy": 1, "capacity": 0}},
                            mode="all")


def test_l3_subject_resolves_via_source_partitions():
    """两级命中（2026-09-13 集成缝修复）：subject=板级分区号（SP-04，仅存在于条目
    source_partitions）→ 渲染成功且高亮落在容器条目 PG-04；直接命中 subject 记
    自身为容器；两级都不中（SP-99）仍 ValueError fail-closed。"""
    board = _make_board()
    ptable = _make_ptable(board)   # 各条目 source_partitions = SP-01..SP-08
    conf = _make_conflicts(board, [{
        "conflict_id": "CF-MERGED", "kind": "capacity_infeasible",
        "subjects": ["PG-01", "SP-04"], "zone": None,
        "basis": "板级 id 经 source_partitions 归并",
        "arithmetic": "1.0<1.2", "severity": "blocking"}])
    svg = view.render_l3_view(board, ptable, conf, mode="all")   # 不崩
    subj_rects = [ln for ln in svg.split("\n")
                  if ln.startswith("<rect ") and "data-conflict-subject=" in ln]
    assert len(subj_rects) == 2                  # 每 subject 恰一条带钩子轮廓
    direct = [ln for ln in subj_rects if 'data-conflict-subject="PG-01"' in ln]
    assert len(direct) == 1
    assert 'data-partition-id="PG-01"' in direct[0]   # 直接命中：容器=自身
    merged = [ln for ln in subj_rects if 'data-conflict-subject="SP-04"' in ln]
    assert len(merged) == 1
    assert 'data-partition-id="PG-04"' in merged[0]   # 归并命中：容器条目 id
    assert 'data-conflict-id="CF-MERGED"' in merged[0]
    assert 'data-severity="blocking"' in merged[0]
    # 几何=容器条目端点包围盒 ± PAD：PG-04 端点 [[24,34],[28,16]]，视图投影精确断言
    f, s = _proj(board)
    x, y = f(24.0, 16.0)
    pad = view.CONFLICT_PAD_PX
    expected = '<rect x="%.3f" y="%.3f" width="%.3f" height="%.3f"' % (
        x - pad, y - pad, 4.0 * s + 2 * pad, 18.0 * s + 2 * pad)
    assert expected in merged[0]
    with pytest.raises(ValueError):              # 两级都不中仍 fail-closed
        bad = _make_conflicts(board, [dict(conf["conflicts"][0], subjects=["SP-99"])])
        view.render_l3_view(board, ptable, bad, mode="all")


# ================================================================= P2：落盘与冒烟

def test_write_view_l2_l3_kinds_and_tree_green(tmp_path, monkeypatch):
    """新 kind 令牌（l2-all / l3-all）落盘：sidecar 命名 + provenance 头在场 +
    混合树过 check_tree。（注：write_view 现实现无 kind 白名单，只查令牌字符集，
    无白名单可扩展——按源码实况只验证新令牌可用。）"""
    monkeypatch.setattr(sidecar, "ALLOWED_ROOTS", (str(tmp_path),))
    board = _make_board()
    ptable = _make_ptable(board)
    sha = board["provenance"]["board_sha256"]
    out_dir = str(tmp_path / "out")
    l2 = view.render_l2_view(board, ptable, _make_envelope(board, ptable), "all")
    l3 = view.render_l3_view(board, ptable, _make_conflicts(board), mode="all")
    p2 = view.write_view(l2, "l2-all", board["board_id"], sha, out_dir)
    p3 = view.write_view(l3, "l3-all", board["board_id"], sha, out_dir)
    assert os.path.basename(p2) == "view-test-0.l2-all.svg"
    assert os.path.basename(p3) == "view-test-0.l3-all.svg"
    for path, kind, payload in ((p2, "l2-all", l2), (p3, "l3-all", l3)):
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


def test_demo01_real_artifacts_smoke():
    """demo-01 只读冒烟（任务令例外）：真实 board+partition+envelope 工件作输入，
    L2/L3 渲染不空不崩；文件不在场则 skip（不写回任何字节）。"""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    art_dir = os.path.join(root, "out", "v5-p1", "artifacts")
    paths = {
        # 板在 boards/d/；L1/L2 工件在 out/v5-p1/artifacts/（P1 产物，只读）
        "board": os.path.join(root, "boards", "d",
                              "demo-01-v2-corridor.board.v1.json"),
        "partition": os.path.join(art_dir, "demo-01-v2-corridor.partition.json"),
        "envelope": os.path.join(art_dir, "demo-01-v2-corridor.envelope.json"),
    }
    if not all(os.path.isfile(p) for p in paths.values()):
        pytest.skip("P1 demo-01 工件不在场（只读冒烟可跳过）")
    blobs = {}
    for name, path in paths.items():
        with open(path, encoding="utf-8") as f:
            blobs[name] = json.load(f)          # 只读，不回写
    board = blobs["board"]
    ptable = blobs["partition"]
    env = blobs["envelope"]

    l2 = view.render_l2_view(board, ptable, env, "all")
    assert l2 and ET.fromstring(l2).tag.endswith("svg")
    assert 'data-partition-id="P1"' in l2       # 首个真实分区包络在场
    assert "P1 w∈[" in l2                       # 宽度先验区间文本在场

    ledger = (env.get("corridor_ledger") or {}).get("C1") or {}
    conf = _make_conflicts(board, [{
        "conflict_id": "CF-SMOKE", "kind": "capacity_infeasible",
        "subjects": ["P1"], "zone": "C1", "basis": "冒烟",
        "arithmetic": "occ=%.3fmm>cap=%.3fmm" % (ledger.get("occupancy_mm", 0.0),
                                                 ledger.get("capacity_mm", 0.0)),
        "severity": "blocking"}])
    stats = {"C1": {"occupancy": ledger.get("occupancy_mm", 0.0),
                    "capacity": ledger.get("capacity_mm", 1.0)}}
    l3 = view.render_l3_view(board, ptable, conf, corridor_stats=stats, mode="all")
    assert l3 and ET.fromstring(l3).tag.endswith("svg")
    assert 'data-conflict-id="CF-SMOKE"' in l3
    assert "C1 7.050/4.300 OVER" in l3          # 真实账本值（7.05/4.3）驱动的热区文本


def test_demo01_real_chain_l3_smoke():
    """demo-01 只读真实链冒烟（2026-09-13 集成炸点回归）：boards/d 板 → 真实
    build_partition_artifact + build_conflicts（subjects 引用板级分区号，L1 已把
    P7/P9 合并为 PG-7）→ render_l3_view 全 14 条冲突渲染不崩。纯函数链，不落盘。"""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    board_path = os.path.join(root, "boards", "d", "demo-01-v2-corridor.board.v1.json")
    if not os.path.isfile(board_path):
        pytest.skip("demo-01 板不在场（只读冒烟可跳过）")
    try:
        from v5.overlay import build_conflicts
        from v5.partition import build_partition_artifact
    except ImportError:                          # 并行产出模块不在场则跳过
        pytest.skip("v5.overlay / v5.partition 不在场（只读冒烟可跳过）")
    with open(board_path, encoding="utf-8") as f:
        board = json.load(f)                     # 只读，不回写
    ptable = build_partition_artifact(board)
    conf = build_conflicts(board)
    l3 = view.render_l3_view(board, ptable, conf, corridor_stats=None, mode="all")
    assert l3 and ET.fromstring(l3).tag.endswith("svg")   # 整段良构不崩
    assert len(conf["conflicts"]) == 14                   # 真实链全量冲突
    for c in conf["conflicts"]:
        assert 'data-conflict-id="%s"' % c["conflict_id"] in l3
    # 集成炸点键：CF-002 subjects=[P1,P2,P4,P7,P9]，P7/P9 归并高亮到容器条目 PG-7
    assert 'data-conflict-subject="P7" data-partition-id="PG-7"' in l3
    assert 'data-conflict-subject="P9" data-partition-id="PG-7"' in l3
    assert 'class="v5-conflict-zone"' in l3               # 冲突 zone 轮廓在场
