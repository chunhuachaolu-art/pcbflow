"""RIPUP-1：live 板受控 ripup 收断点战役（纯函数核）。

风格对齐 fb1_experiment.py（板文本 → 板文本纯函数 + 判定纯函数；零落盘、
零子进程；落盘、kicad-cli 与 live 写入由编排侧 out/coreboard-ripup1/
ripup1_orchestrate.py 在 Bash 驱动下完成）。与 fb1_experiment 的关系：
拆线/落铜/批判定复用其既有原语（removed_spans/apply_ripup_commit/
batch_verdict），route_grid.py 零改动；本模块只补战役语义——

  1. 拆铜偏好序（战役硬门 4）：信号网优先；电源/地网（GND/GNDA/3V3/5V/
     SW_NODE/VDDA/VBAT/VDD 一类）只在无信号网替代方案时才许拆，且逐处
     记账 si_review_required=true（回流路径风险超出 kicad-cli DRC
     authority，须人工 SI 复核）。pcbagent 原生 Router.route_net(ripup=True)
     只返回第一个成功候选（混合序，可能先命中电源网即停）；本模块用同一
     批锁定 adapter 的 Router 内部原语（_ripup_candidates/_try_route/
     _replan_net/leg.ignore_ids）按类分序重排尝试：类间=信号先行，类内=
     router 原序（封堵次数降序+字典序，禁随机）。预算与禁拆网取 pcbagent
     config 原值（L3_RIPUP_BUDGET=3、L3_RIPUP_FORBIDDEN=("GND",)）。
  2. unconnected 单调硬门（硬门 1）：候选批 unconnected 计数必须 ≤ 上一
     收工值；被拆网不得新增 unconnected 条目（"拆 A 补 B 却丢了 A" 即整批
     否决）。零新增 severity-error 门（硬门 2）委托 fb1_experiment.
     batch_verdict 同一 keyset 口径。
  3. 批操作数（硬门 3）：批 ≤10 网；本战役每批=1 目标行 + 其被拆网
     （≤2 网），由 orchestrate 侧断言。

zones/铺铜图元一律不碰（removed_spans 只匹配顶层 segment/via 节点）。
"""

from __future__ import annotations

import re

from . import fb1_experiment, residual_cmd

RIPUP1_SCHEMA = "1.0"
RIPUP1_DATASET = "coreboard-ripup1"
RIPUP1_DATE = "2026-09-11"

# pcbagent config.L3_RIPUP_BUDGET / L3_RIPUP_FORBIDDEN 原值（与
# fb1_experiment.RIPUP_PREMISE 同源；pcbagent 零改动，取值须一致）
RIPUP1_BUDGET = 3
RIPUP1_FORBIDDEN = ("GND",)

# 电源/地网判别（战役硬门 4 口径）：精确名 + VDD/GND 前缀族。本板实测
# 电源地网名：GND/GNDA/3V3/5V/SW_NODE/VDDA/VBAT（targets 含 VBAT/GNDA/
# 3V3 本身不影响——它们是行目标，只作为"被拆网"时才进入本判别）。
POWER_GROUND_EXACT = frozenset({
    "GND", "GNDA", "3V3", "5V", "SW_NODE", "VDDA", "VBAT", "VDD", "VBUS",
})
POWER_GROUND_PREFIX = ("GND", "VDD", "VBUS", "+3V3", "+5V")

_NET_RE = re.compile(r"\[([^\[\]]+)\]")


# ---- 拆铜偏好序（硬门 4） ----------------------------------------------------
def is_power_ground(net):
    """网名 → 电源/地网判定（精确名 + 前缀族；纯函数）。"""
    if not net:
        return False
    return net in POWER_GROUND_EXACT or net.startswith(POWER_GROUND_PREFIX)


def net_class(net):
    """网名 → "power_ground" | "signal"（台账口径）。"""
    return "power_ground" if is_power_ground(net) else "signal"


def ordered_ripup_candidates(blocks, own, forbidden=RIPUP1_FORBIDDEN):
    """封堵归因 blocks → 候选拆网序（router._ripup_candidates 同口径：
    次数降序+字典序；滤掉本网与禁拆网；确定性）。"""
    cnt = {}
    for b in blocks:
        for m in _NET_RE.finditer(b):
            n = m.group(1)
            if n and n != own and n not in forbidden:
                cnt[n] = cnt.get(n, 0) + 1
    return [k for k in sorted(cnt, key=lambda k: (-cnt[k], k))]


