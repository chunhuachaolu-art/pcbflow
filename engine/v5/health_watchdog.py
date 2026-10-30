# -*- coding: utf-8 -*-
"""OPT-09 候选级健康度看门狗与真实工作进度 sidecar 支持（EXEC-R2 E2，2026-10-08）。

A1 裁定（exec-r2/packages/GATE-A1-RULING.md §三.4 与 OPT-09 applyConditions
09-C/09-D）的机械实现口径：

- **停线资格**（StopLineRule.feed 机械执行）：同一进程身份下，
  CPU 零增量 ∧ 工作输出零增长 ∧ 真实候选/网进度零推进，有效零差分观测
  ≥2 次且首末间隔 ≥600s，期间无任何非零差分或观测缺失。
  三信号任一为 unknown/缺失（None）一律**不充当零**（取消资格）。
- **墙钟时长本身绝不触发停线**：StopLineRule 结构上不接收运行时长/
  开始时间——时长无入口，规则无法按时长判停（负向测试钉死）。
- 取消资格形态：PID 重用（pid 同而进程创建时间不同）、负增量、读取失败
  （信号缺失）、时钟回退（mono_t 非单调）、进程归属不明（创建时间不可得）
  ——全部重置连续零差分链，不以 unknown 当零。
- **ProgressSidecar**（执行线程写侧车）：仅在执行线程实际到达候选/网/
  attempt 边界时写 JSONL 事件（kind="work"，推进 progress_seq）；周期性
  「我还活着」心跳走独立通道（kind="heartbeat"，独立 hb_seq，**不推进
  progress_seq、不计入工作输出字节**）；监控器自身输出/轮询时间戳/空转
  心跳一律不是工作信号源（SidecarReader 只把 kind="work" 行计入
  work_bytes/progress_seq）。
- **有界写入**：事件数/字节数双上界，越界写一条 sidecar_truncated 注记后
  停写（不无限增长）；一切侧车 IO 失败只降级（disabled），绝不抛回引擎。
- 侧车/看门狗一切输出为独立 sidecar 文件，**不触碰 canonical routes hash**。
- 无计数器 → `not_available`；剩余估计不可推导 → `unknown`
  （不以 0/估算冒充）——由调用方（tools/opt09_watchdog.py）如实落账。

本模块仅依赖 stdlib，不 import v5 引擎任何模块（防环导、防引擎行为耦合）。
"""
import ctypes
import json
import os
import threading
import time
from ctypes import wintypes
from datetime import datetime

VERSION = "v5.health_watchdog/0.1.0"
SIDECAR_SCHEMA = "pcbf-flow.opt09.progress-sidecar.v1"

# A1 09-C 机械常数（真实时钟语义，不可配置缩短——「真实时钟含义不得缩短为
# “等价十分钟」；负向规则用受控 fixture/虚拟时间验证，不走缩短真实间隔）。
STOP_INTERVAL_MIN_S = 600.0     # 两次有效零差分观测的最小间隔（≥10 分钟）
STOP_ZERO_OBS_REQUIRED = 2      # 零差分观测最少次数

# sidecar 有界写入缺省（事件数 / 字节双上界）
DEFAULT_MAX_EVENTS = 200000
DEFAULT_MAX_BYTES = 8 * 1024 * 1024

# 环境变量（opt-in；未设 = sidecar 关闭 = 引擎零行为差）
ENV_SIDECAR = "V5_OPT09_PROGRESS_SIDECAR"
ENV_WORLD_ID = "V5_OPT09_WORLD_ID"
ENV_HEARTBEAT_S = "V5_OPT09_HEARTBEAT_S"

NOT_AVAILABLE = "not_available"
UNKNOWN = "unknown"


def now_wall_iso():
    return datetime.now().astimezone().isoformat(timespec="milliseconds")


# ---------------------------------------------------------------- 进程身份

_kernel32 = None


def _get_kernel32():
    global _kernel32
    if _kernel32 is None:
        _kernel32 = ctypes.windll.kernel32
    return _kernel32


def _filetime_unix(ft):
    v = (ft.dwHighDateTime << 32) | ft.dwLowDateTime
    if v == 0:
        return None
    return v / 10_000_000.0 - 11644473600.0


