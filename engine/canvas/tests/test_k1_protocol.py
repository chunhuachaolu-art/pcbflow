# -*- coding: utf-8 -*-
"""Lane-K1 protocol 测试: 两层拒收矩阵。

- 格式层（整批拒收 BatchReject）: v1 全部 E_* 码照合同词表 + v2 动作键集；
- 语义层（逐动作拒收，批内后续继续）: v1 V_* 码语义原样 + v2 追加码
  （V_UNKNOWN_WIDTH_CLASS / V_PLACEMENT_COLLISION 占位 / V_TUNING_KIND /
  V_TUNING_PARAMS）。
矩阵计数见 REPORT（格式层 18 例 + 语义层 16 例 ≥ 合同下限）。
"""
import json

import pytest

from canvas import protocol as cpr
from canvas.tests.test_k1_fixtures import synth_state, run_batch

SUB = {"action": "submit"}


def _parse(actions, round_no=1, **doc_extra):
    doc = {"round": round_no, "actions": actions}
    doc.update(doc_extra)
    return cpr.parse_batch(json.dumps(doc), round_no)


def _rejects(actions, code, round_no=1):
    with pytest.raises(cpr.BatchReject) as ei:
        _parse(actions, round_no=round_no)
    assert ei.value.code == code, \
        "期望 %s 实得 %s: %s" % (code, ei.value.code, ei.value.detail)
    return ei.value


# ================================================================ 格式层

def test_format_e_parse_and_not_object():
    with pytest.raises(cpr.BatchReject) as ei:
        cpr.parse_batch("this is not json", 1)
    assert ei.value.code == cpr.E_PARSE
    with pytest.raises(cpr.BatchReject) as ei:
        cpr.parse_batch("[1, 2]", 1)
    assert ei.value.code == cpr.E_NOT_OBJECT


def test_format_round_and_actions_container():
    _rejects([], cpr.E_NO_SUBMIT)                                   # 顺带: 无 submit
    with pytest.raises(cpr.BatchReject) as ei:                      # round 不符
        cpr.parse_batch(json.dumps({"round": 1, "actions": [SUB]}), 2)
    assert ei.value.code == cpr.E_ROUND_MISMATCH
    with pytest.raises(cpr.BatchReject) as ei:
        cpr.parse_batch(json.dumps({"round": 1, "actions": {"a": 1}}), 1)
    assert ei.value.code == cpr.E_ACTIONS_NOT_LIST
    _rejects([[1, 2]], cpr.E_ACTION_NOT_OBJECT)


def test_format_unknown_action_missing_extra_key():
    _rejects([{"action": "teleport"}, SUB], cpr.E_UNKNOWN_ACTION)
    _rejects([{"action": "route", "net_id": "NET-A",
               "waypoints": [[4, 4], [20, 4]]}, SUB],              # 缺 layer
             cpr.E_MISSING_KEY)
    _rejects([{"action": "route", "net_id": "NET-A",
               "waypoints": [[4, 4], [20, 4]], "layer": "F.Cu",
               "width": 9}, SUB],                                   # 合同外键
             cpr.E_EXTRA_KEY)
    _rejects([{"action": "flip", "partition_id": "PA", "why": 1}, SUB],
             cpr.E_EXTRA_KEY)
    _rejects([{"action": "tuning", "net_id": "NET-A", "group_id": "g",
               "kind": "detour"}, SUB],                             # 缺 params
             cpr.E_MISSING_KEY)


