# -*- coding: utf-8 -*-
"""L5② 引擎默认规划器测试（V5.0-DEV-TASKBOOK §4 L5 + A10；stdlib+pytest）。

夹具：内联小板（build→load_board 口径全过 schema+哈希链）+ 真实 boards/d/demo-01
（只读）。覆盖：双跑字节等（双臂）、双臂差异断言、generation_trace 覆盖率数据源、
组合截断披露、层合法性、validate 拆坏报错、demo-01 冒烟、反事实行为
（关规则→生成行为必变）。
"""
import copy
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from v5 import canonical, schema_loader  # noqa: E402
from v5.board import compute_board_sha256, load_board_file  # noqa: E402
from v5.compiler import compile_board  # noqa: E402
from v5.planner import (  # noqa: E402
    MAX_COMBINATIONS,
    PLANNER_VERSION,
    PlannerError,
    plan_candidates,
    validate_candidate,
)

DEMO01_PATH = os.path.join(ROOT, "boards", "d", "demo-01-v2-corridor.board.v1.json")

HARD_RULES = {
    "R1": {"floor_mm": 0.3, "k_a": 0.4},
    "R2": {"max_parallel_mm": 5.0, "min_distance_mm": 3.0},
    "R3": {"unsplittable": True},
    "R4": {"max_distance_mm": 2.0, "return_via_required": True},
    "R5": {"min_clearance_mm": 0.5},
    "R6": {"keepout_zones_forbidden": True, "plane_forbidden": True},
}

STACKUP_4 = [
    {"id": "F.Cu", "kind": "signal", "preferred_direction": "h", "available": True},
    {"id": "In1.Cu", "kind": "signal", "preferred_direction": "v", "available": True},
    {"id": "In2.Cu", "kind": "plane", "preferred_direction": "any", "available": False},
    {"id": "B.Cu", "kind": "signal", "preferred_direction": "any", "available": True},
]
STACKUP_2 = STACKUP_4[:1] + [STACKUP_4[3]]
STACKUP_3SIG = [STACKUP_4[0], STACKUP_4[1], STACKUP_4[3]]


# ---------------------------------------------------------------- 夹具构造

def _hash_entry(entry):
    """source_hash = sha256(canonical(剔除 source_hash 后的条目))（与编译器同口径）。"""
    view = {k: v for k, v in entry.items() if k != "source_hash"}
    import hashlib
    return hashlib.sha256(canonical.canonical_json(view)).hexdigest()


def make_entry(pid, *, scope, target, priority, kind, params=None,
               enforcement="generation", version="1.0.0"):
    """构造一条 schema 合法的 15 字段 principle 条目（source_hash 现算）。"""
    entry = {
        "principle_id": pid,
        "name": "测试理念 %s" % pid,
        "intent": {"protects": "保护资源 X", "sacrifices": "牺牲普通网 Y 的短路径"},
        "scope": scope,
        "protected_resources": ["资源 X"],
        "target_freedom": target,
        "priority": priority,
        "hard_or_soft": "soft",
        "overridable": True,
        "compiled_rule": {"kind": kind, "params": dict(params or {})},
        "enforcement": enforcement,
        "conflict_policy": {"conflicts_with": [], "yields_to": []},
        "evidence_refs": ["v5.planner 测试夹具"],
        "version": version,
    }
    entry["source_hash"] = _hash_entry(entry)
    return entry


def part(pid, ptype, e1, e2, policy="any"):
    """最小合法分区（board.v1 schema required 七字段）。"""
    return {"partition_id": pid, "ptype": ptype,
            "geometry": {"endpoints": [list(e1), list(e2)]},
            "layer_policy": policy,
            "width_prior": {"w_min": 0.1, "w_max": 0.3},
            "current_a": 0.0, "speed_class": "low_speed"}


def zone(zid, kind, x0, y0, x1, y1, layers="all", **extra):
    z = {"zone_id": zid, "kind": kind,
         "rect": {"x_min": x0, "y_min": y0, "x_max": x1, "y_max": y1},
         "layers": layers}
    z.update(extra)
    return z