def _filetime_s(ft):
    v = (ft.dwHighDateTime << 32) | ft.dwLowDateTime
    return v / 10_000_000.0


def process_times(pid):
    """按 pid 读进程 (cpu_s, create_time_unix)；失败/不支持 → (None, None)。

    Windows：OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION)+GetProcessTimes
    （纯 ctypes，无子进程、无本地化输出=无 GBK 坑）；cpu_s=kernel+user 秒。
    create_time_unix 用于 PID 重用识别（同 pid 不同创建时间=身份变化）。
    """
    if os.name != "nt":
        return None, None
    try:
        k32 = _get_kernel32()
        h = k32.OpenProcess(0x1000, False, int(pid))   # QUERY_LIMITED_INFORMATION
        if not h:
            return None, None
        try:
            ct = wintypes.FILETIME()
            et = wintypes.FILETIME()
            kt = wintypes.FILETIME()
            ut = wintypes.FILETIME()
            if not k32.GetProcessTimes(h, ctypes.byref(ct), ctypes.byref(et),
                                       ctypes.byref(kt), ctypes.byref(ut)):
                return None, None
            cpu = _filetime_s(kt) + _filetime_s(ut)
            return round(cpu, 3), _filetime_unix(ct)
        finally:
            k32.CloseHandle(h)
    except Exception:
        return None, None


def process_identity_self():
    """本进程身份（sidecar manifest 用）：pid + 创建时间 + 主机名。"""
    pid = os.getpid()
    _cpu, create = process_times(pid)
    return {
        "pid": pid,
        "pid_create_time": create,           # None=不可得（manifest 如实记）
        "pid_create_source": ("ctypes-getprocesstimes"
                              if create is not None else NOT_AVAILABLE),
        "host": os.environ.get("COMPUTERNAME") or UNKNOWN,
    }


def process_exit_state(pid):
    """停止后残留核验：OpenProcess+GetProcessTimes 读退出时间。

    返回："still_running"（句柄可开且退出时间=0=真残留）/"exited"（句柄可开
    且退出时间非零=已退出，对象未拆）/"gone"（句柄不可开=进程已不在）/
    "not_available"（非 Windows）/"unknown"（读取异常）。
    """
    if os.name != "nt":
        return "not_available"
    try:
        k32 = _get_kernel32()
        h = k32.OpenProcess(0x1000, False, int(pid))
        if not h:
            return "gone"
        try:
            ft_create = wintypes.FILETIME()
            ft_exit = wintypes.FILETIME()
            ft_kernel = wintypes.FILETIME()
            ft_user = wintypes.FILETIME()
            if not k32.GetProcessTimes(h, ctypes.byref(ft_create),
                                       ctypes.byref(ft_exit),
                                       ctypes.byref(ft_kernel),
                                       ctypes.byref(ft_user)):
                return "unknown"
            if ft_exit.dwHighDateTime == 0 and ft_exit.dwLowDateTime == 0:
                return "still_running"
            return "exited"
        finally:
            k32.CloseHandle(h)
    except Exception:
        return "unknown"


def kill_tree_bytes(pid):
    """taskkill 结束本工具自起子进程树（bytes 面 + errors=replace 解码）。

    GBK 坑修复（E1-a §6.3）：taskkill 中文输出为 GBK，绝不设 text=True 让
    子进程按隐式编码解码——这里按字节捕获、显式 utf-8+replace 解码，任何
    本地化输出都不再使采样器收尾崩溃。只对调用方**自己 spawn 的 pid** 用。
    返回 (returncode, 输出尾部文本)。
    """
    import subprocess
    try:
        r = subprocess.run(["taskkill", "/PID", str(int(pid)), "/T", "/F"],
                           capture_output=True)   # bytes：无解码线程
        out = (r.stdout or b"") + (r.stderr or b"")
        return r.returncode, out[-200:].decode("utf-8", errors="replace")
    except Exception as exc:
        return -1, "kill-error: %r" % (exc,)


# ---------------------------------------------------------------- 三信号样本

