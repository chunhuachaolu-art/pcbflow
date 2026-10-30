# -*- coding: utf-8 -*-
"""KiCad 导出净类口径透传测试（P5 升级件②：R5→净类 + 封装库解析）。

覆盖（实现与换算推导见 v5.kicad_export 模块 docstring）：
- **R5 透传**：``project_kicad_pro_bytes`` 内嵌 Default 净类 clearance =
  max(0, R5 − 导出走线宽度最大值)、min_track_width = 导出走线宽度最小值；
  改板参数（R5 值 / routes 宽度）→ .kicad_pro bytes 随之变化而 .kicad_pcb
  bytes 不变（净类只落项目文件，板文件 version token 20171130 口径不变）；
- **确定性**：.kicad_pro 双跑字节等；board/routes canonical 键序往返稳定；
- **demo-02（boards/d）**：真实 demo 板 + 手工局部 routes → 净类 JSON 内含
  按公式推导的 clearance/min_track_width 值；
- **封装库解析**：anchor module 无库昵称（``V5-anchor-…`` 无冒号）——kicad-cli
  lib parity 不再报「当前配置中不包含封装库 'V5'」的根因修复回归锚；
- **fail-closed**：hard_rules.R5.min_clearance_mm 缺失 / 非正 / 非有限 /
  非数值 → 两导出函数一并 ExportError（键路径入信息），write_kicad_pcb
  零文件落盘；
- **write_kicad_pcb 双件落盘**：.kicad_pcb + 同 stem .kicad_pro，内容与纯
  函数一致；board 只读。零 LLM API、零网络、不装不调 kicad-cli（套件纪律，
  外权威实测由 D 层 scratch 驱动另行处置）。
"""
import copy
import json
import os

import pytest

from v5 import canonical, sidecar
from v5.board import compute_board_sha256, load_board
from v5.kicad_export import (
    PRO_NET_SETTINGS_META_VERSION,
    ExportError,
    kicad_pcb_bytes,
    project_kicad_pro_bytes,
    write_kicad_pcb,
)

# --------------------------------------------------------------- 夹具


def _hand_board(r5=0.5, w_max_prior=0.4, w_min_prior=0.2, board_id="hand-netclass"):
    """自造合法板（synthetic provenance；load_board 落链）。"""
    bd = {
        "schema_version": "v5.board.v1",
        "board_id": board_id,
        "stackup": [
            {"id": "F.Cu", "kind": "signal", "preferred_direction": "any",
             "available": True},
            {"id": "B.Cu", "kind": "signal", "preferred_direction": "any",
             "available": True},
        ],
        "workspace": {"x_min": 0.0, "y_min": 0.0, "x_max": 40.0, "y_max": 30.0},
        "zones": [],
        "partitions": [
            {"partition_id": "PA", "ptype": "MISC",
             "geometry": {"endpoints": [[0.0, 0.0], [10.0, 0.0]]},
             "layer_policy": "any",
             "width_prior": {"w_min": w_min_prior, "w_max": w_max_prior},
             "current_a": 0, "speed_class": "unknown"},
            {"partition_id": "PB", "ptype": "MISC",
             "geometry": {"endpoints": [[0.0, 20.0], [10.0, 20.0]]},
             "layer_policy": "any",
             "width_prior": {"w_min": w_min_prior, "w_max": w_max_prior},
             "current_a": 0, "speed_class": "unknown"},
        ],
        "nets": [{"net_id": "NA", "partitions": ["PA"]},
                 {"net_id": "NB", "partitions": ["PB"]}],
        "hard_rules": {
            "R1": {"k_a": 0.4, "floor_mm": 0.3},
            "R2": {"min_distance_mm": 3.0, "max_parallel_mm": 5.0},
            "R3": {"unsplittable": True},
            "R4": {"return_via_required": True, "max_distance_mm": 2.0},
            "R5": {"min_clearance_mm": r5},
            "R6": {"plane_forbidden": True, "keepout_zones_forbidden": True},
        },
        "principle_registry": [],
        "provenance": {"source_type": "synthetic", "source_uri": "synthetic://hand",
                       "source_sha256": "0" * 64, "adapter": "hand"},
    }
    bd["provenance"]["board_sha256"] = compute_board_sha256(bd)
    load_board(bd)
    return bd