def partition_candidates(ordered):
    """候选序 → {"signal": [...], "power_ground": [...]}（类内保持原序）。"""
    part = {"signal": [], "power_ground": []}
    for n in ordered:
        part[net_class(n)].append(n)
    return part


# ---- 单行 ripup 求解（最小拆集贪心序；纯内存） ------------------------------
def plan_row_with_ripup(bm, net, ax, ay, alayers, bx, by, blayers,
                        max_rip=RIPUP1_BUDGET, forbidden=RIPUP1_FORBIDDEN,
                        log=None):
    """单行"最小拆集+重布"求解：无拆线先解 → 封堵归因 → 逐个加拆（每步取
    当前归因的最优候选：信号网先行、电源网殿后，类内=router 原序次数降序
    +字典序）→ 全部拆网同轮全焊盘链重布（router.route_net ripup 分支原语，
    语义一致，仅扩为有序拆集）。纯内存。

    贪心纪律：每步只加拆 1 网（当前归因最优），重搜成功即停（拆集最小性）；
    被拆网重布按拆序进行，先前重布铜作后续重布障碍（保守：被拆网旧铜仍在
    镜像内，重布绕行它仍合法——commit 时旧铜才真删）。

    返回归一化 dict + 战役记账：ripup_set=[{net,class,si_review_required,
    replan}]、ripup_trials（逐步试拆账）、candidates_history。"""
    pa = bm["pa"]
    router = pa["Router"](bm["mirror"],
                          legality=pa["Legality"](bm["mirror"]),
                          corridor_of=None, log=log or (lambda *_a: None))
    A = (ax, ay, frozenset(alayers))
    B = (bx, by, frozenset(blayers))
    plan0 = router._fresh_plan(net, A, B)
    bbox = router._region_bbox(plan0)
    p = router._try_route(plan0, bbox, excluded_items=())

    trials = []            # [{step, candidate, class, outcome}]
    candidates_history = []  # 每步封堵归因的类分候选
    ripped = []            # 最终拆序 [(net, class)]
    rip_set = []           # 最终重布账 [{net,class,si_review_required,replan}]
    picked = []            # 已入拆集（含尚未解锁的步进候选）
    solved = bool(p.ok)    # 无拆线已解=成功；进循环后须"解锁+重布全过"
    if not p.ok:
        for step in range(1, max_rip + 1):
            ordered = ordered_ripup_candidates(p.blocks, net, forbidden)
            part = partition_candidates(ordered)
            picks = ([c for c in part["signal"] if c not in picked]
                     + [c for c in part["power_ground"] if c not in picked])
            candidates_history.append({"step": step, "signal": part["signal"],
                                       "power_ground": part["power_ground"]})
            if not picks:
                trials.append({"step": step, "candidate": None,
                               "outcome": "no-candidate-left"})
                break
            cand, cls = picks[0], net_class(picks[0])
            removed_items = [it for rn in picked
                             for it in _items_of_net(bm, rn)]
            removed_items += _items_of_net(bm, cand)
            # 与 router.route_net 同法：被拆铜在 L1 终判/区域里视同已删
            # （finally 还原；失败=内存态丢弃即回滚）
            router.leg.ignore_ids = {id(it) for it in removed_items}
            try:
                p2 = router._try_route(router._fresh_plan(net, A, B), bbox,
                                       excluded_items=removed_items)
                if not p2.ok:
                    trials.append({"step": step, "candidate": cand,
                                   "class": cls, "outcome": "retry-UNKNOWN",
                                   "fail": p2.fail})
                    picked.append(cand)  # 步进加入拆集（贪心增长）
                    p = p2
                    continue
                # 解锁 ≠ 成功：被拆网重布也要全过才算（重布不可行→继续
                # 增长拆集——多拆一网同时给重布让出走廊）
                ripped_try = [(c, net_class(c)) for c in picked + [cand]]
                rip_set_try, ok_seq = _try_replan_seq(
                    router, bm, p2, ripped_try, trials)
                if not ok_seq:
                    picked.append(cand)
                    p = p2
                    continue
                p = p2
                ripped = ripped_try
                rip_set = rip_set_try
                solved = True
                trials.append({"step": step, "candidate": cand, "class": cls,
                               "outcome": "unlocked+replanned",
                               "rip_set": [c for (c, _k) in ripped]})
                break
            finally:
                router.leg.ignore_ids = set()
        if not solved:
            # 预算内无"解锁+重布"可行解：显式回滚为未解（禁止把"解锁但
            # 重布失败"的最后一步当 SAT——那会落下无重布的拆线残局）
            p = router._fresh_plan(net, A, B)
            p.fail = ("拆集预算内无可行解（解锁后重布不可行或持续不可达；"
                      "max_rip=%d）" % max_rip)

    norm = fb1_experiment.normalize_plan(p)
    norm.update({
        "ripup_set": rip_set if norm["ok"] else [],
        "ripup_trials": trials,
        "candidates_history": candidates_history,
    })
    return norm


