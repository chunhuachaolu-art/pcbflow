# -*- coding: utf-8 -*-
"""Lane-M2X 动作 fail-closed 矩阵: runner 生成动作（及其确定性变造）经
canvas.protocol parse/apply_batch 的拒收路径逐路一测。

- 语义层（apply_batch 逐动作拒收）: 越界/未知网/未知层/附着失败/自缠/
  触孔(track)/via 脱径/via 重复/via 触孔/ripup 目标不存在（shape 与 net
  两寻址）/宽度类非法——每路断言拒收码+拒收后画板态字节不变（fail-closed
  不留半落态）。
- 格式层（parse_batch 整批拒收）: 浮点坐标/单 waypoint/ripup 双键/无
  submit。
- runner 级 fail-closed: 非法 budget ValueError; 单层互锁板 unresolved
  如实上报且摘要 canonical 可序列化。
计数: 语义层 13 + 格式层 4 + runner 级 4 ≥ 合同下限 10。
"""
import json

import pytest

from canvas import protocol as cpr
from canvas import validate as cval
from canvas.runners.m2 import plan_actions, run_m2
from canvas.state import state_sha256
from canvas.tests.test_k1_fixtures import synth_state, run_batch
from canvas.tests.test_m2_multilayer import hole_edge_state, ripup_state


def _apply_one(st, action):
    return cpr.apply_batch(st, [action, {"action": "submit"}])


def _rejected_with(st, action, code):
    """语义层单动作拒收: 断言码 + 拒收前后画板态字节等。"""
    before = state_sha256(st)
    results = _apply_one(st, action)
    bad = [r for r in results if not r["accepted"]]
    assert len(bad) == 1, "应恰一拒收: %r" % (results,)
    assert bad[0]["code"] == code, \
        "期望 %s 实得 %s (%s)" % (code, bad[0]["code"], bad[0]["detail"])
    assert state_sha256(st) == before, "拒收不得改动画板态"


# ================================================================ 语义层

def test_sem_route_grid_out_of_bounds():
    st = synth_state()
    _rejected_with(st, {"action": "route", "net_id": "NET-A",
                        "waypoints": [[4, 4], [50, 4]], "layer": "F.Cu"},
                   cpr.E_GRID_OUT_OF_BOUNDS)


def test_sem_route_unknown_net():
    st = synth_state()
    _rejected_with(st, {"action": "route", "net_id": "NET-ZZZ",
                        "waypoints": [[4, 4], [20, 4]], "layer": "F.Cu"},
                   cpr.E_UNKNOWN_NET)


def test_sem_route_unknown_layer():
    st = synth_state()
    _rejected_with(st, {"action": "route", "net_id": "NET-A",
                        "waypoints": [[4, 4], [20, 4]], "layer": "In9.Cu"},
                   cpr.E_UNKNOWN_LAYER)


def test_sem_route_endpoint_not_attached():
    st = synth_state()
    # 起终点都非端点锚亦非本网 via 格点（悬空中段）
    _rejected_with(st, {"action": "route", "net_id": "NET-A",
                        "waypoints": [[5, 5], [6, 6]], "layer": "F.Cu"},
                   cpr.V_ENDPT_NOT_ATTACHED)


def test_sem_route_self_snag():
    st = synth_state()
    _rejected_with(st, {"action": "route", "net_id": "NET-A",
                        "waypoints": [[4, 4], [4, 4]], "layer": "F.Cu"},
                   cpr.V_SELF_SNAG)


def test_sem_route_through_hole():
    st = synth_state()
    # NET-C 跨板直连必经板固孔 (7,5)（attach 双端锚合法、几何触孔拒收）
    _rejected_with(st, {"action": "route", "net_id": "NET-C",
                        "waypoints": [[6, 10], [22, 10]], "layer": "F.Cu"},
                   cpr.V_HOLE_TRACK)


def test_sem_route_clearance_collision():
    st = synth_state()
    run_batch(st, [{"action": "route", "net_id": "NET-A",
                    "waypoints": [[4, 4], [20, 4]], "layer": "F.Cu"}])
    # NET-B 平行走廊行 j=5（表面间隙 0.2 < R5 0.5）——跨网铜碰撞归责路径
    _rejected_with(st, {"action": "route", "net_id": "NET-B",
                        "waypoints": [[4, 16], [4, 5], [20, 5], [20, 16]],
                        "layer": "F.Cu"},
                   cpr.V_CLEARANCE)


def test_sem_via_off_path():
    st = synth_state()
    _rejected_with(st, {"action": "via", "net_id": "NET-A",
                        "grid": [10, 5]},
                   cpr.V_VIA_OFF_PATH)


def test_sem_via_duplicate():
    st = synth_state()
    run_batch(st, [{"action": "route", "net_id": "NET-A",
                    "waypoints": [[4, 4], [20, 4]], "layer": "F.Cu"},
                   {"action": "via", "net_id": "NET-A", "grid": [12, 4]}])
    _rejected_with(st, {"action": "via", "net_id": "NET-A",
                        "grid": [12, 4]},
                   cpr.V_DUPLICATE_VIA)


