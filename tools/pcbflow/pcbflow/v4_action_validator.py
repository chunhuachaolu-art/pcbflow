"""pcbflow.v4_action_validator -- V4.0-B planner action 失败关闭校验器。

校验模式与风格复用 pcbflow/v4exp/actions.py 的 validate_response（E1 实验
80/80 负向全拦截的同一套口径），面向 V4 方案 §6 合同 + §9 安全约束：

* verdict 只有 "accepted" / "blocked" 两值；
* 失败关闭 —— 以下任一即整份 blocked（validated_actions 返回空列表，
  从结构上不给下游任何可消费物）：
  - response 不是 JSON 对象；
  - 根级出现白名单外未知键（杜绝夹带写板几何/指令）；
  - schema_version 不是 "v4-planner-action-1"；
  - board_snapshot_sha256 / route_manifest_sha256 缺失、非字符串，或与
    expected_hashes 不一致（stale hash）；
  - expected_hashes 本身缺键（无法验证即视为失败，绝不放行）；
  - actions 缺失或不是列表；uncertainties 不是字符串列表；
  - 任何 action：未知键、type 不在白名单（越权动作类型 —— 写板、commit、
    宣布 DRC pass、gate pass 等意图在白名单外，一律 blocked）、action_id
    缺失/重复/非字符串、字段类型非法、引用不存在的 route_id/net_id/
    bus_id/corridor_id/layer、region_mm 出板 bbox、confidence 出 [0,1]。
* validator 决不改写 planner 语义：通过校验的字段原样透传（顺序、坐标、
  层序都不重排）；validated_actions 只保留通过白名单校验的动作并附
  reason 透传。

registry 口径（全部来自可信管线输入，不来自模型）：
- net_ids     <- board["nets"][*]["net_id"]
- route_ids   <- manifest["routes"][*]["route_id"]
- bus_ids     <- board/manifest 中 relation_type=="bus" 的 relation_id
- corridor_ids<- manifest.get("corridors")（未注册即空集 => 任何 corridor
  引用都 blocked，registry 默认拒绝）
- layers      <- board["board"]["layers"]

零子进程、零 argv、零 wall-clock、零网络；同输入同结果。
"""

from __future__ import annotations

import math

from . import v4_planner_contract as contract
from .v4_planner_contract import (
    ALLOWED_ACTION_TYPES,
    COMMON_ACTION_KEYS,
    FORBIDDEN_INTENT_MARKERS,
    PER_TYPE_KEYS,
    PLANNER_ACTION_SCHEMA,
    REQUIRED_PER_TYPE_KEYS,
    ROOT_KEYS,
)

VERDICT_ACCEPTED = "accepted"
VERDICT_BLOCKED = "blocked"

EXPECTED_HASH_KEYS = ("board_snapshot_sha256", "route_manifest_sha256")


# ---------------------------------------------------------------- 基础判定

def _is_num(v):
    # 仅接受有限数值：NaN/Inf 会让链式比较全为 False，从而绕过边界检查，
    # 必须在此 fail-closed 拒绝。
    return isinstance(v, (int, float)) and not isinstance(v, bool) \
        and math.isfinite(float(v))


def _is_str_list(v):
    return isinstance(v, list) and all(isinstance(s, str) for s in v)


def _is_unique_str_list(v):
    return _is_str_list(v) and len(set(v)) == len(v)


def _registries(board, manifest):
    """从可信管线输入收集 id/层 registry；模型引用一律对这些判定。"""
    net_ids = {str(n["net_id"]) for n in board.get("nets", [])
               if isinstance(n, dict) and "net_id" in n}
    route_ids = {str(r["route_id"]) for r in manifest.get("routes", [])
                 if isinstance(r, dict) and "route_id" in r}
    bus_ids = set()
    for rel in (list(board.get("relations", []))
                + list(manifest.get("relations", []))):
        if isinstance(rel, dict) and rel.get("relation_type") == "bus" \
                and isinstance(rel.get("relation_id"), str):
            bus_ids.add(rel["relation_id"])
    corridor_ids = {str(c["corridor_id"]) for c in manifest.get("corridors", [])
                    if isinstance(c, dict) and "corridor_id" in c}
    board_obj = board.get("board", {})
    layers = {str(s) for s in board_obj.get("layers", [])
              if isinstance(s, str)}
    bbox = board_obj.get("bbox_mm")
    if (isinstance(bbox, list) and len(bbox) == 4
            and all(_is_num(v) for v in bbox)):
        bbox = [float(v) for v in bbox]
    else:
        bbox = None
    return {"net_ids": net_ids, "route_ids": route_ids, "bus_ids": bus_ids,
            "corridor_ids": corridor_ids, "layers": layers, "bbox": bbox}


def _known_refs(items, reg_key, regs):
    """返回 (是否全部已知, 首个未知项)。"""
    known = regs[reg_key]
    for item in items:
        if item not in known:
            return False, item
    return True, None


