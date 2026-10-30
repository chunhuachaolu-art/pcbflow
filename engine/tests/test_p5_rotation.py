# -*- coding: utf-8 -*-
"""P5⑤-F3 execute 候选轮换驱动层单测（run_p5_board 0.3.0）。

范围：只测 tools/run_p5_board.py 的驱动层轮换逻辑（终局 FAILED → 按候选序
轮换重试 execute_candidate，预算 min(K, len(cands)) 含首轮；tried_candidates
逐轮登记；candidate_source=plan_candidates[k] 口径演进）。

构造手段（任务令许可）：全打桩——plan_candidates / select_best /
execute_candidate / 编译链（build_partition_artifact / compile_board /
build_conflicts / build_pkg 及校验）/ load_stage_board / 台账（rp.ledger 替
身）全部 monkeypatch 于 run_p5_board 模块内，不触真实 v5
编译器/执行器/选择器语义（v5/ 全目录零触碰），不触 out/v5-p5（夹具写
out/v5-upg2/_p5-rotation-tests/，sidecar 越界卫生允许的 out/ 之内），
不触 holdout 台账（替身只记录），零网络、零 kicad-cli（全败路径
check/export/drc 优雅跳过，成功路径 stages=execute 不进 drc）。
"""
import json
import os
import shutil
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
if os.path.join(ROOT, "tools") not in sys.path:
    sys.path.insert(0, os.path.join(ROOT, "tools"))

import run_p5_board as rp  # noqa: E402

# out/ 写入红线：仅限 out/v5-upg2/（自造夹具区，sidecar.assert_allowed 允许）。
CASES_ROOT = os.path.join(ROOT, "out", "v5-upg2", "_p5-rotation-tests")
BOARD_ID = "upg2-rotation-fixture"  # 自造夹具板 id（台账替身认领，非真板）

_ROUTED_ROUTES = {"routes": [{"net_id": "N0", "polyline": [[0.0, 0.0],
                                                            [1.0, 0.0]]}],
                  "stub": True}


class _FakeLedger:
    """tools/p5_holdout_ledger 替身：只记录事件，不触真模块/真台账。"""

    A_LAYER_PREREG = {BOARD_ID: {"nets": 3, "layers": 2, "sha256": "0" * 64}}

    @staticmethod
    def source_path_for(board_id):
        return os.path.join(CASES_ROOT, "fake-src.kicad_pcb")

    def __init__(self):
        self.events = []

    def append(self, *args, **kwargs):
        self.events.append({"action": args[1] if len(args) > 1
                            else kwargs.get("action")})
        return None


def _per_net(idx, status):
    return [{"partition_id": "p%d" % idx, "net_id": "N%d" % idx,
             "status": status, "attempts": 4, "negotiated": True, "vias": 0,
             "length_mm": (1.0 if status == "ROUTED" else 0.0),
             "width_mm": 0.2,
             "layers": (["S1"] if status == "ROUTED" else [])}]


def _install_stubs(monkeypatch, behavior, n_cands, sel_best_idx=None):
    """在 run_p5_board 模块内打桩编译链/规划/选择/执行/台账，返回
    (execute_candidate 调用序号表, 台账替身)。behavior: idx→(verdict, routes)。
    打桩为确定性纯函数（同输入同输出），支撑夹具双跑字节等断言。"""
    calls = []
    monkeypatch.setattr(rp, "build_partition_artifact",
                        lambda board: {"partitions": []})
    monkeypatch.setattr(rp, "compile_board",
                        lambda board: ({"rules": [],
                                        "coverage": {"coverage_pct": 100.0}},
                                       []))
    monkeypatch.setattr(rp, "build_conflicts", lambda board: {"conflicts": []})
    monkeypatch.setattr(rp, "validate_conflicts_artifact", lambda cf: None)
    monkeypatch.setattr(rp, "build_pkg", lambda board, p_art, cf:
                        {"entries": []})
    monkeypatch.setattr(rp, "validate_pkg", lambda pkg: None)

    cands = [{"route_order": ["p%d" % i],
              "layer_assignment": {"p%d" % i: "S1"}, "idx": i}
             for i in range(n_cands)]
    monkeypatch.setattr(rp, "plan_candidates",
                        lambda board, c_art, arm="principle":
                            [dict(c) for c in cands])
    sel_verdict = "SAT" if sel_best_idx is not None else "UNSAT"
    best = dict(cands[sel_best_idx]) if sel_best_idx is not None else None
    monkeypatch.setattr(rp, "select_best",
                        lambda board, cs: {"verdict": sel_verdict,
                                           "best": best,
                                           "per_candidate": []})

    def exec_stub(board, cand, out_dir=None):
        calls.append(cand["idx"])
        verdict, routes = behavior[cand["idx"]]
        status = "ribbon" if verdict == "ROUTED" else "failed"
        return {"verdict": verdict, "routes": routes,
                "per_net": _per_net(cand["idx"], status),
                "negotiation_log": ["stub idx=%d %s" % (cand["idx"], verdict)]}

    monkeypatch.setattr(rp, "execute_candidate", exec_stub)
    fake = _FakeLedger()
    monkeypatch.setattr(rp, "ledger", fake)
    monkeypatch.setattr(rp, "load_stage_board", lambda bid: {
        "provenance": {"board_sha256": "b" * 64}, "board_id": BOARD_ID})
    return calls, fake


