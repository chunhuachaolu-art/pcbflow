"""LIVE2B-S1：live 快照 6 目标网 WIN-1 式全窗重解（纯函数核）。

背景：RIPUP-1（out/coreboard-ripup1）对 6 目标网（SWDIO/LTDC_VSYNC/
FMC_SDNE0/VBAT/GNDA/3V3，行号 RPL-054/052/038/056/039/019）只给出
A* 不可达 + 洪泛封堵归因（heuristic），无 WIN-1 式 restricted UNSAT
证书。本模块补 LIVE2B-S1 的账本纯函数：行号钉死、失败集差集、割元素
网属直方图、与 RIPUP-1 归因的一致性对照、verdict 行装配。

合同红线（编排侧 scripts/live2s1_run.py 强制，本模块只提供纯函数）：
- 无 ripup：他网铜与目标网已落铜全部冻结障碍；全程内存 dry-run 零板写；
- 求解复用 pcbflow/win1_window（渐进窗梯 frozen_600k→corridor→board，
  UNSAT=route_grid.solve_cert 割 + verify_cert 独立复核 verified=true）；
- 扩大窗口不自动把 UNKNOWN 改判 UNSAT（win1_window 原语义）；
- 证书语义=模型化路线空间内不可布，restricted 声明逐条带。

风格对齐 win1_window.py / ripup1_campaign.py：零落盘、零子进程、无
wall-clock；落盘与驱动在编排侧。
"""

from __future__ import annotations

import json
import re

LIVE2S1_SCHEMA = "1.0"
LIVE2S1_ARTIFACT_KIND = "live2s1_window_experiment"
LIVE2S1_DATASET = "coreboard-live2b-s1"
LIVE2S1_DATE = "2026-09-11"

# 6 目标行（live 分母；行号口径=opens.csv 61 信号行 sorted(net,
# distance_mm) 序，与 RIPUP-1 / LIVE-1 gateA/gateB/gateC 权威一致；
# 漂移即中止）。
TARGETS = ["FMC_SDNE0", "GNDA", "LTDC_VSYNC", "SWDIO", "VBAT", "3V3"]
EXPECT_ROW = {"FMC_SDNE0": "RPL-038", "GNDA": "RPL-039",
              "LTDC_VSYNC": "RPL-052", "SWDIO": "RPL-054",
              "VBAT": "RPL-056", "3V3": "RPL-019"}

# live 板冻结见证（开工/收工双验；不符即停）
LIVE_BOARD_SHA_PREFIX = "8029f5ff"
# 受保护文件（cli.py 由 copper-loop 外部工作流并行改写，已登记事件，
# 本实验代码路径零依赖 cli.py，不列入钉死清单）
PROTECTED = [
    ("pcbflow/config.py", "f515c348"),
    ("toolchain_lock.json", "d43dad89"),
]

_NET_RE = re.compile(r"\[([^\[\]]+)\]")


class RowDrift(RuntimeError):
    """目标行号与权威不一致（fail-closed）。"""


# ---- 行号钉死（ripup1_orchestrate._rows_by_net 同口径纯函数化） --------------
def assign_target_rows(rows, expect_row=None):
    """opens.csv 61 信号行 → {net: row}（仅 6 目标网；含 row_id）。

    同网多断点（如 3V3×N 行）各自成行：每网取 EXPECT_ROW 钉死的特定行；
    目标网行号与权威不一致即 raise RowDrift（行漂移防护，fail-closed）。
    纯函数：rows 为 residual_cmd._read_opens_rows(bm) 形状（dict 列表）。"""
    expect = dict(EXPECT_ROW)
    if expect_row:
        expect.update(expect_row)
    ordered = sorted(rows, key=lambda r: (r["net"], r["distance_mm"]))
    by_net = {}
    for i, row in enumerate(ordered):
        rid = "RPL-%03d" % i
        net = row["net"]
        if net in expect:
            if rid == expect[net]:
                by_net[net] = dict(row, row_id=rid)
            elif net != "3V3":
                raise RowDrift("行漂移：%s → %s（期望 %s）"
                               % (net, rid, expect[net]))
    missing = [n for n in expect if n not in by_net]
    if missing:
        raise RowDrift("目标行未命中：%s（EXPECT_ROW=%s）"
                       % (missing, expect))
    return by_net