def make_board(*, partitions, registry=(), stackup=None, zones=(),
               board_id="planner-inline"):
    """组装内联板并复算 provenance.board_sha256（load_board 哈希链要求）。"""
    board = {
        "schema_version": "v5.board.v1",
        "board_id": board_id,
        "stackup": copy.deepcopy(stackup if stackup is not None else STACKUP_4),
        "workspace": {"x_min": 0.0, "y_min": 0.0, "x_max": 50.0, "y_max": 40.0},
        "zones": copy.deepcopy(list(zones)),
        "partitions": copy.deepcopy(list(partitions)),
        "nets": [{"net_id": "N-" + p["partition_id"], "net_class": "MISC",
                  "partitions": [p["partition_id"]]} for p in partitions],
        "hard_rules": copy.deepcopy(HARD_RULES),
        "principle_registry": copy.deepcopy(list(registry)),
        "provenance": {"source_type": "synthetic",
                       "source_uri": "inline://planner-test",
                       "source_sha256": "0" * 64, "adapter": "hand"},
    }
    board["provenance"]["board_sha256"] = compute_board_sha256(board)
    return board


def plan(board, arm="principle"):
    """编译+规划一步（测试辅助）；返回 (候选列表, 编译工件)。"""
    artifact, _fp = compile_board(board)
    return plan_candidates(board, artifact, arm=arm), artifact


def load_demo01():
    return load_board_file(DEMO01_PATH)


# ---------------------------------------------------------------- demo-01 冒烟

def test_demo01_smoke_principle_single_candidate():
    """冒烟：全部分区 layer_policy=F.Cu → 恰 1 个合法组合；首候选摘要正确。"""
    board = load_demo01()
    candidates, artifact = plan(board)
    assert len(candidates) == 1
    c = candidates[0]
    assert c["candidate_id"] == "C-001"
    assert c["arm"] == "principle"
    assert c["provenance"]["generator"] == PLANNER_VERSION == "v5.planner/0.1.0"
    assert c["provenance"]["compiled_sha256"] == canonical.canonical_sha256(artifact)
    pids = sorted(p["partition_id"] for p in board["partitions"])
    assert sorted(c["layer_assignment"]) == pids
    assert set(c["layer_assignment"].values()) == {"F.Cu"}  # 全部指派在信号层 F.Cu
    assert sorted(c["polylines"]) == pids
    assert c["polylines"]["P1"] == [[2.0, 38.0], [44.0, 38.0]]
    assert c["route_order"] == ["P7", "P9", "P2", "P4", "P1", "P3", "P8", "P5", "P6"]


def test_demo01_principle_route_order():
    """主路径排序：ordering 提升(P7,P9 队首) > 过廊同档前移(P2,P4,P1) > 其余按阶梯。"""
    board = load_demo01()
    candidates, _ = plan(board)
    assert candidates[0]["route_order"] == \
        ["P7", "P9", "P2", "P4", "P1", "P3", "P8", "P5", "P6"]


def test_demo01_no_principle_route_order_and_empty_trace():
    """诊断臂：纯阶梯+字典序（CLK>HS>BUS>PWR>{MISC+未列档}），trace/rules 双空。"""
    board = load_demo01()
    candidates, _ = plan(board, arm="no-principle")
    assert len(candidates) == 1
    c = candidates[0]
    assert c["arm"] == "no-principle"
    assert c["route_order"] == ["P2", "P3", "P4", "P1", "P8", "P5", "P6", "P7", "P9"]
    assert c["generation_trace"] == []
    assert c["provenance"]["rules_consumed"] == []


def test_demo01_trace_coverage_and_check_only_excluded():
    """覆盖率数据源：artifact.rules 每条必在 trace；check_only 条目不进 trace。"""
    board = load_demo01()
    candidates, artifact = plan(board)
    trace = candidates[0]["generation_trace"]
    rule_pids = {r["principle_id"] for r in artifact["rules"]}
    traced = {t["rule"] for t in trace}
    assert traced == rule_pids == {
        "P-PART-GRAN-DEMO01", "P-COR-CAP-C1-DEMO01", "P-XCOPPER-GUARD-DEMO01"}
    assert "P-CHECK-WIDTHPRIOR-DEMO01" not in traced  # check_only 条目
    assert len(trace) == len(rule_pids) >= 1


def test_demo01_trace_stage_order_and_effects():
    """留痕序=layer_plan→corridor→ordering→allocation（各阶段按 priority 降序）；
    effect 一句话可读；freedom 在四自由度枚举内。"""
    board = load_demo01()
    candidates, _ = plan(board)
    trace = candidates[0]["generation_trace"]
    assert [t["rule"] for t in trace] == [
        "P-COR-CAP-C1-DEMO01", "P-PART-GRAN-DEMO01", "P-XCOPPER-GUARD-DEMO01"]
    assert [t["freedom"] for t in trace] == ["corridor", "corridor", "ordering"]
    for t in trace:
        assert set(t) == {"rule", "freedom", "effect"}
        assert isinstance(t["effect"], str) and t["effect"]
    assert trace[0]["effect"] == \
        "过廊分区同档位排序前移 5 个: [P1, P2, P4, P7, P9]（走廊 [C1] 稀缺资源先行）"
    assert "排序前移 2 个分区: [P7, P9]" in trace[2]["effect"]


