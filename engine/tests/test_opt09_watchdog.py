# -*- coding: utf-8 -*-
"""OPT-09 候选级健康度看门狗测试（EXEC-R2 E2，2026-10-08；stdlib+pytest）。

正负机械规则测试（A1 applyConditions 09-F 逐条；虚拟时间=受控 fixture，
真实 600s 常数由 test_rule_constants_pinned 钉死、绝不缩短真实时钟语义）：
- 应停：三零 ×2 次有效观测、首末间隔 ≥600s、同进程身份；
- 不停：单次三零 / 间隔不足 / 任一信号推进（CPU、输出、进度分别证伪）/
  unknown 或观测缺失 / PID 重用 / 身份不可验证 / 负增量 / 时钟回退 /
  纯墙钟时长（结构上无入口）；
- 监控器自身输出与空转心跳不算输出增长或候选推进（既不虚增健康、也不
  掩盖停滞）。
接线与字节隔离：executor 默认关闭零行为差；sidecar 开/关 canonical 字节
相等；真实边界事件（candidate_start/partition_start/attempt/net_done/
candidate_done）由执行线程产出；短路路径收口；有界写入与 IO 降级。
"""
import importlib.util
import json
import os
import sys
import time

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from v5 import canonical  # noqa: E402
from v5.board import compute_board_sha256, load_board  # noqa: E402
from v5.executor import execute_candidate  # noqa: E402
from v5.health_watchdog import (  # noqa: E402
    DEFAULT_MAX_BYTES, DEFAULT_MAX_EVENTS, ENV_SIDECAR, ENV_WORLD_ID,
    STOP_INTERVAL_MIN_S, STOP_ZERO_OBS_REQUIRED, ProgressSidecar,
    SidecarReader, SignalSample, StopLineRule, collect_output_state,
    kill_tree_bytes, process_identity_self, process_times)

_spec = importlib.util.spec_from_file_location(
    "opt09_watchdog", os.path.join(ROOT, "tools", "opt09_watchdog.py"))
opt09_watchdog = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(opt09_watchdog)


# ---------------------------------------------------------------- 夹具

SIG = [{"id": "F.Cu", "kind": "signal", "preferred_direction": "h", "available": True},
       {"id": "B.Cu", "kind": "signal", "preferred_direction": "any", "available": True}]
WS = {"x_min": 0.0, "y_min": 0.0, "x_max": 20.0, "y_max": 20.0}
HARD = {"R1": {"floor_mm": 0.3, "k_a": 0.4},
        "R2": {"max_parallel_mm": 5.0, "min_distance_mm": 3.0},
        "R3": {"unsplittable": True},
        "R4": {"max_distance_mm": 2.0, "return_via_required": True},
        "R5": {"min_clearance_mm": 0.5},
        "R6": {"keepout_zones_forbidden": True, "plane_forbidden": True}}


def part(pid, a, b):
    return {"partition_id": pid, "ptype": "MISC", "layer_policy": "F.Cu",
            "planned_width": 0.2, "current_a": 0.0,
            "geometry": {"endpoints": [list(a), list(b)]},
            "speed_class": "low_speed",
            "width_prior": {"w_min": 0.2, "w_max": 0.2}}


def net(nid, pids):
    return {"net_id": nid, "net_class": "MISC", "partitions": list(pids)}


def tiny_board():
    board = {"schema_version": "v5.board.v1", "board_id": "opt09-test",
             "stackup": SIG, "workspace": WS, "zones": [],
             "partitions": [part("P1", (2, 2), (12, 2)),
                            part("P2", (2, 10), (12, 10))],
             "nets": [net("N1", ["P1"]), net("N2", ["P2"])],
             "hard_rules": HARD, "principle_registry": [],
             "provenance": {"source_type": "synthetic", "source_uri": "hand",
                            "source_sha256": "0" * 64, "adapter": "hand"}}
    board["provenance"]["board_sha256"] = compute_board_sha256(board)
    return load_board(board)