def test_format_grid_discipline():
    _rejects([{"action": "via", "net_id": "NET-A", "grid": [4]}, SUB],
             cpr.E_NON_INTEGER_GRID)                                # 非二元
    _rejects([{"action": "via", "net_id": "NET-A", "grid": [True, 4]}, SUB],
             cpr.E_NON_INTEGER_GRID)                                # bool 冒充
    _rejects([{"action": "via", "net_id": "NET-A", "grid": [4.0, 4]}, SUB],
             cpr.E_FLOAT_COORD)                                     # 浮点坐标
    _rejects([{"action": "via", "net_id": "NET-A", "grid": ["4", 4]}, SUB],
             cpr.E_FLOAT_COORD)                                     # 字符串坐标
    _rejects([{"action": "move", "partition_id": "PA",
               "target": [1.5, 2]}, SUB], cpr.E_FLOAT_COORD)
    _rejects([{"action": "route", "net_id": "NET-A",
               "waypoints": [[4, 4], [3]], "layer": "F.Cu"}, SUB],
             cpr.E_NON_INTEGER_GRID)                                # waypoint 非二元
    _rejects([{"action": "route", "net_id": "NET-A",
               "waypoints": "from A to B", "layer": "F.Cu"}, SUB],
             cpr.E_NON_INTEGER_GRID)                                # 非数组折算


def test_format_waypoints_submit_trailing_ripup():
    _rejects([{"action": "route", "net_id": "NET-A",
               "waypoints": [[4, 4]], "layer": "F.Cu"}, SUB],
             cpr.E_WAYPOINTS_TOO_FEW)
    _rejects([SUB,
              {"action": "via", "net_id": "NET-A", "grid": [4, 4]}],
             cpr.E_TRAILING_ACTION)
    _rejects([{"action": "ripup", "net_id": "NET-A",
               "shape_id": "seg:NET-A:0"}, SUB], cpr.E_RIPUP_TARGET)
    _rejects([{"action": "ripup"}, SUB], cpr.E_RIPUP_TARGET)


def test_format_v2_turns_and_params():
    _rejects([{"action": "rotate", "partition_id": "PA", "turns": 0}, SUB],
             cpr.E_GRID_OUT_OF_BOUNDS)                              # turns 越界
    _rejects([{"action": "rotate", "partition_id": "PA", "turns": 4}, SUB],
             cpr.E_GRID_OUT_OF_BOUNDS)
    _rejects([{"action": "rotate", "partition_id": "PA", "turns": "2"}, SUB],
             cpr.E_NON_INTEGER_GRID)
    _rejects([{"action": "tuning", "net_id": "NET-A", "group_id": "g",
               "kind": "detour", "params": [1, 2]}, SUB],
             cpr.E_MISSING_KEY)                                     # params 非对象折算


def test_format_keysets_all_nine_actions():
    """九动作 REQUIRED/ALLOWED 严格照合同 §2: 每动作的合法批可解析。"""
    acts = _parse([
        {"action": "route", "net_id": "NET-A",
         "waypoints": [[4, 4], [20, 4]], "layer": "F.Cu"},
        {"action": "via", "net_id": "NET-A", "grid": [12, 4]},
        {"action": "ripup", "net_id": "NET-A"},
        {"action": "ripup", "shape_id": "seg:NET-A:0"},
        {"action": "width_class", "net_id": "NET-A", "class": "max"},
        {"action": "move", "partition_id": "PA", "target": [8, 8]},
        {"action": "rotate", "partition_id": "PA", "turns": 3},
        {"action": "flip", "partition_id": "PA"},
        {"action": "tuning", "net_id": "NET-A", "group_id": "g",
         "kind": "accordion", "params": {"amp_mm": 1.0, "count": 2}},
        SUB,
    ])
    assert len(acts) == 10
    # 逐动作缺必含键各拒一次（表格右列全集的负例抽查）
    _rejects([{"action": "via", "grid": [1, 1]}, SUB], cpr.E_MISSING_KEY)
    _rejects([{"action": "width_class", "net_id": "NET-A"}, SUB],
             cpr.E_MISSING_KEY)
    _rejects([{"action": "move", "target": [1, 1]}, SUB], cpr.E_MISSING_KEY)
    _rejects([{"action": "rotate", "partition_id": "PA"}, SUB],
             cpr.E_MISSING_KEY)
    _rejects([{"action": "flip"}, SUB], cpr.E_MISSING_KEY)


# ================================================================ 语义层

def _codes(st, actions, round_no=1):
    return [(r["action"], r["accepted"], r.get("code")) for r in
            run_batch(st, actions, round_no=round_no)]