def _routes_doc(bd, entries):
    doc = {
        "schema_version": "v5.routes.v1",
        "board_id": bd["board_id"],
        "board_sha256": bd["provenance"]["board_sha256"],
        "routes": entries,
        "negotiation_log": [],
        "provenance": {"generator": "v5.executor/0.1.0",
                       "board_sha256": bd["provenance"]["board_sha256"]},
    }
    return doc


def _entry(pid, nid, width, y=0.0):
    return {"partition_id": pid, "net_id": nid, "layer": "F.Cu", "width": width,
            "polyline": [[0.0, y], [10.0, y]],
            "transition_vias": [], "return_vias": []}


def _pro_dict(data):
    return json.loads(data.decode("utf-8"))


# --------------------------------------------------------------- 确定性


def test_pro_bytes_deterministic_double_run():
    bd = _hand_board()
    doc = _routes_doc(bd, [_entry("PA", "NA", 0.2)])
    assert project_kicad_pro_bytes(bd, doc) == project_kicad_pro_bytes(bd, doc)
    assert isinstance(project_kicad_pro_bytes(bd, doc), bytes)
    assert project_kicad_pro_bytes(bd, doc)


def test_pro_stable_under_dict_key_order():
    """PS 稳定性口径：board/routes canonical 键序化往返后 .kicad_pro 字节等。"""
    bd = _hand_board()
    doc = _routes_doc(bd, [_entry("PA", "NA", 0.2)])
    bd2 = json.loads(canonical.canonical_text(bd))
    doc2 = json.loads(canonical.canonical_text(doc))
    assert project_kicad_pro_bytes(bd2, doc2) == project_kicad_pro_bytes(bd, doc)


def test_board_not_mutated_by_pro_bytes():
    bd = _hand_board()
    doc = _routes_doc(bd, [_entry("PA", "NA", 0.2)])
    before = canonical.canonical_json(copy.deepcopy(bd))
    project_kicad_pro_bytes(bd, doc)
    assert canonical.canonical_json(bd) == before


# --------------------------------------------------------------- R5 透传


def test_r5_passthrough_changes_pro_not_pcb():
    """改板参数（R5）→ .kicad_pro 变；净类只落项目文件——.kicad_pcb 内无任何
    净类/间距约束 token（board_sha256 随 R5 进 host 行属落链事实，另计）。"""
    bd_a, bd_b = _hand_board(r5=0.5), _hand_board(r5=1.0)
    doc_a = _routes_doc(bd_a, [_entry("PA", "NA", 0.2)])
    doc_b = _routes_doc(bd_b, [_entry("PA", "NA", 0.2)])
    for pcb in (kicad_pcb_bytes(bd_a, doc_a), kicad_pcb_bytes(bd_b, doc_b)):
        assert b"clearance" not in pcb and b"net_settings" not in pcb
    pro_a, pro_b = (project_kicad_pro_bytes(bd_a, doc_a),
                    project_kicad_pro_bytes(bd_b, doc_b))
    assert pro_a != pro_b
    # 推导：C = R5 − w_max = 0.5−0.2=0.3 / 1.0−0.2=0.8
    assert _pro_dict(pro_a)["net_settings"]["classes"][0]["clearance"] == 0.3
    assert _pro_dict(pro_b)["net_settings"]["classes"][0]["clearance"] == 0.8


def test_derived_widths_across_routes():
    """w_max/w_min 取全部导出走线宽度的极值：C = R5 − max，min_track = min。"""
    bd = _hand_board(r5=0.5)
    doc = _routes_doc(bd, [_entry("PA", "NA", 0.2), _entry("PB", "NB", 0.35)])
    pro = _pro_dict(project_kicad_pro_bytes(bd, doc))
    cls = pro["net_settings"]["classes"][0]
    assert cls["clearance"] == 0.15       # 0.5 − 0.35
    assert cls["track_width"] == 0.2
    assert pro["board"]["design_settings"]["rules"]["min_track_width"] == 0.2


