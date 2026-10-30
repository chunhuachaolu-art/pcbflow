# -*- coding: utf-8 -*-
"""OPT-07／EXEC-R4-B 失败事件契约（fail-event.v1）。

本模块是**只加不改的 opt-in instrumentation**（sidecar 模式，骑 OPT-09
ProgressSidecar 同款纪律）：

- 开关=环境变量 ``V5_R4B_FAIL_EVENTS``（未设 → journal=None → 引擎零行为差；
  不动 canonical routes hash、不入 canonical 运行账、不改路由决策/返回工件/
  日志语义与序）。
- world 绑定复用 ``V5_OPT09_WORLD_ID``（与 OPT-09 同名同源）。
- 载体=独立 JSONL 侧车（每行一个 canonical JSON 事件）+ 独立 manifest 文件
  ``<path>.manifest.json``（绑 world/executor/board/schema/candidate hash 与
  进程身份）。

## 事件面（五类 fail_kind）

| fail_kind | scope | stage |
|---|---|---|
| sealed_short_circuit | net | preflight_seal |
| fixed_shape_failed | net | fixed_shape |
| net_exhausted | net | attempt_ladder_ripup |
| final_check_infeasible | candidate | final_route_check |
| candidate_failed | candidate | candidate_close |

最终 DRC/candidate 失败与 net 失败分开（R4B-04）。

## event_id 与 volatile 边界（R4B-08：先声明）

- 语义字段（入 event_id 重算面）：schema_version、fail_kind、scope、stage、
  attempts、cause、geom_secondary、blocker_nets、available_layers、
  tried_layers、topology、capacity_cert、bindings、event_seq。
- volatile 字段（排除在 event_id 外，单列 ``runtime`` 键）：wall_t、mono_t、
  pid、process_identity。原始 sidecar 跨进程不要求 byte 等；语义事件
  （去 runtime 后 canonical bytes）须等。
- ``event_id = canonical_sha256(payload − {event_id, runtime})``。

## 关键口径（R4B-03/04）

- blocker_nets：computed_selection（已计算选择集，非穷尽几何阻塞真值；空集=
  该 reach 下测量为空，非「已证无几何阻塞」）｜geometric_blocking_evidence
  （事前密封短路的封死铜证据）｜not_available（未测量，附原因）。零 rip-up
  日志不推出无 blocker；未计算不能填空集冒充已证空。
- available_layers=view.signal_layers（真实 stackup available=true 信号层）；
  不取失败 per_net.layers=[]。
- tried_layers：attempt 阶梯不外露逐尝试层集 → not_available+原因，不补猜。
- capacity_cert：verified 须走廊×层容量+实际占用/条目/单位/算术可独立复算
  （occupancy = round(Σterms + spacing×(n−1), 10)，v5.metrics.capacity 同式），
  且 ctx.ledger 增量账与场景重算双源一致；空走廊（板无 corridor zone）=
  not_available——**空摘要不构成证书、不作扩展凭证**；cause 文本/既有
  selection 报告不冒充。
"""
import json
import os
import time

from . import canonical
from .health_watchdog import (ENV_WORLD_ID, NOT_AVAILABLE, now_wall_iso,
                              process_identity_self)
from .metrics import capacity as cap_mod

FAIL_EVENT_SCHEMA_VERSION = "fail-event.v1"
ENV_FAIL_EVENTS = "V5_R4B_FAIL_EVENTS"
FAIL_EVENT_SIDECAR_VERSION = "v5.failure_events/0.1.0"

DEFAULT_MAX_EVENTS = 20000
DEFAULT_MAX_BYTES = 64 * 1024 * 1024

BLOCKER_SEMANTICS_NOTE = (
    "computed-selection/geometric-blocking-evidence 仅表征证据类型："
    "computed_selection=有界联合/成本选择集（非穷尽几何阻塞真值，空集=该 "
    "measurement_reach 下测量为空，非已证无几何阻塞）；"
    "geometric_blocking_evidence=封死铜证据（preflight 密封）")
