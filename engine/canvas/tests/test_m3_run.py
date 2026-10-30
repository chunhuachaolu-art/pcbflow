# -*- coding: utf-8 -*-
"""Lane-M3 修整 runner 测试: 每批连通 100% 不变量（含注入回退）/ v5.drc
绑定一致（修整终态 validate_full 零新增违例; hole/edge 绑定断言）/
确定性双跑字节等 / totals 对照与摘要可序列化。"""
import json

import pytest

from v5 import drc
from v5.canonical import canonical_json

from canvas import state as cst
from canvas import validate as cva
from canvas.runners import m3
from canvas.tests.test_k1_fixtures import (
    apply_ok, real_state, synth_state)


# ---------------------------------------------------------------- 夹具

def synth_full_state():
    """合成微板全布态: 三网全连通（NET-C 双分区绕板固孔）。"""
    st = synth_state()
    apply_ok(st, [
        {"action": "route", "net_id": "NET-A",
         "waypoints": [[4, 4], [20, 4]], "layer": "F.Cu"},
        {"action": "route", "net_id": "NET-B",
         "waypoints": [[4, 16], [20, 16]], "layer": "F.Cu"},
        {"action": "route", "net_id": "NET-C",
         "waypoints": [[2, 10], [6, 10]], "layer": "F.Cu"},
        {"action": "via", "net_id": "NET-C", "grid": [6, 10]},
        {"action": "route", "net_id": "NET-C",
         "waypoints": [[6, 10], [12, 10], [12, 6], [16, 6], [16, 10],
                       [22, 10]], "layer": "F.Cu"},
        {"action": "via", "net_id": "NET-C", "grid": [22, 10]},
        {"action": "route", "net_id": "NET-C",
         "waypoints": [[22, 10], [26, 10]], "layer": "F.Cu"},
    ])
    return st


def synth_merge_state():
    """NET-A 两段同层共线衔接于 via (12,4)（冗余过孔消减靶）。"""
    st = synth_state()
    apply_ok(st, [
        {"action": "route", "net_id": "NET-A",
         "waypoints": [[4, 4], [12, 4]], "layer": "F.Cu"},
        {"action": "via", "net_id": "NET-A", "grid": [12, 4]},
        {"action": "route", "net_id": "NET-A",
         "waypoints": [[12, 4], [20, 4]], "layer": "F.Cu"},
    ])
    return st


def synth_spur_state():
    """NET-B 主路 + 协议合法死枝（尾 via 落地）。"""
    st = synth_state()
    apply_ok(st, [
        {"action": "route", "net_id": "NET-B",
         "waypoints": [[4, 16], [20, 16]], "layer": "F.Cu"},
        {"action": "via", "net_id": "NET-B", "grid": [12, 16]},
        {"action": "route", "net_id": "NET-B",
         "waypoints": [[12, 16], [12, 12]], "layer": "F.Cu"},
        {"action": "via", "net_id": "NET-B", "grid": [12, 12]},
    ])
    return st


def real_routed_state():
    """真板已布态: D2 三段链（段1/2 共线衔接 via 27,35）+ D1 主路+死枝
    （动作形态复用 test_k1_instantiate.py:117 的 Net-(D2-Pad1) 合法批）。"""
    st = real_state()
    apply_ok(st, [
        {"action": "route", "net_id": "Net-(D2-Pad1)",
         "waypoints": [[27, 31], [27, 35]], "layer": "F.Cu"},
        {"action": "via", "net_id": "Net-(D2-Pad1)", "grid": [27, 35]},
        {"action": "route", "net_id": "Net-(D2-Pad1)",
         "waypoints": [[27, 35], [27, 39]], "layer": "F.Cu"},
        {"action": "via", "net_id": "Net-(D2-Pad1)", "grid": [27, 39]},
        # V6-ANCHOR-R1 口径 v2: 原西进尾锚走法 [[27,39],[52,39],[52,25],[55,25]]
        # 在真端点绑定几何下侵 pad:PT-Net-_D1-Pad1_:1 gap=0.2934（旧口径
        # anchor 几何 0.8172=假接受实锤），改东进走廊（v2 真几何合法）。
        {"action": "route", "net_id": "Net-(D2-Pad1)",
         "waypoints": [[27, 39], [58, 39], [58, 25], [56, 25], [55, 25]],
         "layer": "F.Cu"},
        # V6-ANCHOR-R1 口径 v2 + D-ORACLE-1 修复后真几何全批复验: 原 D1 主路
        # col-58 竖腿距 pad:PT-Net-_D2-Pad1_:1 真值 0.492<0.5（被旧剪枝误剪
        # 隐藏）、原 D2 尾段西走侵 D1 pad 真值 0.273——两条均为双缺陷假接受。
        # 改 D1 西走 col-52（真距 0.908）/D2 东走（见上段）, via/spur 随移。
        {"action": "route", "net_id": "Net-(D1-Pad1)",
         "waypoints": [[27, 4], [27, 8], [52, 8], [52, 36], [54, 36]],
         "layer": "F.Cu"},
        {"action": "via", "net_id": "Net-(D1-Pad1)", "grid": [52, 20]},
        {"action": "route", "net_id": "Net-(D1-Pad1)",
         "waypoints": [[52, 20], [64, 20]], "layer": "F.Cu"},
        {"action": "via", "net_id": "Net-(D1-Pad1)", "grid": [64, 20]},
    ])
    return st


