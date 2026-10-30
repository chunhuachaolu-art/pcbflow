"""pcbflow v3.0 命令面（SPEC-v3.0-PROPOSAL TL-0..TL-3）。

独立于 pcbflow.cli（v1.x 命令面 byte-exact 不动）。生成器模式沿用：
stdout 输出 canonical JSON、零落盘、零子进程；落盘由 shell 重定向完成。

用法（产物落盘示例；<> 为参数）：
  python -m pcbflow.v3cli manifest --manifest profiles/smoke-2l/manifest.json
  python -m pcbflow.v3cli context  --manifest profiles/smoke-2l/manifest.json
  python -m pcbflow.v3cli graph    --graph profiles/smoke-2l/graph.json
        > out/v3-smoke-2l/graph-report.json
  python -m pcbflow.v3cli lease --state - --select acquire --scope <scope> \
        --holder <actor>          > lease-state.json（首取）
  python -m pcbflow.v3cli lease --state lease-state.json --select release \
        --lease-id <id> --holder <actor> > lease-state.json
  python -m pcbflow.v3cli inventory > asm-inventory.json
  python -m pcbflow.v3cli physics --report physics-report.json \
        --required required.json > physics-gate.json
  python -m pcbflow.v3cli physics --select required-chain \
        --profile profiles/smoke-4l/profile.json \
        --evidence profiles/smoke-4l/inputs/physics-evidence.json \
        > tl3-chain-bundle.json（TL-3 required 全链编排）
  python -m pcbflow.v3cli backend --select capability
  python -m pcbflow.v3cli proposer --select validate --patch patch.json \
        --allowlist allowlist.json

TL-1/TL-2 命令（ledger/judge/gate/critic/queue）在对应模块就绪后挂载；
未挂载命令如实回 not_implemented（exit 4），不冒充可用。

exit-code 契约同 config.py：0=ok 1=failed 2=blocked 3=unknown 4=specified。
"""

from __future__ import annotations

import argparse
import json
import sys

from . import artifact_graph, config, external_backend, hashing, manifest
from . import asm_inventory, physics as physics_mod, proposer as proposer_mod
from . import schemas as schemas_mod

TOOL_VERSION = config.TOOL_VERSION
_PENDING_COMMANDS: tuple = ()


def _emit(obj) -> None:
    sys.stdout.buffer.write(hashing.canonical_json_bytes(obj))
    sys.stdout.buffer.flush()


def _exit(status: str) -> int:
    return {"ok": config.EXIT_OK, "failed": config.EXIT_FAILED,
            "blocked": config.EXIT_BLOCKED,
            "unknown": config.EXIT_UNKNOWN}[status]


def _read_json(path: str):
    with open(path, "r", encoding=config.ENCODING) as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# TL-0：manifest / context / graph / lease / inventory
# ---------------------------------------------------------------------------

def cmd_manifest(args) -> int:
    try:
        mf, mf_sha = manifest.load_manifest(args.manifest)
        errors = manifest.validate_manifest(mf)
        profile_sha = None
        import os
        cand = args.profile or None
        if cand is None:
            cand = os.path.join(os.path.dirname(
                os.path.abspath(args.manifest)), "profile.json")
        if os.path.isfile(cand):
            _, profile_sha = manifest.load_profile(cand)
        out = {
            "command": "v3-manifest", "status": "ok" if not errors
            else "blocked",
            "manifest_path": args.manifest,
            "manifest_sha256": mf_sha,
            "profile_sha256": profile_sha,
            "project_id": mf.get("project_id"),
            "profile_id": mf.get("profile_id"),
            "errors": errors,
        }
        _emit(out)
        return _exit(out["status"])
    except Exception as exc:
        _emit({"command": "v3-manifest", "status": "failed",
               "error": str(exc)})
        return config.EXIT_FAILED


def cmd_context(args) -> int:
    try:
        from . import context as context_mod
        ctx = context_mod.build_context(args.manifest, args.profile)
        errors = context_mod.validate_context(ctx)
        out = dict(ctx)
        out["command"] = "v3-context"
        out["status"] = "ok" if not errors else "blocked"
        out["context_errors"] = errors
        _emit(out)
        return _exit(out["status"])
    except Exception as exc:
        _emit({"command": "v3-context", "status": "failed",
               "error": str(exc)})
        return config.EXIT_FAILED