# ---- RIPUP-1 封堵归因解析（campaign-ledger blockers 口径） -------------------
def parse_blocker_nets(blocker_descs):
    """blockers_gateB/gateC 描述串列表 → 封堵网名有序去重列表。

    "[ADC_A3] 走线 (…)…" → "ADC_A3"；无 [NET] 前缀的条目忽略。"""
    nets = []
    for d in blocker_descs or []:
        m = _NET_RE.search(d or "")
        if m and m.group(1) not in nets:
            nets.append(m.group(1))
    return nets


# ---- 验收门：测试失败集差集 --------------------------------------------------
def failure_set_diff(pre_ids, post_ids):
    """开工/收工失败集（test id 列表）→ 差集账。

    gates_ok=True ⟺ 收工失败集 ⊆ 开工失败集（不新增任何失败；
    收工时新增的本实验测试必须全绿，否则 gates_ok=False）。"""
    pre, post = set(pre_ids or []), set(post_ids or [])
    return {
        "new_failures": sorted(post - pre),
        "fixed": sorted(pre - post),
        "unchanged_count": len(pre & post),
        "gates_ok": not (post - pre),
    }


# ---- UNSAT 证书割元素的网属归因（一致性对照输入） ----------------------------
def collect_prim_bboxes(obj):
    """嵌套 why 论据 → prim_bbox（round6 四元组）列表（递归）。"""
    out = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "prim_bbox" and isinstance(v, (list, tuple)) \
                    and len(v) == 4:
                out.append(tuple(round(float(x), 6) for x in v))
            else:
                out.extend(collect_prim_bboxes(v))
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            out.extend(collect_prim_bboxes(v))
    return out


def cert_net_histogram(cut_groups, bbox_to_nets):
    """cert.cut_groups + {prim_bbox: [net,…]} 索引 → 割元素网属直方图。

    归因粒度=割组（why 按组聚合）：组的论据 prim_bbox 命中索引的网各记
    len(items) 次（多网共堵同组则各记一次，直方图只作对照不作门）；
    boundary（出窗界）单独计数；其余无 prim_bbox 论据（孔/板边）计入
    other_unattributed。纯函数。"""
    hist = {}
    boundary = 0
    other = 0
    for g in cut_groups or []:
        items = len(g.get("items") or [])
        if g.get("kind") == "boundary":
            boundary += items
            continue
        nets = []
        for bb in collect_prim_bboxes(g.get("why")):
            for n in bbox_to_nets.get(bb, ()):
                if n not in nets:
                    nets.append(n)
        if nets:
            for n in nets:
                hist[n] = hist.get(n, 0) + items
        else:
            other += items
    return {"nets": dict(sorted(hist.items())),
            "boundary_cuts": boundary,
            "other_unattributed": other}


def consistency_compare(ripup1_nets, cert_nets):
    """RIPUP-1 封堵网集 vs 证书割元素网集 → 对照账（如实记录，不作门）。"""
    a, b = set(ripup1_nets or []), set(cert_nets or [])
    shared = sorted(a & b)
    if not b:
        relation = "no_cert_attribution"   # UNKNOWN 行或割论据全部无网属
    elif not a:
        relation = "no_ripup1_blockers"
    elif b <= a:
        relation = "cert_subset_of_ripup1"
    elif a <= b:
        relation = "ripup1_subset_of_cert"
    elif not shared:
        relation = "disjoint"
    else:
        relation = "overlap"
    return {"relation": relation,
            "shared": shared,
            "ripup1_only": sorted(a - b),
            "cert_only": sorted(b - a)}


# ---- restricted 声明（逐条随行） ---------------------------------------------
_BASE_DECLARATIONS = (
    "no-ripup：他网铜与目标网已落铜全部冻结障碍，全程内存 dry-run、"
    "零板写（live 板 pre/post sha256 双验）",
    "求解=pcbagent Router.route_net(ripup=False)（A*+L1 终判）+ "
    "route_grid 栅格证书模型（同一冻结语义），不触碰 cli.py",
    "证书模型内同网铜不作障碍（route_grid._PrimIndex 原生语义：同电位"
    "零间距合法；冻结=零拆除，非解锁重布）",
)


