"""pcbflow.v4_planner_contract -- V4.0-B planner response 合同与 canonical hash。

多模态模型输出的规划响应永远是 untrusted 输入（V4 方案 §5/§6/§9）。本模块
只定义合同的三件事：

1) schema 常量与 action 类型白名单。初版只开放规划动作（方案 §6："初版
   只开放规划动作"，waypoint 未开放）：
   - set_route_order        路由顺序建议（§5.1 route order；可带 target_bus_ids）
   - prefer_corridor        走廊偏好（§6 示例 corridor_id；须在 manifest 注册）
   - prefer_layer           层偏好（§5.1 layer preference）
   - lock_route             建议锁定哪些已存在的 route（§5.1 哪些路线应锁定）
   - flag_suspect_region    疑似拥挤/冲突区域标记（§5.1 疑点发现）
   - suggest_ripup_reroute  局部 rip-up/reroute 建议（§5.1）
   - rank_candidates        候选方案高层排序（§5.1 排序和理由）
   白名单之外任何动作类型一律不得通过 validator（写板、commit、宣布 DRC
   pass、gate pass 等意图在结构上不可能合法）。
2) parse_planner_response：严格 JSON 解析（接受 str 或 dict）；
   schema_version 不符即抛 PlannerContractError，绝不宽容。
3) canonical_planner_response / planner_response_hash：canonical 序列化
   （sort_keys、固定缩进、无 wall-clock、无绝对路径）与 sha256 绑定。
   注意：响应中的 board_snapshot_sha256 / route_manifest_sha256 是被绑定
   身份的一部分（planner 的声明本身是证据），因此 hash 前**不做**
   strip_sha —— 这与重算 board payload hash 的口径（v4exp.model.sha256_of）
   有意不同。

canonical 序列化复用 pcbflow/hashing.py（SPEC §2.2 确定性写出参数）。
零子进程、零 argv、零 wall-clock、零网络；同输入逐字节一致。
"""

from __future__ import annotations

import json

from . import hashing

PLANNER_ACTION_SCHEMA = "v4-planner-action-1"

# 白名单：初版仅规划动作（方案 §5.1/§6；不含任何 waypoint / 写板动作）。
ALLOWED_ACTION_TYPES = (
    "set_route_order",
    "prefer_corridor",
    "prefer_layer",
    "lock_route",
    "flag_suspect_region",
    "suggest_ripup_reroute",
    "rank_candidates",
)

# 明确越权的意图标记：仅用于给出更精确的 blocked reason；
# 无论是否命中标记，白名单外的类型一律 blocked。
FORBIDDEN_INTENT_MARKERS = ("write", "commit", "drc", "gate", "approve",
                            "signoff", "production")

# 根级键白名单（方案 §6 响应结构；白名单外一律 blocked，由 validator 执行）
ROOT_KEYS = ("schema_version", "board_snapshot_sha256",
             "route_manifest_sha256", "actions", "uncertainties")

# 动作级键白名单：公共键 + 各类型专有键（validator 据此拒绝未知键）
COMMON_ACTION_KEYS = ("action_id", "type", "reason", "confidence")
PER_TYPE_KEYS = {
    "set_route_order": ("target_bus_ids", "order"),
    "prefer_corridor": ("target_net_ids", "corridor_id", "preferred_layers"),
    "prefer_layer": ("target_net_ids", "preferred_layers"),
    "lock_route": ("target_route_ids",),
    "flag_suspect_region": ("region_mm", "related_net_ids"),
    "suggest_ripup_reroute": ("target_net_ids",),
    "rank_candidates": ("candidate_ids",),
}
REQUIRED_PER_TYPE_KEYS = {
    "set_route_order": ("order",),
    "prefer_corridor": ("target_net_ids", "corridor_id"),
    "prefer_layer": ("target_net_ids", "preferred_layers"),
    "lock_route": ("target_route_ids",),
    "flag_suspect_region": ("region_mm",),
    "suggest_ripup_reroute": ("target_net_ids",),
    "rank_candidates": ("candidate_ids",),
}


class PlannerContractError(ValueError):
    """planner response 违反合同（非 JSON / 非对象 / schema_version 不符）。"""


def _reject_json_constant(name):
    """json.loads 的 parse_constant 回调：NaN/Infinity/-Infinity 字面量
    直接拒绝（Python json 默认宽容这些非标准常量，必须在入口堵死）。"""
    raise PlannerContractError(
        "planner response 含非 JSON 标准常量 %r（NaN/Infinity 一律拒绝）"
        % (name,))


def parse_planner_response(raw):
    """严格解析 planner 响应；返回 dict。

    - raw 为 dict：校验 schema_version 后原样返回（不做深拷贝、不改写）；
    - raw 为 str：严格 json.loads，NaN/Infinity/-Infinity 字面量在入口
      直接拒绝（parse_constant fail-closed），必须是 JSON 对象；
    - 其余类型、解析失败、非对象、schema_version 缺失或不符：
      抛 PlannerContractError（fail-closed，绝不宽容未知字段结构）。
    """
    if isinstance(raw, dict):
        response = raw
    elif isinstance(raw, str):
        try:
            response = json.loads(raw, parse_constant=_reject_json_constant)
        except PlannerContractError:
            raise
        except (ValueError, TypeError) as exc:
            raise PlannerContractError(
                "planner response 不是合法 JSON: %s" % (exc,)) from exc
    else:
        raise PlannerContractError(
            "planner response 须为 JSON 字符串或对象，收到 %r"
            % (type(raw).__name__,))
    if not isinstance(response, dict):
        raise PlannerContractError(
            "planner response 不是 JSON 对象（收到 %r）"
            % (type(response).__name__,))
    got = response.get("schema_version")
    if got != PLANNER_ACTION_SCHEMA:
        raise PlannerContractError(
            "schema_version 非法: %r（期望 %r）"
            % (got, PLANNER_ACTION_SCHEMA))
    return response


def canonical_planner_response(response) -> str:
    """canonical 序列化：sort_keys + 固定缩进 + ensure_ascii=False。

    无 wall-clock、无绝对路径、稳定排序（§9）。响应里的两个 *_sha256
    声明键是身份的一部分，有意不剔除。
    """
    return hashing.json_dumps(response)


def planner_response_hash(response) -> str:
    """canonical 响应的 sha256，用于把下游产物绑定到确切的那份响应。"""
    return hashing.sha256_text(canonical_planner_response(response))