def cmd_graph(args) -> int:
    try:
        import os
        spec = _read_json(args.graph)
        root = os.path.dirname(os.path.abspath(args.graph))
        nodes = []
        for n in spec.get("nodes", []):
            n = dict(n)
            if n.get("sha256") is None and n.get("path"):
                p = os.path.join(root, *n["path"].split("/"))
                if os.path.isfile(p):
                    n["sha256"] = hashing.sha256_file(p)
                else:
                    n["status"] = "missing"
            nodes.append(artifact_graph.make_node(
                n["artifact_id"], n["kind"], sha256=n.get("sha256"),
                path=n.get("path"), inputs=n.get("inputs", []),
                status=n.get("status", "present"),
                revision=n.get("revision"), stage_label=n.get("stage_label"),
                expected_input_hashes=n.get("expected_input_hashes")))
        graph = artifact_graph.build_graph(nodes)
        report = artifact_graph.validate_graph(graph)
        disk = artifact_graph.compare_with_disk(graph, root)
        bad_disk = sorted(k for k, v in disk.items() if v != "present")
        clean = (report["acyclic"] and not report["cycle_nodes"]
                 and not report["stale_nodes"]
                 and not report["unresolved_inputs"]
                 and not report["cross_revision_edges"]
                 and not report["future_label_violations"]
                 and not bad_disk)
        out = {
            "command": "v3-graph", "status": "ok" if clean else "blocked",
            "graph_spec": args.graph,
            "graph_sha256": artifact_graph.graph_sha256(graph),
            "report": report,
            "disk_status": disk,
            "disk_stale_or_missing": bad_disk,
        }
        _emit(out)
        return _exit(out["status"])
    except Exception as exc:
        _emit({"command": "v3-graph", "status": "failed",
               "error": str(exc)})
        return config.EXIT_FAILED


def cmd_lease(args) -> int:
    from . import lease as lease_mod
    try:
        if args.state == "-":
            state = lease_mod.empty_state()
        else:
            state = _read_json(args.state)
            if not isinstance(state, dict) or "leases" not in state \
                    or "journal" not in state:
                _emit({"command": "v3-lease", "select": args.select,
                       "status": "blocked",
                       "error": "state 文件非法（应为纯 lease 状态对象"
                                "{schema_version,epoch,leases,journal}，"
                                "非 CLI 信封；首取请用 --state -）"})
                return config.EXIT_BLOCKED
        if args.select == "verify":
            errors = lease_mod.verify_journal(state.get("journal", []))
            _emit({"command": "v3-lease", "select": "verify",
                   "status": "ok" if not errors else "blocked",
                   "errors": errors})
            return _exit("ok" if not errors else "blocked")
        if args.select == "status":
            _emit({"command": "v3-lease", "select": "status", "status": "ok",
                   "leases": lease_mod.lease_status(
                       state, args.scope) if args.scope else
                   [lease_mod.lease_status(state, s)
                    for s in state.get("leases", {})]})
            return config.EXIT_OK
        record = None
        error = None
        if args.select == "acquire":
            state, record, error = lease_mod.acquire(
                state, args.scope, args.holder)
        elif args.select == "release":
            state, record, error = lease_mod.release(
                state, args.lease_id, args.holder)
        elif args.select == "extend":
            state, record, error = lease_mod.extend(
                state, args.lease_id, args.holder)
        if error is not None:
            # 冲突：输出未变更状态（盲目重定向也不破坏状态文件）+ exit 2
            sys.stderr.write(f"blocked: {error}\n")
            _emit(state)
            return config.EXIT_BLOCKED
        # 成功转移：stdout=新纯状态对象（shell 重定向覆盖状态文件）
        _emit(state)
        return config.EXIT_OK
    except Exception as exc:
        _emit({"command": "v3-lease", "status": "failed", "error": str(exc)})
        return config.EXIT_FAILED


def cmd_inventory(args) -> int:
    try:
        inv = asm_inventory.build_inventory(
            roots=tuple(args.roots.split(",")) if args.roots else None)
        errors = asm_inventory.validate_inventory(inv)
        out = dict(inv)
        out["command"] = "v3-inventory"
        out["status"] = "ok" if not errors else "blocked"
        out["validation_errors"] = errors
        _emit(out)
        return _exit(out["status"])
    except Exception as exc:
        _emit({"command": "v3-inventory", "status": "failed",
               "error": str(exc)})
        return config.EXIT_FAILED


# ---------------------------------------------------------------------------
# TL-3/TD7/TD11 薄封装
# ---------------------------------------------------------------------------

#: TL-3 required 链的账本文件写入口径（编排侧按此落盘 out/v3-tl3/
#: decision-ledger.jsonl；每条 canonical JSON + 换行）
def _chain_input_hashes(manifest_path: str, evidence_path: str) -> tuple:
    """从磁盘计算 required 链输入绑定（manifest 解析 + 文件 sha256）。

    返回 (input_hashes, errors)。路径全部经 manifest.resolve_path 规范化
    （越界/缺失按缺输入处理，不猜默认）。只读，不落盘。
    """
    import os

    from . import toolchain as tc_mod

    mf, _ = manifest.load_manifest(manifest_path)
    wanted = [("profile", args_profile_path(manifest_path))]
    for name in ("board", "netlist", "stackup", "constraints"):
        rel = (mf.get("inputs") or {}).get(name)
        resolved = manifest.resolve_path(mf, manifest_path, rel)
        wanted.append((name, resolved))
    tc_rel = (mf.get("toolchain") or {}).get("lock_path")
    wanted.append(("toolchain_lock",
                   manifest.resolve_path(mf, manifest_path, tc_rel)))
    wanted.append(("physics_evidence", os.path.abspath(evidence_path)))
    hashes: dict = {}
    errors: list = []
    for name, path in wanted:
        if path is None or not os.path.isfile(path):
            errors.append(f"输入 {name!r} 路径缺失或不可解析: {path!r}")
        else:
            hashes[name] = hashing.sha256_file(path)
    if tc_mod.load_lock() is None:
        errors.append("toolchain_lock 未探测（load_lock=None）")
    return hashes, errors