def test_semantic_route_codes():
    st = synth_state()
    got = _codes(st, [
        {"action": "route", "net_id": "NOPE",
         "waypoints": [[4, 4], [6, 4]], "layer": "F.Cu"},           # 未知网
        {"action": "route", "net_id": "NET-A",
         "waypoints": [[4, 4], [6, 4]], "layer": "In1.Cu"},         # 未知层
        {"action": "route", "net_id": "NET-A",
         "waypoints": [[4, 4], [99, 99]], "layer": "F.Cu"},         # 越界
        {"action": "route", "net_id": "NET-A",
         "waypoints": [[4, 4], [4, 4]], "layer": "F.Cu"},           # 零长自绞
        {"action": "route", "net_id": "NET-A",
         "waypoints": [[6, 6], [8, 6]], "layer": "F.Cu"},           # 两端不附着
        {"action": "route", "net_id": "NET-B",                       # R5 贴 pad
         "waypoints": [[4, 16], [4, 5], [20, 5], [20, 16]], "layer": "F.Cu"},
        {"action": "route", "net_id": "NET-B",                       # 板边带
         "waypoints": [[4, 16], [4, 20], [20, 20], [20, 16]],
         "layer": "F.Cu"},
        {"action": "route", "net_id": "NET-C",                       # 板固孔
         "waypoints": [[26, 10], [2, 10]], "layer": "F.Cu"},
        SUB,
    ])
    expect = [
        ("route", False, "E_UNKNOWN_NET"),
        ("route", False, "E_UNKNOWN_LAYER"),
        ("route", False, "E_GRID_OUT_OF_BOUNDS"),
        ("route", False, "V_SELF_SNAG"),
        ("route", False, "V_ENDPT_NOT_ATTACHED"),
        ("route", False, "V_CLEARANCE"),
        ("route", False, "V_EDGE"),
        ("route", False, "V_HOLE_TRACK"),
        ("submit", True, None),
    ]
    assert got == expect
    assert not st.segs                              # 全拒 → 零落铜


def test_semantic_route_accept_and_batch_cross_layer_chain():
    st = synth_state()
    got = _codes(st, [
        {"action": "via", "net_id": "NET-A", "grid": [12, 4]},      # 先于段（批内视图）
        {"action": "route", "net_id": "NET-A",
         "waypoints": [[4, 4], [12, 4]], "layer": "F.Cu"},          # 尾=via 格点
        {"action": "route", "net_id": "NET-A",
         "waypoints": [[12, 4], [20, 4]], "layer": "B.Cu"},         # 首=via 格点
        SUB,
    ])
    assert got == [("via", True, None), ("route", True, None),
                   ("route", True, None), ("submit", True, None)]
    assert st.connectivity["NET-A"] is True
    # 同链无 via → 附着违例（批内视图不含 via 时）
    st2 = synth_state()
    got2 = _codes(st2, [
        {"action": "route", "net_id": "NET-A",
         "waypoints": [[4, 4], [12, 4]], "layer": "F.Cu"},
        {"action": "route", "net_id": "NET-A",
         "waypoints": [[12, 4], [20, 4]], "layer": "B.Cu"},
        SUB,
    ])
    assert got2[0][2] == "V_ENDPT_NOT_ATTACHED"
    assert got2[1][2] == "V_ENDPT_NOT_ATTACHED"


def test_semantic_via_codes():
    st = synth_state()
    apply = lambda acts: run_batch(st, acts)     # noqa: E731
    got = [(r["accepted"], r.get("code")) for r in apply([
        {"action": "via", "net_id": "NOPE", "grid": [12, 4]},       # 未知网
        {"action": "via", "net_id": "NET-A", "grid": [99, 4]},      # 越界
        {"action": "via", "net_id": "NET-A", "grid": [12, 4]},      # 不在路径上
        SUB,
    ])]
    assert got == [(False, "E_UNKNOWN_NET"), (False, "E_GRID_OUT_OF_BOUNDS"),
                   (False, "V_VIA_OFF_PATH"), (True, None)]
    # 落段后: 重复 via / 合法 via
    got = [(r["accepted"], r.get("code")) for r in apply([
        {"action": "route", "net_id": "NET-A",
         "waypoints": [[4, 4], [12, 4], [20, 4]], "layer": "F.Cu"},
        {"action": "via", "net_id": "NET-A", "grid": [12, 4]},
        {"action": "via", "net_id": "NET-A", "grid": [12, 4]},      # 重复
        SUB,
    ])]
    assert got == [(True, None), (True, None), (False, "V_DUPLICATE_VIA"),
                   (True, None)]