# ---------------------------------------------------------------- 动作校验

def _check_action(act, idx, regs, seen_action_ids):
    """校验单个 action；返回 (cleaned_action 或 None, reason 或 None)。"""
    label = "actions[%d]" % idx
    if not isinstance(act, dict):
        return None, "%s: 不是对象" % label
    atype = act.get("type")
    if atype not in ALLOWED_ACTION_TYPES:
        hit = any(m in str(atype) for m in FORBIDDEN_INTENT_MARKERS)
        if hit:
            return None, ("%s: 越权动作类型 %r（写板/commit/宣布 pass 类意图"
                          " 不在规划白名单，一律 blocked）" % (label, atype))
        return None, "%s: 非白名单动作类型 %r" % (label, atype)
    allowed_keys = COMMON_ACTION_KEYS + PER_TYPE_KEYS[atype]
    for k in act:
        if k not in allowed_keys:
            return None, "%s: 未知键 %r（白名单外一律 blocked）" % (label, k)
    aid = act.get("action_id")
    if not isinstance(aid, str) or not aid:
        return None, "%s: action_id 缺失或非字符串" % label
    if aid in seen_action_ids:
        return None, "%s: action_id 重复 %r" % (label, aid)
    seen_action_ids.add(aid)
    label = "actions[%s]" % aid
    reason = act.get("reason")
    if reason is not None and not isinstance(reason, str):
        return None, "%s: reason 必须是字符串" % label
    confidence = act.get("confidence")
    if confidence is not None \
            and (not _is_num(confidence) or not 0.0 <= float(confidence) <= 1.0):
        return None, "%s: confidence 必须是 [0,1] 内数值" % label

    for key in REQUIRED_PER_TYPE_KEYS[atype]:
        if act.get(key) is None:
            return None, "%s: %s 缺失（type=%s 必填）" % (label, key, atype)

    cleaned = {"action_id": aid, "type": atype}
    if reason is not None:
        cleaned["reason"] = reason  # reason 透传
    if confidence is not None:
        cleaned["confidence"] = confidence

    if atype == "set_route_order":
        order = act["order"]
        if not _is_unique_str_list(order) or not order:
            return None, ("%s: order 必须是非空、无重复的 net_id 字符串列表"
                          % label)
        ok, bad = _known_refs(order, "net_ids", regs)
        if not ok:
            return None, "%s: order 引用不存在的 net_id %r" % (label, bad)
        bus_ids = act.get("target_bus_ids")
        if bus_ids is not None:
            if not _is_unique_str_list(bus_ids):
                return None, "%s: target_bus_ids 结构畸形" % label
            ok, bad = _known_refs(bus_ids, "bus_ids", regs)
            if not ok:
                return None, ("%s: target_bus_ids 引用不存在的 bus_id %r"
                              % (label, bad))
            cleaned["target_bus_ids"] = list(bus_ids)
        cleaned["order"] = list(order)

    elif atype == "prefer_corridor":
        nets = act["target_net_ids"]
        if not _is_unique_str_list(nets) or not nets:
            return None, "%s: target_net_ids 结构畸形" % label
        ok, bad = _known_refs(nets, "net_ids", regs)
        if not ok:
            return None, "%s: target_net_ids 引用不存在的 net_id %r" \
                % (label, bad)
        corridor_id = act["corridor_id"]
        if not isinstance(corridor_id, str):
            return None, "%s: corridor_id 必须是字符串" % label
        if corridor_id not in regs["corridor_ids"]:
            return None, ("%s: corridor_id %r 未在 manifest corridors 注册"
                          "（registry 默认拒绝）" % (label, corridor_id))
        layers = act.get("preferred_layers")
        if layers is not None:
            if not _is_unique_str_list(layers):
                return None, "%s: preferred_layers 结构畸形" % label
            ok, bad = _known_refs(layers, "layers", regs)
            if not ok:
                return None, "%s: preferred_layers 引用不存在的层 %r" \
                    % (label, bad)
            cleaned["preferred_layers"] = list(layers)
        cleaned["target_net_ids"] = list(nets)
        cleaned["corridor_id"] = corridor_id

    elif atype == "prefer_layer":
        nets = act["target_net_ids"]
        if not _is_unique_str_list(nets) or not nets:
            return None, "%s: target_net_ids 结构畸形" % label
        ok, bad = _known_refs(nets, "net_ids", regs)
        if not ok:
            return None, "%s: target_net_ids 引用不存在的 net_id %r" \
                % (label, bad)
        layers = act["preferred_layers"]
        if not _is_unique_str_list(layers) or not layers:
            return None, "%s: preferred_layers 必须是非空、无重复层列表" % label
        ok, bad = _known_refs(layers, "layers", regs)
        if not ok:
            return None, "%s: preferred_layers 引用不存在的层 %r" \
                % (label, bad)
        cleaned["target_net_ids"] = list(nets)
        cleaned["preferred_layers"] = list(layers)

    elif atype == "lock_route":
        rids = act["target_route_ids"]
        if not _is_unique_str_list(rids) or not rids:
            return None, "%s: target_route_ids 结构畸形" % label
        ok, bad = _known_refs(rids, "route_ids", regs)
        if not ok:
            return None, "%s: target_route_ids 引用不存在的 route_id %r" \
                % (label, bad)
        cleaned["target_route_ids"] = list(rids)

    elif atype == "flag_suspect_region":
        region = act["region_mm"]
        if not isinstance(region, list) or len(region) != 4 \
                or not all(_is_num(v) for v in region):
            return None, "%s: region_mm 必须是 [x0,y0,x1,y1] 数值列表" % label
        region = [float(v) for v in region]
        bbox = regs["bbox"]
        if bbox is None:
            return None, "%s: board bbox 缺失，无法验证区域（fail-closed）" \
                % label
        if region[0] >= region[2] or region[1] >= region[3]:
            return None, "%s: region_mm 需 x0<x1 且 y0<y1" % label
        if (region[0] < bbox[0] or region[1] < bbox[1]
                or region[2] > bbox[2] or region[3] > bbox[3]):
            return None, "%s: region_mm 超出板 bbox" % label
        cleaned["region_mm"] = region
        related = act.get("related_net_ids")
        if related is not None:
            if not _is_unique_str_list(related):
                return None, "%s: related_net_ids 结构畸形" % label
            ok, bad = _known_refs(related, "net_ids", regs)
            if not ok:
                return None, ("%s: related_net_ids 引用不存在的 net_id %r"
                              % (label, bad))
            cleaned["related_net_ids"] = list(related)

    elif atype == "suggest_ripup_reroute":
        nets = act["target_net_ids"]
        if not _is_unique_str_list(nets) or not nets:
            return None, "%s: target_net_ids 结构畸形" % label
        ok, bad = _known_refs(nets, "net_ids", regs)
        if not ok:
            return None, "%s: target_net_ids 引用不存在的 net_id %r" \
                % (label, bad)
        cleaned["target_net_ids"] = list(nets)

    elif atype == "rank_candidates":
        cands = act["candidate_ids"]
        # 规划时点尚无 candidate registry：只做类型/非空/唯一性硬校验。
        if not _is_unique_str_list(cands) or not cands:
            return None, ("%s: candidate_ids 必须是非空、无重复的字符串列表"
                          % label)
        cleaned["candidate_ids"] = list(cands)

    return cleaned, None