def cand_for(board):
    order = [p["partition_id"] for p in board["partitions"]]
    return {"candidate_id": "C-001", "arm": "no-principle",
            "provenance": {"generator": "v5.planner/0.1.0",
                           "rules_consumed": [], "compiled_sha256": "0" * 64},
            "route_order": order,
            "layer_assignment": {p: "F.Cu" for p in order},
            "polylines": {}, "generation_trace": []}


def result_core_sha(res):
    return canonical.canonical_sha256(
        {"verdict": res["verdict"], "routes": res["routes"],
         "per_net": res["per_net"], "negotiation_log": res["negotiation_log"]})


def sample(t, cpu, out, prg, pid=101, create=1_700_000_000.0):
    return SignalSample(t, pid, create, cpu, out, prg)


# ------------------------------------------------- 一、停线规则（虚拟时间）

def test_rule_constants_pinned():
    """真实时钟机械常数钉死：600s 双采样不可配置缩短（A1 09-C）。"""
    assert STOP_INTERVAL_MIN_S == 600.0
    assert STOP_ZERO_OBS_REQUIRED == 2
    assert StopLineRule().interval_min_s == 600.0


def test_stop_qualified_two_zero_records_span_600s():
    """应停（正样本）：三零连续观测、首末间隔恰 ≥600s。"""
    rule = StopLineRule()
    rule.feed(sample(0, 100.0, 500, 3))
    for i in range(1, 11):
        t = 60.0 * i
        d = rule.feed(sample(t, 100.0, 500, 3))
        assert not d.qualified
    d = rule.feed(sample(660.0, 100.0, 500, 3))
    assert d.qualified and d.state == "stop_qualified"
    assert d.details["zero_obs_count"] == 11
    assert d.details["streak_span_s"] == 600.0


def test_single_zero_record_never_stops():
    """不停：单次三零（无第二次有效观测）。"""
    rule = StopLineRule()
    rule.feed(sample(0, 10.0, 100, 1))
    d = rule.feed(sample(60.0, 10.0, 100, 1))
    assert not d.qualified and d.state == "zero_streak"


def test_zero_records_interval_below_600_never_stops():
    """不停：两次三零但间隔 <600s。"""
    rule = StopLineRule()
    rule.feed(sample(0, 10.0, 100, 1))
    d = rule.feed(sample(60.0, 10.0, 100, 1))
    d = rule.feed(sample(599.9, 10.0, 100, 1))
    assert not d.qualified and d.state == "zero_streak"
    assert d.details["streak_span_s"] == 539.9


def test_cpu_advance_resets_and_never_stops():
    """不停：CPU 增量 >0（活跃样本）；且推进重置零链——若未重置，60→660
    本会在 660 判停，此处必须仍不停（间隔从 420 起算 <600）。"""
    rule = StopLineRule()
    rule.feed(sample(0, 10.0, 100, 1))
    rule.feed(sample(60, 10.0, 100, 1))
    rule.feed(sample(120, 10.0, 100, 1))
    d = rule.feed(sample(360, 15.0, 100, 1))     # CPU 推进 → active
    assert not d.qualified and d.state == "active"
    for t in (420, 480, 540, 600, 660):
        d = rule.feed(sample(t, 15.0, 100, 1))
        assert not d.qualified


def test_output_advance_never_stops():
    """不停：工作输出增长（输出增长=真实工作信号）。"""
    rule = StopLineRule()
    rule.feed(sample(0, 10.0, 100, 1))
    d = rule.feed(sample(600, 10.0, 100, 1))
    assert d.state == "zero_streak"
    d = rule.feed(sample(1200, 10.0, 250, 1))
    assert not d.qualified and d.state == "active"


def test_progress_advance_never_stops():
    """不停：真实候选/网进度推进。"""
    rule = StopLineRule()
    rule.feed(sample(0, 10.0, 100, 1))
    d = rule.feed(sample(600, 10.0, 100, 1))
    assert d.state == "zero_streak"
    d = rule.feed(sample(1200, 10.0, 100, 4))
    assert not d.qualified and d.state == "active"