BLOCKER_SELECTION_RULE = (
    "executor._ripup_blocker_ids F4c 三阶段：阶段1 hits=铜落入失败走廊带"
    "(width/2+R5)或端点逃逸邻域(reach+R5)盘的已布网；阶段2 alts=与 hit 段"
    "重布走廊交叠(seg-seg<corr_hw)的已布网；阶段3 联合集 vs hits 纯整数段数"
    "贪心，启用判据 score(joint)<=joint_factor*score(greedy)；集合迭代一律"
    "sorted()，选中序 tie-break=(联合评估分, 网id字典序)")
TRIED_LAYERS_REASON = (
    "attempt 阶梯（_run_attempt_ladder）不外露逐尝试层集——层试足迹无结构化"
    "出口，不补猜（R4B-03 typed not_available）")
CAPACITY_AUTHORITY_CTX = (
    "v5.failure_events.build_capacity_cert_from_ctx：场景重算="
    "v5.route_check.capacity_ledger(view, fixed+route_coppers, declared)，"
    "交叉核对=v5.executor._Context.ledger 增量账（初始化 capacity_ledger+"
    "commit_entries/rip_net 维护）")
CAPACITY_AUTHORITY_META = (
    "v5.route_check._capacity_checks 报告面（capacity_meta terms/capacity_mm，"
    "selection._capacity_core_entry 同型同源算术）")
CAPACITY_SCOPE = (
    "corridor×signal-layer 实占条目（固定铜板注册序在前+routes 铜 entry 序在"
    "后；仅含有实占条目的走廊格，空格省略）")

_KINDS = ("sealed_short_circuit", "fixed_shape_failed", "net_exhausted",
          "final_check_infeasible", "candidate_failed")
_STAGES = ("preflight_seal", "fixed_shape", "attempt_ladder_ripup",
           "final_route_check", "candidate_close")
_EDGE_SOURCES = ("board_topology_dfs", "mst_fallback", "topology_hints",
                 "not_computed_preflight", "not_computed_fixed_shape",
                 "not_computed_candidate_scope")


# ---------------------------------------------------------------- 纯构建件

def build_blocker_not_available(reason):
    return {"kind": "not_available", "measured": False,
            "semantics_note": BLOCKER_SEMANTICS_NOTE, "reason": reason}


def build_blocker_from_measurement(measurement):
    """已计算选择集（measurement=record_blocker_measurement 登记 dict）。"""
    return {"kind": "computed_selection", "measured": True,
            "semantics_note": BLOCKER_SEMANTICS_NOTE,
            "net_ids": list(measurement["blockers"]),
            "selection_rule": BLOCKER_SELECTION_RULE,
            "measurement_stage": measurement["measurement_stage"],
            "measurement_reach_mm": measurement["reach_mm"],
            "ripup_round": measurement["ripup_round"],
            "joint_factor": measurement["joint_factor"]}


def build_blocker_geometric(net_ids, detail):
    return {"kind": "geometric_blocking_evidence", "measured": True,
            "semantics_note": BLOCKER_SEMANTICS_NOTE,
            "net_ids": list(net_ids),
            "selection_rule": (
                "preflight seal survey：附着点位集（栅格+端点精确坐标）×全信号"
                "层逐 (p,层) edge_blocked(exempt_same_partition=True) 复核全同意"),
            "measurement_stage": "preflight_seal_survey",
            "measurement_reach_mm": None,
            "ripup_round": None,
            "joint_factor": None,
            "detail": detail}


def build_available_layers(view):
    layers = [str(l) for l in view.signal_layers]
    return {"kind": "stackup_signal_available", "layers": layers,
            "source": "board.stackup（kind=signal 且 available=true 的层，"
                      "stackup 序）"}


