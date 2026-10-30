"""FB-1 三臂配对实验：③ 重放 + 局部 ripup 解锁（纯函数核）。

风格对齐 board_writer（板文本 → 板文本纯函数；零落盘、零子进程；落盘由
编排侧 scripts/fb1_arm_orchestrate.py 完成）。与 route_grid.py 的关系：
route_grid.route_one 调用点硬编码 ripup=False（主链冻结语义，本实验不改、
不回写）；本模块在实验面直接消费同一 pcbagent 锁定 adapter 的
Router.route_net(ripup=True)，前提差异（无 ripup 前提 vs ripup 前提）在
产物 schema 里显式分列——既有 UNSAT 证书只绑定"无 ripup 前提"，禁止与
本实验 ripup 前提混比。

三臂定义（dataset=coreboard-fb1，全部在 p3 快照副本、live 板零写）：
  arm0  基线复现：③ 重放板 + 既有 6 批 routes（ripup=False）→ 55/61；
  arm1  仅 ③ 重放：同基线底座 + 剩余 6 断点 ripup=False 重跑；
  arm2  ③ 重放 + 局部 ripup：同 arm1 布局，剩余 6 断点 ripup=True 重跑，
        拆线范围=Router 洪泛归因出的实际阻塞邻网（GND 禁拆、预算 3 网/行，
        pcbagent L3_RIPUP_FORBIDDEN/L3_RIPUP_BUDGET 原值），逐条记账；
        批纪律=§10.4（≤10 网/批 + 批 DRC severity-error，新增 error 整批
        回滚），终检 severity-all 零新增 error 为硬门。
"""

from __future__ import annotations

import math
import re

from . import board_writer, residual_cmd

FB1_SCHEMA = "1.0"
FB1_DATASET = "coreboard-fb1"

_NET_RE = re.compile(r'\(net "([^"]*)"\)')

# ripup 前提声明（schema 随行；语义=pcbagent Router.route_net(ripup=True)）
RIPUP_PREMISE = {
    "premise": "ripup_allowed",
    "budget_per_row": 3,          # pcbagent config.L3_RIPUP_BUDGET 原值
    "forbidden_nets": ["GND"],    # pcbagent config.L3_RIPUP_FORBIDDEN 原值
    "note": "拆线范围=洪泛封堵归因出的实际阻塞邻网（为打开该断点所必需）；"
            "被拆网由 Router._replan_net 全焊盘最近链重布；主链 UNSAT 证书"
            "（无 ripup 前提）不适用于本臂，不混比",
}


# ---- pcbagent Plan → 归一化 dict（口径对齐 route_grid.route_one） -----------
def normalize_plan(plan):
    """pcbagent Plan → 归一化 dict + ripup 依赖字段（纯函数）。"""
    out = {
        "net": plan.net, "ok": bool(plan.ok), "fail": plan.fail,
        "blocks": [str(b) for b in (plan.blocks or [])],
        "width": plan.width,
        "via_size": plan.via_size, "via_drill": plan.via_drill,
        "refine_rounds": plan.refine_rounds,
        "region_mm": round(plan.region_mm, 3),
        "segments": [[int(L), round(x1, 4), round(y1, 4),
                      round(x2, 4), round(y2, 4)]
                     for (L, x1, y1, x2, y2) in plan.segments],
        "vias": [[round(x, 4), round(y, 4)] for (x, y) in plan.vias],
        "length_mm": round(sum(math.hypot(x2 - x1, y2 - y1)
                               for (_L, x1, y1, x2, y2) in plan.segments), 3),
        "ripup_net": plan.ripup_net,
        "ripup_plan": (normalize_replan(plan.ripup_plan)
                       if plan.ripup_plan is not None else None),
    }
    return out