def test_semantic_via_hole_face_big_via_model():
    # via_model 加大（r=0.5）→ (16,10) 距孔心 1.0: track 面 ≥0.8 合法、
    # via 面 <1.15 拒收（两阈值不同源值各得其所）
    st = synth_state(via_model={"drill_mm": 0.6, "annular_mm": 0.2})
    got = [(r["accepted"], r.get("code")) for r in run_batch(st, [
        {"action": "route", "net_id": "NET-C",
         "waypoints": [[26, 10], [16, 10], [16, 13], [4, 13], [2, 10]],
         "layer": "F.Cu"},
        {"action": "via", "net_id": "NET-C", "grid": [16, 10]},
        SUB,
    ])]
    assert got[0] == (True, None)
    assert got[1] == (False, "V_HOLE_VIA")
    # 缺省 via_model（r=0.3）: 1.0 ≥ 0.95 擦边合规
    st2 = synth_state()
    got2 = [(r["accepted"], r.get("code")) for r in run_batch(st2, [
        {"action": "route", "net_id": "NET-C",
         "waypoints": [[26, 10], [16, 10], [16, 13], [4, 13], [2, 10]],
         "layer": "F.Cu"},
        {"action": "via", "net_id": "NET-C", "grid": [16, 10]},
        SUB,
    ])]
    assert got2[0][0] is True and got2[1][0] is True


def test_semantic_ripup_codes():
    st = synth_state()
    got = [(r["accepted"], r.get("code")) for r in run_batch(st, [
        {"action": "ripup", "net_id": "NOPE"},                      # 未知网
        {"action": "ripup", "net_id": "NET-A"},                     # 无铜可拆
        {"action": "ripup", "shape_id": "seg:NET-A:9"},             # 未知 shape
        SUB,
    ])]
    assert got == [(False, "E_UNKNOWN_NET"), (False, "V_RIPUP_UNKNOWN"),
                   (False, "V_RIPUP_UNKNOWN"), (True, None)]
    got = [(r["accepted"], r.get("code")) for r in run_batch(st, [
        {"action": "route", "net_id": "NET-A",
         "waypoints": [[4, 4], [20, 4]], "layer": "F.Cu"},
        {"action": "ripup", "shape_id": "seg:NET-A:0"},
        {"action": "ripup", "shape_id": "seg:NET-A:0"},             # 已不在场
        SUB,
    ], round_no=2)]
    assert got == [(True, None), (True, None), (False, "V_RIPUP_UNKNOWN"),
                   (True, None)]


def test_semantic_width_class_codes():
    st = synth_state()
    got = [(r["accepted"], r.get("code")) for r in run_batch(st, [
        {"action": "width_class", "net_id": "NOPE", "class": "max"},
        {"action": "width_class", "net_id": "NET-A", "class": "fat"},
        {"action": "width_class", "net_id": "NET-A", "class": "max"},
        SUB,
    ])]
    assert got == [(False, "E_UNKNOWN_NET"),
                   (False, "V_UNKNOWN_WIDTH_CLASS"), (True, None),
                   (True, None)]          # 末位=自动补的 submit
    assert st.widths["NET-A"] == "max"


