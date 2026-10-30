"""pcbflow.v4exp.actions -- planner-response contract + fail-closed validator.

E1 的 untrusted 边界：planner response 永远是 untrusted 输入。本模块把一份
response 对照板快照做全量校验，产出 solver 可安全消费的 validated-actions
JSON；solver 只允许消费 validated-actions。

失败语义（合同钉死）：
* 全局项任一违例 => 整份响应 blocked（accepted=null）：
  - schema 串不是 "pcbflow.v4exp.planner-response/1"；
  - scenario_id 与板不一致；
  - board_snapshot_sha256 缺失 / 非字符串 / 与 model.sha256_of(board) 重算值
    不一致（stale hash）；
  - group 缺失 / 不在 {"B","C","D"} / 与期望组不一致；
  - actions 缺失或不是对象；
  - route_order 缺失 / 为空 / 含未知 net / 含重复 net / 不是全部 net 的
    完整排列（router 要求恰好每个 net 一次，缺 net 同样无法求解）；
  - protect 含未知 net；
  - 根级 / actions 级 / 动作对象内部出现任何未知键（白名单之外即 blocked，
    从结构上杜绝"响应里夹带写板几何/指令"；唯一允许出现的几何坐标是
    corridor_preferences 的 waypoints_mm）；
  - 已知键的结构性类型错误（如 route_order 不是字符串列表、notes 不是字符串）。
* 逐项可拒绝（只剔除该项并记 rejection，不整体 blocked）：
  - corridor 项：net 未知 / waypoints_mm 多于 3 个 / waypoint 出板 bbox /
    waypoint 落 keepout（按该 net 允许层与 keepout 层的交集判定）/
    waypoints_mm 结构畸形 / 重复的 net 项；
  - layer_preferences 项：net 未知 / 层不在 rules.allowed_layers[net_class] /
    layers 结构畸形 / 重复的 net 项；
  - uncertainty 不在 {"low","medium","high"} 枚举内。

validator 决不改写 planner 语义：接受的 corridor waypoint 坐标原样透传
（格点吸附是 router 的事），route_order 原样透传，protect 原样透传。

CLI（stdin JSON -> stdout；无 argv）：{"planner_response_path", "board_path",
"expected_group", "out_path"}；校验结果写 out_path（可选）并打印到 stdout。

零子进程、零 argv、零 wall-clock、零网络；同输入产出逐字节一致。
"""

from __future__ import annotations

from pcbflow.v4exp import model

RESPONSE_SCHEMA = "pcbflow.v4exp.planner-response/1"
VALIDATED_SCHEMA = "pcbflow.v4exp.validated-actions/1"

GROUPS = ("B", "C", "D")
UNCERTAINTY_LEVELS = ("low", "medium", "high")
MAX_WAYPOINTS = 3

ROOT_KEYS = ("schema", "scenario_id", "board_snapshot_sha256", "group",
             "actions")
ACTIONS_KEYS = ("route_order", "corridor_preferences", "layer_preferences",
                "protect", "notes", "uncertainty")
CORRIDOR_KEYS = ("net_id", "waypoints_mm")
LAYERPREF_KEYS = ("net_id", "layers")


# ---------------------------------------------------------------- 基础判定

def _is_num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _is_str_list(v):
    return isinstance(v, list) and all(isinstance(s, str) for s in v)


def _net_ids_of(board):
    return [str(n["net_id"]) for n in board["nets"]]


def _net_class_of(board, net_id):
    for n in board["nets"]:
        if str(n["net_id"]) == net_id:
            return str(n["net_class"])
    return None


def _net_allowed_layers(board, net_class):
    """与 grid.GridWorld.net_allowed_layer_indices 相同的回退链。"""
    allowed = board["rules"].get("allowed_layers", {})
    names = allowed.get(net_class) or allowed.get("default") \
        or board["board"]["layers"]
    layer_set = set(board["board"]["layers"])
    return [str(s) for s in names if str(s) in layer_set]


def _waypoint_keepout_hit(board, x, y, allowed_layer_names):
    """waypoint (x, y) 是否落在对该 net 生效的 keepout 内（按层判）。"""
    allowed = set(allowed_layer_names)
    for ko in board.get("keepouts", []):
        rect = [float(v) for v in ko["rect_mm"]]
        if not (rect[0] <= x <= rect[2] and rect[1] <= y <= rect[3]):
            continue
        if any(str(l) in allowed for l in ko.get("layers", [])):
            return True
    return False


