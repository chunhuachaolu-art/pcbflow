# -*- coding: utf-8 -*-
"""V5-R2 钉值（任务书 V5-R2-RIPUP-DEEPEN-GUIDE-TASKBOOK-2026-09-24.md §3 门 1：
新增钉值=参数化常量/联合重排选择器/导引展开确定性；executor 0.6.1→0.7.0）。

覆盖面：
- v5.guide（W-3 落点=新件）：波次分波/展开序确定性（k 冻结规则、x 带连续
  分波、块内 id 字典序）、档位序（宽度三档、n≤12 启用上限）、探针交换
  （一步交换、越界回绕、单网不适用）。
- W-1 ripup_params：白名单键校验 fail-closed（未知键/类型/负值）、缺省=
  模块常量、guide 开关。
- W-2 联合重排：上位替代者并入（重布走廊交叠）、护栏启用判据（纯整数
  段数、factor×greedy）、joint_factor=0 退化纯贪心、(cost,id) 冻结序。
- W-4 探针预算参数面（probe_budget 可配 3/5；victim 定向 probe_swap）。
- 导引确定性：ripup 路径双跑 negotiation_log 逐字节等（0.7.0 世界内）；
  guide=False 对照臂=committed 序（无 guide-order 行）。

全部夹具内联合成（F12 先例）：零 out/ 写入、零网络、零 LLM API。
"""
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from v5 import executor as ex  # noqa: E402
from v5 import guide  # noqa: E402
from v5.executor import EXECUTOR_VERSION, execute_candidate  # noqa: E402

sys.path.insert(0, os.path.join(ROOT, "tests"))
from test_upgrade5_engine_capability import (  # noqa: E402
    _board, _cand, _commit_run, _ripup_fail_board, _ripup_ok_board)


# ---------------------------------------------------------------- v5.guide

def test_guide_version():
    assert guide.GUIDE_VERSION == "v5.guide/0.1.0"
    # V5-EXECUTOR-ENG-R1 翻转披露（2026-10-02）：executor 0.8.0→0.9.0
    assert EXECUTOR_VERSION == "v5.executor/0.13.0"  # 0.13.0 同步（engine-fix-r1 阶段一：FX-1 梯内 memo＋FX-2 微优化，纯等价提速；0.11.0=EXEC-R8-B）  # EXEC-R8-B 同步（候选出口事件接线）


def test_guide_wave_k_frozen_rule():
    """k 冻结规则：n<3→1、n<5→2、n≥5→3。"""
    assert [guide.wave_k(n) for n in (1, 2)] == [1, 1]
    assert [guide.wave_k(n) for n in (3, 4)] == [2, 2]
    assert [guide.wave_k(n) for n in (5, 8, 12, 40)] == [3, 3, 3, 3]


def test_guide_wave_order_deterministic_band_split():
    """波次展开：x 带连续分波（按 (x,id) 排序切 k 块）+块内 id 字典序+
    重复求值逐位等。"""
    geo = {"NC": (9.0, 0.0), "NA": (1.0, 5.0), "NB": (5.0, 2.0),
           "ND": (3.0, 7.0), "NE": (7.0, 1.0)}
    o1 = guide.wave_order(list(geo), geo)
    o2 = guide.wave_order(list(geo), geo)
    assert o1 == o2 == ["NA", "ND", "NB", "NE", "NC"]  # 波[NA,ND]、[NB,NE]、[NC]
    # 输入集合序扰动不改变输出（sorted() 冻结）
    shuffled = ["NC", "NE", "NA", "ND", "NB"]
    assert guide.wave_order(shuffled, geo) == o1


def test_guide_wave_order_single_or_double_net():
    geo = {"NA": (9.0, 0.0), "NB": (1.0, 0.0)}
    assert guide.wave_order(["NA", "NB"], geo) == ["NA", "NB"]   # k=1=字典序（块内 sorted）
    geo3 = {"NA": (1.0, 0.0), "NB": (5.0, 0.0), "NC": (9.0, 0.0)}
    assert guide.wave_order(list(geo3), geo3) == ["NA", "NB", "NC"]  # k=2


def test_guide_tier_order_width_bands():
    """档位展开：tier=(w≥0.3→1、≥0.2→2、else 3)，序=(tier,id)；n≤12 上限。"""
    widths = {"NW": 0.4, "NS": 0.25, "NF": 0.15, "NA": 0.3, "NB": 0.2}
    assert guide.tier_order(list(widths), widths) == ["NA", "NW", "NB", "NS", "NF"]
    assert guide.TIER_MAX_NETS == 12


def test_guide_probe_swap_one_step():
    """W-4 交换：一步邻位交换（回绕）、victim 缺席/单网=None 不适用。"""
    assert guide.probe_swap(["a", "b", "c"], "b", 1) == ["a", "c", "b"]
    assert guide.probe_swap(["a", "b", "c"], "a", -1) == ["c", "b", "a"]
    assert guide.probe_swap(["a", "b", "c"], "a", 2) == ["c", "b", "a"]
    assert guide.probe_swap(["a", "b"], "x", 1) is None
    assert guide.probe_swap(["a"], "a", 1) is None


# ---------------------------------------------------------------- W-1 params

def test_ripup_params_default_and_override():
    p = ex._ripup_params(None)
    assert p == {"max_rounds_per_net": 5, "max_total_per_candidate": 12,
                 "reroute_max_plans": 30, "probe_budget": 3,
                 "joint_cost_factor": 2, "guide": True}
    q = ex._ripup_params({"probe_budget": 5, "guide": False})
    assert q["probe_budget"] == 5 and q["guide"] is False
    assert q["max_rounds_per_net"] == 5