def build_tried_layers_not_available():
    return {"kind": "not_available", "reason": TRIED_LAYERS_REASON}


def build_topology(endpoints, edges, edges_computed, edge_order_source,
                   partition_id=None, net_id=None):
    return {
        "partition_id": partition_id,
        "net_id": net_id,
        "endpoints": [[float(p[0]), float(p[1])] for p in endpoints],
        "edges": [{"edge_id": str(eid), "a": [float(a[0]), float(a[1])],
                   "b": [float(b[0]), float(b[1])]}
                  for eid, a, b in (edges or [])],
        "edges_computed": bool(edges_computed),
        "edge_order_source": edge_order_source,
    }


def _corridor_row(clid, entries, capacity_mm):
    terms = [float(e.occupancy) for e in entries]
    occ = cap_mod.corridor_occupancy(entries)
    n = len(terms)
    return {
        "corridor_layer_id": clid,
        "capacity_mm": float(capacity_mm),
        "terms": terms,
        "occupancy_mm": occ,
        "spacing_mm": float(cap_mod.NET_NET_SPACING),
        "arithmetic": "occupancy=round(Σterms+spacing×(n−1),10)"
                      "=%r+%r×%d=%r" % (round(sum(terms), 10),
                                        float(cap_mod.NET_NET_SPACING),
                                        max(n - 1, 0), occ),
        "entries_count": n,
    }


def _finalize_cert(corridors, authority, cross_check, status, reason=None):
    cert = {"status": status, "authority": authority, "scope": CAPACITY_SCOPE,
            "units": "mm", "corridors": corridors,
            "cert_sha256": (canonical.canonical_sha256(corridors)
                            if corridors else None),
            "cross_check": cross_check, "reason": reason}
    return cert


def build_capacity_cert_from_ctx(ctx):
    """净失败口的容量证书：场景重算+ctx.ledger 增量账交叉核对（双源独立）。

    cross_check 语义：ctx.ledger 增量账只为固定铜预置过的走廊建格（空起
    走廊不入增量账——engine _Context 合同），故「重算有、增量账无」不算
    不一致，记 not_available；两侧都有但不一致记 mismatch（fail-closed
    unknown）；「增量账有、重算无」记 mismatch。verified 的独立复核=
    verify_fail_event 对 terms 的算术复算+cert_sha256 绑定（与账本来源
    无关的第三方复核面）。
    """
    from .route_check import capacity_ledger as _rc_capacity_ledger
    view = ctx.view
    recomputed = _rc_capacity_ledger(
        view, list(ctx.fixed) + list(ctx.route_coppers), ctx.declared)
    corridors = []
    mismatch = False
    untracked = 0
    for clid in sorted(recomputed):
        item = recomputed[clid]
        row = _corridor_row(clid, item["entries"], item["capacity_mm"])
        zid, layer = clid.split("/", 1)
        cell = ctx.ledger.get((zid, layer))
        if cell is None:
            untracked += 1
        else:
            inc_terms = [float(w) for w in cell["widths"]]
            inc_occ = round(sum(inc_terms) + cap_mod.NET_NET_SPACING
                            * max(len(inc_terms) - 1, 0), 10)
            if (inc_terms != row["terms"]
                    or abs(inc_occ - row["occupancy_mm"]) > 1e-9
                    or abs(float(cell["capacity"]) - row["capacity_mm"])
                    > 1e-9):
                mismatch = True
        corridors.append(row)
    extra = [k for k in ctx.ledger
             if "%s/%s" % (k[0], k[1]) not in recomputed]
    if extra:
        mismatch = True
    if not corridors:
        return _finalize_cert(
            [], CAPACITY_AUTHORITY_CTX, "not_available", "not_available",
            reason="板无 corridor 容量 zone（场景重算台账为空）——空摘要不构成"
                   "容量证书、不作扩展凭证（R4B-03）")
    if mismatch:
        return _finalize_cert(
            corridors, CAPACITY_AUTHORITY_CTX, "mismatch", "unknown",
            reason="ctx.ledger 增量账与场景重算不一致——fail-closed 记 unknown")
    cross_check = "not_available" if untracked else "agree"
    return _finalize_cert(corridors, CAPACITY_AUTHORITY_CTX, cross_check,
                          "verified")