# ---------------------------------------------------------------- 主校验

def validate_actions(response, board, manifest, expected_hashes):
    """校验一份（已解析的）planner 响应。

    返回 (verdict, reasons, validated_actions)：
    - verdict: "accepted" | "blocked"；
    - reasons: 全部失败原因（evidence 完整收集，逐动作独立）；
    - validated_actions: 仅 accepted 时保留通过白名单校验的干净动作
      （reason 等字段原样透传）；blocked 时恒为 []。
    """
    reasons = []

    if not isinstance(response, dict):
        return VERDICT_BLOCKED, ["response 不是 JSON 对象"], []
    for k in response:
        if k not in ROOT_KEYS:
            reasons.append("根级未知键 %r（白名单外一律 blocked）" % (k,))
    if response.get("schema_version") != PLANNER_ACTION_SCHEMA:
        reasons.append("schema_version 非法: %r（期望 %r）"
                       % (response.get("schema_version"),
                          PLANNER_ACTION_SCHEMA))
    if not isinstance(expected_hashes, dict):
        reasons.append("expected_hashes 不是字典（无法验证，fail-closed）")
        expected_hashes = {}
    for key in EXPECTED_HASH_KEYS:
        expected = expected_hashes.get(key)
        if not isinstance(expected, str) or not expected:
            reasons.append("expected_hashes.%s 缺失（无法验证即 blocked）"
                           % key)
            continue
        claim = response.get(key)
        if not isinstance(claim, str):
            reasons.append("%s 缺失或非字符串" % key)
        elif claim != expected:
            reasons.append("%s 与 expected 不一致（stale/错误 hash）" % key)

    actions = response.get("actions")
    if not isinstance(actions, list):
        reasons.append("actions 缺失或不是列表")
        actions = []
    uncertainties = response.get("uncertainties")
    if uncertainties is not None and not _is_str_list(uncertainties):
        reasons.append("uncertainties 必须是字符串列表")

    # 全局项任一违例 => 整份 blocked，不再逐动作消耗证据。
    if reasons:
        return VERDICT_BLOCKED, reasons, []

    regs = _registries(board, manifest)
    validated = []
    seen_action_ids = set()
    for i, act in enumerate(actions):
        cleaned, reason = _check_action(act, i, regs, seen_action_ids)
        if reason is not None:
            reasons.append(reason)
        elif cleaned is not None:
            validated.append(cleaned)

    if reasons:
        return VERDICT_BLOCKED, reasons, []
    return VERDICT_ACCEPTED, [], validated