def test_unknown_or_missing_observation_is_not_zero():
    """不停：任一信号 None（unknown/读取失败）——缺失绝不充当零，链重置。"""
    rule = StopLineRule()
    rule.feed(sample(0, 10.0, 100, 1))
    rule.feed(sample(60, 10.0, 100, 1))
    d = rule.feed(sample(120, None, 100, 1))     # CPU 读取失败
    assert not d.qualified and d.state == "observation_missing"
    # 缺失后即便再满 600s 三零，也只能从缺失之后重新起算（缺失样本本身
    # 还吞掉一个有效差分位：t=180 的差分对侧=t=120 缺失样本→仍无效）
    for t in range(180, 901, 60):
        d = rule.feed(sample(float(t), 10.0, 100, 1))
    assert d.qualified          # 240→840 共 600s，缺失后重新成链（机械正确）


def test_pid_reuse_cancels_and_never_qualifies():
    """不停：PID 重用（同 pid 不同创建时间）——身份变化重置，不以旧链判停。"""
    rule = StopLineRule()
    rule.feed(sample(0, 10.0, 100, 1, create=111.0))
    rule.feed(sample(600, 10.0, 100, 1, create=111.0))
    d = rule.feed(sample(601, 10.0, 100, 1, create=222.0))   # 重用
    assert not d.qualified and d.state == "identity_change"
    d = rule.feed(sample(700, 10.0, 100, 1, create=222.0))
    assert not d.qualified      # 新身份须重新双采样 600s


def test_identity_unverified_never_qualifies():
    """不停：创建时间不可得（进程归属不明）——机械上不可能取得停线资格。"""
    rule = StopLineRule()
    rule.feed(sample(0, 10.0, 100, 1, create=None))
    for t in range(60, 3001, 60):     # 50 分钟纯三零
        d = rule.feed(sample(float(t), 10.0, 100, 1, create=None))
        assert not d.qualified
    assert d.state == "identity_unverified"


def test_negative_increment_cancels():
    """不停：负增量（读取/时钟异常）。"""
    rule = StopLineRule()
    rule.feed(sample(0, 10.0, 100, 1))
    d = rule.feed(sample(60, 9.5, 100, 1))
    assert not d.qualified and d.state == "negative_increment"


def test_clock_regression_cancels():
    """不停：mono_t 回退（时钟异常）。"""
    rule = StopLineRule()
    rule.feed(sample(100.0, 10.0, 100, 1))
    d = rule.feed(sample(99.0, 10.0, 100, 1))
    assert not d.qualified and d.state == "clock_anomaly"


def test_duration_alone_never_qualifies():
    """不停：纯墙钟时长（模拟 3 天、500 样本、CPU 恒推进）——规则结构上
    无时长入口，永不判停（26h 真耗时前科的「慢而活」保护）。"""
    rule = StopLineRule()
    d = None
    for i in range(1, 501):
        d = rule.feed(sample(60.0 * i * 8.64, 10.0 + 0.001 * i, 100, 1))
        assert not d.qualified
    assert d.state == "active"


# --------------------------------------- 二、监控器自输出/心跳不计入（A1 核心）