def normalize_replan(plan):
    """被拆网重布 Plan → 归一化 dict（嵌套不递归；重布无二级 ripup）。"""
    return {
        "net": plan.net, "ok": bool(plan.ok),
        "width": plan.width, "via_size": plan.via_size,
        "via_drill": plan.via_drill,
        "segments": [[int(L), round(x1, 4), round(y1, 4),
                      round(x2, 4), round(y2, 4)]
                     for (L, x1, y1, x2, y2) in plan.segments],
        "vias": [[round(x, 4), round(y, 4)] for (x, y) in plan.vias],
        "length_mm": round(sum(math.hypot(x2 - x1, y2 - y1)
                               for (_L, x1, y1, x2, y2) in plan.segments), 3),
    }


def plan_to_route(norm, row_id=None, net_id=None, bus_id=None):
    """归一化 plan dict → board_writer 可落板 route dict（uuid 内容派生）。"""
    return {
        "row_id": row_id, "net_id": net_id, "bus_id": bus_id,
        "net": norm["net"], "width": norm["width"],
        "via_size": norm["via_size"], "via_drill": norm["via_drill"],
        "segments": norm["segments"], "vias": norm["vias"],
        "uuid": board_writer.route_uuid(
            {"net": norm["net"], "segments": norm["segments"],
             "vias": norm["vias"]}),
    }


def ripup_ops_of(norm):
    """归一化 plan → [(ripped_net, replan_norm)]（空=无拆线依赖）。"""
    if not norm.get("ripup_net"):
        return []
    return [(norm["ripup_net"], norm.get("ripup_plan"))]


# ---- 板文本拆线（拓扑级删除；口径=顶层 segment/via 节点按 net 过滤） --------
def _node_net(node_text):
    m = _NET_RE.search(node_text)
    return m.group(1) if m else None


def removed_spans(board_text, net):
    """板文本中该网的全部顶层 segment/via 节点跨度 [(start, end, kind)]。"""
    spans = []
    for tag, kind in (("segment", "segment"), ("via", "via")):
        for (i, j) in board_writer._top_level_nodes(board_text, tag):
            if _node_net(board_text[i:j]) == net:
                spans.append((i, j, kind))
    return sorted(spans)


def count_net_nodes(board_text, net):
    """该网顶层铜节点计数 {"segment": n, "via": m}（记账用）。"""
    spans = removed_spans(board_text, net)
    return {"segment": sum(1 for s in spans if s[2] == "segment"),
            "via": sum(1 for s in spans if s[2] == "via"),
            "total": len(spans)}


def strip_spans(board_text, spans):
    """按跨度删除节点（倒序删保持偏移有效；纯函数）。"""
    out = board_text
    for (i, j, _k) in sorted(spans, reverse=True):
        out = out[:i] + out[j:]
    return out


def apply_ripup_commit(board_text, routes, ripped_nets):
    """拆线 + 落新铜：先删 ripped_nets 全部顶层铜节点，再追加 routes 节点。

    拆线计数与实物一一对应由编排侧用 count_net_nodes 预先记账（本函数不
    返回计数，保持 board 文本 → board 文本纯函数口径）。"""
    spans = []
    for net in ripped_nets:
        spans.extend(removed_spans(board_text, net))
    text = strip_spans(board_text, spans)
    return board_writer.apply_routes(text, routes), spans


# ---- 批 DRC 判定（口径=residual_cmd._drc_ledger 同一 keyset 语义） ----------
def batch_verdict(baseline_drc, candidate_drc):
    """baseline/candidate DRC JSON dict → 批判定（新增 error=0 才接受）。

    baseline=severity-all（底座板），candidate=severity-error（批后板）；
    新增=候选 keyset − 基线 keyset（type/severity/description 三元组）。"""
    base = residual_cmd._viol_keyset(baseline_drc)
    cand = residual_cmd._viol_keyset(candidate_drc)
    cand_err = {k for k in cand if k[1] == "error"}
    new_all = cand - base
    new_err = cand_err - {k for k in base if k[1] == "error"}
    return {
        "candidate_violations": len(cand),
        "new_vs_baseline": len(new_all),
        "new_errors_vs_baseline": len(new_err),
        "new_detail": sorted(v[0] + ":" + v[2][:60] for v in new_all),
        "accepted": len(new_err) == 0,
    }
