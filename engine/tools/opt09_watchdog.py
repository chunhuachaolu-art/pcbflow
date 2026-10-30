# -*- coding: utf-8 -*-
"""OPT-09 有界观测窗采样/健康看门狗入口（EXEC-R2 E2，2026-10-08）。

用法：
  python tools/opt09_watchdog.py observe --run-id ID --out-root DIR
      [--world-id W] [--window-s 1800] [--interval-s 60] [--cwd DIR]
      [--stop-mode audit|stop] [--no-sidecar]
      -- <child command...>

  python tools/opt09_watchdog.py audit-samples --samples PATH [--out PATH]

口径（A1 裁定 GATE-A1-RULING.md §三.4 / applyConditions 09-C~09-F）：
- 观测窗硬界 ≤30 分钟（--window-s 上限 1800 机械校验）且**含采样粒度**：
  采样排程按「剩余时间 − 估计采样耗时 − kill 余量」裁剪，窗到即收，
  不会重现 E1 的 1841.6s 越窗形态（实测窗长 ≤ 预算）。
- 三信号逐采样：s1=CPU 增量（ctypes GetProcessTimes，无 PowerShell=无
  GBK 面）；s2=工作输出增长（run.log/result/negotiation/sidecar **work 行**
  字节）；s3=真实进度（sidecar progress_seq，仅执行线程 work 事件推进）。
  监控器自身输出（本工具的 samples/summary）、心跳行、注记行一律不计入。
- 停线规则=health_watchdog.StopLineRule（600s 双采样机械规则，**不经 CLI
  配置**——真实时钟语义不得缩短；短间隔只在测试内直接构造规则对象）。
- 到窗未完结=unfinished_in_window_killed_by_window_end，只结束**本工具
  自起子进程**（杀前重验进程身份，PID 重用嫌疑则跳过杀并如实记录），
  事后残留核验；该状态**不是**三信号停线通过（summary 显式分列）。
- 墙钟时长本身绝不触发 kill；search_nodes 无计数器=not_available；
  剩余估计不可推导=unknown（不补猜）。
"""
import argparse
import json
import os
import sys
import time
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from v5.health_watchdog import (NOT_AVAILABLE, UNKNOWN,  # noqa: E402
                                ENV_SIDECAR, ENV_WORLD_ID,
                                SidecarReader, StopLineRule,
                                collect_output_state, kill_tree_bytes,
                                process_exit_state, process_times,
                                now_wall_iso)

WINDOW_MAX_S = 1800            # A1：单板观测窗硬上限 30 分钟
KILL_RESERVE_S = 1.0           # 窗末 kill 余量（taskkill 起进程+收尾写）
SAMPLE_DUR_MARGIN_S = 0.5      # 采样耗时估计安全裕度


def _open_log(path, cmd, cwd):
    lf = open(path, "wb")
    lf.write(("[opt09-watchdog] child=%s\n[opt09-watchdog] cwd=%s\n"
              % (" ".join(cmd), cwd)).encode("utf-8"))
    lf.flush()
    return lf