def test_sem_via_on_hole_positive():
    """孔环带板: 合法走线上的 via 触孔（0.8≤d<0.95 环带正例）。"""
    st = hole_edge_state()
    run_batch(st, [{"action": "route", "net_id": "NET-X",
                    "waypoints": [[10, 8], [10, 10]], "layer": "F.Cu"}])
    _rejected_with(st, {"action": "via", "net_id": "NET-X",
                        "grid": [10, 10]},
                   cpr.V_HOLE_VIA)


def test_sem_ripup_shape_unknown():
    st = synth_state()
    _rejected_with(st, {"action": "ripup", "shape_id": "seg:NET-A:999"},
                   cpr.V_RIPUP_UNKNOWN)


def test_sem_ripup_net_without_copper():
    st = synth_state()
    _rejected_with(st, {"action": "ripup", "net_id": "NET-A"},
                   cpr.V_RIPUP_UNKNOWN)


def test_sem_width_class_unknown_vocab():
    st = synth_state()
    _rejected_with(st, {"action": "width_class", "net_id": "NET-A",
                        "class": "fat"},
                   cpr.V_UNKNOWN_WIDTH_CLASS)


def test_sem_width_class_unknown_net():
    st = synth_state()
    _rejected_with(st, {"action": "width_class", "net_id": "NET-ZZZ",
                        "class": "min"},
                   cpr.E_UNKNOWN_NET)


# ================================================================ 格式层

def _parse_reject(actions, code):
    doc = json.dumps({"round": 1, "actions": actions})
    with pytest.raises(cpr.BatchReject) as ei:
        cpr.parse_batch(doc, 1)
    assert ei.value.code == code, \
        "期望 %s 实得 %s: %s" % (code, ei.value.code, ei.value.detail)


def test_format_float_coord_rejected():
    _parse_reject([{"action": "route", "net_id": "NET-A",
                    "waypoints": [[4.0, 4], [20, 4]], "layer": "F.Cu"},
                   {"action": "submit"}], cpr.E_FLOAT_COORD)


def test_format_waypoints_too_few():
    _parse_reject([{"action": "route", "net_id": "NET-A",
                    "waypoints": [[4, 4]], "layer": "F.Cu"},
                   {"action": "submit"}], cpr.E_WAYPOINTS_TOO_FEW)


def test_format_ripup_target_both_keys():
    _parse_reject([{"action": "ripup", "net_id": "NET-A",
                    "shape_id": "seg:NET-A:0"}, {"action": "submit"}],
                  cpr.E_RIPUP_TARGET)


def test_format_no_submit():
    _parse_reject([{"action": "route", "net_id": "NET-A",
                    "waypoints": [[4, 4], [20, 4]], "layer": "F.Cu"}],
                  cpr.E_NO_SUBMIT)


# ================================================================ runner 级

def test_runner_budget_fail_closed():
    st = synth_state()
    for bad in ({"max_rounds": 0, "per_net_retry": 3},
                {"max_rounds": 3},
                {"max_rounds": 3, "per_net_retry": True},
                {"max_rounds": 2.5, "per_net_retry": 3},
                {"max_rounds": 1, "per_net_retry": 1, "extra": 1},
                ["max_rounds"]):
        with pytest.raises(ValueError):
            plan_actions(st, bad)
        with pytest.raises(ValueError):
            run_m2(st, bad)


def test_runner_unresolved_reported_honestly():
    """单层互锁板: 确定性乒乓终态 1 网未连通——如实进 unresolved_nets,
    摘要仍 canonical 可序列化、无静默拒收。"""
    from v5.canonical import canonical_roundtrip
    st = ripup_state()
    summary = run_m2(st)
    assert summary["unresolved_nets"] == ["NET-A"]
    assert summary["nets_connected_after"] == ["NET-B"]
    assert summary["rejected_count"] == 0
    canonical_roundtrip(summary)


def test_runner_reject_stream_reported_not_hidden():
    """规划全验故正常路径零拒收; 人为向批内塞一个非法动作（模拟席位侧
    变造）→ apply 拒收如实进 rejected 直方图, 其余动作照常应用。"""
    st = synth_state()
    planned = plan_actions(st)
    assert planned, "synth 板应有规划动作"
    poisoned = list(planned[:2]) + \
        [{"action": "route", "net_id": "NET-ZZZ",
          "waypoints": [[1, 1], [2, 2]], "layer": "F.Cu"}] + \
        planned[2:] + [{"action": "submit"}]
    results = cpr.apply_batch(st, poisoned)
    bad = [r for r in results if not r["accepted"]]
    assert len(bad) == 1
    assert bad[0]["code"] == cpr.E_UNKNOWN_NET


def test_runner_idempotent_second_run_empty_plan():
    """已连通板再跑: 空规划、零应用、终态哈希不变（幂等不重复落铜）。"""
    st = synth_state()
    s1 = run_m2(st)
    sha_after_first = s1["state_sha256_after"]
    s2 = run_m2(st)
    assert s2["planned_action_count"] == 0
    assert s2["applied_count"] == 0
    assert s2["state_sha256_after"] == sha_after_first
    assert s2["unresolved_nets"] == s1["unresolved_nets"] == []
