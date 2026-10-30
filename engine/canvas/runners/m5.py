# -*- coding: utf-8 -*-
"""canvas.runners.m5 -- Lane-M5 高速信号调参 runner（合同 §1: run_m5(st,
budget) 长度组 tuning 驱动；确定性调参规划）。

流程: plan_actions（枚举→选第一合法项）→ protocol.apply_batch（语义层缝，
逐动作 validate_edit 同源复检）→ summary。

budget 形态（激活跑 prereg 冻结的输入契约，本件实现缺省）:
    {
      "length_groups": {                     # 缺省/空 = no_length_groups 路径
        "<group_id>": {"nets": [net_id..],   # 组内网（长度匹配成员）
                        "target_mm": float,  # 组目标长度
                        "tol_mm": float}     # 容差带
      },
      "tuning_limits": {                     # 可选，合法档枚举上限覆盖
        "max_amp_mm": .., "max_count": .., "max_offset_mm": ..
      }
    }
长度组数据来源审计（canvas.tuning 模块 docstring 转录）: board.v1 **无长度组
字段**——人口用合成长度组夹具板（budget 注入目标长度表）先行，真板走
no_length_groups 如实登记，激活跑 prereg 转录。

确定性: 组序/net 序 = sorted；档序 = legal_options 钉死序；逐档 R6 预检 +
validate_edit 预检取**第一过检项**；无随机源，同输入同动作序列字节等。
"""
from .. import protocol as cpr
from .. import tuning as ct
from .. import validate as cval


def _limits(budget):
    src = budget.get("tuning_limits") or {}
    out = {}
    for key in ("max_amp_mm", "max_count", "max_offset_mm"):
        if key in src:
            out[key] = src[key]
    return out


def _first_legal_action(st, net_id, group_id, base_len, target, tol, limits):
    """逐档（legal_options 钉死序）取第一个过**精确长度复核** + R6 预检 +
    validate_edit 预检的 tuning 动作；无合法档=None（确定性）。

    精确长度复核: legal_options 的 accordion 闭式 added=2·amp·count 是腿
    起点折返的下界（腿中折返有回退段额外 +2·(pitch−r)，见 canvas.tuning
    精确性披露）——逐档用 option_actual_len_mm（instantiate 几何单源实算）
    核 |target − 精确长| ≤ tol，闭式档序只作枚举序。"""
    for opt in ct.legal_options(base_len, target, tol, **limits):
        actual = ct.option_actual_len_mm(st, net_id, opt["kind"],
                                         opt["params"], group_id)
        if abs(target - actual) > tol:
            continue
        action = {"action": "tuning", "net_id": net_id, "group_id": group_id,
                  "kind": opt["kind"], "params": dict(opt["params"])}
        if ct.r6_violations(st, net_id, opt["kind"], opt["params"], group_id):
            continue
        accepted, _code, _detail = cval.validate_edit(st, action)
        if not accepted:
            continue
        return action
    return None


def plan_actions(st, budget):
    """确定性调参规划 → tuning 动作列表（合同 §1: 先 legal_options 枚举再选
    第一合法项）。

    - 组内逐网（sorted 序）: |target − base| ≤ tol 的网不动；超容差网枚举
      合法档，R6 预检（v5.drc.check_keepout 同源）+ validate_edit 预检后取
      第一合法项；全档被拒（越 zone/间距/容差无解/超长不可救）= 不产该网
      动作（run_m5 摘要经 residuals_after 如实呈现未达标）。
    - 无长度组数据（budget 缺 length_groups/空）= 不产任何 tuning 动作
      （run_m5 报 no_length_groups: true）。
    - 预检状态口径: 逐动作对**规划期态**预检；apply_batch 应用序复检若因批
      内先行 tuning 的累积铜而拒收（跨网同区紧邻的罕见情形），拒收事实入
      summary.rejected——不静默。"""
    groups = budget.get("length_groups") or {}
    limits = _limits(budget)
    actions = []
    for group_id in sorted(groups):
        spec = groups[group_id]
        target = float(spec["target_mm"])
        tol = float(spec["tol_mm"])
        for net_id in sorted(spec["nets"]):
            if net_id not in st.known_nets():
                continue
            grid = cpr.tuning_base_grid(st, net_id)
            if not grid:
                continue          # 无基线段=网未布线，无从调参（不产动作）
            base = ct.net_tuned_len_mm(st, net_id, group_id)
            if abs(target - base) <= tol:
                continue          # 已在容差带内
            act = _first_legal_action(st, net_id, group_id, base, target,
                                      tol, limits)
            if act is not None:
                actions.append(act)
    return actions


def _groups_residuals(st, groups):
    return {gid: ct.residual(st, gid, groups) for gid in sorted(groups)}


def run_m5(st, budget):
    """高速调参一轮: plan → apply_batch → summary。

    summary = {no_length_groups, planned, applied, rejected, tuned_groups,
    residuals_before, residuals_after, board_id}（canonical_json 可直落，
    双跑字节等）。rejected=[{index, code, detail}]（apply 层复检拒收——
    常态为空: 预检同一 validate_edit 判定器）。"""
    budget = budget or {}
    groups = budget.get("length_groups") or {}
    residuals_before = _groups_residuals(st, groups) if groups else {}
    actions = plan_actions(st, budget)
    results = cpr.apply_batch(st, actions)
    residuals_after = _groups_residuals(st, groups) if groups else {}
    applied_groups = set()
    rejected = []
    applied = 0
    for r in results:
        if r.get("accepted"):
            applied += 1
            sid = r.get("shape_id")
            if sid and sid.startswith("tun:"):
                applied_groups.add(sid.split(":")[2])
        else:
            rejected.append({"index": r["index"], "code": r.get("code"),
                             "detail": r.get("detail")})
    return {
        "board_id": st.board["board_id"],
        "no_length_groups": not groups,
        "planned": len(actions),
        "applied": applied,
        "rejected": rejected,
        "tuned_groups": sorted(applied_groups),
        "residuals_before": residuals_before,
        "residuals_after": residuals_after,
    }
