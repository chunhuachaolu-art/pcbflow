"""pcbflow.v4_solver_bridge -- V4.0-B 已校验动作 -> 确定性 solver 参数桥。

职责边界（V4 方案 §5/§6/§8 V4.0-B）：
- 只消费 v4_action_validator 产出的 validated_actions（白名单动作），
  绝不直接触碰模型原始输出；
- 只把动作翻译成确定性 solver 参数：route order、corridor 偏好、layer
  偏好、lock 集合；flag_suspect_region / suggest_ripup_reroute /
  rank_candidates 是 advisory，进入 solver_input["advisory"]，不绑定
  求解语义；
- board_write=False 硬编码：本模块不存在任何写板路径；模型输出永远标记
  untrusted，只有 validator 通过的白名单字段进入 solver 参数；
- phase_gate：E0/E1（合成板）直接放行；E2/E3（真实板范围）默认 blocked，
  须用户批准（allow_real_board=True 时也只返回 requires_approval_record，
  不伪造批准记录）。

合并规则（确定性，docstring 钉死）：
- route_order / locked_route_ids：按动作顺序扩展，保留首次出现位置去重；
- corridor / layer 偏好：按 net_id 逐键 last-wins（后面的动作细化前面的），
  输出按 net_id 稳定排序；
- advisory：按 validated 顺序追加。

run record 含 solver_input 更新与动作来源 hash（对被消费的
validated_actions 列表做 canonical sha256；同输入逐字节一致，
无 wall-clock、无绝对路径）。零子进程、零 argv、零网络。
"""

from __future__ import annotations

from . import hashing
from .v4_planner_contract import PLANNER_ACTION_SCHEMA

RUN_RECORD_SCHEMA = "pcbflow.v4.solver-bridge-run/1"

# 硬编码红线：本模块永远不写板、不 commit（§9 默认安全约束）。
BOARD_WRITE = False
LIVE_COMMIT = False

# 进入确定性 solver 参数的动作类型（白名单子集）
SOLVER_PARAM_TYPES = ("set_route_order", "prefer_corridor", "prefer_layer",
                      "lock_route")
# 仅记录为 advisory、不绑定求解语义的动作类型
ADVISORY_TYPES = ("flag_suspect_region", "suggest_ripup_reroute",
                  "rank_candidates")

SYNTHETIC_PHASES = ("E0", "E1")
REAL_BOARD_PHASES = ("E2", "E3")
KNOWN_PHASES = SYNTHETIC_PHASES + REAL_BOARD_PHASES

APPROVAL_RECORD_REQUIRED_FIELDS = (
    "approver", "scope", "board_ids", "approval_record_sha256")


def _scenario_id_of(board):
    if isinstance(board, dict):
        return board.get("scenario_id")
    return getattr(board, "scenario_id", None)


# ---------------------------------------------------------------- 桥接

