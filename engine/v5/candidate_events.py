# -*- coding: utf-8 -*-
"""OPT-07／EXEC-R4-B 候选事件登记与证书准入门（candidate-event.v1）。

独立确定性 adapter（sidecar 登记）：**不给原候选载荷强塞未知键**、不改原
24 候选面/planner/selection/原候选 schema；几何/可行性仍归 executor/DRC
（本门只裁「有可复核证书才准入有界离散自由度候选」，不做 OPT-08 局部
beam 或无界层组合）。

## 准入门（fail-closed，R4B-05）

- 证书面（父证据，来自 fail-event.v1）：
  - capacity_ledger 证书=fail 事件 capacity_cert.status=="verified"（走廊×层
    容量+占用+算术+hash 已独立核验）；
  - blocker_selection 证书=fail 事件 blocker_nets.kind ∈
    {computed_selection, geometric_blocking_evidence} 且 measured=true 且
    net_ids 非空。
- expected_cert_change：cert_field/cert_kind/current_value/proposed_change{
  freedom（预注册有界离散自由度：route_order_permutation |
  edge_order_permutation | layer_assignment）/discrete_value/
  prediction_basis/cert_sha256_parent（绑定父证书）}。
- 拒绝面（typed）：parent_missing/parent_unverified/board_mismatch/
  world_mismatch/cert_not_available/cert_unknown/no_change/
  unprovable_freedom/baseline_not_extension。父证书缺失/损坏/错板错世界/
  UNKNOWN、无变化、无法证明可改变几何/阻塞证书一律拒扩。
- baseline 候选可显式标 baseline/not_applicable，登记
  registered_not_extension——**不得算证书扩展**。
- 正负向验收：正向有证书夹具须真正获准并核操纵；负向无证书/错绑/无变化
  夹具须拒绝——不能用扩展数恒 0 冒充门通过。

## event_id 与 volatile 边界

同 fail-event.v1 口径：``event_id = canonical_sha256(payload − {event_id,
runtime})``；runtime（wall_t/mono_t/pid/process_identity）单列、不入语义。
"""
import json
import os
import time

from . import canonical
from .health_watchdog import (ENV_WORLD_ID, NOT_AVAILABLE, now_wall_iso,
                              process_identity_self)
from .failure_events import (FAIL_EVENT_SCHEMA_VERSION,
                             verify_fail_event)

CANDIDATE_EVENT_SCHEMA_VERSION = "candidate-event.v1"
ENV_CANDIDATE_EVENTS = "V5_R4B_CANDIDATE_EVENTS"
CANDIDATE_EVENT_SIDECAR_VERSION = "v5.candidate_events/0.1.0"

CANDIDATE_REASONS = (
    "baseline",
    "cert_extension_route_order",
    "cert_extension_edge_order",
    "cert_extension_layer_assignment",
)
FREEDOMS = (
    "route_order_permutation",
    "edge_order_permutation",
    "layer_assignment",
)
CERT_KINDS = ("capacity_ledger", "blocker_selection")
REJECTION_REASONS = (
    "parent_missing", "parent_unverified", "board_mismatch",
    "world_mismatch", "cert_not_available", "cert_unknown", "no_change",
    "unprovable_freedom", "baseline_not_extension",
)
ADMIT_REASONS = ("all_checks_passed", "baseline_registered_not_extension")


# ---------------------------------------------------------------- 准入门

def _cert_state(fail_event):
    """从 fail 事件提取可用证书面。

    返回 {cert_kind: cert_sha256|None}：
    - capacity_ledger：capacity_cert.status=="verified" 且 corridors 非空 →
      hash=capacity_cert.cert_sha256；否则不列（not_available/unknown 记入
      _cert_status_raw）。
    - blocker_selection：blocker_nets.kind ∈ {computed_selection,
      geometric_blocking_evidence} 且 measured=true 且 net_ids 非空 →
      hash=父 fail 事件 event_id。
    """
    certs = {}
    cert = fail_event.get("capacity_cert") or {}
    blk = fail_event.get("blocker_nets") or {}
    if cert.get("status") == "verified" and cert.get("corridors"):
        certs["capacity_ledger"] = cert.get("cert_sha256")
    if (blk.get("kind") in ("computed_selection",
                            "geometric_blocking_evidence")
            and blk.get("measured") and blk.get("net_ids")):
        certs["blocker_selection"] = fail_event.get("event_id")
    return certs