def args_profile_path(manifest_path: str) -> str:
    import os
    return os.path.join(os.path.dirname(os.path.abspath(manifest_path)),
                        "profile.json")


def _autotune_input_hashes(manifest_path: str, space_path: str,
                           baseline_path: str) -> tuple:
    """TL-4 autotune 链输入绑定（manifest 解析 + 文件 sha256；只读不落盘）。

    必需：profile/manifest/search_space/baseline_config/constraints/board/
    toolchain_lock；netlist/stackup 声明非 null 时一并对账绑定。
    返回 (input_hashes, errors)。
    """
    import os

    from . import toolchain as tc_mod

    mf, _ = manifest.load_manifest(manifest_path)
    wanted = [("profile", args_profile_path(manifest_path)),
              ("manifest", os.path.abspath(manifest_path)),
              ("constraints",
               manifest.resolve_path(
                   mf, manifest_path, (mf.get("inputs") or {}).get(
                       "constraints"))),
              ("board",
               manifest.resolve_path(
                   mf, manifest_path, (mf.get("inputs") or {}).get("board")))]
    for name in ("netlist", "stackup"):
        rel = (mf.get("inputs") or {}).get(name)
        if rel is not None:
            wanted.append((name, manifest.resolve_path(mf, manifest_path,
                                                       rel)))
    tc_rel = (mf.get("toolchain") or {}).get("lock_path")
    wanted.append(("toolchain_lock",
                   manifest.resolve_path(mf, manifest_path, tc_rel)))
    wanted.append(("search_space", os.path.abspath(space_path)))
    wanted.append(("baseline_config", os.path.abspath(baseline_path)))
    hashes: dict = {}
    errors: list = []
    for name, path in wanted:
        if path is None or not os.path.isfile(path):
            errors.append(f"输入 {name!r} 路径缺失或不可解析: {path!r}")
        else:
            hashes[name] = hashing.sha256_file(path)
    if tc_mod.load_lock() is None:
        errors.append("toolchain_lock 未探测（load_lock=None）")
    return hashes, errors


def cmd_physics(args) -> int:
    try:
        if args.select == "required-chain":
            import os

            from . import physics_chain
            if not args.profile or not args.evidence:
                _emit({"command": "v3-physics",
                       "select": "required-chain", "status": "failed",
                       "error": "required-chain 需要 --profile 与 --evidence"})
                return config.EXIT_FAILED
            manifest_path = os.path.join(
                os.path.dirname(os.path.abspath(args.profile)),
                "manifest.json")
            if not os.path.isfile(manifest_path):
                _emit({"command": "v3-physics",
                       "select": "required-chain", "status": "failed",
                       "error": f"manifest 不存在: {manifest_path}"})
                return config.EXIT_FAILED
            input_hashes, errors = _chain_input_hashes(
                manifest_path, args.evidence)
            if errors:
                _emit({"command": "v3-physics",
                       "select": "required-chain", "status": "blocked",
                       "errors": errors})
                return config.EXIT_BLOCKED
            profile, _ = manifest.load_profile(args.profile)
            evidence = _read_json(args.evidence)
            from . import gate as gate_mod
            bundle = physics_chain.build_chain(
                profile, evidence, input_hashes,
                snapshot_revision=args.snapshot_revision,
                gate_id=args.gate_id,
                evaluator={"name": "pcbflow-v3-physics-chain",
                           "version": "1.0",
                           "code_sha256": hashing.sha256_file(
                               physics_chain.__file__)})
            ledger_ok = not bundle["ledger_verify"]["chain_errors"] \
                and not bundle["ledger_verify"]["supersedes_errors"]
            record = bundle["gate_record"]
            if not ledger_ok or bundle["gate_verify_errors"]:
                status = "blocked"
            elif record["result"] == "pass":
                status = "ok"
            elif record["result"] == "blocked":
                status = "blocked"
            else:
                status = "failed"
            out = dict(bundle)
            out["command"] = "v3-physics"
            out["select"] = "required-chain"
            out["status"] = status
            out["gate_evaluator_bound"] = {
                "module": "pcbflow.physics_chain",
                "code_sha256": hashing.sha256_file(physics_chain.__file__),
                "note": "evaluator.code_sha256 绑定判定代码版本"
                        "（gate 由机器谓词计算，人工不可直写）"}
            _emit(out)
            return _exit(status)
        # select=gate：对既有 report 做 fail-closed 门评估（原合同不变）
        if not args.report:
            _emit({"command": "v3-physics", "select": "gate",
                   "status": "failed", "error": "gate 需要 --report"})
            return config.EXIT_FAILED
        report = _read_json(args.report)
        required = _read_json(args.required) if args.required else \
            [i["item_id"] for i in report.get("items", [])]
        result = physics_mod.evaluate_gate(report.get("items", []), required)
        _emit({"command": "v3-physics", "status": "ok", **result})
        return config.EXIT_OK
    except Exception as exc:
        _emit({"command": "v3-physics", "status": "failed",
               "error": str(exc)})
        return config.EXIT_FAILED