def restricted_declarations(status, cert):
    """三态 × 证书 → restricted 声明列表（逐条随 verdict 落盘）。"""
    decls = list(_BASE_DECLARATIONS)
    if status == "SAT":
        decls.append("SAT=Router witness + L1 终判全过（witness 即证据，"
                     "route_grid.route_one 内全过）")
    elif status == "UNSAT" and cert:
        s = cert.get("scope") or {}
        decls.append(
            "UNSAT 证书 restricted 作用域=%s；区域窗=%s mm；格距=%s mm；"
            "割元素=%d（cut_count）" % (s.get("model"), s.get("region_mm"),
                                       s.get("res_mm"),
                                       cert.get("cut_count", -1)))
        decls.append("证书语义=模型化路线空间内不可布（0.05mm 格心 4 邻格网"
                     "+同格位过孔+端点 8 邻辐条+区域窗内冻结铜），不等价于"
                     "全域物理不可布（SPEC §10.3 restricted blocking "
                     "certificate）")
        decls.append("证书经 route_grid.verify_cert 独立复核 verified=true"
                     "（论据数值重算 + 仅信任割条目的封闭性 BFS）")
    else:
        decls.append("UNKNOWN=无 witness 且无 verified 割（含候选通径/"
                     "区域超窗/复核失败等，原因见 unknown_reason）；扩窗"
                     "不自动改判")
    return decls


# ---- verdict 行装配（账本纯函数） --------------------------------------------
def steps_summary(steps):
    """win1 steps → 账本摘要（含割量级与跳过理由）。"""
    out = []
    for s in steps or []:
        cert = s.get("certificate") or {}
        out.append({
            "tier": s.get("tier"),
            "skipped": bool(s.get("skipped")),
            "skip_reason": s.get("skip_reason"),
            "status": s.get("status"),
            "unknown_reason": s.get("unknown_reason"),
            "window_nodes": s.get("window_nodes"),
            "margin_mm": s.get("margin_mm"),
            "cut_count": cert.get("cut_count"),
            "verified": cert.get("verified"),
        })
    return out


def verdict_row(row_id, net, win1_result, ripup1_blocker_nets,
                cert_net_hist, board_strengthen=None):
    """win1_window.run_row 结果 → LIVE2B-S1 verdict 行（纯函数）。

    board_strengthen：编排侧板级强化梯步（dict 或 None）——走廊 scope 割
    的范围强化（板级窗重解），verified=true 才升格为最终证书。"""
    res = win1_result
    cert = res.get("certificate")
    status = res["status"]
    if board_strengthen and board_strengthen.get("status") == "UNSAT":
        cert = board_strengthen.get("certificate")
    hist = cert_net_hist or {}
    row = {
        "row_id": row_id, "net": net,
        "live2s1_status": status,
        "upgrade_from": res.get("upgrade_from"),
        "unknown_reason": res.get("unknown_reason"),
        "witness": res.get("witness"),
        "router": res.get("router"),
        "ladder": res.get("ladder"),
        "steps": steps_summary(res.get("steps")),
        "board_strengthen": board_strengthen,
        "final_certificate": cert,
        "certificate_cut_count": (cert or {}).get("cut_count"),
        "certificate_scope": (cert or {}).get("scope"),
        "cert_cut_net_histogram": hist,
        "ripup1_blocker_nets": list(ripup1_blocker_nets or []),
        "ripup1_consistency": consistency_compare(ripup1_blocker_nets,
                                                  sorted((hist or {})
                                                         .get("nets",
                                                              {}))),
        "restricted_declarations": restricted_declarations(status, cert),
    }
    return row


def summary_counts(verdict_rows):
    """verdict 行列表 → {SAT/UNSAT/UNKNOWN: n}（含越界状态 fail-closed）。"""
    counts = {"SAT": 0, "UNSAT": 0, "UNKNOWN": 0}
    for r in verdict_rows:
        s = r["live2s1_status"]
        if s not in counts:
            raise RuntimeError("未知三态 %r（fail-closed）" % (s,))
        counts[s] += 1
    return counts
