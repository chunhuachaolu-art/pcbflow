# -*- coding: utf-8 -*-
"""Lane-M3 修整规划测试: budget fail-closed 矩阵 / 丝印条款探针 / 四类动作
规划器单元（残段误判防线/过孔消减防线/宽归一/档位爬升）/ 只读性/确定性序。"""
import json

import pytest

from canvas import protocol as cpr
from canvas import state as cst
from canvas.runners import m3
from canvas.tests.test_k1_fixtures import (
    apply_ok, run_batch, synth_state)


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


def synth_split_state(layer2="F.Cu", with_tuning=False):
    """NET-A 两段共线衔接于 via (12,4)（可带 tuning）。"""
    st = synth_state()
    acts = [
        {"action": "route", "net_id": "NET-A",
         "waypoints": [[4, 4], [12, 4]], "layer": "F.Cu"},
        {"action": "via", "net_id": "NET-A", "grid": [12, 4]},
        {"action": "route", "net_id": "NET-A",
         "waypoints": [[12, 4], [20, 4]], "layer": layer2},
    ]
    if with_tuning:
        acts.append({"action": "tuning", "net_id": "NET-A", "group_id": "g",
                     "kind": "detour", "params": {"offset_mm": 1.0}})
    apply_ok(st, acts)
    return st


def synth_spur_state():
    """NET-B 主路 + 协议合法死枝（尾 via 落地——协议路径上死枝必带尾 via）。"""
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


def _acts(actions):
    return [(a["action"], a.get("net_id") or a.get("shape_id"))
            for a in actions if a["action"] != "submit"]


# ---------------------------------------------------------------- budget

def test_budget_defaults_and_normalization():
    nb = m3.normalize_budget(None)
    assert nb == {"max_actions": 24, "categories": list(m3.CATEGORIES),
                  "silkscreen": False}
    # 类别去重+规范序（合同序钉死）
    nb2 = m3.normalize_budget({"categories": ["width_gap", "dead_branch",
                                              "width_gap"]})
    assert nb2["categories"] == ["dead_branch", "width_gap"]


def test_budget_fail_closed_matrix():
    """budget 拒收路径: 非对象/合同外键/负数/布尔/非整数/未知类别/非序列/
    非 bool 丝印 → BudgetError（fail-closed，8 例）。"""
    bad = [
        42,
        {"unknown_key": 1},
        {"max_actions": -1},
        {"max_actions": True},
        {"max_actions": 1.5},
        {"categories": ["no_such_category"]},
        {"categories": "dead_branch"},
        {"silkscreen": "yes"},
    ]
    for b in bad:
        with pytest.raises(m3.BudgetError):
            m3.normalize_budget(b)
        with pytest.raises(m3.BudgetError):
            m3.plan_actions(synth_state(), b)


def test_budget_max_actions_cap_atomic():
    st = synth_split_state()
    # merge 批=4 动作; 上限 3 → 整批不规划（批原子）
    acts = m3.plan_actions(st, {"max_actions": 3})
    assert all(a["action"] != "route" for a in acts)
    # 上限 0 → 零规划
    assert m3.plan_actions(st, {"max_actions": 0}) == []
    # 上限 4 → merge 批在（后续类别可能仍被预算挡住）
    acts4 = m3.plan_actions(st, {"max_actions": 4})
    assert sum(1 for a in acts4 if a["action"] != "submit") <= 4
    assert any(a["action"] == "route" for a in acts4)


def test_categories_subset():
    st = synth_full_state()
    acts = m3.plan_actions(st, {"categories": ["dead_branch"]})
    assert all(a["action"] in ("ripup", "submit") for a in acts)
    acts2 = m3.plan_actions(st, {"categories": ["width_unify"]})
    assert all(a["action"] in ("width_class", "submit") for a in acts2)
    assert len(_acts(acts2)) == 3          # 三网 widths 台账补全


# ---------------------------------------------------------------- 丝印条款

def test_silkscreen_probe_false_on_both_boards():
    """探明结论: 真板与合成夹具 board 体均无丝印数据。"""
    from canvas.tests.test_k1_fixtures import real_state
    for st in (real_state(), synth_state()):
        scope = m3.silkscreen_scope(st)
        assert scope["available"] is False
        assert "board.v1" in scope["reason"]
        assert "signal" in scope["evidence"]["stackup_kinds"]
        assert scope["evidence"]["silk_layers"] == []
        assert scope["evidence"]["silk_keys"] == []


