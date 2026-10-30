"""pcbflow.v4_experiment -- V4.0-B 薄编排层（phase run + hash 链记录）。

只做编排，不复制实验逻辑：
- 每个 phase 先过 v4_solver_bridge.phase_gate；gate 非 allowed 只落
  blocked / requires_approval_record 记录，绝不执行；
- E0：委托 V4.0-A 载体链（v4exp.model / ref_route / svg_pkg 生成
  manifest + SVG）与一致性核对（v4exp.e0_parse / e0_checks 的 5 项机器
  检查：identity_recovery、manifest_svg_consistency、roundtrip_mm、
  hash_binding、color_independence）。PNG 分辨率检查仍属完整 E0
  （v4exp.run_e0），本层不重复；
- E1：委托 contract -> validator -> bridge 链路
  （v4_planner_contract.parse_planner_response ->
   v4_action_validator.validate_actions -> v4_solver_bridge.apply_actions），
  expected hash 一律由本层从可信管线输入重算（v4exp.model.sha256_of），
  并交叉核对 manifest 自带的 manifest_payload_sha256；
- 每步写 hash 链记录（step -> step_record_sha256 -> prev），链头入
  run record；记录 canonical、无 wall-clock、无主机绝对路径（只存
  scenario_id 与文件基名）。

本模块不裁决策：E2/E3 需要 phase_gate 放行 + 用户批准记录后才可能执行，
而本层当前没有可委托的 E2/E3 实现，gate 放行也只落
requires_approval_record。零子进程、零 argv、零 wall-clock、零网络。
"""

from __future__ import annotations

import os

from . import hashing, v4_action_validator, v4_planner_contract
from . import v4_solver_bridge
from .v4_planner_contract import PlannerContractError
from .v4exp import e0_checks, e0_parse, model, ref_route, svg_pkg

RUN_RECORD_SCHEMA = "pcbflow.v4.phase-run/1"
SUPPORTED_PHASES = ("E0", "E1", "E2", "E3")

E0_CHECK_NAMES = ("identity_recovery", "manifest_svg_consistency",
                  "roundtrip_mm", "hash_binding", "color_independence")

HASH_KEYS = ("board_snapshot_sha256", "route_manifest_sha256")


# ---------------------------------------------------------------- hash 链

class _HashChain:
    """追加式 step 链：每步绑定 payload hash 与前步记录 hash。"""

    def __init__(self):
        self.steps = []
        self._prev = None

    def add(self, board, name, payload_sha256, detail=None):
        body = {"step": len(self.steps) + 1, "board": str(board),
                "name": name, "payload_sha256": str(payload_sha256),
                "prev_step_sha256": self._prev}
        if detail is not None:
            body["detail"] = detail
        step = dict(body)
        step["step_record_sha256"] = hashing.sha256_text(
            hashing.json_dumps(body))
        self._prev = step["step_record_sha256"]
        self.steps.append(step)
        return step

    @property
    def head(self):
        return self.steps[-1]["step_record_sha256"] if self.steps else None


def _write_record(out_dir, phase, record):
    path = os.path.join(out_dir,
                        "v4-phase-%s-run-record.json" % phase.lower())
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, "wb") as f:
        f.write(hashing.canonical_json_bytes(record))
    return os.path.basename(path)


def _new_record(phase, gate):
    return {"schema": RUN_RECORD_SCHEMA, "phase": phase, "gate": gate,
            "board_count": 0, "boards": [], "steps": [],
            "chain_head_sha256": None, "verdict": gate["verdict"]}


# ---------------------------------------------------------------- E0