def _keyset(rep):
    return {(v.rule, str(v.subject_a), str(v.subject_b),
             json.dumps(v.data, sort_keys=True))
            for v in rep.violations}


# ---------------------------------------------------- 连通不变量（≥2）

def test_connectivity_invariant_end_to_end():
    """修整前后+逐批: 已连通网全程保持（三夹具: 全布/共线合并/死枝）。"""
    for st in (synth_full_state(), synth_merge_state(), synth_spur_state()):
        conn_before = dict(st.connectivity)
        summary = m3.run_m3(st, None)
        assert summary["connectivity"]["preserved"] is True
        for net, ok in conn_before.items():
            if ok:
                assert st.connectivity[net] is True
        for rec in summary["batches"]:            # 逐批断言在场且全过
            assert rec["connectivity_ok"] is True
            assert rec["rolled_back"] is False
        assert summary["connectivity"]["routed_after_n"] == \
            summary["connectivity"]["routed_before_n"]


def test_connectivity_gate_rollback_on_injected_break():
    """逐批连通门注入: 拆活段批（陈旧账本形态）→ 回退+unresolved+态字节复原。"""
    st = synth_spur_state()
    sha0 = cst.state_sha256(st)
    rec = m3._apply_gated(
        st, "dead_branch",
        [{"action": "ripup", "shape_id": "seg:NET-B:0"},   # 活段（主路）
         {"action": "submit"}], 0)
    assert rec["connectivity_ok"] is False
    assert rec["rolled_back"] is True
    assert len(rec["unresolved"]) == 1
    assert rec["unresolved"][0]["reason"] == "connectivity_invariant"
    assert cst.state_sha256(st) == sha0          # 快照还原=字节复原
    assert st.connectivity["NET-B"] is True


def test_unrouted_to_routed_improvement_allowed():
    """不变量只保护修整前已连通网: 死枝为唯一缺陷的未通网 → 清理后转连通。"""
    st = synth_state()
    apply_ok(st, [{"action": "route", "net_id": "NET-B",
                   "waypoints": [[4, 16], [20, 16]], "layer": "F.Cu"}])
    st.add_seg("NET-B", "PB", "F.Cu", [[8, 16], [8, 12]], "min")  # 悬尾死枝
    st.recompute_connectivity()
    assert st.connectivity["NET-B"] is False
    summary = m3.run_m3(st, {"categories": ["dead_branch"]})
    assert summary["connectivity"]["preserved"] is True
    assert summary["connectivity"]["routed_after_n"] == \
        summary["connectivity"]["routed_before_n"] + 1
    assert st.connectivity["NET-B"] is True


# ---------------------------------------------------- v5.drc 绑定（≥8）

def test_drc_binding_zero_new_violations_synth():
    st = synth_full_state()
    before = _keyset(cva.validate_full(st))
    assert isinstance(cva.validate_full(st), drc.DRCReport)
    summary = m3.run_m3(st, None)
    after = _keyset(cva.validate_full(st))
    assert after <= before                       # 零新增（子集）
    assert summary["drc"]["new_violation_keys_n"] == 0