def _cert_status_raw(fail_event):
    cert = fail_event.get("capacity_cert") or {}
    if cert.get("status") == "unknown":
        return "unknown"
    if cert.get("status") == "verified":
        return "verified"
    return "not_available"


def evaluate_admission(*, fail_event, candidate_reason, expected_cert_change,
                       board_sha256, world_id):
    """准入门判定（纯函数）。返回 admission 块 dict。

    fail_event=None → parent_missing；event_id/载荷核验不过 →
    parent_unverified；board/world 绑定不符 → *_mismatch；证书不可得 →
    cert_not_available/cert_unknown；无变化 → no_change；自由度不可证明 →
    unprovable_freedom；baseline → registered_not_extension。
    """
    checks = {
        "parent_event_present": fail_event is not None,
        "parent_event_verified": False,
        "board_binding_match": False,
        "world_binding_match": False,
        "cert_verified": False,
        "expected_change_actionable": False,
    }
    if candidate_reason == "baseline":
        # baseline 显式标记，不主张证书、不要求父失败事件（可先于任何失败
        # 存在）；登记 registered_not_extension——不得算证书扩展。
        checks["parent_event_present"] = fail_event is not None
        checks["board_binding_match"] = True
        checks["world_binding_match"] = True
        return {"decision": "registered_not_extension",
                "reason": "baseline_registered_not_extension",
                "cert_status": "not_applicable", "checks": checks}
    if fail_event is None:
        return {"decision": "rejected", "reason": "parent_missing",
                "cert_status": "not_available", "checks": checks}
    ok, errors = verify_fail_event(fail_event)
    checks["parent_event_verified"] = ok
    if not ok:
        return {"decision": "rejected", "reason": "parent_unverified",
                "cert_status": "corrupt", "checks": checks,
                "verify_errors": errors[:5]}
    fb = fail_event.get("bindings") or {}
    checks["board_binding_match"] = (fb.get("board_sha256") == board_sha256)
    if not checks["board_binding_match"]:
        return {"decision": "rejected", "reason": "board_mismatch",
                "cert_status": _cert_status_raw(fail_event),
                "checks": checks}
    checks["world_binding_match"] = (fb.get("world_id") == world_id)
    if not checks["world_binding_match"]:
        return {"decision": "rejected", "reason": "world_mismatch",
                "cert_status": _cert_status_raw(fail_event), "checks": checks}
    if candidate_reason == "baseline":
        checks["cert_verified"] = False   # baseline 不主张证书
        return {"decision": "registered_not_extension",
                "reason": "baseline_registered_not_extension",
                "cert_status": "not_applicable", "checks": checks}
    certs = _cert_state(fail_event)
    raw_status = _cert_status_raw(fail_event)
    if not certs:
        reason = ("cert_not_available" if raw_status == "not_available"
                  else "cert_unknown")
        return {"decision": "rejected", "reason": reason,
                "cert_status": raw_status, "checks": checks}
    ecc = expected_cert_change or {}
    if ecc.get("kind") != "cert_field_change":
        return {"decision": "rejected", "reason": "unprovable_freedom",
                "cert_status": raw_status, "checks": checks,
                "note": "扩展候选须 kind=cert_field_change（baseline 专用 "
                        "not_applicable 不适用于扩展）"}
    pc = ecc.get("proposed_change") or {}
    freedom = pc.get("freedom")
    if freedom not in FREEDOMS or not pc.get("prediction_basis"):
        return {"decision": "rejected", "reason": "unprovable_freedom",
                "cert_status": raw_status, "checks": checks}
    cert_kind = ecc.get("cert_kind")
    if cert_kind not in certs:
        return {"decision": "rejected", "reason": "unprovable_freedom",
                "cert_status": raw_status, "checks": checks,
                "note": "cert_kind=%r 与父事件可用证书 %s 不符"
                        % (cert_kind, sorted(certs))}
    cert_sha = certs[cert_kind]
    checks["cert_verified"] = True
    if pc.get("cert_sha256_parent") != cert_sha:
        return {"decision": "rejected", "reason": "unprovable_freedom",
                "cert_status": "verified", "checks": checks,
                "note": "cert_sha256_parent 未绑定所选父证书 hash"}
    if (ecc.get("current_value") is None
            or pc.get("discrete_value") in (None, ecc.get("current_value"))):
        return {"decision": "rejected", "reason": "no_change",
                "cert_status": "verified", "checks": checks}
    checks["expected_change_actionable"] = True
    return {"decision": "admitted", "reason": "all_checks_passed",
            "cert_status": "verified", "checks": checks,
            "cert_kind": cert_kind, "cert_sha256": cert_sha}


