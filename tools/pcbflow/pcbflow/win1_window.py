"""WIN-1：UNKNOWN(region_over_window) 窗自适应渐进实验（零写提案器）。

背景：FC2 靶 1 的 61 信号断点三态（out/revc-fc2/residual-certs.json，
8 SAT / 40 UNSAT / 13 UNKNOWN）中 13 条 UNKNOWN 全部由
route_grid.CERT_WINDOW_NODES（600_000 模型节点窗）封顶（region_over_window：
模型还没建就被节点计数门拒掉）。本模块对这 13 条逐条做渐进窗重求解，
判定三态能否如实升级。

冻结链保护（WIN-1 验收门）：
- route_grid.build_cert_model 仅新增可选参数 window_nodes（默认=模块常量
  CERT_WINDOW_NODES=600_000）；residual_cmd 等冻结调用点零改动，默认路径
  行为字节不变（tests/test_win1_window.py 强制）。

求解器合同（不容破坏；与 residual_cmd._classify 同一映射语义）：
- SAT：Router witness + L1 终判全过（route_grid.route_one）；
- UNSAT：受限阻塞证书 route_grid.solve_cert 的 reachable_b=False 割 +
  独立复核 route_grid.verify_cert verified=true（复用现有证书验证机制，
  不另造验证器）；
- 其余一律如实 UNKNOWN。扩窗不把 UNKNOWN 自动改判 UNSAT——升级唯一途径
  是窗内找到 witness 或 verified 证书。模型内候选通径（reachable_b=True）
  仍如实记 UNKNOWN（模型开放≠L1 合法，route_grid 原语义）。

渐进窗梯（每行独立、确定性、升序去重）：
- T0 frozen_600k：margin=CERT_MARGIN_MM、窗=600_000 → 复现冻结门
  （预期 region_over_window；走真实 build_cert_model 门路径）；
- T1 corridor：margin=CERT_MARGIN_MM、窗=该区域精确节点数 → 冻结语义里
  被拒建的那个自然模型（端点 bbox+1mm 夹紧板框；BFS 闭包即连通组件分析，
  对应任务书的"走廊窗/连通组件窗"）；
- T2 board：margin=WIN1_BOARD_MARGIN_MM（远超板对角线，bbox 夹紧到整板）、
  窗=整板区域精确节点数 → 板级窗。仅当 T1 产出 verified 割时运行（范围
  强化测试：割是否只是走廊窗伪影）；T1 若为候选通径（UNKNOWN），走廊
  bbox ⊆ 板 bbox，子模型通径在母模型中仍是通径，T2 必然同判 → 确定性
  跳过并记录理由。

每行先做一次 route_one 见证尝试（冻结调用、确定性；若意外 ok 即真 SAT
升级）。生成器模式：零落盘、零子进程、板只读（内存 dry-run）；核心产物
无 wall-clock（run manifest 由编排侧单列）。
"""

from __future__ import annotations

import math

from . import route_grid

WIN1_SCHEMA = "1.3"
WIN1_ARTIFACT_KIND = "win1_window_experiment"
WIN1_BASELINE_WINDOW = route_grid.CERT_WINDOW_NODES   # 600_000（冻结门）
WIN1_BOARD_MARGIN_MM = 1000.0   # 板级窗 margin：远超板对角线 → 夹紧整板框


# ---- 渐进窗几何（纯计数，与 build_cert_model 同式） --------------------------
def region_nodes(board_bb, ax, ay, bx, by, margin_mm,
                 res=route_grid.CERT_RES_MM):
    """区域节点计数（build_cert_model 的 bbox 推导同式：端点 bbox+margin
    夹紧板框；0.05mm 格；节点=3*nx*ny=2 信号层格+过孔位）。"""
    x0 = max(min(ax, bx) - margin_mm, board_bb[0])
    y0 = max(min(ay, by) - margin_mm, board_bb[1])
    x1 = min(max(ax, bx) + margin_mm, board_bb[2])
    y1 = min(max(ay, by) + margin_mm, board_bb[3])
    nx = int(math.floor((x1 - x0) / res)) + 1
    ny = int(math.floor((y1 - y0) / res)) + 1
    return {"nodes": 3 * nx * ny, "nx": nx, "ny": ny,
            "region_mm": [round(x0, 3), round(y0, 3),
                          round(x1, 3), round(y1, 3)]}