def test_drc_binding_zero_new_violations_real():
    st = real_routed_state()
    before = _keyset(cva.validate_full(st))
    assert len(before) >= 1                      # 板固有 pad 违例在场（基线）
    summary = m3.run_m3(st, None)
    after = _keyset(cva.validate_full(st))
    assert after <= before
    assert summary["drc"]["new_violation_keys_n"] == 0
    # 板固有违例不归责修整（差集法同源纪律）
    assert before - after >= set()


def test_drc_binding_per_batch_all_clean():
    for st in (synth_full_state(), synth_merge_state(), real_routed_state()):
        summary = m3.run_m3(st, None)
        assert all(r["drc_ok"] for r in summary["batches"])
        assert all(not r["rolled_back"] for r in summary["batches"])


def test_drc_binding_no_new_hole_rule():
    """修整不引入 hole 违例（hole_to_hole 绑定: 死枝贴近板固孔清理后无新增）。"""
    st = synth_full_state()
    # 贴孔死枝: NET-C 主链边 via (16,10) 上引、逼近板固孔 (7,5)mm=(14,10)
    st.add_via("NET-C", [16, 10])
    st.add_seg("NET-C", "PC1", "F.Cu", [[16, 10], [15, 10]], "min")
    st.recompute_connectivity()
    rules_before = {v.rule for v in cva.validate_full(st).violations}
    summary = m3.run_m3(st, None)
    rules_after = {v.rule for v in cva.validate_full(st).violations}
    assert rules_after <= rules_before           # 规则级零新增
    assert "hole_to_hole" not in (rules_after - rules_before)
    assert "edge_clearance" not in (rules_after - rules_before)
    assert summary["drc"]["new_violation_keys_n"] == 0


def test_drc_binding_cleanup_only_reduces_violations():
    """修整只减不增: 手放贴边死段（y=10 顶格，edge 违例在场）→ 清理后
    违例计数下降。"""
    st = synth_spur_state()
    st.add_seg("NET-B", "PB", "F.Cu", [[4, 20], [20, 20]], "min")  # 顶边死段
    st.recompute_connectivity()
    rep_before = cva.validate_full(st)
    edge_before = [v for v in rep_before.violations
                   if v.rule == "edge_clearance"]
    assert edge_before                           # 死段触边（基线在场）
    summary = m3.run_m3(st, None)
    rep_after = cva.validate_full(st)
    assert len(rep_after.violations) < len(rep_before.violations)
    assert not [v for v in rep_after.violations if v.rule == "edge_clearance"]


def test_drc_gate_rollback_on_injected_width_widening():
    """DRC 门注入: 板固孔近旁网强升 max 档（新 hole_to_hole）→ 回退+态复原。"""
    st = synth_full_state()
    sha0 = cst.state_sha256(st)
    rec = m3._apply_gated(
        st, "width_gap",
        [{"action": "width_class", "net_id": "NET-C", "class": "max"},
         {"action": "submit"}], 0)
    assert rec["drc_ok"] is False
    assert rec["rolled_back"] is True
    assert rec["unresolved"][0]["reason"] == "drc_new_violation"
    assert cst.state_sha256(st) == sha0
    assert {v.rule for v in cva.validate_full(st).violations} == set()


def test_width_gap_ladder_stops_at_hole_ceiling():
    """宽度间隙规整的 validate-only 判定: NET-C 绕孔列升 max 触孔带 →
    爬停在 nom（终态零新增）; NET-B 空旷可到顶。"""
    st = synth_full_state()
    summary = m3.run_m3(st, None)
    widths = summary["totals_after"]["widths"]
    assert widths["NET-C"] == "nom"              # 孔带封顶（max 被 validate 拒）
    assert widths["NET-B"] == "max"              # 空旷到顶
    assert summary["drc"]["new_violation_keys_n"] == 0
    # 爬升后网内档混用归零（档位对齐）
    for net, mix in summary["totals_after"]["width_mix"].items():
        assert len(mix) == 1


def test_width_unify_normalizes_mix_through_run():
    st = synth_merge_state()
    st.segs["seg:NET-A:1"] = dict(st.segs["seg:NET-A:1"],
                                  width_class="max")   # 手构混用
    st.recompute_connectivity()
    summary = m3.run_m3(st, {"categories": ["width_unify"]})
    assert len(summary["totals_after"]["width_mix"]["NET-A"]) == 1
    assert all(s["width_class"] == st.widths["NET-A"]
               for s in st.segs.values())