def test_clearance_floor_zero_when_r5_le_wmax():
    """R5 ≤ w_max → 下限 0.0（docstring 下限语义披露；确定性量化）。"""
    bd = _hand_board(r5=0.2, w_max_prior=0.4)
    doc = _routes_doc(bd, [_entry("PA", "NA", 0.4)])
    pro = _pro_dict(project_kicad_pro_bytes(bd, doc))
    assert pro["net_settings"]["classes"][0]["clearance"] == 0.0
    assert pro["net_settings"]["classes"][0]["clearance"] >= 0.0


def test_fallback_widths_from_width_prior_when_no_routes():
    """routes 空 → 回退分区 width_prior 极值（确定性回退链）。"""
    bd = _hand_board(r5=0.5, w_max_prior=0.4, w_min_prior=0.2)
    doc = _routes_doc(bd, [])
    pro = _pro_dict(project_kicad_pro_bytes(bd, doc))
    cls = pro["net_settings"]["classes"][0]
    assert cls["clearance"] == 0.1        # 0.5 − 0.4
    assert cls["track_width"] == 0.2
    assert pro["board"]["design_settings"]["rules"]["min_track_width"] == 0.2


def test_pro_json_shape():
    """形状合同：Default 单净类 + 板级 min_track_width + meta 版本，键最省。"""
    bd = _hand_board(r5=0.5)
    doc = _routes_doc(bd, [_entry("PA", "NA", 0.2)])
    pro = _pro_dict(project_kicad_pro_bytes(bd, doc))
    assert set(pro.keys()) == {"board", "net_settings"}
    classes = pro["net_settings"]["classes"]
    assert len(classes) == 1 and classes[0]["name"] == "Default"
    assert set(classes[0].keys()) == {"clearance", "name", "track_width"}
    assert pro["net_settings"]["meta"] == {"version": PRO_NET_SETTINGS_META_VERSION}
    assert pro["net_settings"]["netclass_patterns"] == []
    assert pro["net_settings"]["net_colors"] is None
    assert pro["net_settings"]["netclass_assignments"] is None
    rules = pro["board"]["design_settings"]["rules"]
    assert set(rules.keys()) == {"min_track_width"}


# --------------------------------------------------------------- demo-02（boards/d）


def _demo_board(board_id):
    from boards import build_demo_boards
    path = os.path.join(build_demo_boards.OUT_DIR,
                        "%s.board.v1.json" % board_id)
    return load_board(json.load(open(path, encoding="utf-8")))


def test_demo02_netclass_contains_derived_values():
    """demo-02 导出件净类 JSON 内含推导值：R5=0.5、routes 宽 {0.3, 0.2}
    → clearance=0.2、min_track_width=0.2（D 层真实板 + 局部 routes）。"""
    bd = _demo_board("demo-02-mixed-types")
    assert bd["hard_rules"]["R5"]["min_clearance_mm"] == 0.5
    n0, n1 = bd["nets"][0], bd["nets"][1]
    # 取两网各自首分区的端点连线为走线（宽度自选 0.3 / 0.2）
    def _entry_of(net, width):
        pid = net["partitions"][0]
        part = next(p for p in bd["partitions"]
                    if p["partition_id"] == pid)
        a, b = part["geometry"]["endpoints"]
        return {"partition_id": pid, "net_id": net["net_id"], "layer": bd["stackup"][0]["id"],
                "width": width, "polyline": [list(a), list(b)],
                "transition_vias": [], "return_vias": []}
    doc = _routes_doc(bd, [_entry_of(n0, 0.3), _entry_of(n1, 0.2)])
    pro = _pro_dict(project_kicad_pro_bytes(bd, doc))
    cls = pro["net_settings"]["classes"][0]
    assert cls["clearance"] == 0.2        # 0.5 − 0.3
    assert cls["track_width"] == 0.2
    assert pro["board"]["design_settings"]["rules"]["min_track_width"] == 0.2


# --------------------------------------------------------------- 封装库解析