def test_silkscreen_request_zero_actions_and_deviation():
    """无丝印数据时丝印动作拒收: 请求丝印修整 → 零丝印动作 + 收窄偏差登记。"""
    st = synth_split_state()
    acts = m3.plan_actions(st, {"silkscreen": True})
    # 协议九动作内不存在丝印动作类; plan 层即 fail-closed 不产
    assert all(a["action"] in cpr.ACTION_NAMES for a in acts)
    summary = m3.run_m3(st, {"silkscreen": True})
    dev = summary["scope"]["deviations"]
    assert len(dev) == 1
    assert dev[0]["code"] == "M3-SILK-SCOPE-NARROW"
    assert "铜层面" in dev[0]["detail"]
    assert summary["scope"]["silkscreen"]["requested"] is True
    assert summary["scope"]["silkscreen"]["available"] is False
    # 铜层面修整照常（不受丝印请求影响）
    assert any(a["action"] == "route" for r in summary["batches"]
               for a in r["actions"])


def test_no_silkscreen_request_no_deviation():
    st = synth_split_state()
    summary = m3.run_m3(st, {"categories": ["width_unify"]})
    assert summary["scope"]["deviations"] == []
    assert summary["scope"]["silkscreen"]["requested"] is False


# ---------------------------------------------------------------- 宽归一

def _hand_mixed_state():
    """手构 width 混用: 3×min + 1×max（协议路径不可能产生——set_width_class
    全网重印; 混用只能来自手构/hand-built 态，防御面）。"""
    st = synth_state()
    st.add_seg("NET-A", "PA", "F.Cu", [[4, 4], [8, 4]], "min")
    st.add_seg("NET-A", "PA", "F.Cu", [[8, 4], [12, 4]], "min")
    st.add_seg("NET-A", "PA", "F.Cu", [[12, 4], [16, 4]], "min")
    st.add_seg("NET-A", "PA", "F.Cu", [[16, 4], [20, 4]], "max")
    st.add_via("NET-A", [8, 4])
    st.add_via("NET-A", [12, 4])
    st.add_via("NET-A", [16, 4])
    st.recompute_connectivity()
    return st


def test_width_unify_mix_to_dominant():
    st = _hand_mixed_state()
    acts = m3.plan_actions(st, {"categories": ["width_unify"]})
    assert _acts(acts) == [("width_class", "NET-A")]
    assert acts[0]["class"] == "min"                  # 主导档=3/4
    cpr.apply_batch(st, acts)
    assert st.widths["NET-A"] == "min"
    assert all(s["width_class"] == "min" for s in st.segs.values())


def test_width_unify_tie_prefers_narrower():
    st = _hand_mixed_state()
    st.segs["seg:NET-A:3"] = dict(st.segs["seg:NET-A:3"], width_class="max")
    st.add_seg("NET-A", "PA", "F.Cu", [[20, 4], [24, 4]], "max")
    st.recompute_connectivity()          # 2 min + 2 max → 并列取更窄 min
    acts = m3.plan_actions(st, {"categories": ["width_unify"]})
    assert acts[0]["class"] == "min"


def test_width_unify_invalid_class_fails_closed():
    """词表外档 fail-closed: 带词表外 width_class 的态不可修整（波1
    validate_full 对词表外档即抛）→ M3StateError 显式早拒。"""
    st = synth_state()
    st.add_seg("NET-A", "PA", "F.Cu", [[4, 4], [20, 4]], "mega")
    st.recompute_connectivity()
    with pytest.raises(m3.M3StateError, match="mega"):
        m3.plan_actions(st, {"categories": ["width_unify"]})
    with pytest.raises(m3.M3StateError, match="mega"):
        m3.run_m3(st, {"categories": ["width_unify"]})
    # widths 台账词表外同样早拒
    st2 = synth_state()
    apply_ok(st2, [{"action": "route", "net_id": "NET-A",
                    "waypoints": [[4, 4], [20, 4]], "layer": "F.Cu"}])
    st2.widths = {"NET-A": "mega"}
    st2.recompute_connectivity()
    with pytest.raises(m3.M3StateError, match="widths"):
        m3.plan_actions(st2, None)


def test_width_unify_emits_on_ledger_desync_with_mix():
    """widths 台账=主导档但 seg 仍混用（hand-built desync）→ 仍规划归一。"""
    st = _hand_mixed_state()
    st.set_width_class("NET-A", "min")    # 重印为全 min 后再打回一个 max
    st.segs["seg:NET-A:3"] = dict(st.segs["seg:NET-A:3"], width_class="max")
    st.recompute_connectivity()
    acts = m3.plan_actions(st, {"categories": ["width_unify"]})
    assert _acts(acts) == [("width_class", "NET-A")]