def test_ripup_params_fail_closed():
    with pytest.raises(Exception):
        ex._ripup_params({"unknown_key": 1})          # 非白名单键
    with pytest.raises(Exception):
        ex._ripup_params({"max_rounds_per_net": 0})   # <1
    with pytest.raises(Exception):
        ex._ripup_params({"max_rounds_per_net": 2.5})  # 非整
    with pytest.raises(Exception):
        ex._ripup_params({"probe_budget": True})      # bool 非整型键
    with pytest.raises(Exception):
        ex._ripup_params("wave")                      # 非 dict
    assert ex._ripup_params({"probe_budget": 0})["probe_budget"] == 0  # 0=关探针合法


def test_ripup_params_passthrough_changes_rounds():
    """参数透传面：probe_budget=0（等效关探针）+guide=False+轮 1 →
    ripup_fail 板 log 行数收缩（每轮 1 序、无 guide-order/probe 行）。"""
    board = _board(_ripup_fail_board)
    full = execute_candidate(board, _cand(board))
    lean = execute_candidate(board, _cand(board), ripup_params={
        "max_rounds_per_net": 1, "guide": False, "probe_budget": 0})
    lg = lean["negotiation_log"]
    assert not any("guide-order" in l for l in lg)
    assert not any("probe=" in l for l in lg)
    assert len([l for l in lg if "ripped=['NA']" in l]) == 1
    bn = {pn["net_id"]: pn for pn in lean["per_net"]}
    assert bn["NB"]["attempts"] == 106 + 1 * 1
    # 缺省臂 0.7.0 行为=5 轮×2 序
    bnf = {pn["net_id"]: pn for pn in full["per_net"]}
    assert bnf["NB"]["attempts"] == 106 + 5 * 2


# ---------------------------------------------------------------- W-2 联合重排

def test_joint_rearrangement_includes_upstream_alternates():
    """W-2：与 hit 段重布走廊交叠的网并入联合候选（护护栏内）；远处网不并。"""
    board = _board(_ripup_ok_board)
    ctx = _Context_lite(board)
    # NHIT 命中 N 失败走廊；NALT 与 NHIT 平行贴行（<corr_hw 重布走廊交叠）
    # → 上位替代者；NFAR 远处 → 不入。
    _commit_run(ctx, "NHIT", "PT-A", "F.Cu", [(5.0, 4.0), (5.0, 6.0)])
    _commit_run(ctx, "NALT", "PT-A", "F.Cu", [(3.0, 4.0), (7.0, 4.0)], k=1)
    _commit_run(ctx, "NFAR", "PT-A", "F.Cu", [(0.5, 9.5), (1.0, 9.5)], k=2)
    got, _geo = ex._ripup_blocker_ids(ctx, "NX", 0.2, (2.0, 5.0), (8.0, 5.0),
                                      ex._RIPUP_ESCAPE_REACH_MM)
    assert got == ["NALT", "NHIT"]   # 联合集（NALT 并入；(cost,id) 序）
    # joint_factor=0 → 纯贪心（NALT 非命中者不入）
    g0, _ = ex._ripup_blocker_ids(ctx, "NX", 0.2, (2.0, 5.0), (8.0, 5.0),
                                  ex._RIPUP_ESCAPE_REACH_MM, joint_factor=0)
    assert g0 == ["NHIT"]


def test_joint_guardrail_blocks_explosion():
    """护栏：联合集段数和 > factor×贪心段数和 → 不启用（维持贪心集）。
    构造 3 网贴行 hit（贪心 3 段）+2 网长走线（各 10 段）与 hit 交叠。"""
    board = _board(_ripup_ok_board)
    ctx = _Context_lite(board)
    _commit_run(ctx, "NH1", "PT-A", "F.Cu", [(5.0, 4.0), (5.0, 6.0)])
    long1 = [(3.0 + i * 0.25, 4.0) for i in range(17)]   # x∈[3,7] 避端点盘
    _commit_run(ctx, "NL1", "PT-B", "F.Cu", long1, k=1)
    long2 = [(3.0 + i * 0.25, 6.0) for i in range(17)]   # x∈[3,7] 避端点盘
    _commit_run(ctx, "NL2", "PT-B", "F.Cu", long2, k=2)
    # 联合=NH1(1 段)+NL1(16)+NL2(16)=33 > 2×1 → 护栏拒（贪得=NH1；
    # x∈[3,7] 避开 N 端点逃逸盘 1.25——长网起点再近会被 disc 判 hit）
    got, _ = ex._ripup_blocker_ids(ctx, "NX", 0.2, (2.0, 5.0), (8.0, 5.0),
                                   ex._RIPUP_ESCAPE_REACH_MM,
                                   joint_factor=2)
    assert got == ["NH1"]


def _Context_lite(board):
    from v5.executor import _Context
    return _Context(board)


# ---------------------------------------------------------------- 确定性

@pytest.mark.parametrize("builder,use_params", [
    (_ripup_ok_board, None),
    (_ripup_fail_board, None),
    (_ripup_fail_board, {"guide": False, "probe_budget": 5}),
])
def test_r2_double_run_byte_equal(builder, use_params):
    """0.7.0 世界内双跑字节等（导引/探针/联合重排全确定性冻结前提）。"""
    board = _board(builder)
    r1 = execute_candidate(board, _cand(board), ripup_params=use_params)
    r2 = execute_candidate(board, _cand(board), ripup_params=use_params)
    assert r1["negotiation_log"] == r2["negotiation_log"]
    assert r1["per_net"] == r2["per_net"]