def apply_actions(validated_actions, board, solver_input):
    """把已校验动作翻译进 solver_input（原地更新）并返回 run record。

    validated_actions 必须是 validator 产出的干净动作列表；board 仅用于
    读取 scenario_id 做记录绑定。返回 dict：
      {schema, scenario_id, board_write, live_commit, input_trust,
       actions_source_schema, actions_source_sha256, applied, solver_input}
    其中 actions_source_sha256 是对被消费的 validated_actions 列表的
    canonical sha256（动作来源 hash，用于下游 hash 链绑定）。
    """
    if not isinstance(solver_input, dict):
        raise ValueError("solver_input 必须是字典")
    validated_actions = list(validated_actions or [])
    applied = {t: 0 for t in SOLVER_PARAM_TYPES}
    advisory = []

    for act in validated_actions:
        if not isinstance(act, dict) or "type" not in act:
            raise ValueError("validated_actions 含非法项（必须来自 validator）")
        atype = act["type"]
        if atype == "set_route_order":
            order = list(solver_input.get("route_order", []))
            for nid in act["order"]:
                if nid not in order:
                    order.append(nid)
            solver_input["route_order"] = order
            applied[atype] += 1
        elif atype == "prefer_corridor":
            prefs = {p["net_id"]: p
                     for p in solver_input.get("corridor_preferences", [])}
            for nid in act["target_net_ids"]:
                entry = {"net_id": nid, "corridor_id": act["corridor_id"]}
                if "preferred_layers" in act:
                    entry["preferred_layers"] = list(act["preferred_layers"])
                prefs[nid] = entry  # last-wins：后到动作细化偏好
            solver_input["corridor_preferences"] = [prefs[k]
                                                    for k in sorted(prefs)]
            applied[atype] += 1
        elif atype == "prefer_layer":
            prefs = {p["net_id"]: p
                     for p in solver_input.get("layer_preferences", [])}
            for nid in act["target_net_ids"]:
                prefs[nid] = {"net_id": nid,
                              "layers": list(act["preferred_layers"])}
            solver_input["layer_preferences"] = [prefs[k]
                                                 for k in sorted(prefs)]
            applied[atype] += 1
        elif atype == "lock_route":
            locked = list(solver_input.get("locked_route_ids", []))
            for rid in act["target_route_ids"]:
                if rid not in locked:
                    locked.append(rid)
            solver_input["locked_route_ids"] = locked
            applied[atype] += 1
        elif atype in ADVISORY_TYPES:
            item = {"action_id": act["action_id"], "type": atype}
            for k in ("reason", "confidence"):
                if k in act:
                    item[k] = act[k]
            for k in ("target_net_ids", "related_net_ids", "region_mm",
                      "candidate_ids"):
                if k in act:
                    item[k] = act[k]
            advisory.append(item)
        else:
            # validator 白名单之外的任何类型到不了这里；到即编程错误。
            raise ValueError("validated_actions 含未知动作类型 %r" % (atype,))
    if advisory:
        solver_input["advisory"] = list(solver_input.get("advisory", [])) \
            + advisory

    source_bytes = hashing.json_dumps(validated_actions)
    return {
        "schema": RUN_RECORD_SCHEMA,
        "scenario_id": _scenario_id_of(board),
        "board_write": BOARD_WRITE,
        "live_commit": LIVE_COMMIT,
        "input_trust": "untrusted_planner_output_validated",
        "actions_source_schema": PLANNER_ACTION_SCHEMA,
        "actions_source_sha256": hashing.sha256_text(source_bytes),
        "applied": {**applied, "advisory": len(advisory)},
        "solver_input": solver_input,
    }


# ---------------------------------------------------------------- 阶段门

def phase_gate(phase, allow_real_board=False):
    """阶段门（§8/§9）：合成板实验直接放行；真实板范围 fail-closed。

    - E0/E1（合成板载体与规划链路）: verdict="allowed"；
    - E2/E3（真实板 staging / paired holdout）:
        allow_real_board=False -> verdict="blocked"（真实板范围须用户批准）；
        allow_real_board=True  -> verdict="requires_approval_record"
        （仍不执行，等待带 sha256 的用户批准记录，本模块不伪造批准）；
    - 未知 phase: verdict="blocked"（fail-closed）。
    """
    phase = str(phase)
    base = {"phase": phase, "allow_real_board": bool(allow_real_board)}
    if phase in SYNTHETIC_PHASES:
        return {**base, "verdict": "allowed",
                "board_scope": "synthetic",
                "reason": "合成板阶段（%s）按方案 §8 直接放行" % phase}
    if phase in REAL_BOARD_PHASES:
        if not allow_real_board:
            return {**base, "verdict": "blocked",
                    "board_scope": "real-board",
                    "reason": "真实板范围须用户批准（%s 默认 fail-closed）"
                              % phase}
        return {**base, "verdict": "requires_approval_record",
                "board_scope": "real-board",
                "reason": "%s 须先落一份含 %s 的用户批准记录；本模块不伪造"
                          % (phase, "/".join(APPROVAL_RECORD_REQUIRED_FIELDS)),
                "approval_record_required_fields":
                    list(APPROVAL_RECORD_REQUIRED_FIELDS)}
    return {**base, "verdict": "blocked", "board_scope": "unknown",
            "reason": "未知 phase %r（允许 %r，fail-closed）"
                      % (phase, KNOWN_PHASES)}