def test_demo01_rules_consumed_sorted():
    """rules_consumed = trace 中 principle_id 去重排序。"""
    board = load_demo01()
    candidates, _ = plan(board)
    consumed = candidates[0]["provenance"]["rules_consumed"]
    assert consumed == sorted(consumed) == [
        "P-COR-CAP-C1-DEMO01", "P-PART-GRAN-DEMO01", "P-XCOPPER-GUARD-DEMO01"]


def test_demo01_double_run_byte_equal_both_arms():
    """确定性硬测试：双跑 canonical 字节相等（双臂）。"""
    board = load_demo01()
    for arm in ("principle", "no-principle"):
        a1, _ = plan(board, arm=arm)
        a2, _ = plan(board, arm=arm)
        assert canonical.canonical_json(a1) == canonical.canonical_json(a2)


def test_validate_all_demo01_candidates_pass():
    """规划产物全部过 validate_candidate（自查入口原样返回）。"""
    board = load_demo01()
    for arm in ("principle", "no-principle"):
        candidates, _ = plan(board, arm=arm)
        for c in candidates:
            assert validate_candidate(c, board) is c


# ---------------------------------------------------------------- 组合枚举与截断

def _truncation_board():
    parts = [part("T1", "MISC", (1, 1), (2, 2)),
             part("T2", "MISC", (10, 1), (11, 2)),
             part("T3", "MISC", (20, 1), (21, 2))]
    registry = [make_entry("P-ALLOC-T", scope="partitioning", target="allocation",
                           priority=35, kind="via_frugal",
                           params={"max_extra_vias": 1})]
    return make_board(partitions=parts, registry=registry,
                      stackup=STACKUP_3SIG, board_id="planner-truncation")


def test_combination_truncation_keeps_first_24():
    """3 分区 × 3 信号层 = 27 组合 > 24 → 按组合键字典序截断保留前 24（披露可查）。"""
    board = _truncation_board()
    candidates, _ = plan(board)
    assert MAX_COMBINATIONS == 24
    assert len(candidates) == 24
    assert [c["candidate_id"] for c in candidates] == \
        ["C-%03d" % i for i in range(1, 25)]
    # 枚举序 = 各位置按偏好序字母表的字典序（右位先变）：
    # 首组合=全首偏好；序号 23（第 24 个）= T1/T3 末位、T2 第 2 位（截断非整圈）
    assert candidates[0]["layer_assignment"] == \
        {"T1": "F.Cu", "T2": "F.Cu", "T3": "F.Cu"}
    assert candidates[-1]["layer_assignment"] == \
        {"T1": "B.Cu", "T2": "In1.Cu", "T3": "B.Cu"}
    # 截断在 allocation 规则留痕中如实披露
    alloc = [t for t in candidates[0]["generation_trace"]
             if t["freedom"] == "allocation"]
    assert len(alloc) == 1
    assert "全板 27 组合" in alloc[0]["effect"]
    assert "截断保留前 24" in alloc[0]["effect"]
    # 双跑字节等（截断路径）
    a1, _ = plan(board)
    a2, _ = plan(board)
    assert canonical.canonical_json(a1) == canonical.canonical_json(a2)


# ---------------------------------------------------------------- layer_plan

def _pref_board(with_rule=True):
    parts = [part("X1", "CLK", (2, 2), (20, 2)),
             part("X2", "MISC", (2, 10), (20, 10))]
    registry = []
    if with_rule:
        registry.append(make_entry("P-PREF", scope="partition:X1",
                                   target="layer_plan", priority=40,
                                   kind="layer_preference", params={"layer": "B.Cu"}))
    return make_board(partitions=parts, registry=registry, stackup=STACKUP_2,
                      board_id="planner-pref")


def test_layer_plan_reorders_preference_and_first_candidate():
    """layer_plan 规则把偏好层 B.Cu 稳定前置 → 枚举序随偏好变，C-001 指派随之。"""
    board = _pref_board(with_rule=True)
    candidates, _ = plan(board)
    assert len(candidates) == 4  # 2 分区 × 2 层
    assert candidates[0]["layer_assignment"] == {"X1": "B.Cu", "X2": "F.Cu"}
    assert [c["layer_assignment"]["X1"] for c in candidates] == \
        ["B.Cu", "B.Cu", "F.Cu", "F.Cu"]
    eff = [t for t in candidates[0]["generation_trace"]
           if t["rule"] == "P-PREF" and t["freedom"] == "layer_plan"]
    assert len(eff) == 1 and "层偏好重排" in eff[0]["effect"] and "X1" in eff[0]["effect"]