def _run(monkeypatch, case_name, behavior, n_cands, sel_best_idx=None,
         stages="execute", rotate_budget=None):
    calls, fake = _install_stubs(monkeypatch, behavior, n_cands, sel_best_idx)
    out_dir = os.path.join(CASES_ROOT, case_name)
    monkeypatch.setattr(rp, "OUT", out_dir)
    argv = ["--board", BOARD_ID, "--stages", stages]
    if rotate_budget is not None:
        argv += ["--rotate-budget", str(rotate_budget)]
    rc = rp.main(argv)
    bdir = os.path.join(out_dir, "boards", BOARD_ID)
    with open(os.path.join(bdir, "run-result.json"), encoding="utf-8") as f:
        rr = json.load(f)["run"]
    with open(os.path.join(bdir, "execute.json"), encoding="utf-8") as f:
        exdoc = json.load(f)
    return rc, rr, exdoc, calls, fake, bdir


@pytest.fixture(scope="module", autouse=True)
def _cases_root():
    """夹具区生命周期：模块级建、模块级整树清除（零残留）。"""
    os.makedirs(CASES_ROOT, exist_ok=True)
    yield CASES_ROOT
    shutil.rmtree(CASES_ROOT, ignore_errors=True)


def test_first_fail_then_second_routes(monkeypatch):
    """验收①：candidate[0] 失败、candidate[1] ROUTED → tried_candidates 2 项、
    candidate_source=plan_candidates[1]、成功即收口。"""
    behavior = {0: ("FAILED", None), 1: ("ROUTED", dict(_ROUTED_ROUTES))}
    rc, rr, exdoc, calls, fake, bdir = _run(
        monkeypatch, "case-success", behavior, n_cands=2)
    assert rc == 0
    ex = rr["execute"]
    assert ex["tried_candidates"] == [
        {"index": 0, "verdict": "FAILED", "first_fail_net": "N0"},
        {"index": 1, "verdict": "ROUTED", "first_fail_net": None}]
    assert ex["candidate_source"] == "plan_candidates[1]"
    assert ex["routed"] is True and ex["exec_verdict"] == "ROUTED"
    assert ex["double_run_equal"] is True
    # 候选序即遍历序：试 [0]、[1]，末轮成功候选双跑核等重跑 [1]
    assert calls == [0, 1, 1]
    # execute.json 同步登记（tried_candidates + 演进后 candidate_source）
    assert exdoc["tried_candidates"] == ex["tried_candidates"]
    assert exdoc["candidate_source"] == "plan_candidates[1]"
    assert exdoc["routes_doc"] is not None
    # 首个 ROUTED 即收口：不进优雅跳过路径
    assert "skipped_stages" not in rr
    # 台账替身只收 pipeline 预登记事件（真台账零接触）
    assert [e["action"] for e in fake.events] == ["pipeline"]


def test_all_fail_graceful_close(monkeypatch):
    """验收②：全部候选 FAILED → 优雅收口（check/export/drc SKIPPED 不崩、
    run-result 落盘、tried 全录、无悬空 drc 预登记事件）。"""
    behavior = {i: ("FAILED", None) for i in range(3)}
    rc, rr, exdoc, calls, fake, bdir = _run(
        monkeypatch, "case-all-fail", behavior, n_cands=3,
        stages="execute,check,export,drc")
    assert rc == 0
    ex = rr["execute"]
    assert [t["index"] for t in ex["tried_candidates"]] == [0, 1, 2]
    assert all(t["verdict"] == "FAILED" for t in ex["tried_candidates"])
    assert [t["first_fail_net"] for t in ex["tried_candidates"]] == \
        ["N0", "N1", "N2"]
    assert ex["candidate_source"] is None
    assert ex["routed"] is False and ex["exec_verdict"] == "FAILED"
    assert ex["double_run_equal"] is True  # 末轮候选 verdict 双跑核等
    assert calls == [0, 1, 2, 2]
    assert rr["skipped_stages"] == ["check", "export", "drc"]
    assert "轮换" in rr["skip_reason"]
    # check/export/drc 无输入未落任何工件（SKIPPED 不崩）
    assert not os.path.isfile(os.path.join(bdir, "check.json"))
    assert not os.path.isfile(os.path.join(bdir, BOARD_ID + ".kicad_pcb"))
    assert not os.path.isfile(os.path.join(bdir, "drc-classified.json"))
    # 无悬空 drc 预登记事件（P5② 修复路径保持）
    assert [e["action"] for e in fake.events] == ["pipeline"]
    assert exdoc["tried_candidates"] == ex["tried_candidates"]
    assert exdoc["routes_doc"] is None


