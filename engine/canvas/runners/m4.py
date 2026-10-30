# -*- coding: utf-8 -*-
"""canvas.runners.m4 -- 布局 runner + 基线臂对照 harness（合同 §1 Lane-M4）。

- plan_actions(st, budget=None) -> [action dicts]: 确定性布局改进规划。
  动作=合同 §2 move/rotate/flip 协议形态——**动作批供编排体接线后
  apply_batch 路径消费**（当前 apply_batch 对此三动作占位拒收
  placecheck-not-built，接线归编排体，见 lane-m4 REPORT 接线契约）。
  **不变更 st**（placements 快照回滚; state_sha256 前后不变）。
  重放语义: 同一起始态按序经 run_m4(st, plan=批) 执行得到同一终态
  （rotate/flip 相对动作在执行期折算绝对覆盖，与规划期同轨迹）。
- run_m4(st, budget=None, plan=None) -> summary: 迭代布局改进。runner
  内部**直接 st.set_placement + canvas.placecheck 判定 + canvas.referee
  评分**驱动迭代（不经 apply_batch 的 move/rotate/flip 路径——该路径
  现为占位拒收）。plan=None: greedy score 攀升（候选流×轮，无改善轮或
  预算尽即止）; plan 注入: 逐动作 placecheck 合法性过滤后应用（**不做
  score 改善要求**——plan 驱动语义，rejected 逐条记录; 测量臂替身计划/
  编排体对照消费）。summary:
    {rounds, evals, accepted_moves, score_before, score_after,
     placements_final, actions[, rejected]}
- baseline_vs_measure(st, budget=None, measure_plan=None) -> {baseline,
  measure}: 基线臂对照 harness——**两臂恒并存**（构建期两臂都测试; 选择
  权归测量/激活跑）。基线臂=原位不动（score 初值+终值**同读**、placements
  快照）; 测量臂=plan_actions 驱动（measure_plan 可注入替身计划）。
  measure 含 delta_total = score_after.total - score_before.total。

候选枚举（确定性; OFFSETS 固定表，无随机源）: 每 pid（sorted）依序
rotate turns∈{1,2,3} → flip 翻转 → move 中心偏移 OFFSETS（格步，相对
进入该分区块时的覆盖中心 snap——块内接受的变更对后续块即时可见，轮末
重建候选流）。相对→绝对折算: rotate=(cur+turns)%4、flip=取反、
move=绝对 target（canvas.placecheck.merge_candidate 绝对语义消费）。
接受准则: referee total 严格改善 > IMPROVE_EPS（1e-12）。budget=评估
次数上界（每次 placecheck 判定计 1，含拒收者; 缺省 DEFAULT_BUDGET=600;
plan 模式同额）。evals/rounds/placements_final 全确定性——同输入同预算
双跑字节等（测试钉死）。
"""
from .. import placecheck as _pc
from .. import referee as _ref

#: move 候选中心偏移表（格步; 固定序=确定性枚举源，pitch 0.5 ⇒ 2 步=1mm）
OFFSETS = ((0, 2), (0, -2), (2, 0), (-2, 0),
           (0, 4), (0, -4), (4, 0), (-4, 0),
           (2, 2), (2, -2), (-2, 2), (-2, -2))
#: 缺省评估预算（budget=None 时取; 每次 placecheck 判定计 1）
DEFAULT_BUDGET = 600
#: score 改善接受阈值（严格改善）
IMPROVE_EPS = 1e-12


def _center_grid(board, lattice, placements, pid):
    """分区覆盖中心（覆盖后端点中点）snap 格点。"""
    eps = _pc.covered_endpoints_mm(board, lattice, placements, pid)
    cx = (eps[0][0] + eps[1][0]) / 2.0
    cy = (eps[0][1] + eps[1][1]) / 2.0
    return lattice.snap(cx, cy)


def _candidate_stream(st):
    """确定性候选流: (协议动作 dict, 部分覆盖 candidate)。

    candidate 为绝对覆盖目标（rotate/flip 已折算），供
    placecheck.check_placement 直接消费。"""
    board, lat = st.board, st.lattice
    for pid in sorted(st.known_partitions()):
        cur = st.placement(pid)
        for t in (1, 2, 3):
            yield ({"action": "rotate", "partition_id": pid, "turns": t},
                   {"rotate": (cur["rotate"] + t) % 4})
        yield ({"action": "flip", "partition_id": pid},
               {"flip": not cur["flip"]})
        ci, cj = _center_grid(board, lat, st.placements, pid)
        for di, dj in OFFSETS:
            tgt = [ci + di, cj + dj]
            yield ({"action": "move", "partition_id": pid, "target": tgt},
                   {"move": tgt})


def _action_partial(st, act):
    """协议动作 → (partition_id, 部分覆盖 candidate)。

    非 move/rotate/flip 形态返回 (None, None, code)（E_UNKNOWN_ACTION
    借 protocol 码语义——plan 面动作枚举外）; rotate.turns 非法返回
    E_GRID_OUT_OF_BOUNDS（D-CT-002 归码口径）。"""
    a = act.get("action")
    pid = act.get("partition_id")
    if a == "rotate":
        t = act.get("turns")
        if isinstance(t, bool) or not isinstance(t, int) or t not in (1, 2, 3):
            return None, None, "E_GRID_OUT_OF_BOUNDS"
        return pid, {"rotate": (st.placement(pid)["rotate"] + t) % 4}, None
    if a == "flip":
        return pid, {"flip": not st.placement(pid)["flip"]}, None
    if a == "move":
        return pid, {"move": list(act.get("target"))}, None
    return None, None, "E_UNKNOWN_ACTION"