def test_layer_plan_counterfactual_rule_off_changes_output():
    """反事实：关闭 layer_plan 规则 → 首候选层指派必变（X1 回到 stackup 序首位）。"""
    board = _pref_board(with_rule=False)
    candidates, _ = plan(board)
    assert candidates[0]["layer_assignment"] == {"X1": "F.Cu", "X2": "F.Cu"}
    assert candidates[0]["generation_trace"] == []


# ---------------------------------------------------------------- corridor

def _corridor_board(with_rule=True):
    parts = [part("Z1", "MISC", (0, 5), (5, 5)),      # 不穿越 C1
             part("Z2", "MISC", (12, 2), (18, 2))]    # bbox 落在 C1 x∈[10,20]
    registry = []
    if with_rule:
        registry.append(make_entry("P-CORR", scope="zone:C1", target="corridor",
                                   priority=60, kind="corridor_capacity",
                                   params={"capacity_mm": 4.3, "zone_id": "C1"}))
    zones = [zone("C1", "corridor", 10, 0, 20, 40, layers="signal", capacity=4.3)]
    return make_board(partitions=parts, registry=registry, stackup=STACKUP_2,
                      zones=zones, board_id="planner-corridor")


def test_corridor_rule_elevates_crosser_within_tier():
    """corridor 规则驱动：过廊分区在同类同档（同 ptype=MISC）内前移。"""
    board = _corridor_board(with_rule=True)
    candidates, _ = plan(board)
    assert candidates[0]["route_order"] == ["Z2", "Z1"]
    eff = [t for t in candidates[0]["generation_trace"]
           if t["rule"] == "P-CORR" and t["freedom"] == "corridor"]
    assert len(eff) == 1
    assert "过廊分区同档位排序前移 1 个: [Z2]" in eff[0]["effect"]


def test_corridor_counterfactual_and_no_principle_off():
    """反事实+诊断臂：关规则或 no-principle → 纯阶梯字典序 [Z1, Z2]（行为必变）。"""
    off = _corridor_board(with_rule=False)
    assert plan(off)[0][0]["route_order"] == ["Z1", "Z2"]
    on_np = plan(_corridor_board(with_rule=True), arm="no-principle")[0]
    assert on_np[0]["route_order"] == ["Z1", "Z2"]
    assert on_np[0]["generation_trace"] == []


# ---------------------------------------------------------------- ordering

def test_scope_zero_hit_rule_still_traced():
    """scope 零命中的规则也必须留痕 effect='scope 零命中'（覆盖率 100% 数据源）。"""
    parts = [part("A1", "MISC", (1, 1), (5, 1), policy="F.Cu")]
    board = make_board(
        partitions=parts, stackup=STACKUP_2, board_id="planner-zero-hit",
        registry=[make_entry("P-ZERO", scope="ptype:ANA", target="ordering",
                             priority=30, kind="completion_first", params={})])
    candidates, artifact = plan(board)
    assert [r["principle_id"] for r in artifact["rules"]] == ["P-ZERO"]
    trace = candidates[0]["generation_trace"]
    assert len(trace) == 1
    assert trace[0]["rule"] == "P-ZERO"
    assert trace[0]["effect"] == "scope 零命中"
    assert candidates[0]["provenance"]["rules_consumed"] == ["P-ZERO"]


def test_short_run_orders_by_length_within_tier():
    """short_run（prefer=min_length）：命中分区同档内按端点直线长度升序前移。"""
    parts = [part("L1", "MISC", (0, 0), (40, 0)),   # 长 40
             part("L2", "MISC", (0, 5), (5, 5))]    # 长 5
    registry = [make_entry("P-SHORT", scope="partitioning", target="ordering",
                           priority=30, kind="short_run",
                           params={"prefer": "min_length"})]
    board = make_board(partitions=parts, registry=registry, stackup=STACKUP_2,
                       board_id="planner-short")
    candidates, _ = plan(board)
    assert candidates[0]["route_order"] == ["L2", "L1"]
    eff = [t for t in candidates[0]["generation_trace"]
           if t["rule"] == "P-SHORT" and t["freedom"] == "ordering"]
    assert len(eff) == 1 and "短线偏好" in eff[0]["effect"]
    # 反事实+诊断臂：规则关闭 → 字典序 [L1, L2]
    off = make_board(partitions=parts, registry=[], stackup=STACKUP_2,
                     board_id="planner-short-off")
    assert plan(off)[0][0]["route_order"] == ["L1", "L2"]
    np_cands = plan(board, arm="no-principle")[0]
    assert np_cands[0]["route_order"] == ["L1", "L2"]