# ---------------------------------------------------------------- 残段判定

def test_dead_branch_spur_planned():
    st = synth_spur_state()
    dead = m3._net_dead_segs(st, "NET-B")
    assert dead == {"seg:NET-B:1"}
    acts = m3.plan_actions(st, {"categories": ["dead_branch"]})
    assert _acts(acts) == [("ripup", "seg:NET-B:1")]


def test_dead_branch_island_and_lollipop_and_ring():
    """孤岛（双 via 附件无终端）/棒糖环（衔接 via 自闭环）均判死;
    主链全活。"""
    st = synth_state()
    # 主链: NET-A (4,4)-(20,4) 直连
    st.add_seg("NET-A", "PA", "F.Cu", [[4, 4], [20, 4]], "min")
    # 孤岛: 两段经 via (10,8)-(14,8) 相连，无任何终端
    st.add_seg("NET-A", "PA", "F.Cu", [[10, 8], [12, 8]], "min")
    st.add_via("NET-A", [10, 8])
    st.add_seg("NET-A", "PA", "F.Cu", [[12, 8], [14, 8]], "min")
    st.add_via("NET-A", [14, 8])
    # 棒糖环: 自 via (16,4)（主链中点）出发的闭环（首末点同 via）
    st.add_via("NET-A", [16, 4])
    st.add_seg("NET-A", "PA", "F.Cu",
               [[16, 4], [16, 6], [18, 6], [18, 4], [16, 4]], "min")
    st.recompute_connectivity()
    dead = m3._net_dead_segs(st, "NET-A")
    assert dead == {"seg:NET-A:1", "seg:NET-A:2", "seg:NET-A:3"}


def test_dead_branch_keeps_parallel_redundant_path():
    """残段误判防线: 同一对 via 间的并行冗余支路**参与端到端链**（各在
    某条终端-终端简单路径上）→ 不判死。"""
    st = synth_state()
    st.add_seg("NET-A", "PA", "F.Cu", [[4, 4], [8, 4]], "min")       # 主
    st.add_via("NET-A", [8, 4])
    st.add_via("NET-A", [16, 4])
    st.add_seg("NET-A", "PA", "F.Cu", [[8, 4], [16, 4]], "min")      # 支路1 直
    st.add_seg("NET-A", "PA", "F.Cu",
               [[8, 4], [8, 8], [16, 8], [16, 4]], "min")            # 支路2 绕
    st.add_seg("NET-A", "PA", "F.Cu", [[16, 4], [20, 4]], "min")     # 主
    st.recompute_connectivity()
    assert m3._net_dead_segs(st, "NET-A") == set()


def test_dead_branch_stale_ledger_double_defense():
    """台账只读消费披露: 陈旧账本（手改 dangling 谎报活段）→ 判定层照
    台账判死（tier1 信任）; 规划层预演连通门即丢弃该批——双层防线，
    run 期还有同式门兜底（见 test_m3_run 回退测试）。"""
    st = synth_state()
    apply_ok(st, [{"action": "route", "net_id": "NET-B",
                   "waypoints": [[4, 16], [20, 16]], "layer": "F.Cu"}])
    st.chain_detail["NET-B"]["dangling_segs"] = ["seg:NET-B:0"]
    # 判定层: 只读消费台账（tier1 信任）
    assert m3._net_dead_segs(st, "NET-B") == {"seg:NET-B:0"}
    # 规划层: 预演连通门丢弃（陈旧台账的谎报不致落批）
    assert m3.plan_actions(st, {"categories": ["dead_branch"]}) == []


def test_dead_branch_dfs_cap_falls_back_to_tier1():
    """DFS 超限降级: cap=0 → 只认台账 tier1（孤岛不误判死也不漏 tier1）。"""
    st = synth_state()
    st.add_seg("NET-A", "PA", "F.Cu", [[4, 4], [20, 4]], "min")
    st.add_seg("NET-A", "PA", "F.Cu", [[10, 8], [12, 8]], "min")
    st.add_via("NET-A", [10, 8])
    st.add_via("NET-A", [12, 8])
    st.recompute_connectivity()
    old = m3.DFS_STEP_CAP
    m3.DFS_STEP_CAP = 0
    try:
        dead = m3._net_dead_segs(st, "NET-A")
    finally:
        m3.DFS_STEP_CAP = old
    assert dead == set()               # 孤岛段台账非 dangling → 降级不判死


# ---------------------------------------------------------------- 过孔消减