def test_budget_k2_caps_trials(monkeypatch):
    """验收③：K=2 预算生效——3 候选（[2] 可 ROUTED）只试 [0]、[1] 即收口。"""
    behavior = {0: ("FAILED", None), 1: ("FAILED", None),
                2: ("ROUTED", dict(_ROUTED_ROUTES))}
    rc, rr, exdoc, calls, fake, bdir = _run(
        monkeypatch, "case-budget-k2", behavior, n_cands=3,
        stages="execute,check,export,drc", rotate_budget=2)
    assert rc == 0
    ex = rr["execute"]
    assert ex["rotate_budget"] == 2
    assert [t["index"] for t in ex["tried_candidates"]] == [0, 1]
    assert ex["routed"] is False and ex["candidate_source"] is None
    assert calls == [0, 1, 1]
    assert rr["skipped_stages"] == ["check", "export", "drc"]


def test_select_best_hit_first_trial_unchanged_then_rotate(monkeypatch):
    """select_best 命中 cands[1]（首轮行为与 0.2.x 一致）；[1] FAILED →
    按候选序轮换 [0] ROUTED → candidate_source=plan_candidates[0]。"""
    behavior = {0: ("ROUTED", dict(_ROUTED_ROUTES)), 1: ("FAILED", None)}
    rc, rr, exdoc, calls, fake, bdir = _run(
        monkeypatch, "case-selbest", behavior, n_cands=2, sel_best_idx=1)
    assert rc == 0
    ex = rr["execute"]
    assert ex["selection_verdict"] == "SAT"
    assert [t["index"] for t in ex["tried_candidates"]] == [1, 0]
    assert ex["candidate_source"] == "plan_candidates[0]"
    assert ex["routed"] is True
    assert calls == [1, 0, 0]


def test_budget_1_matches_legacy_single_trial(monkeypatch):
    """K=1 等价 0.2.x 单候选行为：只试首轮（后续候选不触）。"""
    behavior = {0: ("FAILED", None), 1: ("ROUTED", dict(_ROUTED_ROUTES))}
    rc, rr, exdoc, calls, fake, bdir = _run(
        monkeypatch, "case-budget-k1", behavior, n_cands=2, rotate_budget=1)
    assert rc == 0
    assert [t["index"] for t in rr["execute"]["tried_candidates"]] == [0]
    assert calls == [0, 0]
    assert rr["execute"]["routed"] is False


def test_double_run_bytes_equal(monkeypatch):
    """验收④：夹具双跑字节等（run-result.json + execute.json）。"""
    behavior = {0: ("FAILED", None), 1: ("ROUTED", dict(_ROUTED_ROUTES))}
    blobs = []
    for sub in ("det-run-a", "det-run-b"):
        rc, rr, exdoc, calls, fake, bdir = _run(
            monkeypatch, sub, behavior, n_cands=2)
        assert rc == 0
        with open(os.path.join(bdir, "run-result.json"), "rb") as f:
            rr_bytes = f.read()
        with open(os.path.join(bdir, "execute.json"), "rb") as f:
            ex_bytes = f.read()
        blobs.append((rr_bytes, ex_bytes))
    assert blobs[0] == blobs[1]


def test_rotate_budget_zero_fails_closed(monkeypatch):
    """--rotate-budget <1 fail-closed（确定性预算必须 ≥1）。"""
    _install_stubs(monkeypatch, {0: ("FAILED", None)}, n_cands=1)
    monkeypatch.setattr(rp, "OUT", os.path.join(CASES_ROOT, "case-bad-k"))
    with pytest.raises(SystemExit, match="rotate-budget"):
        rp.main(["--board", BOARD_ID, "--stages", "execute",
                 "--rotate-budget", "0"])


def test_tool_version():
    """版本钉：0.5.0→0.6.0（V5-R8 TB2 D-8 2026-10-04：execute 后插入
    postprocess 阶段（v5.postprocess/1.0.0）+D-1 routes-raw/routes-final
    双留+下游懒加载 final 优先；此前 0.4.0→0.5.0=V5-D8 2026-09-22 翻转披露：
    hole_to_hole 分类 engine/board-inherent 两类+DRC_CATEGORIES 五元+
    --operator；0.3.0→0.4.0=P5⑥-D6-4 分类器词表件）。"""
    assert rp.VERSION == "0.6.0"
    assert rp.ROTATE_BUDGET == 4
