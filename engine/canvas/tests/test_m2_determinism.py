# -*- coding: utf-8 -*-
"""Lane-M2X 确定性双跑字节等测试（无随机源纪律的硬门）。

- 真板 badgeleds（2 层）+ 合成微板（k1 夹具）各 1 例: 同板同 budget 双跑
  run_m2 → 摘要 canonical_json 字节等 + 终态 state_sha256 等。
- plan_actions 纯函数性（不改入参）+ 同板双规划字节等。
- 摘要 canonical round-trip 字节等（v5.canonical 同源）。
计数 4（双跑 2 + 纯函数 1 + round-trip 1）≥ 合同下限 2。
"""
from v5.canonical import canonical_json, canonical_roundtrip

from canvas.runners.m2 import DEFAULT_BUDGET, plan_actions, run_m2
from canvas.state import state_sha256
from canvas.tests.test_k1_fixtures import real_state, synth_state


def test_double_run_real_badgeleds_byte_equal():
    """真板 badgeleds 双跑（prereg 冻结缺省 budget）: 摘要字节等+终态锚等。"""
    st1, st2 = real_state(), real_state()
    s1, s2 = run_m2(st1), run_m2(st2)
    assert canonical_json(s1) == canonical_json(s2)
    assert s1["state_sha256_after"] == s2["state_sha256_after"]
    assert state_sha256(st1) == state_sha256(st2)
    # V6-ANCHOR-R1 口径 v2 钉扎（D-ORACLE-1 修复后复测同值）: 真端点绑定
    # 几何下 C1-Pad1 走廊实为合法（旧口径 0.4982 假拒）→ m2 解通; C2-Pad1
    # 转为新未解。确定性本体（双跑字节等）不受口径影响。
    assert s1["unresolved_nets"] == s2["unresolved_nets"] == \
        ["Net-(C2-Pad1)", "Net-(C2-Pad2)"]
    assert s1["applied_count"] == s2["applied_count"] > 0


def test_double_run_synth_byte_equal():
    st1, st2 = synth_state(), synth_state()
    s1, s2 = run_m2(st1), run_m2(st2)
    assert canonical_json(s1) == canonical_json(s2)
    assert s1["state_sha256_after"] == s2["state_sha256_after"]
    assert state_sha256(st1) == state_sha256(st2)
    assert s1["unresolved_nets"] == []
    assert s1["via_cost_facts"]["vias_applied"] >= 1


def test_plan_actions_pure_and_stable():
    """plan_actions 不改入参（副本上演进）且同板双规划字节等。"""
    st = synth_state()
    before = state_sha256(st)
    p1 = plan_actions(st)
    p2 = plan_actions(st)
    assert state_sha256(st) == before
    assert canonical_json(p1) == canonical_json(p2)
    assert p1, "synth 板应有规划动作"
    # 显式 budget 同型（缺省值转录自 DEFAULT_BUDGET）
    p3 = plan_actions(st, dict(DEFAULT_BUDGET))
    assert canonical_json(p3) == canonical_json(p1)


def test_summary_canonical_roundtrip():
    for factory in (synth_state, real_state):
        st = factory()
        summary = run_m2(st)
        first, loaded = canonical_roundtrip(summary)
        assert canonical_json(summary) == first
        assert loaded["state_sha256_after"] == summary["state_sha256_after"]