def test_anchor_module_has_no_lib_nickname():
    """lib_footprint_issues 根因修复回归锚：module 名无库昵称（冒号）。"""
    bd = _hand_board()
    doc = _routes_doc(bd, [_entry("PA", "NA", 0.2)])
    text = kicad_pcb_bytes(bd, doc).decode("utf-8")
    assert "(module \"V5-anchor-PA-a\"" in text
    assert "(module \"V5-anchor-PA-b\"" in text
    assert "(module \"V5:anchor" not in text
    # 每个带引号 module 名都无冒号（KiCad lib_id 昵称分隔符）
    for line in text.splitlines():
        if "(module " in line:
            name = line.split("\"")[1]
            assert ":" not in name, name


# --------------------------------------------------------------- fail-closed


def _strip_r5(bd, mode):
    bd = copy.deepcopy(bd)
    if mode == "no_r5":
        del bd["hard_rules"]["R5"]
    elif mode == "no_hard_rules":
        del bd["hard_rules"]
    elif mode == "r5_not_dict":
        bd["hard_rules"]["R5"] = 0.5
    elif mode == "no_value":
        del bd["hard_rules"]["R5"]["min_clearance_mm"]
    elif mode == "zero":
        bd["hard_rules"]["R5"]["min_clearance_mm"] = 0
    elif mode == "negative":
        bd["hard_rules"]["R5"]["min_clearance_mm"] = -0.5
    elif mode == "nan":
        bd["hard_rules"]["R5"]["min_clearance_mm"] = float("nan")
    elif mode == "inf":
        bd["hard_rules"]["R5"]["min_clearance_mm"] = float("inf")
    elif mode == "string":
        bd["hard_rules"]["R5"]["min_clearance_mm"] = "0.5"
    elif mode == "bool":
        bd["hard_rules"]["R5"]["min_clearance_mm"] = True
    else:
        raise AssertionError(mode)
    return bd


@pytest.mark.parametrize("mode", ["no_r5", "no_hard_rules", "r5_not_dict",
                                  "no_value", "zero", "negative", "nan",
                                  "inf", "string", "bool"])
def test_fail_closed_r5_missing_or_bad(mode):
    """R5 缺失/非正/非有限/非数值 → 两导出函数一并 fail-closed，键路径入信息。"""
    bd = _strip_r5(_hand_board(), mode)
    doc = _routes_doc(bd, [_entry("PA", "NA", 0.2)])
    for fn in (kicad_pcb_bytes, project_kicad_pro_bytes):
        with pytest.raises(ExportError) as ei:
            fn(bd, doc)
        assert "board.hard_rules.R5.min_clearance_mm" in str(ei.value)


def test_write_fail_closed_r5_leaves_no_files(tmp_path, monkeypatch):
    """write_kicad_pcb 在 R5 违约时 .kicad_pcb 与 .kicad_pro 零落盘。"""
    monkeypatch.setattr(sidecar, "ALLOWED_ROOTS", (str(tmp_path),))
    bd = _strip_r5(_hand_board(), "no_r5")
    doc = _routes_doc(bd, [_entry("PA", "NA", 0.2)])
    target = os.path.join(str(tmp_path), "out", "x.kicad_pcb")
    with pytest.raises(ExportError):
        write_kicad_pcb(bd, doc, target)
    assert not os.path.exists(target)
    assert not os.path.exists(os.path.splitext(target)[0] + ".kicad_pro")


# --------------------------------------------------------------- write_kicad_pcb


def test_write_kicad_pcb_writes_pro_sibling(tmp_path, monkeypatch):
    """双件落盘：.kicad_pcb + 同 stem .kicad_pro，内容与纯函数一致；返回 pcb 路径。"""
    monkeypatch.setattr(sidecar, "ALLOWED_ROOTS", (str(tmp_path),))
    bd = _hand_board(r5=0.5)
    doc = _routes_doc(bd, [_entry("PA", "NA", 0.2)])
    target = os.path.join(str(tmp_path), "out", "run-1", "x.kicad_pcb")
    ret = write_kicad_pcb(bd, doc, target)
    assert ret == target
    with open(target, "rb") as f:
        assert f.read() == kicad_pcb_bytes(bd, doc)
    pro_path = os.path.splitext(target)[0] + ".kicad_pro"
    with open(pro_path, "rb") as f:
        assert f.read() == project_kicad_pro_bytes(bd, doc)