def _run_e0_board(board_path, out_dir, chain):
    """V4.0-A 载体生成 + 一致性校验（全部委托 v4exp，本层只编排）。"""
    name = os.path.basename(board_path)
    board_obj = model.read_json(board_path)
    board = model.board_from_obj(board_obj)
    sid = board.scenario_id
    ref = ref_route.route_board(board)
    manifest, svg_text = svg_pkg.build(board, ref)

    mpath = os.path.join(out_dir, "route-manifest-%s.json" % sid)
    spath = os.path.join(out_dir, "route-preview-%s.svg" % sid)
    model.write_json(mpath, manifest)
    with open(spath, "w", encoding="utf-8", newline="\n") as f:
        f.write(svg_text)
    chain.add(sid, "e0.carrier.manifest", hashing.sha256_file(mpath),
              detail=os.path.basename(mpath))
    chain.add(sid, "e0.carrier.svg", hashing.sha256_file(spath),
              detail=os.path.basename(spath))

    facts, reason = e0_parse.try_parse_svg(svg_text)
    bbox = board_obj["board"]["bbox_mm"]
    checks = {}
    if facts is None:
        checks = {c: e0_checks.result(c, False, "SVG 严格解析失败: %s"
                                      % reason) for c in E0_CHECK_NAMES}
    else:
        for c in (e0_checks.identity_recovery(facts, manifest),
                  e0_checks.manifest_svg_consistency(facts, manifest, bbox),
                  e0_checks.roundtrip_mm(facts, manifest, bbox),
                  e0_checks.hash_binding(facts, manifest, board_obj),
                  e0_checks.color_independence(svg_text, facts)):
            checks[c["check"]] = c
    chain.add(sid, "e0.consistency", hashing.sha256_text(
        hashing.json_dumps(checks)),
        detail="; ".join("%s=%s" % (c, checks[c]["pass"])
                         for c in E0_CHECK_NAMES))
    ok = all(checks[c]["pass"] for c in E0_CHECK_NAMES)
    return {"scenario_id": sid, "board_file": name,
            "manifest_file": os.path.basename(mpath),
            "svg_file": os.path.basename(spath),
            "checks": checks, "pass": ok}


# ---------------------------------------------------------------- E1

def _load_responses(board_paths, kwargs):
    """responses 优先（dict sid->raw），否则从 response_dir 读文件。"""
    responses = kwargs.get("responses")
    if isinstance(responses, dict):
        return {str(k): v for k, v in responses.items()}, None
    response_dir = kwargs.get("response_dir")
    if not response_dir:
        return {}, ("kwargs 缺少 responses / response_dir"
                    "（E1 需要 planner 响应输入）")
    out = {}
    for p in board_paths:
        board_obj = model.read_json(p)
        sid = str(board_obj["scenario_id"])
        rpath = os.path.join(response_dir, "planner-response-%s.json" % sid)
        if not os.path.exists(rpath):
            out[sid] = None
        else:
            out[sid] = model.read_json(rpath)
    return out, None


def _run_e1_board(board_path, manifest_dir, response_raw, base_solver_input,
                  chain):
    """contract -> validator -> bridge 链路（单板）。期望 hash 全部重算。"""
    name = os.path.basename(board_path)
    board_obj = model.read_json(board_path)
    sid = str(board_obj["scenario_id"])
    mpath = os.path.join(manifest_dir, "route-manifest-%s.json" % sid)
    if not os.path.exists(mpath):
        chain.add(sid, "e1.blocked", hashing.sha256_text(
            "manifest 缺失: %s" % os.path.basename(mpath)),
            detail="route-manifest 文件缺失（E0 载体未生成？）")
        return {"scenario_id": sid, "board_file": name,
                "verdict": "blocked",
                "reasons": ["route-manifest-%s.json 缺失（先跑 E0 载体生成）"
                            % sid]}
    manifest = model.read_json(mpath)

    expected_board_sha = model.sha256_of(board_obj)
    expected_manifest_sha = model.sha256_of(manifest)
    recorded = manifest.get("manifest_payload_sha256")
    if recorded is not None and recorded != expected_manifest_sha:
        chain.add(sid, "e1.blocked", hashing.sha256_text(
            hashing.json_dumps({"board": sid, "why": "manifest 自身 hash"
                                " 与重算值不一致"})),
            detail="manifest 载体被改动（stale carrier）")
        return {"scenario_id": sid, "board_file": name,
                "verdict": "blocked",
                "reasons": ["manifest_payload_sha256 与重算值不一致"
                            "（stale carrier）"]}

    if response_raw is None:
        chain.add(sid, "e1.blocked", hashing.sha256_text(
            hashing.json_dumps({"board": sid, "why": "planner response"
                                " 缺失"})), detail="UNKNOWN 必须可见")
        return {"scenario_id": sid, "board_file": name,
                "verdict": "blocked",
                "reasons": ["planner response 缺失（UNKNOWN 可见，"
                            "不静默跳过）"]}

    try:
        response = v4_planner_contract.parse_planner_response(response_raw)
    except PlannerContractError as exc:
        chain.add(sid, "e1.parse", hashing.sha256_text(str(exc)),
                  detail="PlannerContractError")
        return {"scenario_id": sid, "board_file": name,
                "verdict": "blocked", "reasons": [str(exc)]}
    chain.add(sid, "e1.parse",
              v4_planner_contract.planner_response_hash(response),
              detail="schema_version=%r"
                     % (response.get("schema_version"),))

    verdict, reasons, validated = v4_action_validator.validate_actions(
        response, board_obj, manifest,
        {"board_snapshot_sha256": expected_board_sha,
         "route_manifest_sha256": expected_manifest_sha})
    chain.add(sid, "e1.validate",
              hashing.sha256_text(hashing.json_dumps(
                  {"verdict": verdict, "reasons": reasons,
                   "validated": validated})),
              detail={"verdict": verdict, "reason_count": len(reasons),
                      "validated_count": len(validated)})
    if verdict != v4_action_validator.VERDICT_ACCEPTED:
        return {"scenario_id": sid, "board_file": name,
                "verdict": "blocked", "reasons": reasons}

    run_record = v4_solver_bridge.apply_actions(
        validated, board_obj, dict(base_solver_input))
    chain.add(sid, "e1.bridge", run_record["actions_source_sha256"],
              detail={"applied": run_record["applied"],
                      "board_write": run_record["board_write"]})
    return {"scenario_id": sid, "board_file": name, "verdict": "accepted",
            "reasons": [], "solver_run": run_record,
            "solver_input": run_record["solver_input"]}