def _blocked(sid, group, reason):
    return {"schema": VALIDATED_SCHEMA, "scenario_id": sid, "group": group,
            "blocked": True, "reason": reason, "rejections": [],
            "accepted": None}


# ---------------------------------------------------------------- 主校验

def validate_response(response, board, expected_group):
    """校验一份 planner response；返回 validated-actions 字典（不落盘）。"""
    sid = str(board["scenario_id"])

    if not isinstance(response, dict):
        return _blocked(sid, expected_group, "response 不是 JSON 对象")
    for k in response:
        if k not in ROOT_KEYS:
            return _blocked(sid, expected_group,
                            "根级未知键 %r（白名单外一律 blocked）" % (k,))
    if response.get("schema") != RESPONSE_SCHEMA:
        return _blocked(sid, expected_group,
                        "schema 非法: %r" % (response.get("schema"),))
    group = response.get("group")
    if group not in GROUPS:
        return _blocked(sid, expected_group,
                        "group 非法: %r（须为 B|C|D）" % (group,))
    if group != expected_group:
        return _blocked(sid, expected_group,
                        "group %r 与期望组 %r 不一致" % (group, expected_group))
    if response.get("scenario_id") != sid:
        return _blocked(sid, group,
                        "scenario_id %r 与板 %r 不一致"
                        % (response.get("scenario_id"), sid))
    got_hash = response.get("board_snapshot_sha256")
    if not isinstance(got_hash, str):
        return _blocked(sid, group, "board_snapshot_sha256 缺失或非字符串")
    want_hash = model.sha256_of(board)
    if got_hash != want_hash:
        return _blocked(sid, group,
                        "board_snapshot_sha256 与重算值不一致（stale/错误 hash）")

    actions = response.get("actions")
    if not isinstance(actions, dict):
        return _blocked(sid, group, "actions 缺失或不是对象")
    for k in actions:
        if k not in ACTIONS_KEYS:
            return _blocked(sid, group,
                            "actions 未知键 %r（白名单外一律 blocked）" % (k,))

    net_ids = _net_ids_of(board)
    net_set = set(net_ids)

    # ---- route_order：必需，完整排列，无未知无重复 ----
    order = actions.get("route_order")
    if not _is_str_list(order) or not order:
        return _blocked(sid, group,
                        "route_order 缺失、为空或不是 net_id 字符串列表")
    seen = set()
    for nid in order:
        if nid not in net_set:
            return _blocked(sid, group, "route_order 含未知 net %r" % (nid,))
        if nid in seen:
            return _blocked(sid, group, "route_order 含重复 net %r" % (nid,))
        seen.add(nid)
    if len(order) != len(net_ids):
        missing = sorted(net_set - seen)
        return _blocked(sid, group,
                        "route_order 不是全部 net 的完整排列（缺 %r）"
                        % (missing,))

    # ---- protect：可选，未知 net 即 blocked ----
    protect = actions.get("protect", [])
    if protect is None:
        protect = []
    if not _is_str_list(protect):
        return _blocked(sid, group, "protect 必须是 net_id 字符串列表")
    for nid in protect:
        if nid not in net_set:
            return _blocked(sid, group, "protect 含未知 net %r" % (nid,))

    # ---- notes / uncertainty ----
    notes = actions.get("notes", "")
    if notes is None:
        notes = ""
    if not isinstance(notes, str):
        return _blocked(sid, group, "notes 必须是字符串")
    uncertainty = actions.get("uncertainty")
    rejections = []
    if uncertainty is not None and uncertainty not in UNCERTAINTY_LEVELS:
        rejections.append({
            "item": "uncertainty",
            "reason": "非枚举值 %r（允许 low|medium|high）" % (uncertainty,),
        })

    # ---- corridor_preferences：逐项可拒绝，坐标原样透传 ----
    corridors_in = actions.get("corridor_preferences", [])
    if corridors_in is None:
        corridors_in = []
    if not isinstance(corridors_in, list):
        return _blocked(sid, group, "corridor_preferences 必须是列表")
    bbox = [float(v) for v in board["board"]["bbox_mm"]]
    corridors_out = []
    corridor_nets = set()
    for i, item in enumerate(corridors_in):
        label = "corridor_preferences[%d]" % i
        if not isinstance(item, dict):
            rejections.append({"item": label, "reason": "项不是对象"})
            continue
        for k in item:
            if k not in CORRIDOR_KEYS:
                return _blocked(sid, group,
                                "%s 未知键 %r" % (label, k))
        nid = item.get("net_id")
        if not isinstance(nid, str):
            rejections.append({"item": label, "reason": "net_id 缺失或非字符串"})
            continue
        label = "corridor_preferences[%s]" % nid
        if nid not in net_set:
            rejections.append({"item": label, "reason": "未知 net %r" % (nid,)})
            continue
        if nid in corridor_nets:
            rejections.append({"item": label, "reason": "重复的 net 项"})
            continue
        wps = item.get("waypoints_mm")
        if not isinstance(wps, list) or not all(
                isinstance(w, list) and len(w) == 2 and _is_num(w[0])
                and _is_num(w[1]) for w in wps):
            rejections.append({"item": label,
                               "reason": "waypoints_mm 结构畸形（须为 [x,y] 数值对列表）"})
            continue
        if len(wps) > MAX_WAYPOINTS:
            rejections.append({"item": label,
                               "reason": "waypoints 超过 %d 个（%d）"
                                         % (MAX_WAYPOINTS, len(wps))})
            continue
        allowed_layers = _net_allowed_layers(board, _net_class_of(board, nid))
        bad = None
        for w in wps:
            x, y = float(w[0]), float(w[1])
            if not (bbox[0] <= x <= bbox[2] and bbox[1] <= y <= bbox[3]):
                bad = "waypoint %r 出板 bbox" % (w,)
                break
            if _waypoint_keepout_hit(board, x, y, allowed_layers):
                bad = "waypoint %r 落 keepout（按该 net 允许层判定）" % (w,)
                break
        if bad is not None:
            rejections.append({"item": label, "reason": bad})
            continue
        corridor_nets.add(nid)
        # 原样透传 planner 给出的坐标（不改写、不吸附、不重排）。
        corridors_out.append({"net_id": nid, "waypoints_mm": wps})

    # ---- layer_preferences：逐项可拒绝 ----
    layerprefs_in = actions.get("layer_preferences", [])
    if layerprefs_in is None:
        layerprefs_in = []
    if not isinstance(layerprefs_in, list):
        return _blocked(sid, group, "layer_preferences 必须是列表")
    layerprefs_out = []
    layerpref_nets = set()
    for i, item in enumerate(layerprefs_in):
        label = "layer_preferences[%d]" % i
        if not isinstance(item, dict):
            rejections.append({"item": label, "reason": "项不是对象"})
            continue
        for k in item:
            if k not in LAYERPREF_KEYS:
                return _blocked(sid, group, "%s 未知键 %r" % (label, k))
        nid = item.get("net_id")
        if not isinstance(nid, str):
            rejections.append({"item": label, "reason": "net_id 缺失或非字符串"})
            continue
        label = "layer_preferences[%s]" % nid
        if nid not in net_set:
            rejections.append({"item": label, "reason": "未知 net %r" % (nid,)})
            continue
        if nid in layerpref_nets:
            rejections.append({"item": label, "reason": "重复的 net 项"})
            continue
        layers = item.get("layers")
        if not _is_str_list(layers):
            rejections.append({"item": label,
                               "reason": "layers 结构畸形（须为层名字符串列表）"})
            continue
        allowed = set(_net_allowed_layers(board, _net_class_of(board, nid)))
        illegal = [l for l in layers if l not in allowed]
        if illegal:
            rejections.append({
                "item": label,
                "reason": "层 %r 不在 allowed_layers[%s]=%r 内"
                          % (illegal, _net_class_of(board, nid), sorted(allowed)),
            })
            continue
        layerpref_nets.add(nid)
        layerprefs_out.append({"net_id": nid, "layers": layers})

    return {
        "schema": VALIDATED_SCHEMA,
        "scenario_id": sid,
        "group": group,
        "blocked": False,
        "rejections": rejections,
        "accepted": {
            "route_order": list(order),
            "corridor_preferences": corridors_out,
            "layer_preferences": layerprefs_out,
            "protect": list(protect),
        },
    }


def validate_response_file(response_path, board_path, expected_group):
    """从文件读 response + board 并校验；返回 validated 字典。"""
    response = model.read_json(response_path)
    board = model.read_json(board_path)
    return validate_response(response, board, expected_group)


def write_validated(path, validated):
    """确定性落盘 validated-actions JSON（LF、2 空格缩进、UTF-8）。"""
    model.write_json(path, validated)


# ---------------------------------------------------------------- CLI

def main():
    payload = model.read_stdin_json()
    validated = validate_response_file(payload["planner_response_path"],
                                       payload["board_path"],
                                       str(payload["expected_group"]))
    out_path = payload.get("out_path")
    if out_path:
        write_validated(out_path, validated)
    import sys
    sys.stdout.write(model.canonical_json(validated))
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