def cmd_backend(args) -> int:
    try:
        if args.select == "capability":
            from . import toolchain as tc_mod
            lock = tc_mod.load_lock()
            if lock is None:
                _emit({"command": "v3-backend", "status": "blocked",
                       "error": "toolchain_lock 未探测（load_lock=None）"})
                return config.EXIT_BLOCKED
            _emit({"command": "v3-backend", "select": "capability",
                   "status": "ok",
                   "claims": external_backend.capability_claims(lock)})
            return config.EXIT_OK
        if args.select == "policy":
            record = _read_json(args.record)
            declaration = _read_json(args.declaration) \
                if args.declaration else {}
            errors = external_backend.validate_policy(record, declaration)
            _emit({"command": "v3-backend", "select": "policy",
                   "status": "ok" if not errors else "blocked",
                   "errors": errors})
            return _exit("ok" if not errors else "blocked")
        if args.select == "assess":
            record = _read_json(args.record)
            stages = _read_json(args.stages)
            _emit({"command": "v3-backend", "select": "assess",
                   "status": "ok",
                   **external_backend.assess_output(record, stages)})
            return config.EXIT_OK
        _emit({"command": "v3-backend", "status": "failed",
               "error": f"未知 select {args.select}"})
        return config.EXIT_FAILED
    except Exception as exc:
        _emit({"command": "v3-backend", "status": "failed",
               "error": str(exc)})
        return config.EXIT_FAILED


def cmd_proposer(args) -> int:
    try:
        if args.select == "autotune-chain":
            # autotune-chain 不消费 patch/allowlist（输入为 profile/space/
            # baseline），提前分流避免无关读取
            return _cmd_proposer_autotune_chain(args)
        patch = _read_json(args.patch)
        allowlist = _read_json(args.allowlist) if args.allowlist else []
        if args.select == "validate":
            errors = proposer_mod.validate_patch(patch, allowlist)
            _emit({"command": "v3-proposer", "select": "validate",
                   "status": "ok" if not errors else "blocked",
                   "errors": errors})
            return _exit("ok" if not errors else "blocked")
        if args.select == "evaluate":
            result = proposer_mod.evaluate_patch(
                patch, args.base or "", allowlist)
            status = {"blocked": "blocked",
                      "human_review_candidate": "blocked",
                      "eligible_for_adoption_flow": "ok"}[result["status"]]
            _emit({"command": "v3-proposer", "select": "evaluate",
                   "status": status, **result,
                   "note": "eligible 仅=可进入 adoption 流程；"
                           "自动 apply 路径不存在（TD11）"})
            return _exit(status)
        if args.select == "adoption":
            payload = _read_json(args.adoption_spec)
            result = proposer_mod.adoption_gate(**payload)
            status = {"adopt_candidate": "ok", "reject": "failed",
                      "blocked": "blocked"}[result["decision"]]
            _emit({"command": "v3-proposer", "select": "adoption",
                   "status": status, **result})
            return _exit(status)
        _emit({"command": "v3-proposer", "status": "failed",
               "error": f"未知 select {args.select}"})
        return config.EXIT_FAILED
    except Exception as exc:
        _emit({"command": "v3-proposer", "status": "failed",
               "error": str(exc)})
        return config.EXIT_FAILED


def _cmd_proposer_autotune_chain(args) -> int:
    """TL-4 autotune 全链编排（search_space → adoption → ledger → gate）。

    生成器纪律：stdout canonical JSON、零子进程、零自身落盘；blocked 如实
    exit 2。产物由 shell 重定向进 out/v3-tl4/。
    """
    import os

    from . import autotune_chain
    try:
        if not args.profile or not args.space or not args.baseline:
            _emit({"command": "v3-proposer", "select": "autotune-chain",
                   "status": "failed",
                   "error": "autotune-chain 需要 --profile、--space "
                            "与 --baseline"})
            return config.EXIT_FAILED
        manifest_path = os.path.join(
            os.path.dirname(os.path.abspath(args.profile)), "manifest.json")
        if not os.path.isfile(manifest_path):
            _emit({"command": "v3-proposer", "select": "autotune-chain",
                   "status": "failed",
                   "error": f"manifest 不存在: {manifest_path}"})
            return config.EXIT_FAILED
        input_hashes, errors = _autotune_input_hashes(
            manifest_path, args.space, args.baseline)
        if errors:
            _emit({"command": "v3-proposer", "select": "autotune-chain",
                   "status": "blocked", "errors": errors})
            return config.EXIT_BLOCKED
        profile, _ = manifest.load_profile(args.profile)
        space = _read_json(args.space)
        baseline = _read_json(args.baseline)
        mf_loaded, _ = manifest.load_manifest(manifest_path)
        constraints_path = manifest.resolve_path(
            mf_loaded, manifest_path,
            (mf_loaded.get("inputs") or {}).get("constraints"))
        constraints = _read_json(constraints_path)
        bundle = autotune_chain.build_chain(
            profile, space, baseline, constraints, input_hashes,
            snapshot_revision=args.snapshot_revision,
            gate_id=args.gate_id,
            evaluator={"name": "pcbflow-v3-autotune-chain", "version": "1.0",
                       "code_sha256": hashing.sha256_file(
                           autotune_chain.__file__)})
        ledger_ok = not bundle["ledger_verify"]["chain_errors"] \
            and not bundle["ledger_verify"]["supersedes_errors"]
        record = bundle["gate_record"]
        if not ledger_ok or bundle["gate_verify_errors"]:
            status = "blocked"
        elif record["result"] == "pass":
            status = "ok"
        elif record["result"] == "blocked":
            status = "blocked"
        else:
            status = "failed"
        out = dict(bundle)
        out["command"] = "v3-proposer"
        out["select"] = "autotune-chain"
        out["status"] = status
        out["gate_evaluator_bound"] = {
            "module": "pcbflow.autotune_chain",
            "code_sha256": hashing.sha256_file(autotune_chain.__file__),
            "note": "evaluator.code_sha256 绑定判定代码版本"
                    "（gate 由机器谓词计算，人工不可直写）"}
        _emit(out)
        return _exit(status)
    except Exception as exc:
        _emit({"command": "v3-proposer", "select": "autotune-chain",
               "status": "failed", "error": str(exc)})
        return config.EXIT_FAILED
    except Exception as exc:
        _emit({"command": "v3-proposer", "status": "failed",
               "error": str(exc)})
        return config.EXIT_FAILED


