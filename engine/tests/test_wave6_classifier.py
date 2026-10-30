# -*- coding: utf-8 -*-
"""P5⑥-D6-4 分类器词表补已知类单测（run_p5_board 0.4.0）。

范围：只测 tools/run_p5_board.py 的 classify_kicad_violations 纯函数（含
显式边距值提取 helper）。钉死：
  - padstack → contract-artifact（焊盘层跨出口画法披露差，⑥后应=0）；
  - copper_edge_clearance 三分支：v5 edge_violations 同位同网 → genuine／
    板显式边距值 ≠ kicad 缺省 0.2mm → config-gap／其余 → contract-artifact；
    含 edge_violations 键缺席的防御路径；
  - 既有分支回归不变（genuine pair / shorting / holes_co_located /
    lib_footprint_issues / dangling / unconnected / clearance config-gap /
    else 保守归真）；
  - rows/counts 结构键不变（报告消费方零感知）。

手段：全内存构造 board/drc/cr 夹具（纯函数，不落盘、零网络、零 kicad-cli，
v5/ 与兄弟包文件零触碰）。cr 的 edge_violations 键按 D6-3 合同形态
（list of {"net_id","pos"}）由兄弟包 route_check 提供，本文件只按合同
形态消费测试。
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
if os.path.join(ROOT, "tools") not in sys.path:
    sys.path.insert(0, os.path.join(ROOT, "tools"))

import run_p5_board as rpb  # noqa: E402

ROW_KEYS = {"kind", "type", "severity", "description", "items", "nets",
            "category", "rationale"}


# ------------------------------------------------------------- 夹具构造

def _board(registry=None, workspace=None):
    """最小 board 夹具：classify 只读 nets/partitions 端点/
    principle_registry/workspace（显式边距扫描）。"""
    return {
        "nets": [
            {"net_id": "N1", "partitions": ["P1"]},
            {"net_id": "N2", "partitions": ["P1"]},
        ],
        "partitions": [
            {"partition_id": "P1",
             "geometry": {"endpoints": [[1.0, 1.0], [9.0, 1.0]]}},
        ],
        "principle_registry": registry if registry is not None else [],
        "workspace": workspace if workspace is not None else
        {"x_min": 0.0, "y_min": 0.0, "x_max": 20.0, "y_max": 20.0},
    }


def _drc(violations, unconnected=None):
    return {"violations": violations,
            "unconnected_items": unconnected or [],
            "schematic_parity": []}


def _vio(vtype, desc, pos=None, items=None):
    """kicad-cli violation 条目夹具（dict pos 形态；多 item 场景传 items）。"""
    if items is None:
        items = []
        if pos is not None:
            items = [{"description": desc, "pos": {"x": pos[0], "y": pos[1]}}]
    return {"type": vtype, "severity": "error", "description": desc,
            "items": items}


def _cr(v5_violations=None, edge_violations=None, routed=("N1", "N2"),
        feasible=True):
    """v5 route_check 结果夹具（_routes_entries 为 run_p5_board 注入键；
    edge_violations=None 时键整体缺席=防御路径）。"""
    cr = {"violations": v5_violations or [], "feasible": feasible,
          "_routes_entries": [{"net_id": n} for n in routed]}
    if edge_violations is not None:
        cr["edge_violations"] = edge_violations
    return cr


def _classify_one(vio, board=None, cr=None):
    rows, counts = rpb.classify_kicad_violations(
        _drc([vio]), board if board is not None else _board(),
        cr if cr is not None else _cr())
    assert len(rows) == 1
    return rows[0], counts


# ------------------------------------------------------- D6-4 padstack

def test_padstack_is_contract_artifact():
    row, counts = _classify_one(
        _vio("padstack", "焊盘 [N1] 在全部铜层出现", pos=(5.0, 5.0)))
    assert row["category"] == "contract-artifact"
    assert "出口画法" in row["rationale"]  # why 逐字披露：层跨出口画法披露差
    assert "非零" in row["rationale"]      # ⑥后应=0，非零逐板披露
    # V5-D8 翻转披露（2026-09-22）：DRC_CATEGORIES 三元→五元（+hole_to_hole-
    # engine/board-inherent 恒零计数补齐）
    assert counts["classified"] == {"config-gap": 0, "contract-artifact": 1,
                                    "genuine": 0,
                                    "hole_to_hole-engine": 0,
                                    "hole_to_hole-board-inherent": 0}


def test_padstack_with_v5_pair_still_genuine_pair_first():
    """既有 genuine pair 判据保持最前（保守归真优先级不被破坏）。"""
    v = _vio("padstack", "焊盘短接 [N1] 与 [N2]", pos=(5.0, 5.0))
    cr = _cr(v5_violations=[{"rule": "R5",
                             "subjects": ["route:N1:p1#0", "route:N2:p2#0"],
                             "data": {}}])
    row, _ = _classify_one(v, cr=cr)
    assert row["category"] == "genuine"
    assert "两权威一致" in row["rationale"]


# ------------------------------------------- D6-4 copper_edge 三分支

def test_edge_genuine_same_pos_same_net():
    v = _vio("copper_edge_clearance", "铜箔离板边太近 [N1]", pos=(5.0, 5.0))
    cr = _cr(edge_violations=[{"net_id": "N1", "pos": [5.4, 5.3]}])
    row, _ = _classify_one(v, cr=cr)
    assert row["category"] == "genuine"
    assert "edge_violations" in row["rationale"]  # why 逐字披露：同位同网归责
    assert "同位" in row["rationale"]


def test_edge_genuine_requires_net_match():
    """同位还须同网：net 不匹配不命中 genuine（归责=网+位）。"""
    v = _vio("copper_edge_clearance", "铜箔离板边太近 [N1]", pos=(5.0, 5.0))
    cr = _cr(edge_violations=[{"net_id": "N2", "pos": [5.1, 5.1]}])
    row, _ = _classify_one(v, cr=cr)
    assert row["category"] == "contract-artifact"


def test_edge_genuine_far_position_not_hit():
    """位置超出 SHARED_PT_TOL_MM 容差不命中 genuine。"""
    v = _vio("copper_edge_clearance", "铜箔离板边太近 [N1]", pos=(5.0, 5.0))
    cr = _cr(edge_violations=[{"net_id": "N1", "pos": [15.0, 15.0]}])
    row, _ = _classify_one(v, cr=cr)
    assert row["category"] == "contract-artifact"


def test_edge_defensive_key_absent_is_contract_artifact():
    """edge_violations 键整体缺席（兄弟包 B 未落地/旧 check.json）→
    防御式 or [] 自然不命中 genuine，落世界模型保真差分支。"""
    v = _vio("copper_edge_clearance", "铜箔离板边太近 [N1]", pos=(5.0, 5.0))
    row, _ = _classify_one(v, cr=_cr())  # 无 edge_violations 键
    assert row["category"] == "contract-artifact"
    assert "世界模型" in row["rationale"]
    assert "0.2" in row["rationale"]     # why 逐字披露 kicad 缺省边距带


def test_edge_defective_entries_ignored():
    """edge_violations 在场但条目形态不可辨（非 dict / pos 缺失）→ 不命中。"""
    v = _vio("copper_edge_clearance", "铜箔离板边太近 [N1]", pos=(5.0, 5.0))
    cr = _cr(edge_violations=["junk", {"net_id": "N1"},
                              {"net_id": "N1", "pos": None}])
    row, _ = _classify_one(v, cr=cr)
    assert row["category"] == "contract-artifact"


def test_edge_config_gap_explicit_margin_differs():
    """板显式边距规则值 0.3 ≠ kicad 缺省 0.2 → config-gap（值源不同）。"""
    board = _board(registry=[{"compiled_rule": {"kind": "edge_clearance",
                                                "min_clearance_mm": 0.3}}])
    v = _vio("copper_edge_clearance", "铜箔离板边太近 [N1]", pos=(5.0, 5.0))
    row, _ = _classify_one(v, board=board, cr=_cr())  # 键缺席 + 显式异值
    assert row["category"] == "config-gap"
    assert "0.3" in row["rationale"] and "0.2" in row["rationale"]
    assert "值源不同" in row["rationale"]


def test_edge_config_gap_via_workspace_margin():
    """workspace 显式边距键（前向兼容防御扫描路径）同样触发 config-gap。"""
    board = _board(workspace={"x_min": 0.0, "y_min": 0.0, "x_max": 20.0,
                              "y_max": 20.0, "margin_mm": 0.5})
    v = _vio("copper_edge_clearance", "铜箔离板边太近 [N1]", pos=(5.0, 5.0))
    row, _ = _classify_one(v, board=board, cr=_cr())
    assert row["category"] == "config-gap"


def test_edge_config_gap_no_field_boards_never_hit():
    """板无显式边距字段 → config-gap 分支自然不命中（D6-4 合同原文）。"""
    v = _vio("copper_edge_clearance", "铜箔离板边太近 [N1]", pos=(5.0, 5.0))
    row, _ = _classify_one(v, cr=_cr())
    assert row["category"] == "contract-artifact"  # 非 config-gap


def test_edge_config_gap_equal_value_not_triggered():
    """显式值 == kicad 缺省 0.2（两侧同值同源）→ 不制造 config-gap。"""
    board = _board(registry=[{"compiled_rule": {"kind": "edge_clearance",
                                                "min_clearance_mm": 0.2}}])
    v = _vio("copper_edge_clearance", "铜箔离板边太近 [N1]", pos=(5.0, 5.0))
    row, _ = _classify_one(v, board=board, cr=_cr())
    assert row["category"] == "contract-artifact"


def test_edge_genuine_precedes_config_gap():
    """分支次序：edge_violations 同位同网命中优先于显式异值 config-gap。"""
    board = _board(registry=[{"compiled_rule": {"kind": "edge_clearance",
                                                "min_clearance_mm": 0.3}}])
    v = _vio("copper_edge_clearance", "铜箔离板边太近 [N1]", pos=(5.0, 5.0))
    cr = _cr(edge_violations=[{"net_id": "N1", "pos": [5.2, 5.2]}])
    row, _ = _classify_one(v, board=board, cr=cr)
    assert row["category"] == "genuine"


def test_edge_far_position_with_margin_differs_config_gap():
    """edge_violations 在场但同位未命中 + 显式异值 → 仍 config-gap。"""
    board = _board(registry=[{"compiled_rule": {"kind": "edge_clearance",
                                                "min_clearance_mm": 0.4}}])
    v = _vio("copper_edge_clearance", "铜箔离板边太近 [N1]", pos=(5.0, 5.0))
    cr = _cr(edge_violations=[{"net_id": "N1", "pos": [18.0, 18.0]}])
    row, _ = _classify_one(v, board=board, cr=cr)
    assert row["category"] == "config-gap"


# ------------------------------------------------- 既有分支回归（不变）

def test_regression_genuine_pair_clearance():
    v = _vio("clearance", "走线间距不足 网络 N1 和 N2", pos=(5.0, 5.0))
    cr = _cr(v5_violations=[{"rule": "R5",
                             "subjects": ["route:N1:p1#0", "route:N2:p2#0"],
                             "data": {}}])
    row, _ = _classify_one(v, cr=cr)
    assert row["category"] == "genuine"
    assert "两权威一致" in row["rationale"]


def test_regression_config_gap_clearance_no_v5_pair():
    """CONFIG_GAP_TYPES（clearance）分支在新增分支之后仍原样命中。"""
    v = _vio("clearance", "走线间距不足 网络 N1 和 N2", pos=(5.0, 5.0))
    row, _ = _classify_one(v)
    assert row["category"] == "config-gap"
    assert "0.2mm" in row["rationale"]


def test_regression_shorting_pad_contract_artifact():
    v = _vio("shorting_items", "短路：焊盘 [N1] 与 [N2]",
             items=[{"description": "焊盘 [N1]", "pos": {"x": 1.0, "y": 1.0}},
                    {"description": "走线 [N2]", "pos": {"x": 1.2, "y": 1.0}}])
    row, _ = _classify_one(v)
    assert row["category"] == "contract-artifact"
    assert "pad" in row["rationale"]


def test_regression_shorting_two_tracks_genuine():
    v = _vio("shorting_items", "短路：走线 [N1] 与 [N2]",
             items=[{"description": "走线 [N1]", "pos": {"x": 12.0, "y": 15.0}},
                    {"description": "走线 [N2]",
                     "pos": {"x": 12.3, "y": 15.0}}])
    row, _ = _classify_one(v)
    assert row["category"] == "genuine"
    assert "保守归真" in row["rationale"]


def test_regression_holes_colocated_and_lib_and_dangling():
    for vtype, want, kw in (
            ("holes_co_located", "contract-artifact", "钻孔同位"),
            ("lib_footprint_issues", "config-gap", "封装库"),
            ("track_dangling", "contract-artifact", "逃逸孔"),
            ("via_dangling", "contract-artifact", "逃逸孔")):
        row, _ = _classify_one(_vio(vtype, "%s违例 [N1]" % vtype,
                                    pos=(3.0, 3.0)))
        assert row["category"] == want, vtype
        assert kw in row["rationale"], vtype


def test_regression_unconnected_routed_vs_unrouted():
    unconnected = [{"description": "未连接 [N1]",
                    "items": [{"description": "焊盘 [N1]",
                               "pos": {"x": 2.0, "y": 2.0}}]}]
    rows, _ = rpb.classify_kicad_violations(
        _drc([], unconnected=unconnected), _board(), _cr())
    assert rows[0]["category"] == "contract-artifact"  # v5 已布通+feasible
    rows, _ = rpb.classify_kicad_violations(
        _drc([], unconnected=unconnected), _board(),
        _cr(routed=("N2",), feasible=True))
    assert rows[0]["category"] == "genuine"  # v5 侧未布通（保守归真）


def test_regression_unknown_type_else_genuine():
    row, _ = _classify_one(_vio("silk_over_copper", "丝印压铜 [N1]",
                                pos=(3.0, 3.0)))
    assert row["category"] == "genuine"
    assert "保守归真" in row["rationale"]


# ------------------------------------------- 结构不变 + 版本钉（验收项）

def test_rows_counts_structure_unchanged():
    """分类输出行键与 counts 结构不动（批次报告/评估器透传键零感知）。"""
    drc = _drc(
        [_vio("padstack", "焊盘 [N1]", pos=(5.0, 5.0)),
         _vio("copper_edge_clearance", "板边 [N1]", pos=(6.0, 5.0)),
         _vio("clearance", "间距 网络 N1 和 N2", pos=(7.0, 5.0))],
        unconnected=[{"description": "未连接 [N1]", "items": []}])
    rows, counts = rpb.classify_kicad_violations(drc, _board(), _cr())
    assert len(rows) == 4
    for r in rows:
        assert set(r.keys()) == ROW_KEYS
    assert set(counts.keys()) == {"violations_total", "unconnected_items",
                                  "schematic_parity", "classified"}
    assert set(counts["classified"].keys()) == set(rpb.DRC_CATEGORIES)
    assert counts["violations_total"] == 3
    assert counts["unconnected_items"] == 1
    assert counts["schematic_parity"] == 0
    assert sum(counts["classified"].values()) == 4


def test_version_bumped_to_0_5_0():
    # V5-D8 翻转披露（2026-09-22）：0.4.0→0.5.0（hole_to_hole 两类分支）；
    # V5-R8 TB2 D-8（2026-10-04）：0.5.0→0.6.0（postprocess 阶段插入，
    # STAGE_ORDER/PIPELINE_STAGES 同步）——钉值随白名单升版同步翻新
    # （R8 第 1 轮判读修复；tools/run_p5_board.py:112 现值核对）。
    assert rpb.VERSION == "0.6.0"


def test_edge_default_constant_pinned():
    """D6-3 带值：kicad-cli 生效缺省 copper_edge_clearance=0.2mm。"""
    assert rpb.KICAD_EDGE_CLEARANCE_DEFAULT_MM == 0.2