def _apply_candidate(st, pid, partial):
    cov = _pc.merge_candidate(st.placements, pid, partial)
    st.set_placement(pid, move=cov["move"], rotate=cov["rotate"],
                     flip=cov["flip"])


def _normalized(st):
    return {pid: {"move": (list(st.placements[pid]["move"])
                           if st.placements[pid].get("move") is not None
                           else None),
                  "rotate": st.placements[pid].get("rotate", 0),
                  "flip": bool(st.placements[pid].get("flip", False))}
            for pid in sorted(st.placements)}


def _run(st, budget, plan, apply):
    board, lat = st.board, st.lattice
    if budget is None:
        budget = DEFAULT_BUDGET
    saved = st.placements
    score_before = _ref.score(board, lat, dict(st.placements))
    cur_total = score_before["total"]
    accepted, rejected = [], []
    evals, rounds = 0, 0
    if plan is not None:
        rounds = 1
        for act in plan:
            if evals >= budget:
                break
            evals += 1
            pid, partial, code = _action_partial(st, act)
            if partial is None:
                rejected.append({"action": dict(act), "code": code,
                                 "detail": "plan 面动作形态非法"})
                continue
            ok, pcode, detail = _pc.check_placement(
                board, lat, st.placements, pid, partial)
            if not ok:
                rejected.append({"action": dict(act), "code": pcode,
                                 "detail": detail})
                continue
            _apply_candidate(st, pid, partial)
            accepted.append(dict(act))
    else:
        improving = True
        while improving and evals < budget:
            improving = False
            rounds += 1
            for act, partial in _candidate_stream(st):
                if evals >= budget:
                    break
                evals += 1
                ok, _code, _detail = _pc.check_placement(
                    board, lat, st.placements, act["partition_id"], partial)
                if not ok:
                    continue
                snap = st.placements
                _apply_candidate(st, act["partition_id"], partial)
                s = _ref.score(board, lat, dict(st.placements))
                if s["total"] > cur_total + IMPROVE_EPS:
                    cur_total = s["total"]
                    accepted.append(dict(act))
                    improving = True
                else:
                    st.placements = snap      # 拒绝即回滚（copy-on-write 快照）
    score_after = _ref.score(board, lat, dict(st.placements))
    placements_final = _normalized(st)
    if not apply:
        st.placements = saved                # plan_actions: 不变更 st
    else:
        st.recompute_connectivity()
    summary = {"rounds": rounds, "evals": evals,
               "accepted_moves": len(accepted),
               "score_before": score_before, "score_after": score_after,
               "placements_final": placements_final,
               "actions": accepted}
    if plan is not None:
        summary["rejected"] = rejected
    return summary


def plan_actions(st, budget=None):
    """确定性布局改进规划（greedy score 攀升; **不变更 st**）→ 协议
    动作批（move/rotate/flip; 合同 §2 形态，供编排体接线后 apply_batch
    路径与台账消费; 重放经 run_m4(st, plan=批)）。"""
    return _run(st, budget, plan=None, apply=False)["actions"]


def run_m4(st, budget=None, plan=None):
    """迭代布局改进 → summary（就地变更 st.placements; 收尾重算连通账本）。

    放置合法性判定=canvas.placecheck（新 validator，非 v5.drc 移植）;
    评分=canvas.referee（确定性）。"""
    return _run(st, budget, plan, apply=True)


def baseline_vs_measure(st, budget=None, measure_plan=None):
    """基线臂对照 harness（两臂恒并存; 构建期两臂都测试）。

    baseline: 原位不动——score 初值/终值**同读**（同一 placements 快照
    两次评分，结构性相等）+ placements 快照。
    measure: plan_actions 驱动（measure_plan=None）或注入替身计划——
    score 初值/终值经 run_m4 实测、accepted_moves、placements_final、
    delta_total=after.total-before.total。"""
    board, lat = st.board, st.lattice
    base_pl = {pid: {"move": (list(cov["move"]) if cov.get("move") is not None
                              else None),
                     "rotate": cov.get("rotate", 0),
                     "flip": bool(cov.get("flip", False))}
               for pid, cov in sorted(st.placements.items())}
    s_base = _ref.score(board, lat, base_pl)
    baseline = {"placements": base_pl,
                "score_initial": s_base,
                "score_final": _ref.score(board, lat, base_pl)}
    summary = run_m4(st, budget, plan=measure_plan)
    measure = {"score_initial": summary["score_before"],
               "score_final": summary["score_after"],
               "accepted_moves": summary["accepted_moves"],
               "placements_final": summary["placements_final"],
               "delta_total": round(summary["score_after"]["total"]
                                    - summary["score_before"]["total"], 9)}
    return {"baseline": baseline, "measure": measure}
