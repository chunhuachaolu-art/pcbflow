# -*- coding: utf-8 -*-
"""Lane-M4 runner/harness 测试: run_m4/plan_actions/baseline_vs_measure
不变量 + **放置后铜面 validate_full 对照**（走真 v5.drc 绑定——与
placecheck 自有夹具矩阵相区隔: placecheck 过 ⇒ 铜面无**新增**违例）+
确定性双跑字节等（真板+合成微板各 1）。"""
import json

from canvas import placecheck as pc
from canvas import referee as ref
from canvas import validate as cv
from canvas.runners import m4
from canvas.tests.test_k1_fixtures import real_state, synth_state
from canvas.tests.test_m4_fixtures import blocked_state


# ---------------------------------------------------------------- runner

def test_plan_actions_is_pure_plan():
    st = blocked_state()
    sha0 = st.sha256()
    plan = m4.plan_actions(st, 200)
    assert st.sha256() == sha0                 # 不变更 st
    assert len(plan) > 0                        # 堵塞板存在改善
    for a in plan:
        assert a["action"] in ("move", "rotate", "flip")
        assert set(a) <= {"action", "partition_id", "target", "turns"}
    json.dumps(plan)                            # 台账面 JSON 可落


def test_run_m4_improves_blocked_board():
    st = blocked_state()
    s = m4.run_m4(st, 200)
    assert s["accepted_moves"] > 0
    assert s["score_after"]["total"] > s["score_before"]["total"]
    assert s["evals"] <= 200 and s["rounds"] >= 1
    # 收工态: 全场布间零违例（runner 只落 placecheck 接受项）
    assert pc.check_all_placements(st.board, st.lattice,
                                   st.placements) == []
    assert st.placements == s["placements_final"]


def test_run_m4_flat_on_open_synth_baseline():
    """合成微板基线开阔: 一切候选 score 不改善 → 零接受、状态不动
    （确定性退化路径——score 平坦不是错误）。"""
    st = synth_state()
    sha0 = st.sha256()
    s = m4.run_m4(st, 200)
    assert s["accepted_moves"] == 0 and s["placements_final"] == {}
    assert s["score_after"]["total"] == s["score_before"]["total"]
    assert st.sha256() == sha0


def test_plan_replay_faithful():
    """plan_actions 批在新鲜态经 run_m4(plan=批) 重放 → 同一终态
    （编排体 apply_batch 接线后的等价性锚）。"""
    st1 = blocked_state()
    plan = m4.plan_actions(st1, 200)
    st2 = blocked_state()
    rep = m4.run_m4(st2, 600, plan=plan)
    assert rep["accepted_moves"] == len(plan)
    assert rep.get("rejected", []) == []
    st3 = blocked_state()
    direct = m4.run_m4(st3, 200)
    assert rep["placements_final"] == direct["placements_final"]


def test_baseline_vs_measure_two_arms():
    st = blocked_state()
    hv = m4.baseline_vs_measure(st, 200)
    # 基线臂: 原位不动——初终同读
    assert hv["baseline"]["score_initial"] == hv["baseline"]["score_final"]
    assert hv["baseline"]["placements"] == {}
    # 测量臂: plan_actions 驱动
    m = hv["measure"]
    assert m["accepted_moves"] > 0
    assert m["delta_total"] == round(m["score_final"]["total"]
                                     - m["score_initial"]["total"], 9)
    assert m["delta_total"] > 0.0
    assert m["placements_final"] == st.placements


def test_baseline_vs_measure_injected_plan():
    st = blocked_state()
    plan = [{"action": "flip", "partition_id": "PC1"}]
    hv = m4.baseline_vs_measure(st, 50, measure_plan=plan)
    assert hv["measure"]["accepted_moves"] == 1
    assert hv["baseline"]["score_initial"] == hv["baseline"]["score_final"]


# ------------------------------------------------- 确定性双跑（≥2）

def test_double_run_byte_equal_synth():
    """双跑 #1（合成微板）: run_m4 摘要 JSON 字节等 + state_sha256 等 +
    referee score 等。"""
    st_a = synth_state()
    st_b = synth_state()
    s_a = m4.run_m4(st_a, 200)
    s_b = m4.run_m4(st_b, 200)
    assert json.dumps(s_a, sort_keys=True) == json.dumps(s_b, sort_keys=True)
    assert st_a.sha256() == st_b.sha256()
    sc_a = ref.score(st_a.board, st_a.lattice, st_a.placements)
    sc_b = ref.score(st_b.board, st_b.lattice, st_b.placements)
    assert sc_a == sc_b