def test_heartbeat_and_monitor_output_do_not_mask_stall(tmp_path):
    """纠正核心：只有监控器自身文件增长 + 侧车空转心跳（无 work、CPU 零）
    → 工作输出/进度恒零 → 三零成立即应停（监控器不得自己制造健康）。"""
    sc_path = str(tmp_path / "sidecar.jsonl")
    sc = ProgressSidecar(sc_path, manifest={"t": 1}, heartbeat_interval_s=0)
    sc.emit_work("candidate_start")
    monitor_file = tmp_path / "samples.jsonl"
    monitor_file.write_text("monitor line 1\n")
    run_log = tmp_path / "run.log"
    run_log.write_text("child header\n")
    reader = SidecarReader(sc_path)
    st1 = collect_output_state(str(run_log), str(tmp_path / "result.json"),
                               reader)
    assert st1["output_bytes"] is not None
    base_out, base_prg = st1["output_bytes"], st1["progress_seq"]
    # 监控器输出增长 ×3、侧车心跳 ×3（同一 sidecar 对象继续写），无新工作
    monitor_file.write_text("monitor line 1\nmonitor 2\nmonitor 3\n")
    sc.emit_heartbeat()
    sc.emit_heartbeat()
    sc.emit_heartbeat()
    st2 = collect_output_state(str(run_log), str(tmp_path / "result.json"),
                               reader)
    assert st2["output_bytes"] == base_out          # 监控器输出/心跳未计入
    assert st2["progress_seq"] == base_prg
    assert st2["sidecar_snapshot"]["heartbeats"] == 3
    rule = StopLineRule()
    ident_create = process_times(os.getpid())[1]
    rule.feed(SignalSample(0.0, os.getpid(), ident_create,
                           5.0, st1["output_bytes"], st1["progress_seq"]))
    rule.feed(SignalSample(60.0, os.getpid(), ident_create,
                           5.0, st2["output_bytes"], st2["progress_seq"]))
    d = rule.feed(SignalSample(660.0, os.getpid(), ident_create,
                               5.0, st2["output_bytes"], st2["progress_seq"]))
    assert d.qualified        # 空转心跳+监控器输出没能掩盖停滞
    sc.close()


def test_work_event_does_advance_progress_and_prevents_stop(tmp_path):
    """反面：真实 work 事件推进 progress_seq → 不停（心跳≠work 的对照）。"""
    sc_path = str(tmp_path / "sidecar.jsonl")
    run_log = tmp_path / "run.log"
    run_log.write_text("child header\n")
    sc = ProgressSidecar(sc_path, heartbeat_interval_s=0)
    sc.emit_work("net_done", status="routed")
    reader = SidecarReader(sc_path)
    st1 = collect_output_state(str(run_log), str(tmp_path / "result.json"),
                               reader)
    assert st1["progress_seq"] == 1
    sc.emit_work("net_done", status="routed")
    st2 = collect_output_state(str(run_log), str(tmp_path / "result.json"),
                               reader)
    assert st2["progress_seq"] == st1["progress_seq"] + 1
    sc.close()
    rule = StopLineRule()
    rule.feed(SignalSample(0.0, 1, 1.0, 5.0, st1["output_bytes"],
                           st1["progress_seq"]))
    d = rule.feed(SignalSample(660.0, 1, 1.0, 5.0, st2["output_bytes"],
                               st2["progress_seq"]))
    assert not d.qualified and d.state == "active"


# --------------------------------------------------------------- 三、侧车

def test_sidecar_manifest_binds_identity_and_world():
    ident = process_identity_self()
    assert ident["pid"] == os.getpid()
    assert ident["pid_create_time"] is not None   # Windows ctypes 可得


def test_sidecar_bounded_write_truncates(tmp_path):
    sc_path = str(tmp_path / "bounded.jsonl")
    sc = ProgressSidecar(sc_path, heartbeat_interval_s=0,
                         max_events=3, max_bytes=1 << 20)
    sc.emit_work("a")
    sc.emit_work("b")
    sc.emit_work("c")
    assert not sc.truncated          # 上界=3：恰可写 3 条
    sc.emit_work("d")                # 第 4 条 → 写截断注记后停写
    assert sc.truncated
    n_before = len(open(sc_path, encoding="utf-8").read().splitlines())
    sc.emit_work("e")
    sc.emit_heartbeat()
    sc.close()
    assert len(open(sc_path, encoding="utf-8").read().splitlines()) == n_before
    snap = SidecarReader(sc_path).snapshot()
    assert snap.truncated and snap.work_events == 3
    # 字节上界同理
    sc2 = ProgressSidecar(str(tmp_path / "b2.jsonl"), heartbeat_interval_s=0,
                          max_events=1000, max_bytes=120)
    for i in range(20):
        sc2.emit_work("evt-%03d" % i)
    assert sc2.truncated
    assert os.path.getsize(str(tmp_path / "b2.jsonl")) <= 120