# ---------------------------------------------------------------- 入口

def run_phase(phase, board_paths, out_dir, **kwargs):
    """薄编排入口：gate -> (E0|E1 链路) -> hash 链 run record 落盘。

    kwargs:
      allow_real_board (bool, 默认 False)   传给 phase_gate；
      responses (dict sid->str|dict)        E1 planner 响应；
      response_dir (str)                    E1 备选：planner-response-*.json；
      manifest_dir (str, 默认 out_dir)      E1 载体 manifest 目录；
      solver_input (dict)                   E1 bridge 基础 solver 参数。
    返回 run record dict；同时写
    <out_dir>/v4-phase-<phase>-run-record.json（canonical、LF、无时间戳）。
    """
    phase = str(phase)
    if phase not in SUPPORTED_PHASES:
        gate = v4_solver_bridge.phase_gate(phase, False)
    else:
        gate = v4_solver_bridge.phase_gate(
            phase, bool(kwargs.get("allow_real_board", False)))
    if isinstance(board_paths, str):
        board_paths = [board_paths]
    board_paths = list(board_paths or [])
    record = _new_record(phase, gate)

    if gate["verdict"] != "allowed":
        # blocked / requires_approval_record：只落记录，绝不执行。
        record["chain_head_sha256"] = None
        record["record_file"] = _write_record(out_dir, phase, record)
        return record

    if phase == "E0":
        os.makedirs(out_dir, exist_ok=True)
        chain = _HashChain()
        for p in board_paths:
            try:
                entry = _run_e0_board(p, out_dir, chain)
            except (ValueError, KeyError, OSError) as exc:
                entry = {"board_file": os.path.basename(p),
                         "verdict": "blocked",
                         "reasons": ["载体生成失败: %s" % exc]}
                chain.add("-", "e0.error", hashing.sha256_text(str(exc)))
            record["boards"].append(entry)
    elif phase == "E1":
        chain = _HashChain()
        responses, err = _load_responses(board_paths, kwargs)
        if err is not None:
            record["verdict"] = "blocked"
            record["reasons"] = [err]
            record["record_file"] = _write_record(out_dir, phase, record)
            return record
        manifest_dir = kwargs.get("manifest_dir") or out_dir
        base_solver_input = dict(kwargs.get("solver_input") or {})
        for p in board_paths:
            board_obj = model.read_json(p)
            sid = str(board_obj["scenario_id"])
            entry = _run_e1_board(p, manifest_dir, responses.get(sid),
                                  base_solver_input, chain)
            if "verdict" not in entry:
                entry["verdict"] = "blocked"
                entry["reasons"] = ["入口异常（fail-closed）"]
            record["boards"].append(entry)
    else:
        # E2/E3 当前无可委托实现；gate 已放行也只落待批准记录。
        chain = _HashChain()
        chain.add("-", "phase.not_implemented", hashing.sha256_text(
            hashing.json_dumps({"phase": phase})),
            detail="无 E2/E3 委托实现（不伪造执行）")
        record["verdict"] = "requires_approval_record"

    record["board_count"] = len(record["boards"])
    record["steps"] = chain.steps
    record["chain_head_sha256"] = chain.head
    if record["verdict"] == "allowed":
        bad = [b for b in record["boards"]
               if isinstance(b, dict) and b.get("pass") is False] \
            if phase == "E0" \
            else [b for b in record["boards"]
                  if isinstance(b, dict) and b.get("verdict") != "accepted"]
        record["verdict"] = "failed" if bad else "complete"
    record["record_file"] = _write_record(out_dir, phase, record)
    return record