def test_double_run_byte_equal_real():
    """双跑 #2（真板）: 同上口径（真板包络语义下零接受——确定性退化）。"""
    st_a = real_state()
    st_b = real_state()
    s_a = m4.run_m4(st_a, 600)
    s_b = m4.run_m4(st_b, 600)
    assert json.dumps(s_a, sort_keys=True) == json.dumps(s_b, sort_keys=True)
    assert st_a.sha256() == st_b.sha256()
    sc_a = ref.score(st_a.board, st_a.lattice, st_a.placements)
    sc_b = ref.score(st_b.board, st_b.lattice, st_b.placements)
    assert sc_a == sc_b


def test_double_run_byte_equal_blocked():
    """双跑 #3（堵塞板, 接受路径在飞）: 摘要/哈希/评分三重字节等。"""
    st_a = blocked_state()
    st_b = blocked_state()
    s_a = m4.run_m4(st_a, 300)
    s_b = m4.run_m4(st_b, 300)
    assert s_a["accepted_moves"] > 0
    assert json.dumps(s_a, sort_keys=True) == json.dumps(s_b, sort_keys=True)
    assert st_a.sha256() == st_b.sha256()


# ------------------------------------------------- 放置后铜面 validate_full
# 对照（≥4 例, 走真 v5.drc 绑定: placecheck 过 ⇒ 铜面无**新增**违例;
# 真板 2 例板固有 R5 违例为基线事实, 差集口径不归责放置——与
# canvas.validate 差集归责纪律同构）

def _vkeys(report):
    return sorted((v.rule, str(v.subject_a), str(v.subject_b))
                  for v in report.violations)


def test_contrast_synth_baseline_full_clean():
    """对照 1: 合成微板基线（无覆盖）→ validate_full 零违例。"""
    rep = cv.validate_full(synth_state())
    assert rep.clean and rep.violations == []


def test_contrast_accepted_moves_add_no_copper_violations():
    """对照 2: 堵塞板 run_m4 接受的放置 → validate_full 违例集==基线
    （零新增, 基线本身净空）。"""
    st0 = blocked_state()
    base_keys = _vkeys(cv.validate_full(st0))
    assert base_keys == []
    st = blocked_state()
    m4.run_m4(st, 200)
    assert st.placements
    after_keys = _vkeys(cv.validate_full(st))
    assert after_keys == base_keys


def test_contrast_handcrafted_move_full_clean():
    """对照 3: 合成微板手工放置（placecheck 收）→ validate_full 净空。"""
    st = synth_state()
    ok, code, _d = pc.check_placement(st.board, st.lattice,
                                      st.placements, "PA",
                                      {"move": [16, 4]})
    assert ok, code
    st.set_placement("PA", move=[16, 4])
    rep = cv.validate_full(st)
    assert rep.clean and rep.violations == []


def test_contrast_rotate_flip_full_clean():
    """对照 4: 合成微板 rotate+flip 覆盖（placecheck 收）→ validate_full
    净空。"""
    st = synth_state()
    ok, code, _d = pc.check_placement(st.board, st.lattice,
                                      st.placements, "PC1",
                                      {"rotate": 1, "flip": True})
    assert ok, code
    st.set_placement("PC1", rotate=1, flip=True)
    rep = cv.validate_full(st)
    assert rep.clean and rep.violations == []


def test_contrast_real_board_baseline_inherent():
    """对照 5（真板）: 基线 2 例板固有 R5 pad 违例（0.22mm, D8 数据源
    事实）; run_m4 零放置 → 违例集差为空（放置不新增铜面违例）。"""
    st = real_state()
    base = cv.validate_full(st)
    assert len(base.violations) == 2
    assert all(v.rule == "R5" for v in base.violations)
    s = m4.run_m4(st, 600)
    assert s["placements_final"] == {}
    after = cv.validate_full(st)
    assert _vkeys(after) == _vkeys(base)