def test_sidecar_io_failure_degrades_never_raises(tmp_path):
    """侧车 IO 失败只降级：引擎绝不受侧车拖累。"""
    blocker = tmp_path / "blocker"
    blocker.write_text("i am a file")
    bad = str(blocker / "sub" / "sidecar.jsonl")   # 父路径是文件 → 必败
    os.environ[ENV_SIDECAR] = bad
    try:
        sc = ProgressSidecar.from_env({"x": 1})
        assert sc is not None and sc.broken
        sc.emit_work("never")       # 不抛
        sc.close()                  # 不抛
    finally:
        os.environ.pop(ENV_SIDECAR, None)


def test_sidecar_heartbeat_thread_writes_channel_only(tmp_path):
    sc_path = str(tmp_path / "hb.jsonl")
    sc = ProgressSidecar(sc_path, heartbeat_interval_s=0.05)
    sc.emit_work("one")
    time.sleep(0.25)
    sc.emit_work("two")
    sc.close()
    lines = [json.loads(l) for l in open(sc_path, encoding="utf-8")]
    kinds = {l["kind"] for l in lines}
    assert "heartbeat" in kinds and "work" in lines[0]["kind"]
    hbs = [l for l in lines if l["kind"] == "heartbeat"]
    works = [l for l in lines if l["kind"] == "work"]
    assert len(hbs) >= 2
    assert all("progress_seq" not in l for l in hbs)   # 心跳不推进度
    assert [l["progress_seq"] for l in works] == [1, 2]
    snap = SidecarReader(sc_path).snapshot()
    assert snap.heartbeats == len(hbs)
    assert snap.work_events == 2 and snap.progress_seq == 2
    assert snap.closed
    # work_bytes 只含 work 行（心跳不计入工作输出）
    work_line_bytes = sum(len(json.dumps(l, ensure_ascii=True,
                                         sort_keys=True)) + 1
                          for l in works)
    assert snap.work_bytes == work_line_bytes


def test_kill_tree_bytes_gbk_safe():
    """GBK 收尾坑修复：解码面对任意本地化字节不抛（errors=replace）。"""
    rc, tail = kill_tree_bytes(999999999)     # 不存在的 pid → taskkill 报错
    assert isinstance(rc, int)
    assert isinstance(tail, str)              # 任意输出（含 GBK 中文）不崩


# ------------------------------------------- 四、executor 接线与字节隔离

def test_execute_candidate_default_off(tmp_path):
    """默认关闭：无环境变量 → 不建任何侧车文件，结果确定性。"""
    board = tiny_board()
    cand = cand_for(board)
    r1 = execute_candidate(board, dict(cand))
    r2 = execute_candidate(board, dict(cand))
    assert r1["verdict"] == "ROUTED"
    assert result_core_sha(r1) == result_core_sha(r2)