def run_observation(argv, *, run_dir, world_id=None, window_s=1800,
                    interval_s=60.0, rule=None, cwd=None, stop_mode="stop",
                    sidecar_on=True, env_extra=None):
    """有界观测一轮子进程；返回 summary dict（一切产物落 run_dir）。

    测试注记：rule 参数仅供受控测试注入短间隔规则对象（真实验证走缺省
    StopLineRule()=600s 机械规则）；window_s/interval_s 是**观测窗与采样
    粒度**，不是停线间隔——停线间隔恒出自规则对象本身。
    """
    import subprocess
    os.makedirs(run_dir, exist_ok=True)
    log_path = os.path.join(run_dir, "run.log")
    result_path = os.path.join(run_dir, "result.json")
    samples_path = os.path.join(run_dir, "samples.jsonl")
    sidecar_path = os.path.join(run_dir, "progress-sidecar.jsonl")

    rule = rule if rule is not None else StopLineRule()
    window_s = float(window_s)
    interval_s = float(interval_s)
    if not (0.5 <= window_s <= WINDOW_MAX_S):
        raise SystemExit("window-s 须在 0.5..%ds（A1 硬界 30 分钟）"
                         % WINDOW_MAX_S)
    if interval_s < 0.2:
        raise SystemExit("interval-s 须 ≥0.2")

    env = os.environ.copy()
    if env_extra:
        env.update(env_extra)
    if sidecar_on:
        env[ENV_SIDECAR] = sidecar_path
        env[ENV_WORLD_ID] = world_id or NOT_AVAILABLE
    else:
        env.pop(ENV_SIDECAR, None)

    lf = _open_log(log_path, argv, cwd or run_dir)
    spawn_wall = now_wall_iso()
    t0 = time.monotonic()
    deadline = t0 + window_s
    proc = subprocess.Popen(argv, cwd=cwd or run_dir, stdout=lf,
                            stderr=subprocess.STDOUT, env=env)
    pid = proc.pid
    identity_spawn = process_times(pid)
    reader = SidecarReader(sidecar_path)
    sidecar_manifest = None
    status = None
    kill_info = None
    samples = []
    max_sample_dur = 0.0
    last_decision = None

    def _write_sample(rec):
        samples.append(rec)
        with open(samples_path, "a", encoding="utf-8", newline="\n") as sf:
            sf.write(json.dumps(rec, ensure_ascii=True, sort_keys=True) + "\n")

    def _kill_owned(reason):
        """只杀本工具自起子进程；杀前重验身份（防 PID 重用误杀）。"""
        cpu_n, create_n = process_times(pid)
        ident_ok = (create_n is not None
                    and identity_spawn[1] is not None
                    and create_n == identity_spawn[1])
        if not ident_ok:
            return {"attempted": False,
                    "skip_reason": "identity_mismatch_or_unverified"
                                   "（PID 重用嫌疑，不杀）",
                    "exit_state": process_exit_state(pid)}
        rc, tail = kill_tree_bytes(pid)
        try:
            proc.wait(timeout=15)
        except Exception:
            pass
        residue = process_exit_state(pid)
        return {"attempted": True, "taskkill_rc": rc,
                "taskkill_out_tail": tail, "exit_state": residue,
                "reason": reason}

    try:
        while True:
            s_start = time.monotonic()
            alive = proc.poll() is None
            cpu_s, pid_create = (process_times(pid) if alive
                                 else (None, None))
            out_state = collect_output_state(log_path, result_path, reader)
            if sidecar_manifest is None:
                sidecar_manifest = SidecarReader.read_manifest(sidecar_path)
            sample = _mk_sample(s_start, pid, pid_create, cpu_s, out_state)
            last_decision = rule.feed(sample)
            _write_sample({
                "i": len(samples), "t": now_wall_iso(),
                "elapsed_s": round(s_start - t0, 3), "pid": pid,
                "pid_create": pid_create, "alive": alive,
                "cpu_s": cpu_s,
                "output": {k: out_state.get(k) for k in
                           ("run_log_bytes", "result_bytes", "neglog_bytes",
                            "sidecar_work_bytes", "sidecar_progress_seq")},
                "output_bytes": out_state["output_bytes"],
                "progress_seq": out_state["progress_seq"],
                "signal_missing": out_state["signal_missing"],
                "decision": last_decision.as_dict(),
                "sample_dur_s": round(time.monotonic() - s_start, 3)})
            max_sample_dur = max(max_sample_dur, time.monotonic() - s_start)

            if last_decision.qualified and stop_mode == "stop":
                status = "stop_line_qualified"
                kill_info = _kill_owned("stop_line_qualified")
                break
            if last_decision.qualified and stop_mode == "audit":
                status = "stop_line_qualified_audit_only"
                kill_info = {"attempted": False,
                             "skip_reason": "stop-mode=audit（只判定不停止）"}
                break
            if not alive:
                status = "finished_in_window"
                break
            now = time.monotonic()
            remaining = deadline - now
            if remaining <= KILL_RESERVE_S:
                status = "unfinished_in_window_killed_by_window_end"
                kill_info = _kill_owned("window_end")
                break
            est_total = max_sample_dur + SAMPLE_DUR_MARGIN_S + KILL_RESERVE_S
            sleep_for = min(interval_s, remaining - est_total)
            if sleep_for <= 0:
                sleep_for = 0.02
            time.sleep(sleep_for)
    finally:
        end_mono = time.monotonic()
        lf.close()
        try:
            proc.wait(timeout=5)
        except Exception:
            pass

    sidecar_final = reader.snapshot().as_dict()
    result_info = {"exists": os.path.exists(result_path)}
    if result_info["exists"]:
        try:
            result_info["bytes"] = os.path.getsize(result_path)
            with open(result_path, encoding="utf-8") as f:
                res = json.load(f)
            if isinstance(res, dict) and "canonical_hashes" in res:
                result_info["canonical_hashes"] = res["canonical_hashes"]
                result_info["verdict"] = res.get("verdict")
                result_info["wall_s"] = res.get("wall_s")
                result_info["cpu_s"] = res.get("cpu_s")
        except Exception as exc:
            result_info["parse_error"] = repr(exc)

    summary = {
        "schema": "pcbf-flow.optimap.exec-r2.opt09.watchdog-observe.v1",
        "run_id": os.path.basename(os.path.normpath(run_dir)),
        "world_id": world_id or NOT_AVAILABLE,
        "child": {"argv": list(argv), "cwd": cwd or run_dir,
                  "spawned_wall": spawn_wall, "pid": pid,
                  "identity_spawn": {"cpu_s": identity_spawn[0],
                                     "pid_create_time": identity_spawn[1]},
                  "returncode": proc.returncode},
        "window": {"budget_s": window_s, "interval_s": interval_s,
                   "observed_s": round(end_mono - t0, 3),
                   "observed_le_budget": (end_mono - t0) <= window_s,
                   "hard_max_s": WINDOW_MAX_S},
        "n_samples": len(samples),
        "status": status,
        # 窗末收尾 ≠ 三信号停线通过（A1：不把按时长/到窗结束写成健康停线）
        "window_end_is_not_stop_line":
            status == "unfinished_in_window_killed_by_window_end",
        "stop_line": {"rule": "health_watchdog.StopLineRule",
                      "interval_min_s": rule.interval_min_s,
                      "zero_obs_required": rule.zero_obs_required,
                      "last_decision": (last_decision.as_dict()
                                        if last_decision else None),
                      "transitions_tail": rule.transitions[-8:],
                      "duration_never_triggers_kill": True},
        "kill": kill_info,
        "sidecar": {"on": sidecar_on, "manifest": sidecar_manifest,
                    "final": sidecar_final},
        "result": result_info,
        "monitor_outputs_excluded_from_signals":
            ["samples.jsonl", "summary.json", "run.log 头两行（监控器前缀）",
             "sidecar heartbeat/sidecar_note 行"],
        "search_nodes": NOT_AVAILABLE,
        "search_nodes_note": "引擎无搜索节点计数器（E1-a 三板实证 log 无 "
                             "nodes= 计数行）——not_available，不以 0 冒充",
        "remaining_estimate": UNKNOWN,
        "remaining_estimate_note": "无计数器且未接入逐候选成本模型，剩余"
                                   "不可推导——unknown，不以估算冒充",
        "finished_wall": now_wall_iso(),
    }
    with open(os.path.join(run_dir, "summary.json"), "w",
              encoding="utf-8", newline="\n") as f:
        json.dump(summary, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write("\n")
    return summary


def _mk_sample(mono_t, pid, pid_create, cpu_s, out_state):
    from v5.health_watchdog import SignalSample
    return SignalSample(mono_t, pid, pid_create, cpu_s,
                        out_state["output_bytes"], out_state["progress_seq"])


# ----------------------------------------------------------- 样本回放审计

def audit_samples(samples_path, out_path=None):
    """离线把 samples.jsonl（E1 形或本工具形）喂进 StopLineRule。

    E1 形样本不含进程创建时间 → 身份不可验证 → 机械结论=identity_unverified
    （不判停）——如实输出，不把「读不到身份」当「已验活」。
    """
    rule = StopLineRule()
    n = 0
    last = None
    with open(samples_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            n += 1
            markers = rec.get("log_markers") or {}
            output = (rec.get("log_size") or 0)
            if rec.get("result_size"):
                output += rec["result_size"]
            sample = _mk_sample(
                float(rec.get("elapsed_s", rec.get("t", n))),
                rec.get("pid"), rec.get("pid_create"),
                rec.get("cpu_s"), {"output_bytes": output,
                                   "progress_seq": sum(markers.values())
                                   if markers else None})
            last = rule.feed(sample)
    summary = {
        "schema": "pcbf-flow.optimap.exec-r2.opt09.audit-samples.v1",
        "samples": samples_path, "n": n,
        "last_decision": last.as_dict() if last else None,
        "state_counts": {},
        "identity_note": "样本缺 pid_create（E1 形）→ identity_unverified，"
                         "停线资格机械不可成立（unknown≠零）",
        "duration_never_triggers_kill": True,
    }
    counts = {}
    for tr in rule.transitions:
        counts[tr["state"]] = counts.get(tr["state"], 0) + 1
    summary["state_counts"] = counts
    if out_path:
        with open(out_path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(summary, f, ensure_ascii=False, indent=1, sort_keys=True)
            f.write("\n")
    return summary


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    ob = sub.add_parser("observe", help="有界观测窗采样/看门狗一轮子进程")
    ob.add_argument("--run-id", required=True)
    ob.add_argument("--out-root", required=True)
    ob.add_argument("--world-id", default=None)
    ob.add_argument("--window-s", type=float, default=1800.0)
    ob.add_argument("--interval-s", type=float, default=60.0)
    ob.add_argument("--cwd", default=None)
    ob.add_argument("--stop-mode", choices=("audit", "stop"), default="stop",
                    help="stop=资格成立且身份复核通过时结束自起子进程"
                         "（默认）；audit=只判定绝不止")
    ob.add_argument("--no-sidecar", action="store_true",
                    help="不给子进程设 sidecar 环境变量（对照臂）")
    ob.add_argument("child", nargs=argparse.REMAINDER,
                    help="-- 之后的子进程命令行")

    au = sub.add_parser("audit-samples", help="离线回放样本过停线规则")
    au.add_argument("--samples", required=True)
    au.add_argument("--out", default=None)

    args = ap.parse_args(argv)
    if args.cmd == "observe":
        child = list(args.child)
        if child and child[0] == "--":
            child = child[1:]
        if not child:
            ap.error("observe 需要在 -- 后给出子进程命令行")
        run_dir = os.path.join(args.out_root, args.run_id)
        if os.path.exists(os.path.join(run_dir, "summary.json")):
            raise SystemExit("run dir 已有 summary（不覆盖既有观测）："
                             "%s" % run_dir)
        summary = run_observation(
            child, run_dir=run_dir, world_id=args.world_id,
            window_s=args.window_s, interval_s=args.interval_s,
            cwd=args.cwd or args.out_root, stop_mode=args.stop_mode,
            sidecar_on=not args.no_sidecar)
        print("OBSERVE-DONE status=%s observed_s=%s n=%s rc=%s"
              % (summary["status"], summary["window"]["observed_s"],
                 summary["n_samples"], summary["child"]["returncode"]))
    elif args.cmd == "audit-samples":
        summary = audit_samples(args.samples, args.out)
        print("AUDIT-DONE n=%s last=%s counts=%s"
              % (summary["n"],
                 summary["last_decision"]["state"] if summary["last_decision"]
                 else None, summary["state_counts"]))


if __name__ == "__main__":
    main()