def window_ladder(board_bb, ax, ay, bx, by):
    """确定性渐进窗梯（升序、按 (tier, window) 去重）。"""
    corridor = region_nodes(board_bb, ax, ay, bx, by,
                            route_grid.CERT_MARGIN_MM)
    board = region_nodes(board_bb, ax, ay, bx, by, WIN1_BOARD_MARGIN_MM)
    ladder = [{"tier": "frozen_600k",
               "margin_mm": route_grid.CERT_MARGIN_MM,
               "window_nodes": WIN1_BASELINE_WINDOW,
               "region_mm": corridor["region_mm"],
               "region_nodes": corridor["nodes"]}]
    if corridor["nodes"] > WIN1_BASELINE_WINDOW:
        ladder.append({"tier": "corridor",
                       "margin_mm": route_grid.CERT_MARGIN_MM,
                       "window_nodes": corridor["nodes"],
                       "region_mm": corridor["region_mm"],
                       "region_nodes": corridor["nodes"]})
    if (corridor["nodes"] > WIN1_BASELINE_WINDOW
            and board["nodes"] > corridor["nodes"]):
        # 只对真被冻结门拒掉的行（corridor nodes>600k ⟺ 超窗）升级板级梯；
        # 门本可通过的行梯到 frozen 为止（无窗可解、无谓建模）。
        ladder.append({"tier": "board",
                       "margin_mm": WIN1_BOARD_MARGIN_MM,
                       "window_nodes": board["nodes"],
                       "region_mm": board["region_mm"],
                       "region_nodes": board["nodes"]})
    return ladder


# ---- 单窗求解（合同如实映射；与 residual_cmd._classify 同语义） --------------
def _cert_step(bm, row, router, margin_mm, window_nodes):
    """证书侧一步：build → solve → verify → 三态。model 门拒=UNKNOWN。"""
    model, unk = route_grid.build_cert_model(
        bm, row["net"], router["width"], router["via_size"],
        router["via_drill"], row["ax"], row["ay"], row["bx"], row["by"],
        margin_mm=margin_mm, window_nodes=window_nodes)
    if model is None:
        return {"status": "UNKNOWN",
                "unknown_reason": "unknown:%s(%s)" % (unk[0], unk[1])}
    cert = route_grid.solve_cert(model)
    if cert.get("reachable_b") is not False:
        return {"status": "UNKNOWN",
                "unknown_reason": "unknown:no_certificate(模型内存在候选通径"
                                  "，模型开放≠L1 合法)",
                "candidate": {"hit_node": cert.get("hit_node"),
                              "spokes_b": cert.get("spokes_b"),
                              "note": cert.get("note")}}
    if cert.get("cert_broken"):
        return {"status": "UNKNOWN",
                "unknown_reason": "unknown:cert_broken_closure"}
    verified = route_grid.verify_cert(model, cert)
    cert = {k: v for k, v in cert.items() if k not in ("s_side_nodes",)}
    cert["verified"] = bool(verified)
    if not verified:
        return {"status": "UNKNOWN",
                "unknown_reason": "unknown:cert_verify_failed"}
    return {"status": "UNSAT", "certificate": cert,
            "unknown_reason": None}