def test_execute_candidate_sidecar_on_canonical_byte_equal(tmp_path):
    """接线不污染 canonical：开/关 sidecar 的 result_core/routes/negotiation
    /per_net canonical 全等（canonical routes 字节隔离，A1 09-B）。"""
    board = tiny_board()
    cand = cand_for(board)
    r_off = execute_candidate(board, dict(cand))
    sc_path = str(tmp_path / "on.jsonl")
    os.environ[ENV_SIDECAR] = sc_path
    os.environ[ENV_WORLD_ID] = "pytest-world"
    os.environ["V5_OPT09_HEARTBEAT_S"] = "0"
    try:
        r_on = execute_candidate(board, dict(cand))
    finally:
        os.environ.pop(ENV_SIDECAR, None)
        os.environ.pop(ENV_WORLD_ID, None)
        os.environ.pop("V5_OPT09_HEARTBEAT_S", None)
    assert r_on["verdict"] == r_off["verdict"] == "ROUTED"
    assert result_core_sha(r_on) == result_core_sha(r_off)
    assert canonical.canonical_sha256(r_on["routes"]) == \
        canonical.canonical_sha256(r_off["routes"])
    assert canonical.canonical_sha256(r_on["negotiation_log"]) == \
        canonical.canonical_sha256(r_off["negotiation_log"])
    assert canonical.canonical_sha256(r_on["per_net"]) == \
        canonical.canonical_sha256(r_off["per_net"])
    # 真实边界事件（执行线程产出）
    lines = [json.loads(l) for l in open(sc_path, encoding="utf-8")]
    works = [l for l in lines if l["kind"] == "work"]
    types = [l["type"] for l in works]
    assert types[0] == "candidate_start"
    assert types[-1] == "candidate_done"
    assert types.count("partition_start") == 2
    assert types.count("net_done") == 2
    assert types.count("attempt") >= 2          # 每网至少一次尝试边界
    seqs = [l["progress_seq"] for l in works]
    assert seqs == list(range(1, len(works) + 1))  # 单调 +1，无虚增
    manifest = SidecarReader.read_manifest(sc_path)
    assert manifest["world_id"] == "pytest-world"
    assert manifest["board_id"] == board["board_id"]
    assert manifest["candidate_sha256"] == canonical.canonical_sha256(cand)
    assert manifest["schema_version"] == r_on["routes"]["schema_version"]
    assert manifest["identity"]["pid"] == os.getpid()
    assert manifest["identity"]["pid_create_time"] is not None


def test_execute_candidate_shortcircuit_path_closes_sidecar(
        tmp_path, monkeypatch):
    """SC-1 短路路径也有候选边界收口（monkeypatch 短路件=只验接线面）。"""
    import v5.executor as ex_mod
    board = tiny_board()
    cand = cand_for(board)
    sc_path = str(tmp_path / "short.jsonl")
    monkeypatch.setenv(ENV_SIDECAR, sc_path)
    monkeypatch.setenv("V5_OPT09_HEARTBEAT_S", "0")
    monkeypatch.setattr(
        ex_mod, "_preflight_seal_shortcircuit",
        lambda ctx, order, log: {"verdict": "FAILED", "routes": None,
                                 "per_net": [], "negotiation_log": log})
    res = execute_candidate(board, dict(cand))
    assert res["verdict"] == "FAILED"
    lines = [json.loads(l) for l in open(sc_path, encoding="utf-8")]
    types = [l["type"] for l in lines if l["kind"] == "work"]
    assert types == ["candidate_start", "candidate_done"]
    done = [l for l in lines if l["type"] == "candidate_done"][0]
    assert done["outcome"] == "sealed-short-circuit"
    assert SidecarReader(sc_path).snapshot().closed


# --------------------------------------------------- 五、工具（观测窗/回放）

def test_observe_window_hard_bound_and_missing_progress_no_false_kill(
        tmp_path):
    """窗硬界含采样粒度（≤预算收窗）+ 缺失进度≠零（绝不误杀无侧车进程）。"""
    run_dir = str(tmp_path / "win")
    s = opt09_watchdog.run_observation(
        [sys.executable, "-c", "import time; time.sleep(60)"],
        run_dir=run_dir, world_id="w-test", window_s=4.0, interval_s=0.5,
        cwd=str(tmp_path), stop_mode="stop", sidecar_on=True)
    assert s["status"] == "unfinished_in_window_killed_by_window_end"
    assert s["window"]["observed_s"] <= 4.0          # 硬界（E1 越窗修复）
    assert s["window"]["observed_le_budget"] is True
    assert s["window_end_is_not_stop_line"] is True  # 窗末≠停线通过
    assert s["kill"]["attempted"] is True
    assert s["kill"]["exit_state"] in ("gone", "exited")   # 残留核验
    # 子进程不产 sidecar → progress 缺失 → 机械上不可能判停（unknown≠零）
    assert s["stop_line"]["last_decision"]["state"] == "observation_missing"
    assert s["search_nodes"] == "not_available"
    assert s["remaining_estimate"] == "unknown"