# ---------------------------------------------------------------- 事件构建

def build_candidate_event(*, candidate_id, candidate_reason, affected_nets,
                          expected_cert_change, source_fail_event,
                          admission, bindings, event_seq):
    if candidate_reason not in CANDIDATE_REASONS:
        raise ValueError("candidate_reason %r 不在受控词表 %s"
                         % (candidate_reason, CANDIDATE_REASONS))
    if not candidate_reason:
        raise ValueError("candidate_reason 须为非空受控词")
    semantic = {
        "schema_version": CANDIDATE_EVENT_SCHEMA_VERSION,
        "candidate_id": str(candidate_id),
        "candidate_reason": candidate_reason,
        "affected_nets": [str(n) for n in (affected_nets or [])],
        "expected_cert_change": expected_cert_change,
        "source_fail_event": source_fail_event,
        "admission": admission,
        "bindings": bindings,
        "event_seq": int(event_seq),
    }
    event = dict(semantic)
    event["event_id"] = canonical.canonical_sha256(semantic)
    return event


def verify_candidate_event(event, expected_bindings=None):
    errors = []
    if not isinstance(event, dict):
        return False, ["event 不是 dict"]
    semantic = {k: v for k, v in event.items()
                if k not in ("event_id", "runtime")}
    if canonical.canonical_sha256(semantic) != event.get("event_id"):
        errors.append("event_id 重算不匹配")
    if event.get("schema_version") != CANDIDATE_EVENT_SCHEMA_VERSION:
        errors.append("schema_version 非法")
    if event.get("candidate_reason") not in CANDIDATE_REASONS:
        errors.append("candidate_reason 不在受控词表")
    adm = event.get("admission") or {}
    decision = adm.get("decision")
    if decision not in ("admitted", "rejected", "registered_not_extension"):
        errors.append("admission.decision 非法")
    elif decision == "admitted" and adm.get("reason") not in ADMIT_REASONS:
        errors.append("admitted 须带通过 reason")
    elif decision == "rejected" and adm.get("reason") not in REJECTION_REASONS:
        errors.append("rejected 须带受控拒绝 reason")
    for key, want in (expected_bindings or {}).items():
        got = (event.get("bindings") or {}).get(key)
        if got != want:
            errors.append("绑定 %s 不匹配：事件=%r 期望=%r" % (key, got, want))
    return (not errors), errors


# ---------------------------------------------------------------- 登记侧车