class SignalSample:
    """一次三信号观测（信号值 None=未观测到，绝不充当零）。

    mono_t: 观测时刻（time.monotonic 口径，由调用方注入——虚拟时间测试
    亦经此注入口）。
    pid/pid_create: 进程身份（create None=不可验证）。
    cpu_s: 进程 CPU 秒累计；output_bytes: 工作输出字节累计（只计受监方
    工作产物，监控器自身输出不计——由调用方装配）；progress_seq: 真实
    候选/网/attempt 边界事件累计序（来自执行线程 sidecar 的 work 事件）。
    """

    __slots__ = ("mono_t", "pid", "pid_create", "cpu_s",
                 "output_bytes", "progress_seq")

    def __init__(self, mono_t, pid, pid_create, cpu_s,
                 output_bytes, progress_seq):
        self.mono_t = mono_t
        self.pid = pid
        self.pid_create = pid_create
        self.cpu_s = cpu_s
        self.output_bytes = output_bytes
        self.progress_seq = progress_seq


class StopLineDecision:
    """feed() 的机械判定输出（可审计；qualified=True 仅=停线资格成立）。"""

    __slots__ = ("qualified", "state", "reason", "details")

    def __init__(self, qualified, state, reason, details=None):
        self.qualified = qualified
        self.state = state
        self.reason = reason
        self.details = details or {}

    def as_dict(self):
        return {"qualified": self.qualified, "state": self.state,
                "reason": self.reason, "details": self.details}

    def __repr__(self):
        return "StopLineDecision(qualified=%r, state=%r)" % (
            self.qualified, self.state)