# ---------------------------------------------------------------- allocation 留痕

def test_allocation_rule_traced_with_noop_disclosure():
    """allocation 规则本阶段无可施加的层指派约束 → 如实披露留痕，不改枚举。"""
    parts = [part("A1", "PWR", (1, 1), (5, 1), policy="F.Cu")]
    board = make_board(
        partitions=parts, stackup=STACKUP_2, board_id="planner-alloc",
        registry=[make_entry("P-ALLOC", scope="ptype:PWR", target="allocation",
                             priority=80, kind="power_corridor_priority",
                             params={"min_width_mm": 0.8})])
    candidates, _ = plan(board)
    assert len(candidates) == 1
    assert candidates[0]["layer_assignment"] == {"A1": "F.Cu"}
    trace = candidates[0]["generation_trace"]
    assert [t["freedom"] for t in trace] == ["allocation"]
    assert "全板 1 组合（未截断）" in trace[0]["effect"]
    assert "power_corridor_priority" in trace[0]["effect"]
    assert "无可施加的层指派约束" in trace[0]["effect"]


# ---------------------------------------------------------------- 入口与防御

def test_invalid_arm_raises():
    board = load_demo01()
    with pytest.raises(PlannerError):
        plan_candidates(board, compile_board(board)[0], arm="shadow")


def test_artifact_board_mismatch_raises():
    """工件↔板指纹交叉核对：错配对 fail-closed。"""
    inline = _pref_board(with_rule=True)
    artifact, _ = compile_board(inline)
    with pytest.raises(PlannerError) as ei:
        plan_candidates(load_demo01(), artifact)
    assert "不匹配" in str(ei.value)


def test_inputs_not_mutated():
    """纯函数：board 与 compiled_artifact 输入零突变。"""
    board = load_demo01()
    artifact, _ = compile_board(board)
    b0, a0 = copy.deepcopy(board), copy.deepcopy(artifact)
    for arm in ("principle", "no-principle"):
        plan_candidates(board, artifact, arm=arm)
    assert board == b0
    assert artifact == a0


# ---------------------------------------------------------------- validate 拆坏

def _one_candidate():
    board = load_demo01()
    candidates, _ = plan(board)
    return board, copy.deepcopy(candidates[0])


def test_validate_rejects_plane_layer_assignment():
    board, c = _one_candidate()
    c["layer_assignment"]["P1"] = "In2.Cu"  # plane 层
    with pytest.raises(PlannerError) as ei:
        validate_candidate(c, board)
    assert "layer_assignment[P1]" in str(ei.value)


def test_validate_rejects_incomplete_route_order():
    board, c = _one_candidate()
    c["route_order"] = c["route_order"][:-1]  # 漏一个分区
    with pytest.raises(PlannerError) as ei:
        validate_candidate(c, board)
    assert "route_order" in str(ei.value)


def test_validate_rejects_polylines_inconsistency():
    board, c = _one_candidate()
    c["polylines"].pop("P5")  # 键与 layer_assignment 不一致
    with pytest.raises(PlannerError) as ei:
        validate_candidate(c, board)
    assert "polylines" in str(ei.value)
    board2, c2 = _one_candidate()
    c2["polylines"]["P5"] = [[0.0, 0.0], [1.0, 1.0]]  # 与分区端点直线不符
    with pytest.raises(PlannerError) as ei2:
        validate_candidate(c2, board2)
    assert "与分区端点直线不符" in str(ei2.value)


def test_validate_rejects_bad_candidate_id():
    board, c = _one_candidate()
    c["candidate_id"] = "X-001"
    with pytest.raises(PlannerError) as ei:
        validate_candidate(c, board)
    assert "candidate_id" in str(ei.value)


def test_validate_rejects_no_principle_with_trace():
    """诊断臂合同：no-principle 臂带非空 trace/rules → 拆坏报错。"""
    board, c = _one_candidate()
    c["arm"] = "no-principle"
    c["generation_trace"] = [{"rule": "P-X", "freedom": "ordering", "effect": "x"}]
    with pytest.raises(PlannerError) as ei:
        validate_candidate(c, board)
    assert "诊断臂合同" in str(ei.value)