class CandidateEventJournal:
    """candidate-event.v1 JSONL 登记侧车（登记+准入门调用面，不抛出到引擎）。"""

    def __init__(self, path, bindings=None):
        self.path = str(path)
        self._fh = None
        self._seq = 0
        self._broken = None
        self._t0 = time.monotonic()
        self.bindings = dict(bindings or {})
        self.bindings.setdefault("world_id",
                                 os.environ.get(ENV_WORLD_ID) or NOT_AVAILABLE)
        self.manifest = {
            "schema": "pcbf-flow.r4b.candidate-event.v1",
            "sidecar_version": CANDIDATE_EVENT_SIDECAR_VERSION,
            "sidecar_path": self.path,
            "started_wall": now_wall_iso(),
            "identity": process_identity_self(),
            "bindings": self.bindings,
        }
        try:
            os.makedirs(os.path.dirname(os.path.abspath(self.path)) or ".",
                        exist_ok=True)
            with open(self.path + ".manifest.json", "w", encoding="utf-8",
                      newline="\n") as f:
                json.dump(self.manifest, f, ensure_ascii=True, indent=1,
                          sort_keys=True)
                f.write("\n")
            self._fh = open(self.path, "a", encoding="utf-8", newline="\n")
        except Exception as exc:
            self._broken = "open: %r" % (exc,)
            self._fh = None

    @classmethod
    def from_env(cls, bindings=None):
        path = os.environ.get(ENV_CANDIDATE_EVENTS)
        if not path:
            return None
        return cls(path, bindings=bindings)

    def register(self, *, candidate, candidate_reason, affected_nets,
                 expected_cert_change, fail_event, board_sha256=None,
                 extra_bindings=None):
        """登记一个候选事件：先过准入门，再落 JSONL。

        返回 (event, admission)。candidate=原候选 dict（只读，不强塞键）。
        """
        board = board_sha256 or (self.bindings.get("board_sha256"))
        admission = evaluate_admission(
            fail_event=fail_event, candidate_reason=candidate_reason,
            expected_cert_change=expected_cert_change,
            board_sha256=board, world_id=self.bindings.get("world_id"))
        bindings = dict(self.bindings)
        if extra_bindings:
            bindings.update(extra_bindings)
        bindings["candidate_sha256"] = canonical.canonical_sha256(candidate)
        event = build_candidate_event(
            candidate_id=candidate.get("candidate_id", ""),
            candidate_reason=candidate_reason,
            affected_nets=affected_nets,
            expected_cert_change=expected_cert_change,
            source_fail_event=(fail_event or {}).get("event_id"),
            admission=admission,
            bindings=bindings,
            event_seq=self._seq + 1)
        self._seq += 1
        event["runtime"] = {
            "event_seq_written": self._seq,
            "wall_t": now_wall_iso(),
            "mono_t": round(time.monotonic() - self._t0, 3),
            "pid": os.getpid(),
            "process_identity": process_identity_self(),
        }
        if self._fh is not None and self._broken is None:
            try:
                self._fh.write(canonical.canonical_json(event).decode("utf-8")
                               + "\n")
                self._fh.flush()
            except Exception as exc:
                self._broken = "write: %r" % (exc,)
        return event, admission

    def close(self):
        try:
            if self._fh is not None:
                self._fh.close()
        except Exception:
            pass

    @property
    def broken(self):
        return self._broken


# ------------------------------------------------ 引擎出口登记（EXEC-R8-B）

def register_engine_exit(journal, *, candidate, affected_nets,
                         source_fail_event_id=None, board_sha256=None):
    """EXEC-R8-B：引擎候选出口登记面（既有契约零改动；仅消费/发射面）。

    引擎出口事件走既有 baseline 通道：candidate_reason=baseline →
    registered_not_extension（不算证书扩展）；expected_cert_change=
    not_applicable（引擎出口不主张证书扩展）。FAILED 收口可携带
    source_fail_event_id（=FailEventJournal.last_event_id 的收口事件 id，
    只引用不重放：baseline 面不触发父事件核验，checks.parent_event_verified
    保持 False=如实「未核验」，source_fail_event 落事件留关联）。
    journal=None（env 未设）→ (None, None) 零行为差。
    """
    if journal is None:
        return None, None
    fail_ref = ({"event_id": source_fail_event_id}
                if source_fail_event_id else None)
    return journal.register(
        candidate=candidate, candidate_reason="baseline",
        affected_nets=affected_nets,
        expected_cert_change={"kind": "not_applicable"},
        fail_event=fail_ref, board_sha256=board_sha256)


# ---------------------------------------------------------------- 汇总

def summarize(path):
    """读 JSONL 汇总：登记/准入/拒绝/baseline 计数（缺文件 → 全 0）。"""
    counts = {"registered": 0, "admitted": 0, "rejected": 0,
              "registered_not_extension": 0,
              "rejected_by_reason": {}, "admitted_cert_kinds": {}}
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    ev = json.loads(line)
                except ValueError:
                    counts["registered"] += 1
                    continue
                counts["registered"] += 1
                adm = ev.get("admission") or {}
                decision = adm.get("decision")
                if decision == "admitted":
                    counts["admitted"] += 1
                    ck = adm.get("cert_kind") or "unknown"
                    counts["admitted_cert_kinds"][ck] = \
                        counts["admitted_cert_kinds"].get(ck, 0) + 1
                elif decision == "rejected":
                    counts["rejected"] += 1
                    reason = adm.get("reason") or "unknown"
                    counts["rejected_by_reason"][reason] = \
                        counts["rejected_by_reason"].get(reason, 0) + 1
                elif decision == "registered_not_extension":
                    counts["registered_not_extension"] += 1
    except FileNotFoundError:
        pass
    return counts