class StopLineRule:
    """三信号双采样停线规则（机械；纯函数式状态机，无墙钟入口）。

    判停语义（A1 09-C 逐条）：
    - 逐样本对前一同样本身份的差分：cpu_delta/output_delta/progress_delta。
    - 三差分全零 = 一次有效零差分观测；连续零差分观测 ≥STOP_ZERO_OBS_REQUIRED
      且（本次时刻 − 链首时刻）≥ STOP_INTERVAL_MIN_S ⇒ qualified=True。
    - 任一信号 None ⇒ observation_missing（重置链；unknown≠零）。
    - pid 变化 / pid 同而 create_time 变化 ⇒ identity_change（PID 重用，重置）。
    - create_time 任一侧不可得 ⇒ identity_unverified（重置；归属不明不判停）。
    - 任一差分为负 ⇒ negative_increment（读取/时钟异常，重置）；
      mono_t 回退 ⇒ clock_anomaly（重置）。
    - 任一差分为正 ⇒ active（重置零链）。
    - **时长本身无入口**：本类不接收也不推导运行时长。
    """

    def __init__(self, interval_min_s=STOP_INTERVAL_MIN_S,
                 zero_obs_required=STOP_ZERO_OBS_REQUIRED):
        self.interval_min_s = float(interval_min_s)
        self.zero_obs_required = int(zero_obs_required)
        self._prev = None
        self._streak_first_t = None
        self._streak_len = 0
        self.last_decision = None
        self.transitions = []          # 全部判定轨迹（审计用）

    def _decide(self, decision):
        self.last_decision = decision
        self.transitions.append(decision.as_dict())
        return decision

    def _reset_streak(self):
        self._streak_first_t = None
        self._streak_len = 0

    def feed(self, sample):
        prev = self._prev
        self._prev = sample
        if prev is None:
            return self._decide(StopLineDecision(
                False, "baseline", "首次采样=基线，无差分"))
        # 身份校验（同链样本必须同一进程身份）
        if sample.pid != prev.pid:
            self._reset_streak()
            return self._decide(StopLineDecision(
                False, "identity_change",
                "pid %s→%s（进程身份变化，链重置）" % (prev.pid, sample.pid)))
        if prev.pid_create is None or sample.pid_create is None:
            self._reset_streak()
            return self._decide(StopLineDecision(
                False, "identity_unverified",
                "进程创建时间不可得（pid=%s）——归属不明，不判停"
                % (sample.pid,)))
        if sample.pid_create != prev.pid_create:
            self._reset_streak()
            return self._decide(StopLineDecision(
                False, "identity_change",
                "pid=%s 创建时间 %s→%s（PID 重用嫌疑，链重置）"
                % (sample.pid, prev.pid_create, sample.pid_create)))
        # 时钟校验
        if sample.mono_t < prev.mono_t:
            self._reset_streak()
            return self._decide(StopLineDecision(
                False, "clock_anomaly",
                "mono_t 回退 %.3f→%.3f" % (prev.mono_t, sample.mono_t)))
        # 观测完备性（unknown/缺失 ≠ 零；两侧任一缺失即无效差分）
        missing = [name for name, v in (("cpu_s", sample.cpu_s),
                                        ("output_bytes", sample.output_bytes),
                                        ("progress_seq", sample.progress_seq))
                   if v is None]
        missing += [name for name, v in (("cpu_s", prev.cpu_s),
                                         ("output_bytes", prev.output_bytes),
                                         ("progress_seq", prev.progress_seq))
                    if v is None]
        if missing:
            self._reset_streak()
            return self._decide(StopLineDecision(
                False, "observation_missing",
                "信号缺失=%s（unknown 不充当零，链重置）" % ",".join(missing)))
        cpu_d = sample.cpu_s - prev.cpu_s
        out_d = sample.output_bytes - prev.output_bytes
        prg_d = sample.progress_seq - prev.progress_seq
        if cpu_d < 0 or out_d < 0 or prg_d < 0:
            self._reset_streak()
            return self._decide(StopLineDecision(
                False, "negative_increment",
                "负增量 cpu=%+.3f output=%+d progress=%+d（异常，链重置）"
                % (cpu_d, out_d, prg_d)))
        if cpu_d == 0 and out_d == 0 and prg_d == 0:
            if self._streak_len == 0:
                self._streak_first_t = sample.mono_t
            self._streak_len += 1
            span = sample.mono_t - self._streak_first_t
            details = {"zero_obs_count": self._streak_len,
                       "streak_span_s": round(span, 3),
                       "interval_min_s": self.interval_min_s,
                       "cpu_delta": cpu_d, "output_delta": out_d,
                       "progress_delta": prg_d,
                       "pid": sample.pid,
                       "pid_create_time": sample.pid_create}
            if (self._streak_len >= self.zero_obs_required
                    and span >= self.interval_min_s):
                return self._decide(StopLineDecision(
                    True, "stop_qualified",
                    "三零双采样成立：连续 %d 次有效零差分、首末间隔 %.1fs"
                    "≥%.1fs（同进程身份，期间无非零/无缺失）"
                    % (self._streak_len, span, self.interval_min_s), details))
            return self._decide(StopLineDecision(
                False, "zero_streak",
                "三零观测中（%d 次 / 跨度 %.1fs / 需 ≥%d 次 ≥%.0fs）"
                % (self._streak_len, span, self.zero_obs_required,
                   self.interval_min_s), details))
        self._reset_streak()
        return self._decide(StopLineDecision(
            False, "active",
            "信号推进 cpu=%+.3f output=%+d progress=%+d"
            % (cpu_d, out_d, prg_d),
            {"cpu_delta": cpu_d, "output_delta": out_d,
             "progress_delta": prg_d}))


# ---------------------------------------------------------------- 侧车（写侧）