def cmd_critic(args) -> int:
    from . import critic as critic_mod
    try:
        run = _read_json(args.run) if args.run else None
        if args.select == "triage":
            ctx = _read_json(args.context) if args.context else {}
            result = critic_mod.triage(run, **{
                "judge_gate_pass": bool(ctx.get("judge_gate_pass")),
                "required_checkers_executed": bool(
                    ctx.get("required_checkers_executed")),
                "no_stale_or_unknown": bool(ctx.get("no_stale_or_unknown")),
                "whitelist_item": bool(ctx.get("whitelist_item"))})
            _emit({"command": "v3-critic", "select": "triage",
                   "status": "ok", "auto_route": result,
                   "run": run,
                   "note": "queue_deprioritized 仅队列分流非质量 pass；"
                           "advisory_only，无门/板写权限"})
            return config.EXIT_OK
        if args.select == "promotion":
            ev = _read_json(args.evaluation)
            result = critic_mod.promotion_gate(ev)
            status = "ok" if result["promotion_state"] == "candidate" \
                else "blocked"
            _emit({"command": "v3-critic", "select": "promotion",
                   "status": status, **result})
            return _exit(status)
        if args.select == "validate":
            errors = critic_mod.validate_run(run)
            _emit({"command": "v3-critic", "select": "validate",
                   "status": "ok" if not errors else "blocked",
                   "errors": errors})
            return _exit("ok" if not errors else "blocked")
        _emit({"command": "v3-critic", "status": "failed",
               "error": f"未知 select {args.select}"})
        return config.EXIT_FAILED
    except Exception as exc:
        _emit({"command": "v3-critic", "status": "failed",
               "error": str(exc)})
        return config.EXIT_FAILED


def _read_events(path: str) -> list:
    if path == "-":
        return []
    events = []
    with open(path, "r", encoding=config.ENCODING) as f:
        for line in f:
            line = line.strip()
            if line:
                events.append(json.loads(line))
    return events


def cmd_queue(args) -> int:
    from . import queue as queue_mod
    try:
        events = _read_events(args.events)
        if args.select == "verify":
            errors = queue_mod.verify_chain(events)
            _emit({"command": "v3-queue", "select": "verify",
                   "status": "ok" if not errors else "blocked",
                   "errors": errors, "event_count": len(events)})
            return _exit("ok" if not errors else "blocked")
        if args.select == "summary":
            _emit({"command": "v3-queue", "select": "summary",
                   "status": "ok",
                   **queue_mod.projection_summary(events)})
            return config.EXIT_OK
        if args.select == "current":
            _emit({"command": "v3-queue", "select": "current",
                   "status": "ok", "items": queue_mod.current_queue(events)})
            return config.EXIT_OK
        if args.select == "append":
            ev = queue_mod.make_event(
                events, event=args.event, item_id=args.item_id,
                actor=args.actor, actor_role=args.actor_role,
                reason_code=args.reason_code)
            # stdout = 单行新事件（shell '>>' 追加到 queue-event-ledger.jsonl）
            sys.stdout.write(json.dumps(
                ev, ensure_ascii=config.JSON_ENSURE_ASCII,
                sort_keys=config.JSON_SORT_KEYS) + "\n")
            sys.stdout.flush()
            return config.EXIT_OK
        _emit({"command": "v3-queue", "status": "failed",
               "error": f"未知 select {args.select}"})
        return config.EXIT_FAILED
    except Exception as exc:
        _emit({"command": "v3-queue", "status": "failed", "error": str(exc)})
        return config.EXIT_FAILED