def test_semantic_placement_placeholder_rejects():
    """move/rotate/flip 经 placecheck 真实判定（lane-m4 §5 接线契约，
    编排体 2026-09-25 收口）: 合成板 PA 包络大——move 目标使包络越框
    拒收 V_PLACEMENT_EDGE、rotate 原位合法接受落覆盖、flip 承袭当前
    覆盖再翻转（相对动作绝对落盘=merge_candidate 完整覆盖）。"""
    st = synth_state()
    got = _codes(st, [
        {"action": "move", "partition_id": "PA", "target": [8, 8]},  # 越框
        {"action": "move", "partition_id": "PA", "target": [99, 8]},  # 越界真判
        {"action": "rotate", "partition_id": "PA", "turns": 2},
        {"action": "flip", "partition_id": "PA"},
        SUB,
    ])
    assert got == [
        ("move", False, "V_PLACEMENT_EDGE"),
        ("move", False, "E_GRID_OUT_OF_BOUNDS"),
        ("rotate", True, None),
        ("flip", True, None),
        ("submit", True, None),
    ]
    assert st.placements == {
        "PA": {"move": None, "rotate": 2, "flip": True}}


def test_semantic_tuning_codes():
    st = synth_state()
    got = [(r["accepted"], r.get("code")) for r in run_batch(st, [
        {"action": "tuning", "net_id": "NOPE", "group_id": "g",
         "kind": "detour", "params": {"offset_mm": 1.0}},
        {"action": "tuning", "net_id": "NET-A", "group_id": "g",
         "kind": "zigzag", "params": {"offset_mm": 1.0}},           # kind 越枚举
        {"action": "tuning", "net_id": "NET-A", "group_id": "g",
         "kind": "detour", "params": {"offset_mm": 0.0}},           # 参数越界
        {"action": "tuning", "net_id": "NET-A", "group_id": "g",
         "kind": "detour", "params": {"amp_mm": 1.0}},              # 键集不符
        {"action": "tuning", "net_id": "NET-A", "group_id": "g",
         "kind": "detour", "params": {"offset_mm": "far"}},         # 非数
        {"action": "tuning", "net_id": "NET-A", "group_id": "g",
         "kind": "accordion", "params": {"amp_mm": 1.0, "count": 0}},
        {"action": "tuning", "net_id": "NET-A", "group_id": "g",
         "kind": "detour", "params": {"offset_mm": 1.0}},           # 网无基线段
        SUB,
    ])]
    codes = [g[1] for g in got[:-1]]
    assert codes == ["E_UNKNOWN_NET", "V_TUNING_KIND", "V_TUNING_PARAMS",
                     "V_TUNING_PARAMS", "V_TUNING_PARAMS", "V_TUNING_PARAMS",
                     "V_TUNING_PARAMS"]
    # 落段后 tuning 可接受（基线=网首段）
    got2 = [(r["accepted"], r.get("code")) for r in run_batch(st, [
        {"action": "route", "net_id": "NET-A",
         "waypoints": [[4, 4], [20, 4]], "layer": "F.Cu"},
        {"action": "tuning", "net_id": "NET-A", "group_id": "g",
         "kind": "detour", "params": {"offset_mm": 1.0}},
        SUB,
    ], round_no=2)]
    assert got2 == [(True, None), (True, None), (True, None)]
    assert list(st.tunings) == ["tun:NET-A:g:0"]
    assert st.tunings["tun:NET-A:g:0"]["grid"] == st.segs["seg:NET-A:0"]["grid"]


def test_semantic_rejection_continues_batch_and_histogram_source():
    """语义层逐动作拒收（批内后续继续）; results 即拒收直方图数据源。"""
    st = synth_state()
    results = run_batch(st, [
        {"action": "route", "net_id": "NET-A",
         "waypoints": [[6, 6], [8, 6]], "layer": "F.Cu"},           # 拒
        {"action": "route", "net_id": "NET-A",
         "waypoints": [[4, 4], [20, 4]], "layer": "F.Cu"},          # 收
        SUB,
    ])
    assert [r["accepted"] for r in results] == [False, True, True]
    assert results[0]["code"] == "V_ENDPT_NOT_ATTACHED"
    assert results[0]["detail"]
    assert results[1]["shape_id"] == "seg:NET-A:0"   # 拒收不占 seq
    hist = {}
    for r in results:
        if not r["accepted"]:
            hist[r["code"]] = hist.get(r["code"], 0) + 1
    assert hist == {"V_ENDPT_NOT_ATTACHED": 1}