def test_via_merge_candidate_positive():
    st = synth_split_state()
    cands = m3._via_merge_candidates(st, "NET-A")
    assert len(cands) == 1
    c = cands[0]
    assert c["via_shape_id"] == "via:NET-A:12_4"
    assert c["layer"] == "F.Cu"
    assert c["waypoints"][0] == [4, 4] and c["waypoints"][-1] == [20, 4]
    acts = m3.plan_actions(st, {"categories": ["redundant_via"]})
    kinds = _acts(acts)
    assert ("route", "NET-A") in kinds
    assert ("ripup", "via:NET-A:12_4") in kinds
    assert ("ripup", "seg:NET-A:0") in kinds
    assert ("ripup", "seg:NET-A:1") in kinds
    # 协议形态: 键集在合同 ALLOWED 内
    for a in acts:
        assert set(a) <= cpr.ALLOWED_KEYS[a["action"]]


def test_via_merge_negative_matrix():
    """过孔消减防线: 异层衔接/L 弯/三段共点/衔接点=端点锚/带 tuning 网
    → 一律不规划合并。"""
    # 异层（合法层过渡 via）
    st_layers = synth_split_state(layer2="B.Cu")
    assert m3._via_merge_candidates(st_layers, "NET-A") == []
    assert all(a["action"] != "route"
               for a in m3.plan_actions(st_layers,
                                        {"categories": ["redundant_via"]}))
    # L 弯衔接（同层不共线）
    st_l = synth_state()
    apply_ok(st_l, [
        {"action": "route", "net_id": "NET-B",
         "waypoints": [[4, 16], [12, 16]], "layer": "F.Cu"},
        {"action": "via", "net_id": "NET-B", "grid": [12, 16]},
        {"action": "route", "net_id": "NET-B",
         "waypoints": [[12, 16], [12, 14], [20, 14], [20, 16]],
         "layer": "F.Cu"},
    ])
    assert m3._via_merge_candidates(st_l, "NET-B") == []
    # 三段共点（第三段=死支不预清理时）
    st3 = synth_state()
    st3.add_seg("NET-A", "PA", "F.Cu", [[4, 4], [12, 4]], "min")
    st3.add_seg("NET-A", "PA", "F.Cu", [[12, 4], [20, 4]], "min")
    st3.add_seg("NET-A", "PA", "F.Cu", [[12, 4], [12, 8]], "min")
    st3.add_via("NET-A", [12, 4])
    st3.add_via("NET-A", [12, 8])
    st3.recompute_connectivity()
    assert m3._via_merge_candidates(st3, "NET-A") == []
    # 衔接点=端点锚（合并会把锚变中点 → 拒）
    st_anchor = synth_full_state()
    assert m3._via_merge_candidates(st_anchor, "NET-C") == []
    # 带 tuning 网（M5 域保守回避）
    st_tun = synth_split_state(with_tuning=True)
    assert m3._via_merge_candidates(st_tun, "NET-A") == []
    assert all(a["action"] != "route"
               for a in m3.plan_actions(st_tun,
                                        {"categories": ["redundant_via"]}))


# ---------------------------------------------------------------- 只读/形态

def test_plan_actions_readonly():
    st = synth_full_state()
    before = cst.state_facts(st)
    sha = cst.state_sha256(st)
    m3.plan_actions(st, None)
    assert cst.state_facts(st) == before
    assert cst.state_sha256(st) == sha


def test_plan_actions_protocol_shaped_and_batched():
    st = synth_full_state()
    acts = m3.plan_actions(st, None)
    assert acts[-1]["action"] == "submit"            # 批以 submit 结尾
    for a in acts:
        assert a["action"] in cpr.ACTION_NAMES
        assert set(a) <= cpr.ALLOWED_KEYS[a["action"]]
    batches = m3._split_batches(acts)
    assert sum(len(b) for b in batches) == len(acts)
    assert all(b[-1]["action"] == "submit" for b in batches)
    # 尾部无 submit 的残批丢弃（防御）
    assert m3._split_batches([{"action": "ripup", "shape_id": "x"}]) == []


def test_width_gap_ladder_steps_in_vocab_order():
    st = synth_full_state()
    planned = m3._plan_batches(st, None)
    per_net = {}
    for kind, batch in planned:
        if kind != "width_gap":
            continue
        for a in batch:
            if a["action"] == "width_class":
                per_net.setdefault(a["net_id"], []).append(a["class"])
    assert per_net                                   # 合成全布态必尝试爬升
    vocab = ["min", "nom", "max"]
    for net, steps in sorted(per_net.items()):
        idxs = [vocab.index(c) for c in steps]
        assert idxs == sorted(idxs)                  # 逐档只升不降
        assert len(set(steps)) == len(steps)         # 无重复档