def build_capacity_cert_from_meta(cap_meta):
    """终检口容量证书：route_check 报告 capacity_meta（terms/capacity_mm）。"""
    corridors = []
    for clid in sorted(cap_meta or {}):
        meta = cap_meta[clid]
        terms = [float(t) for t in meta["terms"]]
        n = len(terms)
        occ = round(sum(terms) + cap_mod.NET_NET_SPACING * max(n - 1, 0), 10)
        corridors.append({
            "corridor_layer_id": clid,
            "capacity_mm": float(meta["capacity_mm"]),
            "terms": terms,
            "occupancy_mm": occ,
            "spacing_mm": float(cap_mod.NET_NET_SPACING),
            "arithmetic": "occupancy=round(Σterms+spacing×(n−1),10)"
                          "=%r+%r×%d=%r" % (round(sum(terms), 10),
                                            float(cap_mod.NET_NET_SPACING),
                                            max(n - 1, 0), occ),
            "entries_count": n,
        })
    if not corridors:
        return _finalize_cert(
            [], CAPACITY_AUTHORITY_META, "not_available", "not_available",
            reason="板无 corridor 容量 zone（capacity_meta 空）——空摘要不构成"
                   "容量证书、不作扩展凭证（R4B-03）")
    return _finalize_cert(corridors, CAPACITY_AUTHORITY_META,
                          "not_available", "verified")


def build_fail_event(*, fail_kind, scope, stage, attempts, cause,
                     geom_secondary, blocker_nets, available_layers,
                     tried_layers, topology, capacity_cert, bindings,
                     event_seq):
    """组装语义载荷并计算 event_id（纯函数；journal/verifier/测试共用）。"""
    if fail_kind not in _KINDS:
        raise ValueError("fail_kind %r 不在 %s" % (fail_kind, _KINDS))
    if stage not in _STAGES:
        raise ValueError("stage %r 不在 %s" % (stage, _STAGES))
    if topology["edge_order_source"] not in _EDGE_SOURCES:
        raise ValueError("edge_order_source %r 不在 %s"
                         % (topology["edge_order_source"], _EDGE_SOURCES))
    semantic = {
        "schema_version": FAIL_EVENT_SCHEMA_VERSION,
        "fail_kind": fail_kind,
        "scope": scope,
        "stage": stage,
        "attempts": int(attempts),
        "cause": str(cause),
        "geom_secondary": str(geom_secondary),
        "blocker_nets": blocker_nets,
        "available_layers": available_layers,
        "tried_layers": tried_layers,
        "topology": topology,
        "capacity_cert": capacity_cert,
        "bindings": bindings,
        "event_seq": int(event_seq),
    }
    event = dict(semantic)
    event["event_id"] = canonical.canonical_sha256(semantic)
    return event


# ---------------------------------------------------------------- 独立复核器