def run_row(bm, row, router_result=None):
    """单行渐进窗实验（板只读、纯内存）。

    row：{row_id, net, ax, ay, alayers, bx, by, blayers, ...}（含 opens
    解析出的层集）。返回核心产物 dict（无 wall-clock）。"""
    router = router_result
    if router is None:
        router = route_grid.route_one(bm, row["net"], row["ax"], row["ay"],
                                      row["alayers"], row["bx"], row["by"],
                                      row["blayers"])
    router_summary = {
        "ok": bool(router["ok"]),
        "fail": router["fail"], "blocks": router["blocks"][:3],
        "refine_rounds": router["refine_rounds"],
        "width": router["width"], "via_size": router["via_size"],
        "via_drill": router["via_drill"],
    }
    board_bb = bm["mirror"].bbox()
    ladder = window_ladder(board_bb, row["ax"], row["ay"],
                           row["bx"], row["by"])

    if router["ok"]:
        # 真 SAT 升级（witness 即证据；L1 终判在 route_one 内全过）
        return {"row_id": row["row_id"], "net": row["net"],
                "status": "SAT",
                "upgrade_from": "UNKNOWN(region_over_window)",
                "witness": {"segments": len(router["segments"]),
                            "vias": len(router["vias"]),
                            "length_mm": router["length_mm"]},
                "segments": router["segments"], "vias": router["vias"],
                "router": router_summary, "ladder": ladder, "steps": []}

    steps = []
    corridor_certified = False
    for step_def in ladder:
        tier = step_def["tier"]
        if tier == "board" and not corridor_certified:
            # 确定性去重：走廊模型有候选通径 → 板级模型（超集）必有同一
            # 通径，必然同判 UNKNOWN；无割则无范围强化可言。跳过≠未测。
            steps.append({"tier": "board",
                          "skipped": True,
                          "skip_reason": "corridor_not_certified(走廊窗未产 "
                                         "出 verified 割：候选通径 UNKNOWN "
                                         "在板级窗必然复现，确定性去重)"})
            continue
        step = _cert_step(bm, row, router, step_def["margin_mm"],
                          step_def["window_nodes"])
        step["tier"] = tier
        step["window_nodes"] = step_def["window_nodes"]
        step["margin_mm"] = step_def["margin_mm"]
        step["skipped"] = False
        steps.append(step)
        if step["status"] == "UNSAT":
            if tier == "corridor":
                corridor_certified = True
            if tier == "board":
                break   # 板级割=最强 scope，已定稿
        # UNKNOWN（含 corridor 门拒/候选通径/证书坏）→ 继续下一梯（board
        # 梯对 corridor UNKNOWN 已被上面的 skip 规则处理：仅 corridor
        # certified 时才跑 board）
    final = "UNKNOWN"
    final_reason = None
    upgrade_cert = None
    for st in steps:
        if st.get("skipped"):
            continue
        if st["status"] == "UNSAT":
            final = "UNSAT"
            upgrade_cert = st["certificate"]
            final_reason = None
            break
        if st["status"] == "UNKNOWN":
            final_reason = st["unknown_reason"]
    # UNKNOWN 行取最具体原因：门拒 → 候选通径/验证失败（后梯覆盖前梯）
    if final == "UNKNOWN":
        for st in steps:
            if not st.get("skipped") and st.get("unknown_reason"):
                final_reason = st["unknown_reason"]
    return {"row_id": row["row_id"], "net": row["net"],
            "status": final,
            "upgrade_from": "UNKNOWN(region_over_window)",
            "unknown_reason": final_reason,
            "certificate": upgrade_cert,
            "router": router_summary,
            "ladder": ladder, "steps": steps}


# ---- 61 行映射辅助（只读；编排侧组装结果表用） --------------------------------
def unknown_rows_from(certs_obj):
    """residual-certs.json 对象 → 13 条 UNKNOWN 行清单（fail-closed）。"""
    rows = [r for r in certs_obj["rows"]
            if r["solver_status"] == "UNKNOWN"
            and (r.get("unknown_reason") or "").startswith(
                "unknown:region_over_window")]
    counts = certs_obj.get("counts") or {}
    if counts.get("UNKNOWN") != len(rows):
        raise RuntimeError("WIN-1 fail-closed：counts.UNKNOWN=%r 与 "
                           "region_over_window 行数 %d 不一致"
                           % (counts.get("UNKNOWN"), len(rows)))
    return rows