# ---------------------------------------------------- 确定性双跑（≥2）

def test_determinism_double_run_real():
    outs = []
    for _ in range(2):
        st = real_routed_state()
        summary = m3.run_m3(st, None)
        outs.append((canonical_json(summary),
                     summary["state_sha256_after"],
                     cst.state_sha256(st)))
    assert outs[0][0] == outs[1][0]              # 摘要字节等
    assert outs[0][1] == outs[1][1]              # state_sha256 等
    assert outs[0][2] == outs[1][2]


def test_determinism_double_run_synth():
    outs = []
    for _ in range(2):
        st = synth_full_state()
        summary = m3.run_m3(st, {"categories": ["dead_branch",
                                                "redundant_via",
                                                "width_unify"]})
        outs.append(canonical_json(summary))
    assert outs[0] == outs[1]


def test_determinism_plan_double_run():
    st = synth_full_state()
    a = canonical_json(m3.plan_actions(st, None))
    b = canonical_json(m3.plan_actions(st, None))
    assert a == b


# ---------------------------------------------------- totals/摘要形态

def test_totals_shape_and_change_real():
    st = real_routed_state()
    summary = m3.run_m3(st, None)
    tb, ta = summary["totals_before"], summary["totals_after"]
    for t in (tb, ta):
        assert set(t) >= {"segs_n", "vias_n", "width_mix", "routed_nets",
                          "widths", "connectivity"}
    # D2 共线合并: 段 3→2; D1 死枝: 段 2→1 → 总 5→3; via 4→2
    assert (tb["segs_n"], ta["segs_n"]) == (5, 3)
    assert (tb["vias_n"], ta["vias_n"]) == (4, 2)
    assert ta["segs_n"] == len(st.segs) and ta["vias_n"] == len(st.vias)
    # 死枝段已不在; D2 两共线段已并一
    assert "seg:Net-(D1-Pad1):4" not in st.segs
    assert "via:Net-(D1-Pad1):64_20" not in st.vias   # 死枝尾孔 gc
    assert "via:Net-(D1-Pad1):52_20" in st.vias       # 干路孔保留（随夹具西移 58→52）
    assert "via:Net-(D2-Pad1):27_35" not in st.vias   # 冗余过孔消减
    assert "via:Net-(D2-Pad1):27_39" in st.vias       # L 衔接孔保留
    assert st.connectivity["Net-(D2-Pad1)"] is True
    assert st.connectivity["Net-(D1-Pad1)"] is True


def test_run_synth_merge_removes_redundant_via():
    st = synth_merge_state()
    summary = m3.run_m3(st, None)
    assert summary["totals_before"]["vias_n"] == 1
    assert summary["totals_after"]["vias_n"] == 0
    assert summary["totals_before"]["segs_n"] == 2
    assert summary["totals_after"]["segs_n"] == 1
    assert st.connectivity["NET-A"] is True
    seg = st.segs["seg:NET-A:2"]
    assert seg["grid"][0] == [4, 4] and seg["grid"][-1] == [20, 4]
    assert len(st.vias) == 0


def test_run_budget_none_and_default_equivalent():
    st = synth_merge_state()
    s1 = m3.run_m3(st, None)
    st2 = synth_merge_state()
    s2 = m3.run_m3(st2, m3.DEFAULT_BUDGET)
    assert s1["batches"] == s2["batches"]
    assert s1["state_sha256_after"] == s2["state_sha256_after"]


def test_summary_canonical_json_serializable():
    for st in (synth_full_state(), real_routed_state()):
        summary = m3.run_m3(st, None)
        data = canonical_json(summary)
        assert isinstance(data, bytes)
        assert json.loads(data.decode("utf-8"))["runner"] == m3.RUNNER_ID


def test_summary_fields_complete():
    st = synth_merge_state()
    s = m3.run_m3(st, None)
    for key in ("runner", "board_id", "board_sha256", "budget", "scope",
                "totals_before", "totals_after", "state_sha256_before",
                "state_sha256_after", "plan_actions_n", "batches",
                "unresolved_actions", "drc", "connectivity"):
        assert key in s
    assert s["state_sha256_before"] != s["state_sha256_after"]
    assert s["unresolved_actions"] == []
    assert s["drc"]["violations_after_n"] <= s["drc"]["violations_before_n"]