def verify_fail_event(event, expected_bindings=None):
    """独立复核：event_id 重算+枚举/结构检查+容量算术复核+绑定核对。

    返回 (ok: bool, errors: [str])；任何语义字段 tamper → event_id 不匹配或
    算术复核失败。expected_bindings：逐键全等子集核对（如 board_sha256/
    world_id/board_id）。
    """
    errors = []
    if not isinstance(event, dict):
        return False, ["event 不是 dict"]
    for key in ("schema_version", "event_id", "fail_kind", "scope", "stage",
                "attempts", "cause", "geom_secondary", "blocker_nets",
                "available_layers", "tried_layers", "topology", "capacity_cert",
                "bindings", "event_seq"):
        if key not in event:
            errors.append("缺语义字段 %s" % key)
    if errors:
        return False, errors
    semantic = {k: v for k, v in event.items()
                if k not in ("event_id", "runtime")}
    recomputed = canonical.canonical_sha256(semantic)
    if recomputed != event.get("event_id"):
        errors.append("event_id 重算不匹配（payload tamper 或 canonical 差）")
    if event["schema_version"] != FAIL_EVENT_SCHEMA_VERSION:
        errors.append("schema_version != %r" % FAIL_EVENT_SCHEMA_VERSION)
    if event["fail_kind"] not in _KINDS:
        errors.append("fail_kind 非法")
    if event["stage"] not in _STAGES:
        errors.append("stage 非法")
    if not isinstance(event["attempts"], int) or event["attempts"] < 0:
        errors.append("attempts 须为 ≥0 整数")
    blk = event["blocker_nets"]
    if blk.get("kind") not in ("computed_selection",
                               "geometric_blocking_evidence",
                               "not_available"):
        errors.append("blocker_nets.kind 非法")
    elif blk["kind"] == "not_available" and not blk.get("reason"):
        errors.append("blocker_nets not_available 缺 reason")
    elif blk["kind"] != "not_available":
        if not blk.get("measured"):
            errors.append("blocker_nets 非 not_available 须 measured=true")
        if not blk.get("selection_rule") or not blk.get("measurement_stage"):
            errors.append("blocker_nets 须带 selection_rule/measurement_stage")
        if blk["kind"] == "computed_selection" and "net_ids" not in blk:
            errors.append("computed_selection 须带 net_ids")
    cert = event["capacity_cert"]
    if cert.get("status") not in ("verified", "not_available", "unknown"):
        errors.append("capacity_cert.status 非法")
    elif cert["status"] == "verified":
        rows = cert.get("corridors") or []
        if not rows:
            errors.append("verified 容量证书 corridors 为空（空摘要不构成证书）")
        for row in rows:
            terms = row.get("terms") or []
            n = len(terms)
            occ = round(sum(terms) + cap_mod.NET_NET_SPACING * max(n - 1, 0), 10)
            if abs(occ - float(row.get("occupancy_mm"))) > 1e-9:
                errors.append("走廊 %s 算术复核失败：terms 复算 %r ≠ 登记 %r"
                              % (row.get("corridor_layer_id"), occ,
                                 row.get("occupancy_mm")))
        if rows and canonical.canonical_sha256(rows) != cert.get("cert_sha256"):
            errors.append("cert_sha256 与 corridors canonical hash 不匹配")
    for key, want in (expected_bindings or {}).items():
        got = event["bindings"].get(key)
        if got != want:
            errors.append("绑定 %s 不匹配：事件=%r 期望=%r" % (key, got, want))
    return (not errors), errors


# ---------------------------------------------------------------- 写侧 journal