def test_observe_stop_line_kills_own_child_on_triple_zero(tmp_path):
    """应停（受控真实进程）：CPU 零+输出零+进度零 ×2 次有效观测（测试内
    构造短间隔规则对象验证环路/杀归属/残留核验；生产 600s 常数已钉死）。"""
    child_code = (
        "import sys, time\n"
        "sys.path.insert(0, %r)\n"
        "from v5.health_watchdog import ProgressSidecar\n"
        "s = ProgressSidecar.from_env({'child': 'stop-fixture'})\n"
        "s.emit_work('fixture_start')\n"
        "s.close()\n"
        "time.sleep(60)\n" % (ROOT,))   # 睡眠进程：CPU 增量恒零（受控零样本）
    run_dir = str(tmp_path / "stop")
    s = opt09_watchdog.run_observation(
        [sys.executable, "-c", child_code],
        run_dir=run_dir, world_id="w-test", window_s=12.0, interval_s=0.5,
        cwd=str(tmp_path), stop_mode="stop", sidecar_on=True,
        env_extra={"V5_OPT09_HEARTBEAT_S": "0"},
        rule=StopLineRule(interval_min_s=2.0, zero_obs_required=2))
    assert s["status"] == "stop_line_qualified"
    assert s["kill"]["attempted"] is True
    assert s["kill"]["exit_state"] in ("gone", "exited")
    d = s["stop_line"]["last_decision"]
    assert d["qualified"] is True
    assert d["details"]["pid_create_time"] is not None   # 身份已验（防重用）
    assert s["sidecar"]["final"]["work_events"] == 1
    # 被杀的是自起子进程，不是别的进程
    assert s["child"]["returncode"] not in (0,)


def test_observe_audit_mode_never_kills(tmp_path):
    child_code = (
        "import sys, time\n"
        "sys.path.insert(0, %r)\n"
        "from v5.health_watchdog import ProgressSidecar\n"
        "s = ProgressSidecar.from_env({'child': 'audit-fixture'})\n"
        "s.emit_work('fixture_start')\n"
        "s.close()\n"
        "time.sleep(60)\n" % (ROOT,))
    s = opt09_watchdog.run_observation(
        [sys.executable, "-c", child_code],
        run_dir=str(tmp_path / "audit"), world_id="w-test", window_s=5.0,
        interval_s=0.5, cwd=str(tmp_path), stop_mode="audit",
        sidecar_on=True, env_extra={"V5_OPT09_HEARTBEAT_S": "0"},
        rule=StopLineRule(interval_min_s=2.0))
    assert s["status"] == "stop_line_qualified_audit_only"
    assert s["kill"]["attempted"] is False


def test_audit_samples_e1_shape_identity_unverified(tmp_path):
    """E1 形样本回放：无进程创建时间 → identity_unverified，不判停
    （对 E1 thatmicpre 样本形态的机械结论，不重跑长尾）。"""
    p = tmp_path / "samples.jsonl"
    rows = []
    for i in range(31):     # 活跃形态：每间隔 CPU +11s（thatmicpre 形）
        rows.append({"i": i, "elapsed_s": 60.0 * i, "pid": 31088,
                     "cpu_s": 11.0 * i, "log_size": 533,
                     "log_markers": {"execute:": 0, "committed:": 0},
                     "result_exists": False})
    p.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
    s = opt09_watchdog.audit_samples(str(p), str(tmp_path / "audit.json"))
    assert s["n"] == 31
    assert s["last_decision"]["qualified"] is False
    assert s["last_decision"]["state"] == "identity_unverified"
    assert "pid_create" in s["identity_note"]


def test_cli_window_over_30min_rejected(tmp_path, capsys):
    """CLI 硬校验：观测窗 >1800s 直接拒绝（A1：单板 ≤30 分钟）。"""
    with pytest.raises(SystemExit):
        opt09_watchdog.run_observation(
            [sys.executable, "-c", "pass"], run_dir=str(tmp_path / "x"),
            window_s=1801.0, interval_s=60.0)