def _read_ledger_entries(path: str) -> list:
    if path == "-":
        return []
    entries = []
    with open(path, "r", encoding=config.ENCODING) as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries


def cmd_ledger(args) -> int:
    from . import ledger as ledger_mod
    try:
        entries = _read_ledger_entries(args.ledger)
        if args.select == "verify":
            errors = ledger_mod.verify_chain(entries)
            errors += ledger_mod.verify_supersedes(entries)
            _emit({"command": "v3-ledger", "select": "verify",
                   "status": "ok" if not errors else "blocked",
                   "errors": errors, "entry_count": len(entries)})
            return _exit("ok" if not errors else "blocked")
        if args.select == "checkpoint":
            ckpt = ledger_mod.make_checkpoint(entries, args.checkpoint_id)
            _emit({"command": "v3-ledger", "select": "checkpoint",
                   "status": "ok", "checkpoint": ckpt})
            return config.EXIT_OK
        if args.select == "verify_checkpoint":
            ckpt = _read_json(args.checkpoint)
            errors = ledger_mod.verify_against_checkpoint(entries, ckpt)
            _emit({"command": "v3-ledger", "select": "verify_checkpoint",
                   "status": "ok" if not errors else "blocked",
                   "errors": errors})
            return _exit("ok" if not errors else "blocked")
        if args.select == "append":
            body = _read_json(args.body)
            new_entries, entry = ledger_mod.append(entries, body)
            # stdout = 单行新 entry（shell '>>' 追加到 decision-ledger.jsonl）
            sys.stdout.write(json.dumps(
                entry, ensure_ascii=config.JSON_ENSURE_ASCII,
                sort_keys=config.JSON_SORT_KEYS) + "\n")
            sys.stdout.flush()
            return config.EXIT_OK
        _emit({"command": "v3-ledger", "status": "failed",
               "error": f"未知 select {args.select}"})
        return config.EXIT_FAILED
    except Exception as exc:
        _emit({"command": "v3-ledger", "status": "failed",
               "error": str(exc)})
        return config.EXIT_FAILED


def cmd_judge(args) -> int:
    from . import judge as judge_mod
    try:
        if args.select == "pre":
            record = judge_mod.build_pre(**_read_json(args.spec))
            evaluation = None
            if args.context:
                evaluation = judge_mod.evaluate_pre(
                    record, _read_json(args.context))
            _emit({"command": "v3-judge", "select": "pre", "status": "ok",
                   "record": record, "evaluation": evaluation,
                   "note": "pre_ok=false 时 Executor 不得启动（§3.2）"})
            return config.EXIT_OK
        if args.select == "post":
            record = judge_mod.build_post(**_read_json(args.spec))
            evaluation = judge_mod.evaluate_post(record)
            _emit({"command": "v3-judge", "select": "post", "status": "ok",
                   "record": record, "evaluation": evaluation})
            return config.EXIT_OK
        if args.select == "facts":
            facts = judge_mod.build_facts(_read_json(args.spec))
            _emit({"command": "v3-judge", "select": "facts", "status": "ok",
                   "facts": facts,
                   "facts_bundle_hash": judge_mod.facts_bundle_hash(facts)})
            return config.EXIT_OK
        if args.select == "adoption":
            spec = _read_json(args.spec)
            errors = judge_mod.adoption_check(
                set(spec.get("pre_sha_set", [])),
                spec.get("post_record", {}))
            _emit({"command": "v3-judge", "select": "adoption",
                   "status": "ok" if not errors else "blocked",
                   "errors": errors})
            return _exit("ok" if not errors else "blocked")
        _emit({"command": "v3-judge", "status": "failed",
               "error": f"未知 select {args.select}"})
        return config.EXIT_FAILED
    except Exception as exc:
        _emit({"command": "v3-judge", "status": "failed",
               "error": str(exc)})
        return config.EXIT_FAILED


def cmd_gate(args) -> int:
    from . import gate as gate_mod
    try:
        spec = _read_json(args.spec)
        record = gate_mod.evaluate_gate(**spec)
        errors = gate_mod.verify_gate_record(record)
        status = "ok" if (record["result"] == "pass" and not errors) else (
            "blocked" if record["result"] == "blocked" else "failed")
        _emit({"command": "v3-gate", "status": status,
               "gate_record": record, "verify_errors": errors,
               "gate_core_hash": gate_mod.gate_core_hash(record)})
        return _exit(status)
    except Exception as exc:
        _emit({"command": "v3-gate", "status": "failed", "error": str(exc)})
        return config.EXIT_FAILED