class FailEventJournal:
    """fail-event.v1 JSONL 侧车（有界写入；IO 失败只降级不抛出）。

    兼容 ProgressSidecar 纪律：manifest 独立文件；work 事件仅由真实失败
    边界触发；blocker 测量记录只保存最近一次（每 net×partition）。
    """

    def __init__(self, path, bindings=None, max_events=DEFAULT_MAX_EVENTS,
                 max_bytes=DEFAULT_MAX_BYTES):
        self.path = str(path)
        self.max_events = int(max_events)
        self.max_bytes = int(max_bytes)
        self._fh = None
        self._seq = 0
        self._bytes = 0
        self._events = 0
        self._truncated = False
        self._broken = None
        self._closed = False
        self._t0 = time.monotonic()
        self._measurements = {}
        self.last_event_id = None
        self.bindings = dict(bindings or {})
        self.bindings.setdefault("world_id",
                                 os.environ.get(ENV_WORLD_ID) or NOT_AVAILABLE)
        self.manifest = {
            "schema": "pcbf-flow.r4b.fail-event.v1",
            "sidecar_version": FAIL_EVENT_SIDECAR_VERSION,
            "sidecar_path": self.path,
            "started_wall": now_wall_iso(),
            "max_events": self.max_events,
            "max_bytes": self.max_bytes,
            "identity": process_identity_self(),
            "bindings": self.bindings,
        }
        self._open()

    @classmethod
    def from_env(cls, bindings=None):
        """opt-in 工厂：ENV_FAIL_EVENTS 未设 → None（引擎零行为差）。"""
        path = os.environ.get(ENV_FAIL_EVENTS)
        if not path:
            return None
        try:
            return cls(path, bindings=bindings)
        except Exception as exc:
            side = cls.__new__(cls)
            side.path = str(path)
            side._fh = None
            side._broken = "from_env: %r" % (exc,)
            side._truncated = False
            side._closed = False
            side._seq = 0
            side._bytes = 0
            side._events = 0
            side._t0 = time.monotonic()
            side._measurements = {}
            side.last_event_id = None
            side.max_events = 0
            side.max_bytes = 0
            side.bindings = {}
            side.manifest = {}
            return side

    # ---- 内部（不抛出） ----

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

    def _write(self, event):
        if self._closed or self._broken is not None or self._truncated:
            return
        try:
            line = canonical.canonical_json(event).decode("utf-8") + "\n"
            raw = line.encode("utf-8")
            if (self._events + 1 > self.max_events
                    or self._bytes + len(raw) > self.max_bytes):
                note = {"schema_version": FAIL_EVENT_SCHEMA_VERSION,
                        "note": "sidecar_truncated", "reason": "bound",
                        "events_written": self._events,
                        "bytes_written": self._bytes}
                nraw = (canonical.canonical_json(note).decode("utf-8")
                        + "\n").encode("utf-8")
                if self._bytes + len(nraw) <= self.max_bytes:
                    self._fh.write(nraw.decode("utf-8"))
                    self._fh.flush()
                self._truncated = True
                return
            self._fh.write(line)
            self._fh.flush()
            self._events += 1
            self._bytes += len(raw)
        except Exception as exc:
            self._broken = "write: %r" % (exc,)

    def _emit(self, event):
        self._seq += 1
        event["runtime"] = {
            "event_seq_written": self._seq,
            "wall_t": now_wall_iso(),
            "mono_t": round(time.monotonic() - self._t0, 3),
            "pid": os.getpid(),
            "process_identity": process_identity_self(),
        }
        self._write(event)
        self.last_event_id = event.get("event_id")

    # ---- 测量登记（_ripup_retry 插桩点） ----

    def record_blocker_measurement(self, net_id, partition_id, blockers,
                                   reach_mm, ripup_round, joint_factor,
                                   params):
        self._measurements[(net_id, partition_id)] = {
            "blockers": [str(b) for b in blockers],
            "reach_mm": float(reach_mm),
            "ripup_round": int(ripup_round),
            "joint_factor": float(joint_factor),
            "measurement_stage": "ripup round %d（阶梯耗尽一致态）"
                                 % ripup_round,
            "params": {k: params.get(k) for k in sorted(params or {})},
        }

    def last_measurement(self, net_id, partition_id):
        return self._measurements.get((net_id, partition_id))

    # ---- 事件发射（引擎插桩点；全部不抛出） ----

    def _state_sha256(self, ctx):
        try:
            import hashlib
            sk = ctx.state_key()
            if isinstance(sk, str):
                sk = sk.encode("utf-8")
            return hashlib.sha256(sk).hexdigest()
        except Exception:
            return None

    def _base_bindings(self, ctx):
        b = dict(self.bindings)
        b["state_sha256"] = self._state_sha256(ctx)
        b["parent_fail_event_id"] = self.last_event_id
        b["routes_sha256"] = None
        return b

    def emit_sealed_short_circuit(self, ctx, pid, net_id, width,
                                  endpoint_index, sealing_cids,
                                  attachment_points, agree):
        if self._broken is not None or self._truncated:
            return
        try:
            view = ctx.view
            sealing_nets = sorted({str(_cid_net(view, c))
                                   for c in sealing_cids})
            event = build_fail_event(
                fail_kind="sealed_short_circuit", scope="net",
                stage="preflight_seal", attempts=0,
                cause="sealed-short-circuit（全层异网固定铜密封构造性无解，"
                      "事前短路类）",
                geom_secondary="not_available:preflight 短路口未算二级归因"
                               "（几何二级归因仅阶梯耗尽口产出）",
                blocker_nets=build_blocker_geometric(
                    sealing_nets,
                    "sealed_endpoint=e%d attachment_sealed=%d/%d layers=all "
                    "sealing_cids=%s cross_check=edge_blocked_agree=%d/%d "
                    "immutable=rip_net-scope-fixed-not-removable"
                    % (endpoint_index, attachment_points, attachment_points,
                       ",".join(sorted(sealing_cids)), agree,
                       attachment_points)),
                available_layers=build_available_layers(view),
                tried_layers=build_tried_layers_not_available(),
                topology=build_topology(
                    _partition_endpoints(view, pid), [], False,
                    "not_computed_preflight", partition_id=pid,
                    net_id=net_id),
                capacity_cert=build_capacity_cert_from_ctx(ctx),
                bindings=self._base_bindings(ctx),
                event_seq=self._seq + 1)
            self._emit(event)
        except Exception:
            self._broken = "emit_sealed_short_circuit: %r" % (_exc(),)

    def emit_fixed_shape_failed(self, ctx, pid, net_id, kind):
        if self._broken is not None or self._truncated:
            return
        try:
            view = ctx.view
            event = build_fail_event(
                fail_kind="fixed_shape_failed", scope="net",
                stage="fixed_shape", attempts=0,
                cause="fixed-shape failed: %s" % (kind,),
                geom_secondary="not_available:fixed-shape 口未算二级归因",
                blocker_nets=build_blocker_not_available(
                    "fixed-shape 失败口无 rip-up blocker 测量（ribbon/既布分区"
                    "不走 A* 阶梯）"),
                available_layers=build_available_layers(view),
                tried_layers=build_tried_layers_not_available(),
                topology=build_topology(
                    _partition_endpoints(view, pid), [], False,
                    "not_computed_fixed_shape", partition_id=pid,
                    net_id=net_id),
                capacity_cert=build_capacity_cert_from_ctx(ctx),
                bindings=self._base_bindings(ctx),
                event_seq=self._seq + 1)
            self._emit(event)
        except Exception:
            self._broken = "emit_fixed_shape_failed: %r" % (_exc(),)

    def emit_net_exhausted(self, ctx, pid, net_id, attempts, cause,
                           geom_secondary, edges, edge_order_source):
        if self._broken is not None or self._truncated:
            return
        try:
            view = ctx.view
            m = self.last_measurement(net_id, pid)
            if m is not None:
                blocker = build_blocker_from_measurement(m)
            else:
                blocker = build_blocker_not_available(
                    "本次失败前无 rip-up blocker 测量记录（_ripup_retry 未进入"
                    "或预算耗尽先返）——未计算不冒充已证空")
            event = build_fail_event(
                fail_kind="net_exhausted", scope="net",
                stage="attempt_ladder_ripup", attempts=attempts, cause=cause,
                geom_secondary=geom_secondary, blocker_nets=blocker,
                available_layers=build_available_layers(view),
                tried_layers=build_tried_layers_not_available(),
                topology=build_topology(
                    _partition_endpoints(view, pid),
                    [(e[0], e[1], e[2]) for e in (edges or [])],
                    bool(edges), edge_order_source, partition_id=pid,
                    net_id=net_id),
                capacity_cert=build_capacity_cert_from_ctx(ctx),
                bindings=self._base_bindings(ctx),
                event_seq=self._seq + 1)
            self._emit(event)
        except Exception:
            self._broken = "emit_net_exhausted: %r" % (_exc(),)

    def emit_final_check_infeasible(self, ctx, attempts, cause, cap_meta,
                                    routes_doc):
        if self._broken is not None or self._truncated:
            return
        try:
            view = ctx.view
            bindings = self._base_bindings(ctx)
            bindings["routes_sha256"] = canonical.canonical_sha256(routes_doc)
            event = build_fail_event(
                fail_kind="final_check_infeasible", scope="candidate",
                stage="final_route_check", attempts=attempts, cause=cause,
                geom_secondary="not_available:终检口无单网二级归因",
                blocker_nets=build_blocker_not_available(
                    "终检阶段无 rip-up blocker 测量（全量自检口，非单网阶梯）"),
                available_layers=build_available_layers(view),
                tried_layers=build_tried_layers_not_available(),
                topology=build_topology([], [], False,
                                        "not_computed_candidate_scope",
                                        partition_id=None, net_id=None),
                capacity_cert=build_capacity_cert_from_meta(cap_meta),
                bindings=bindings,
                event_seq=self._seq + 1)
            self._emit(event)
        except Exception:
            self._broken = "emit_final_check_infeasible: %r" % (_exc(),)

    def emit_candidate_failed_close(self, ctx, verdict_outcome, attempts):
        """候选 FAILED 收口事件（parent=本候选最后一条失败事件）。"""
        if self._broken is not None or self._truncated:
            return
        try:
            view = ctx.view
            event = build_fail_event(
                fail_kind="candidate_failed", scope="candidate",
                stage="candidate_close", attempts=attempts,
                cause="candidate FAILED: %s" % (verdict_outcome,),
                geom_secondary="not_available:候选收口无单网二级归因",
                blocker_nets=build_blocker_not_available(
                    "候选收口为聚总事件，blocker 证据见 parent net 事件"),
                available_layers=build_available_layers(view),
                tried_layers=build_tried_layers_not_available(),
                topology=build_topology([], [], False,
                                        "not_computed_candidate_scope",
                                        partition_id=None, net_id=None),
                capacity_cert={"status": "not_available",
                               "authority": "candidate_close 聚总口不重复"
                                            "出证书（证书见 net/终检事件）",
                               "scope": "candidate_close", "units": "mm",
                               "corridors": [], "cert_sha256": None,
                               "cross_check": "not_available",
                               "reason": "聚总事件不携带走廊证书"},
                bindings=self._base_bindings(ctx),
                event_seq=self._seq + 1)
            self._emit(event)
        except Exception:
            self._broken = "emit_candidate_failed_close: %r" % (_exc(),)

    @property
    def broken(self):
        return self._broken

    @property
    def truncated(self):
        return self._truncated

    def close(self):
        if self._closed:
            return
        self._closed = True
        try:
            if self._fh is not None:
                self._fh.close()
        except Exception:
            pass


# ---------------------------------------------------------------- 小工具

def _exc():
    import traceback
    return traceback.format_exc().strip().splitlines()[-1]


def _cid_net(view, cid):
    """fixed 铜 cid → 其网（pad cid 内嵌 net_id；其余按 pid→net_of 口径）。"""
    if cid.startswith("fixed:pad:"):
        parts = cid.split(":")
        for i, seg in enumerate(parts):
            if seg.startswith("e") and "#" in seg and i > 0:
                return parts[i - 1]
        return cid
    pid = cid[len("fixed:"):].split("#")[0]
    return view.net_of.get(pid, pid)


def _partition_endpoints(view, pid):
    p = view.partitions.get(pid) or {}
    ends = (p.get("geometry") or {}).get("endpoints") or []
    return [[float(x[0]), float(x[1])] for x in ends]