class ProgressSidecar:
    """执行线程真实工作进度 JSONL 侧车（有界写入；IO 失败只降级不抛出）。

    - manifest 落独立文件 <path>.manifest.json：绑定 world/executor/board/
      schema/candidate hash 与进程身份（PID+创建时间）。
    - work 事件：执行线程实际到达候选/网/attempt 边界时写（progress_seq
      仅由 work 事件推进）。
    - heartbeat 事件：周期「我还活着」，独立 hb_seq 通道，不推进
      progress_seq、不计入 work_bytes（可选守护线程按心跳间隔写）。
    - sidecar_note：注记（截断/收尾），非工作非心跳。
    - 双上界（事件数/字节）越界 → 写 sidecar_truncated 后停写。
    """

    def __init__(self, path, manifest=None, max_events=DEFAULT_MAX_EVENTS,
                 max_bytes=DEFAULT_MAX_BYTES, heartbeat_interval_s=None):
        self.path = str(path)
        self.max_events = int(max_events)
        self.max_bytes = int(max_bytes)
        self._lock = threading.Lock()
        self._fh = None
        self._seq = 0                 # 全部事件序（含心跳/注记）
        self._progress_seq = 0        # 仅 work 事件推进（真实进度序）
        self._hb_seq = 0
        self._bytes = 0
        self._events = 0
        self._work_bytes = 0
        self._truncated = False
        self._broken = None           # IO 失败原因（降级标志）
        self._closed = False
        self._hb_thread = None
        self._hb_stop = threading.Event()
        self._t0_mono = time.monotonic()
        self.manifest = dict(manifest or {})
        self.manifest.update({
            "schema": SIDECAR_SCHEMA,
            "sidecar_version": VERSION,
            "sidecar_path": self.path,
            "started_wall": now_wall_iso(),
            "started_mono": self._t0_mono,
            "max_events": self.max_events,
            "max_bytes": self.max_bytes,
            "identity": process_identity_self(),
        })
        self._open()
        if heartbeat_interval_s is None:
            heartbeat_interval_s = float(
                os.environ.get(ENV_HEARTBEAT_S, "30") or 0)
        self.heartbeat_interval_s = heartbeat_interval_s
        if (self._fh is not None and not self._broken
                and self.heartbeat_interval_s and self.heartbeat_interval_s > 0):
            self._start_heartbeat_thread()

    # ---- 工厂 ----

    @classmethod
    def from_env(cls, manifest_bindings=None, heartbeat_interval_s=None):
        """opt-in 工厂：ENV_SIDECAR 未设 → None（调用方零行为差）。"""
        path = os.environ.get(ENV_SIDECAR)
        if not path:
            return None
        manifest = dict(manifest_bindings or {})
        manifest.setdefault("world_id",
                            os.environ.get(ENV_WORLD_ID) or NOT_AVAILABLE)
        try:
            return cls(path, manifest=manifest,
                       heartbeat_interval_s=heartbeat_interval_s)
        except Exception as exc:   # 工厂也不抛（引擎绝不受侧车拖累）
            side = cls.__new__(cls)
            side.path = str(path)
            side._fh = None
            side._broken = "from_env: %r" % (exc,)
            side._truncated = False
            side._closed = False
            side._seq = 0
            side._progress_seq = 0
            side._hb_seq = 0
            side._bytes = 0
            side._events = 0
            side._work_bytes = 0
            side._lock = threading.Lock()
            side._hb_thread = None
            side._hb_stop = threading.Event()
            side._t0_mono = time.monotonic()
            side.heartbeat_interval_s = 0
            side.manifest = {}
            return side

    # ---- 内部 ----

    def _open(self):
        try:
            os.makedirs(os.path.dirname(os.path.abspath(self.path)) or ".",
                        exist_ok=True)
            mpath = self.path + ".manifest.json"
            with open(mpath, "w", encoding="utf-8", newline="\n") as f:
                json.dump(self.manifest, f, ensure_ascii=True, indent=1,
                          sort_keys=True)
                f.write("\n")
            self._fh = open(self.path, "a", encoding="utf-8", newline="\n")
        except Exception as exc:
            self._broken = "open: %r" % (exc,)
            self._fh = None

    def _write_event(self, event):
        """有界写一行；越界 → 截断注记后停写。绝不抛出。"""
        if self._closed or self._broken is not None or self._truncated:
            return
        try:
            with self._lock:
                line = json.dumps(event, ensure_ascii=True,
                                  sort_keys=True) + "\n"
                raw = line.encode("utf-8")
                if (self._events + 1 > self.max_events
                        or self._bytes + len(raw) > self.max_bytes):
                    note = {"seq": self._seq + 1, "kind": "sidecar_note",
                            "type": "sidecar_truncated",
                            "mono_t": round(time.monotonic()
                                            - self._t0_mono, 3),
                            "wall_t": now_wall_iso(),
                            "events_written": self._events,
                            "bytes_written": self._bytes,
                            "reason": "bound"}
                    nraw = (json.dumps(note, ensure_ascii=True,
                                       sort_keys=True) + "\n").encode("utf-8")
                    if self._bytes + len(nraw) <= self.max_bytes:
                        self._fh.write(nraw.decode("utf-8"))
                        self._fh.flush()
                    self._truncated = True
                    return
                self._fh.write(line)
                self._fh.flush()
                self._seq = event.get("seq", self._seq + 1)
                self._events += 1
                self._bytes += len(raw)
                if event.get("kind") == "work":
                    self._work_bytes += len(raw)
        except Exception as exc:
            self._broken = "write: %r" % (exc,)

    def _base_event(self, kind, etype):
        return {"seq": self._seq + 1, "kind": kind, "type": etype,
                "mono_t": round(time.monotonic() - self._t0_mono, 3),
                "wall_t": now_wall_iso()}

    def _start_heartbeat_thread(self):
        def _loop(stop, interval):
            while not stop.wait(interval):
                self.emit_heartbeat()
        t = threading.Thread(target=_loop, args=(self._hb_stop,
                                                 float(self.heartbeat_interval_s)),
                             name="opt09-sidecar-heartbeat", daemon=True)
        t.start()
        self._hb_thread = t

    # ---- 公共 API（引擎/工具调用面） ----

    @property
    def progress_seq(self):
        return self._progress_seq

    @property
    def broken(self):
        return self._broken

    @property
    def truncated(self):
        return self._truncated

    def emit_work(self, etype, **fields):
        """真实工作边界事件（候选/网/attempt 边界到达时；推进 progress_seq）。"""
        if self._broken is not None or self._truncated:
            return
        ev = self._base_event("work", etype)
        self._progress_seq += 1
        ev["progress_seq"] = self._progress_seq
        ev.update(fields)
        self._write_event(ev)

    def emit_heartbeat(self, note=None):
        """周期存活心跳（独立通道；不推进 progress_seq、不计 work_bytes）。"""
        if self._broken is not None or self._truncated:
            return
        ev = self._base_event("heartbeat", "heartbeat")
        self._hb_seq += 1
        ev["hb_seq"] = self._hb_seq
        ev["note"] = note
        self._write_event(ev)

    def emit_note(self, etype, **fields):
        ev = self._base_event("sidecar_note", etype)
        ev.update(fields)
        self._write_event(ev)

    def close(self, verdict=None, **fields):
        """收尾注记 + 关闭（幂等）。"""
        if self._closed:
            return
        self._hb_stop.set()
        summary = {"verdict": verdict,
                   "work_events": self._progress_seq,
                   "heartbeats": self._hb_seq,
                   "bytes_written": self._bytes,
                   "work_bytes": self._work_bytes,
                   "truncated": self._truncated,
                   "broken": self._broken}
        summary.update(fields)
        self.emit_note("sidecar_closed", **summary)   # 先写注记再置 _closed
        self._closed = True
        try:
            if self._fh is not None:
                self._fh.close()
        except Exception as exc:
            self._broken = "close: %r" % (exc,)