def _items_of_net(bm, net):
    """镜像中该网的全部铜 item（拆线排除集用；router.route_net 同口径）。"""
    return [bm["mirror"].items[i]
            for i in bm["mirror"]._items_by_net.get(net, [])]


def _replan_net_excl(router, net, terms, added_prims, excluded_items,
                     margin_mm=None):
    """被拆网重布（router._replan_net 逐边等价重放 + excluded_items）：
    链式端点逐边 route，全部边成功才算成功；任一边失败返回 None
    （内存态自动丢弃即回滚）。

    margin_mm：逐边区域窗外扩（缺省=router 原口径 _region_bbox=
    端点 bbox+L3_MARGIN=3mm）。重布绕行新目标铜常需远超 3mm 的绕行窗，
    本参数只放大搜索窗（合法性不变：逐边仍过 _try_route 的 Region/A*+
    L1 终判，批 DRC 仍裁决），属搜索参数而非语义变更。"""
    mb = router.m.bbox()

    def bbox_of(a, b):
        if margin_mm is None:
            return None  # None → 调用方退回 router._region_bbox 原口径
        m = margin_mm
        return (max(min(a[0], b[0]) - m, mb[0]), max(min(a[1], b[1]) - m,
                                                    mb[1]),
                min(max(a[0], b[0]) + m, mb[2]), min(max(a[1], b[1]) + m,
                                                     mb[3]))

    whole = router._fresh_plan(net, terms[0], terms[-1])
    for i in range(len(terms) - 1):
        sub = router._fresh_plan(net, terms[i], terms[i + 1])
        bb = bbox_of(terms[i], terms[i + 1])
        r = router._try_route(sub, bb if bb is not None
                              else router._region_bbox(sub),
                              excluded_items=excluded_items,
                              added_prims=added_prims)
        if not r.ok:
            return None
        whole.segments.extend(r.segments)
        whole.vias.extend(r.vias)
        whole.refine_rounds += r.refine_rounds
    whole.ok = True
    return whole


def _try_replan_seq(router, bm, p_ok, ripped, trials):
    """整序重布：目标新铜 prims 作障碍、先前重布铜叠加；全部被拆网旧铜按
    commit 语义视同已删（注入同一排除集——否则尚未删除的他拆网旧铜会伪堵
    重布）。先取 router 原口径重布窗，任一边失败整序重试放大窗
    （9mm=3×L3_MARGIN，仅搜索参数）。返回 (rip_set, all_ok)。"""
    prims = router._plan_prims(p_ok)
    excl_items = [it for (rn, _c) in ripped
                  for it in _items_of_net(bm, rn)]

    def seq(margin):
        seq_prims = prims
        out = []
        for (rnet, rcls) in ripped:
            terms = router._net_endpoints(rnet)
            rp = (_replan_net_excl(router, rnet, terms, seq_prims,
                                   excl_items, margin_mm=margin)
                  if len(terms) >= 2 else None)
            out.append({"net": rnet, "class": rcls,
                        "si_review_required": (rcls == "power_ground"),
                        "replan": (fb1_experiment.normalize_replan(rp)
                                   if rp is not None else None)})
            if rp is None:
                return out, False
            seq_prims = seq_prims + router._plan_prims(rp)
        return out, True

    out, ok = seq(None)
    if not ok:
        wide = 9.0  # 3×pcbagent L3_MARGIN
        out2, ok2 = seq(wide)
        trials.append({"step": len(trials) + 1, "candidate": None,
                       "outcome": ("replan-retried-wide-margin" if ok2
                                   else "replan-failed(wide-margin-too)"),
                       "replan_margin_mm": wide})
        if ok2:
            return out2, True
    return out, ok


def partition_of_blocks(blocks, own, forbidden=RIPUP1_FORBIDDEN):
    """（独立导出）封堵归因 → 类分候选（台账用，不触 router）。"""
    return partition_candidates(ordered_ripup_candidates(blocks, own,
                                                         forbidden))