def cmd_approvals(args) -> int:
    """APPROVALS-1 人工批准登记（disposition 域；stdout canonical JSON）。

    build：从 --root（缺省 cwd，即仓库根）实读 evidence 文件 hash，
    构造六项批准的 dispositions + human disposition ledger + verify +
    checkpoint。批准不改任何机器门裁决（TL-3 fail / TL-4-G blocked /
    TL-2 not reached 保持），evidence 缺失 fail-closed（blocked）。
    """
    from . import approvals as approvals_mod
    try:
        if args.select == "build":
            hashes, errors = approvals_mod.collect_evidence_hashes(
                args.root or ".")
            if errors:
                _emit({"command": "v3-approvals", "select": "build",
                       "status": "blocked", "errors": errors})
                return config.EXIT_BLOCKED
            bundle = approvals_mod.build_approvals_bundle(hashes)
            verify = bundle["ledger_verify"]
            clean = (not verify["chain_errors"]
                     and not verify["supersedes_errors"]
                     and not any(bundle["gate_write_scan"].values()))
            out = dict(bundle)
            out["command"] = "v3-approvals"
            out["select"] = "build"
            out["status"] = "ok" if clean else "failed"
            _emit(out)
            return _exit(out["status"])
        _emit({"command": "v3-approvals", "status": "failed",
               "error": f"未知 select {args.select}"})
        return config.EXIT_FAILED
    except Exception as exc:
        _emit({"command": "v3-approvals", "status": "failed",
               "error": str(exc)})
        return config.EXIT_FAILED


def cmd_archive(args) -> int:
    """S13-ARCHIVE TD7 线收档治理登记（disposition 域；stdout canonical JSON）。

    build：从 --root（缺省 cwd，即仓库根）实读 evidence 文件 hash，构造
    四项收档处置（TD7 线 archived / toolchain_lock 提案 not_adopted /
    D20③ 批门语义+freerouting v2.4.1 调研 closed_by_archive）+ human
    disposition ledger + verify + checkpoint。收档不改任何机器门与冻结
    产物（out/v3-td7|s12 只读），evidence 缺失 fail-closed（blocked）。
    """
    from . import archive as archive_mod
    try:
        if args.select == "build":
            hashes, errors = archive_mod.collect_evidence_hashes(
                args.root or ".")
            if errors:
                _emit({"command": "v3-archive", "select": "build",
                       "status": "blocked", "errors": errors})
                return config.EXIT_BLOCKED
            bundle = archive_mod.build_archive_bundle(hashes)
            verify = bundle["ledger_verify"]
            clean = (not verify["chain_errors"]
                     and not verify["supersedes_errors"]
                     and not any(bundle["gate_write_scan"].values()))
            out = dict(bundle)
            out["command"] = "v3-archive"
            out["select"] = "build"
            out["status"] = "ok" if clean else "failed"
            _emit(out)
            return _exit(out["status"])
        _emit({"command": "v3-archive", "status": "failed",
               "error": f"未知 select {args.select}"})
        return config.EXIT_FAILED
    except Exception as exc:
        _emit({"command": "v3-archive", "status": "failed",
               "error": str(exc)})
        return config.EXIT_FAILED


def cmd_pending(name: str) -> int:
    _emit({"command": f"v3-{name}", "status": "unknown",
           "error": "TL-1/TL-2 模块挂载中（spec=specified；本会话未接线）",
           "command_status": "specified_not_wired"})
    return config.EXIT_NOT_IMPLEMENTED