# ---------------------------------------------------------------- 侧车（读侧）

class WorkProgressSnapshot:
    """侧车工作进度快照（只统计 work 行=真实进度；心跳/注记分列）。"""

    __slots__ = ("work_events", "progress_seq", "heartbeats", "notes",
                 "work_bytes", "file_bytes", "truncated", "closed",
                 "parse_error", "last_event_seq", "last_work_mono_t",
                 "exists")

    def __init__(self):
        self.work_events = 0
        self.progress_seq = 0
        self.heartbeats = 0
        self.notes = 0
        self.work_bytes = 0
        self.file_bytes = 0
        self.truncated = False
        self.closed = False
        self.parse_error = False
        self.last_event_seq = 0
        self.last_work_mono_t = None
        self.exists = False

    def as_dict(self):
        return {k: getattr(self, k) for k in self.__slots__}


class SidecarReader:
    """增量读侧车 JSONL（监控方用；只把 kind=work 行计入工作信号）。

    逐次 snapshot() 增量解析新字节；半行（写入中途）暂存待补；完整行
    JSON 解析失败 → parse_error=True（该次观测按缺失处理，不充当零）。
    """

    def __init__(self, path):
        self.path = str(path)
        self._offset = 0
        self._pending = b""
        self._snap = WorkProgressSnapshot()

    @staticmethod
    def read_manifest(path):
        try:
            with open(str(path) + ".manifest.json", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    def snapshot(self):
        """返回 WorkProgressSnapshot（增量累积；每次调用为全量累计态）。"""
        snap = self._snap
        try:
            with open(self.path, "rb") as f:
                f.seek(self._offset)
                chunk = f.read()
                self._offset = f.tell()
        except FileNotFoundError:
            return snap          # 侧车尚未出现：exists=False（缺失≠零）
        except OSError:
            snap.parse_error = True
            return snap
        if chunk:
            snap.exists = True
        data = self._pending + chunk
        lines = data.split(b"\n")
        self._pending = lines.pop()
        for raw in lines:
            if not raw.strip():
                continue
            try:
                ev = json.loads(raw.decode("utf-8"))
            except Exception:
                snap.parse_error = True
                continue
            kind = ev.get("kind")
            snap.last_event_seq = max(snap.last_event_seq,
                                      int(ev.get("seq", 0)))
            if kind == "work":
                snap.work_events += 1
                snap.work_bytes += len(raw) + 1
                ps = ev.get("progress_seq")
                if isinstance(ps, int) and ps > snap.progress_seq:
                    snap.progress_seq = ps
                m = ev.get("mono_t")
                if m is not None:
                    snap.last_work_mono_t = m
            elif kind == "heartbeat":
                snap.heartbeats += 1
            elif kind == "sidecar_note":
                snap.notes += 1
                if ev.get("type") == "sidecar_truncated":
                    snap.truncated = True
                if ev.get("type") == "sidecar_closed":
                    snap.closed = True
        try:
            snap.file_bytes = os.path.getsize(self.path)
        except OSError:
            pass
        return snap


# ------------------------------------------------------- 工作输出信号装配

def collect_output_state(run_log_path, result_path, sidecar_reader):
    """装配 s2（工作输出字节）/s3（真实进度序）——只计受监方工作产物。

    计入：run.log（受监进程 stdout）、result.json 及 .negotiation_log.json
    （受监进程产物）、sidecar 的 **work 行字节**。
    不计入：监控器自身采样/汇总文件、sidecar 心跳/注记行（A1 09-D）。
    返回 dict（signal_missing 列出全部不可得分量——缺失绝不充当零）。
    """
    state = {"run_log_bytes": None, "result_bytes": None,
             "neglog_bytes": None, "sidecar_work_bytes": None,
             "sidecar_progress_seq": None, "sidecar_exists": False,
             "signal_missing": []}
    try:
        state["run_log_bytes"] = os.path.getsize(run_log_path)
    except OSError:
        state["signal_missing"].append("run_log_bytes")
    try:
        state["result_bytes"] = os.path.getsize(result_path)
    except OSError:
        state["result_bytes"] = 0     # 结果未落盘=0 字节（存在性事实，非缺失）
    try:
        state["neglog_bytes"] = os.path.getsize(str(result_path)
                                                + ".negotiation_log.json")
    except OSError:
        state["neglog_bytes"] = 0
    if sidecar_reader is not None:
        snap = sidecar_reader.snapshot()
        state["sidecar_exists"] = snap.exists
        if snap.parse_error or not snap.exists:
            state["signal_missing"].append("sidecar_progress_seq")
        else:
            state["sidecar_work_bytes"] = snap.work_bytes
            state["sidecar_progress_seq"] = snap.progress_seq
            state["sidecar_snapshot"] = snap.as_dict()
    else:
        state["signal_missing"].append("sidecar_progress_seq")
    if not state["signal_missing"]:
        state["output_bytes"] = (state["run_log_bytes"]
                                 + state["result_bytes"]
                                 + state["neglog_bytes"]
                                 + state["sidecar_work_bytes"])
        state["progress_seq"] = state["sidecar_progress_seq"]
    else:
        state["output_bytes"] = None
        state["progress_seq"] = None
    return state