# ---- 批判定（硬门 1+2：零新增 error + unconnected 单调 + 被拆网不新增悬空） --
def unconn_nets_of(drc_data):
    """DRC JSON → unconnected 条目涉及的网名集合（item 描述 [NET] 解析）。"""
    nets = set()
    for entry in drc_data.get("unconnected_items") or []:
        for it in entry.get("items") or []:
            m = _NET_RE.search(it.get("description") or "")
            if m:
                nets.add(m.group(1))
    return nets


def unconn_entry_counts(drc_data):
    """DRC JSON → {net: unconnected 条目数}（行关闭证据的细粒度口径）。"""
    counts = {}
    for entry in drc_data.get("unconnected_items") or []:
        nets = set()
        for it in entry.get("items") or []:
            m = _NET_RE.search(it.get("description") or "")
            if m:
                nets.add(m.group(1))
        for n in nets:
            counts[n] = counts.get(n, 0) + 1
    return counts


def campaign_batch_verdict(baseline_drc, candidate_drc, prev_unconn):
    """基线/候选 DRC JSON + 上一收工 unconnected → 战役批判定。

    accepted = 零新增 severity-error（fb1 口径） 且 unconnected ≤ prev
    且 无新增悬空网（被拆网丢连通即否决）。"""
    core = fb1_experiment.batch_verdict(baseline_drc, candidate_drc)
    unconn = residual_cmd._unconn_count(candidate_drc)
    pre_nets = unconn_nets_of(baseline_drc)
    post_nets = unconn_nets_of(candidate_drc)
    newly = sorted(post_nets - pre_nets)
    verdict = dict(core)
    verdict.update({
        "unconnected": unconn,
        "unconnected_prev": prev_unconn,
        "unconnected_monotonic": bool(unconn <= prev_unconn),
        "newly_dangling_nets": newly,
        "closed_nets": sorted(pre_nets - post_nets),
        "unconn_counts_pre": unconn_entry_counts(baseline_drc),
        "unconn_counts_post": unconn_entry_counts(candidate_drc),
    })
    verdict["accepted"] = bool(core["accepted"]
                               and verdict["unconnected_monotonic"]
                               and not newly)
    return verdict


# ---- 批装配与批操作数（硬门 3） ----------------------------------------------
def batch_nets(route_nets, ripped_nets):
    """批操作数口径：本批拆+布涉及的网总数（去重、排序）。"""
    nets = set(route_nets)
    nets.update(n for n in ripped_nets if n)
    return sorted(nets)


def assemble_batch(board_text, target_route, rip_ops, eol="auto"):
    """单行批装配：拆 rip_ops 各网全部顶层铜 → 落目标网+各重布新铜。

    rip_ops = [(ripped_net, replan_route_dict), ...]（硬门 1：每个被拆网
    必须带同批重布；replan_route 为 None 即装配失败返回 (None, 0)）。
    zones 不在 removed_spans 匹配面，天然零触碰。"""
    if any(rp is None for (_n, rp) in rip_ops):
        return None, 0
    ripped = [n for (n, _rp) in rip_ops]
    routes = ([target_route] if target_route is not None else []) \
        + [rp for (_n, rp) in rip_ops]
    candidate, spans = fb1_experiment.apply_ripup_commit(board_text, routes,
                                                         ripped)
    return candidate, len(spans)


# ---- 行结果账本（台账纯函数） ------------------------------------------------
def row_account(row_id, net, norm, removed_nodes_by_net):
    """单行求解结果 → 台账行（关闭?/拆了谁/重布长度/操作数网集）。

    removed_nodes_by_net = {net: count_net_nodes dict}（每个被拆网逐处记账）。"""
    rip_set = norm.get("ripup_set") or []
    ripped_nets = [e["net"] for e in rip_set]
    return {
        "row_id": row_id, "net": net,
        "status": "SAT" if norm["ok"] else "UNKNOWN",
        "fail": norm.get("fail"),
        "blocks_top3": norm.get("blocks", [])[:3],
        "ripped_nets": ripped_nets,
        "ripped_classes": [e["class"] for e in rip_set],
        "si_review_nets": [e["net"] for e in rip_set
                           if e.get("si_review_required")],
        "si_review_required": any(e.get("si_review_required")
                                  for e in rip_set),
        "removed_nodes": removed_nodes_by_net,
        "route_length_mm": norm.get("length_mm"),
        "replan_length_mm": {e["net"]: (e["replan"] or {}).get("length_mm")
                             for e in rip_set},
        "batch_nets": batch_nets([net], ripped_nets),
        "candidates_history": norm.get("candidates_history"),
        "ripup_trials": norm.get("ripup_trials"),
    }