# ---------------------------------------------------------------------------

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="pcbflow-v3",
        description="pcbflow v3.0 训练环命令面（SPEC-v3.0-PROPOSAL）")
    sub = ap.add_subparsers(dest="command", required=True)

    m = sub.add_parser("manifest", help="TD10 manifest 校验")
    m.add_argument("--manifest", required=True)
    m.add_argument("--profile", default=None)
    m.set_defaults(func=cmd_manifest)

    c = sub.add_parser("context", help="TD10/v2.1 §4.3 ProjectContext")
    c.add_argument("--manifest", required=True)
    c.add_argument("--profile", default=None)
    c.set_defaults(func=cmd_context)

    g = sub.add_parser("graph", help="Artifact Graph 构建与六件套校验")
    g.add_argument("--graph", required=True)
    g.set_defaults(func=cmd_graph)

    l = sub.add_parser("lease", help="单写者 lease / journal（TL-0）")
    l.add_argument("--select", default="status",
                   choices=("acquire", "extend", "release", "status",
                            "verify"))
    l.add_argument("--state", required=True,
                   help="lease 状态 JSON 路径；'-'=空状态（首取）")
    l.add_argument("--scope", default=None)
    l.add_argument("--holder", default=None)
    l.add_argument("--lease-id", default=None)
    l.set_defaults(func=cmd_lease)

    inv = sub.add_parser("inventory", help="TD9 湿区 inventory（只读）")
    inv.add_argument("--roots", default=None,
                     help="逗号分隔扫描根（缺省 out/revc-asm,scripts）")
    inv.set_defaults(func=cmd_inventory)

    ph = sub.add_parser("physics", help="TD6 physics gate 评估 / TL-3 required 链")
    ph.add_argument("--select", default="gate",
                    choices=("gate", "required-chain"),
                    help="gate=对既有 report 评估；required-chain=TL-3 "
                         "required 全链编排（profile→report/coverage→"
                         "judge→ledger→gate-record）")
    ph.add_argument("--report", default=None,
                    help="gate：physics-report JSON 路径")
    ph.add_argument("--required", default=None,
                    help="gate：required item_id 列表 JSON（缺省=report 全部项）")
    ph.add_argument("--profile", default=None,
                    help="required-chain：profile.json 路径")
    ph.add_argument("--evidence", default=None,
                    help="required-chain：physics 证据 bundle JSON 路径")
    ph.add_argument("--snapshot-revision", default="smoke-r1")
    ph.add_argument("--gate-id", default="TL-3-G1")
    ph.set_defaults(func=cmd_physics)

    b = sub.add_parser("backend", help="TD7 外部后端合同")
    b.add_argument("--select", default="capability",
                   choices=("capability", "policy", "assess"))
    b.add_argument("--record", default=None)
    b.add_argument("--declaration", default=None)
    b.add_argument("--stages", default=None)
    b.set_defaults(func=cmd_backend)

    pr = sub.add_parser("proposer", help="TD11/TD3 patch 与 adoption 门")
    pr.add_argument("--select", default="validate",
                    choices=("validate", "evaluate", "adoption",
                             "autotune-chain"))
    pr.add_argument("--patch", default=None)
    pr.add_argument("--allowlist", default=None)
    pr.add_argument("--base", default=None)
    pr.add_argument("--adoption-spec", default=None)
    pr.add_argument("--profile", default=None,
                    help="autotune-chain：profile.json 路径")
    pr.add_argument("--space", default=None,
                    help="autotune-chain：search-space.json 路径")
    pr.add_argument("--baseline", default=None,
                    help="autotune-chain：baseline-config.json 路径")
    pr.add_argument("--snapshot-revision", default="smoke-r1")
    pr.add_argument("--gate-id", default="TL-4-G")
    pr.set_defaults(func=cmd_proposer)

    for name in _PENDING_COMMANDS:  # 当前为空：TL-0..TL-2 全部已接线
        p = sub.add_parser(name, help=f"{name}（挂载中）")
        p.set_defaults(func=lambda a, _n=name: cmd_pending(_n))

    lg = sub.add_parser("ledger", help="TD1 decision-ledger（jsonl hash 链）")
    lg.add_argument("--select", default="verify",
                    choices=("verify", "checkpoint", "verify_checkpoint",
                             "append"))
    lg.add_argument("--ledger", required=True,
                    help="decision-ledger.jsonl 路径；'-'=空账本")
    lg.add_argument("--body", default=None,
                    help="append：entry body JSON（make_entry kwargs）")
    lg.add_argument("--checkpoint-id", default="CKPT-1")
    lg.add_argument("--checkpoint", default=None,
                    help="verify_checkpoint：checkpoint JSON 路径")
    lg.set_defaults(func=cmd_ledger)

    jg = sub.add_parser("judge", help="§1.3 双阶段 Judge")
    jg.add_argument("--select", default="pre",
                    choices=("pre", "post", "facts", "adoption"))
    jg.add_argument("--spec", default=None, help="构造参数 JSON")
    jg.add_argument("--context", default=None,
                    help="pre：上游 hash 对账上下文 JSON")
    jg.set_defaults(func=cmd_judge)

    gt = sub.add_parser("gate", help="§1.4 gate-record 机器谓词评估")
    gt.add_argument("--spec", required=True, help="gate 构造参数 JSON")
    gt.set_defaults(func=cmd_gate)

    cr = sub.add_parser("critic", help="TD4 Critic advisory 分诊")
    cr.add_argument("--select", default="triage",
                    choices=("triage", "promotion", "validate"))
    cr.add_argument("--run", default=None, help="critic_run_record JSON")
    cr.add_argument("--context", default=None,
                    help="TD5 路由上下文 JSON（judge_gate_pass 等四布尔）")
    cr.add_argument("--evaluation", default=None,
                    help="promotion 评估 JSON")
    cr.set_defaults(func=cmd_critic)

    q = sub.add_parser("queue", help="TD5 queue-event-ledger")
    q.add_argument("--select", default="summary",
                   choices=("append", "verify", "summary", "current"))
    q.add_argument("--events", required=True,
                   help="queue-event-ledger.jsonl 路径；'-'=空账本")
    q.add_argument("--event", default=None,
                   choices=("enqueue", "assign", "review", "escalate",
                            "approve", "reject", "downgrade", "expire"))
    q.add_argument("--item-id", default=None)
    q.add_argument("--actor", default=None)
    q.add_argument("--actor-role", default=None)
    q.add_argument("--reason-code", default=None)
    q.set_defaults(func=cmd_queue)

    ap2 = sub.add_parser(
        "approvals", help="APPROVALS-1 人工批准登记（disposition 域）")
    ap2.add_argument("--select", default="build", choices=("build",))
    ap2.add_argument("--root", default=".",
                     help="evidence 根目录（仓库相对路径的基准；缺省 cwd）")
    ap2.set_defaults(func=cmd_approvals)

    arc = sub.add_parser(
        "archive", help="S13-ARCHIVE TD7 线收档治理登记（disposition 域）")
    arc.add_argument("--select", default="build", choices=("build",))
    arc.add_argument("--root", default=".",
                     help="evidence 根目录（仓库相对路径的基准；缺省 cwd）")
    arc.set_defaults(func=cmd_archive)

    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
