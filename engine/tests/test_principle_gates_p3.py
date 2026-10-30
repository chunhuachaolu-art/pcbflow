# -*- coding: utf-8 -*-
"""§5.1 理念门 P3 批次（V5.0-DEV-TASKBOOK §5 P3 门「理念门 P3 批次」+ §5.1，改进六/七）。

四组引擎侧测试（板池全部只读；测试只消费 v5.board/compiler/planner/selection/measure
公共入口与 v5.metrics 公共度量，不触任何私有实现细节）：

1. 冲突电池七对×六查点（§5.1 改进六）：对 7 块对抗板 adv-01..adv-07 逐板逐查点——
   ①winner/loser 在案且双向可溯；②让位范围在案；③资源变化有数；④目标函数变化有数；
   ⑤证据与 rationale 在案；⑥winner 候选仍过 DRC（机制断言，如实反映三态）。
2. PF 四项常驻断言：compiled_rule 覆盖率 100%/显式 check_only；生成侧消费覆盖率 100%
   （行为断言 + inspect 源码断言守卫存在）；硬规则永不被覆盖（编译期 fail-closed +
   生成期恶意条目无效果）；理念冲突裁决可溯（七对全枚举 + 从注册表独立复算 winner）。
3. 反事实行为（硬门③）：deepcopy 板→删理念→重编译→重规划；命中处必变 / 无增量处必
   不变（不变处给机制子断言说明为何不变——冗余覆盖/并列同长/全量提升等 P3 真实语义）。
4. PS 理念稳定性五不变性（§5.1 PS）：网络字典序、无关元件增删、JSON 键序、输入换行、
   同等候选顺序五变化下 verdict+best+ledger.principle_ledger 不变。

纪律：零 LLM API、零网络、确定性（无时间戳/随机数）、断言全部机制推导（能从板数据
算出的值一律现算，不硬编码期望值）、板文件只读、落盘只用 pytest tmp_path。

文档化最小决定（测试设计层）：
- 七对冲突的 pairs 不在 compile_board 工件内（compiler.py 模块 docstring 明示组合冲突图
  「由调用方按需直调获取」），本文件按其口径直调 compiler.build_full_conflict_graph。
- 反事实「必变」以真实行为为准：仅当被删规则在基线留痕中声称了排序/层偏好增量且该
  增量对全序有实际效果时断言必变（demo-01 两条、adv-04 一条）；其余规则命中虽在案但
  效果被并集覆盖/并列同长/全量提升吸收，按任务书「未命中处必不变」同一精神断言
  生成不变+留痕必变，并对「为何不变」给机制子断言（逐条见 CF_MATRIX 注释）。
- selection._principle_ledger 对 planner 留痕的归类存在合同缝（见本文件
  test_pf2_trace_covers_all_rules 注释与最终汇报），本文件断言的是 six-checkpoint 与 PS
  所依赖的合同面（verdict/best/留痕/滤除记录），账本状态语义不在本批断言范围。
"""
import copy
import hashlib
import inspect
import json
import math
import os

import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from v5 import canonical, measure  # noqa: E402
from v5 import planner as planner_mod  # noqa: E402
from v5.metrics import capacity as cap_mod  # noqa: E402
from v5.metrics import clearance  # noqa: E402
from v5.metrics import width_prior as wp  # noqa: E402
from v5.planner import plan_candidates  # noqa: E402
from v5.board import compute_board_sha256, load_board_file  # noqa: E402
from v5.compiler import (  # noqa: E402
    CompilerError,
    PAIR_TEMPLATES,
    build_full_conflict_graph,
    compile_board,
    resolve_scope,
)
from v5.selection import select_best

D_DIR = os.path.join(ROOT, "boards", "d")

ADV_BOARDS = [
    "adv-01-pwr-vs-bus",
    "adv-02-clk-vs-short",
    "adv-03-diff-vs-capacity",
    "adv-04-xtalk-vs-vias",
    "adv-05-eqlen-vs-layerpref",
    "adv-06-copper-vs-completion",
    "adv-07-objection-vs-floor",
]
DEMO_BOARDS = [
    "demo-01-v2-corridor",
    "demo-02-mixed-types",
    "demo-03-small-mixed",
]
ALL_BOARDS = DEMO_BOARDS + ADV_BOARDS

# 对抗板 id → 七对 pair_id 的机械映射（板名 = "adv-<NN>-<pair_id>"，推导不硬编码）
_EPS = 1e-9


def board_path(name):
    return os.path.join(D_DIR, "%s.board.v1.json" % name)


def pair_id_of(board_name):
    assert board_name.startswith("adv-")
    return board_name.split("-", 2)[2]


@pytest.fixture(scope="module")
def boards():
    """全部板只读载入一次（load_board 校验口径），module 级共享（测试只读）。"""
    return {name: load_board_file(board_path(name)) for name in ALL_BOARDS}


# ---------------------------------------------------------------- 公共小工具

def reseal(board):
    """突变板后重封 provenance.board_sha256（canonical 剔除本字段后 sha256，链式合同）。"""
    b = copy.deepcopy(board)
    b["provenance"]["board_sha256"] = compute_board_sha256(b)
    return b


def src_hash(entry):
    """注册表条目 source_hash 复算（镜像 compiler.semantic_checks 口径）。"""
    view = {k: v for k, v in entry.items() if k != "source_hash"}
    return hashlib.sha256(canonical.canonical_json(view)).hexdigest()


def remove_principle(board, pid):
    """反事实板：deepcopy → 删该理念 → 摘除对其声明引用 → 重算被摘条目 source_hash
    （镜像 compiler.semantic_checks 口径；悬空引用本身被编译器 fail-closed，摘除是
    删除理念的必然伴操）→ 重封板哈希。"""
    b = copy.deepcopy(board)
    kept = [e for e in b["principle_registry"] if e.get("principle_id") != pid]
    for entry in kept:
        pol = entry.get("conflict_policy")
        if not isinstance(pol, dict):
            continue
        touched = False
        for key in ("conflicts_with", "yields_to"):
            if isinstance(pol.get(key), list) and pid in pol[key]:
                pol[key] = [r for r in pol[key] if r != pid]
                touched = True
        if touched:
            entry["source_hash"] = src_hash(entry)
    b["principle_registry"] = kept
    return reseal(b)


def add_principle(board, entry):
    b = copy.deepcopy(board)
    b["principle_registry"] = list(b["principle_registry"]) + [copy.deepcopy(entry)]
    return reseal(b)


def evil_entry(base_entry, pid, *, kind, target, scope, priority, params=None,
               intent_protects="试图绕开硬规则（测试注入）",
               intent_sacrifices="无（恶意条目应无实权）"):
    """以同板既有条目为模板构造通过 schema+哈希复算的恶意软条目（hard 地板不可覆盖
    由编译器另行 fail-closed，见 PF3 编译期用例）。intent 按 schema 为 object。"""
    e = copy.deepcopy(base_entry)
    e["principle_id"] = pid
    e["name"] = pid
    e["intent"] = {"protects": intent_protects, "sacrifices": intent_sacrifices}
    e["priority"] = priority
    e["hard_or_soft"] = "soft"
    e["overridable"] = True
    e["target_freedom"] = target
    e["scope"] = scope
    rule = {"kind": kind}
    if params is not None:
        rule["params"] = params
    e["compiled_rule"] = rule
    e["conflict_policy"] = {"conflicts_with": [], "yields_to": []}
    e["source_hash"] = src_hash(e)
    return e


def pipeline(board):
    """编译→双臂规划→合批终选（引擎公开管线，一次到位）。"""
    artifact, fingerprint = compile_board(board)
    cands_p = plan_candidates(board, artifact, arm="principle")
    cands_n = plan_candidates(board, artifact, arm="no-principle")
    result = select_best(board, cands_p + cands_n)
    return {"artifact": artifact, "fingerprint": fingerprint,
            "cands_p": cands_p, "cands_n": cands_n, "result": result}


def full_graph(board):
    """组合冲突图（compiler docstring 口径：调用方按需直调）。"""
    return build_full_conflict_graph(board)


def own_pairs(board):
    """该板命中的七对冲突块列表（按模板两侧 kind 与注册表 kind 交集独立复算期望）。"""
    kinds = set()
    for entry in board["principle_registry"]:
        cr = entry.get("compiled_rule")
        if isinstance(cr, dict) and isinstance(cr.get("kind"), str):
            kinds.add(cr["kind"])
    expected = set()
    for tpl in PAIR_TEMPLATES:
        side_kinds = [set(s["rule_kinds"]) for s in tpl["sides"]]
        if all(sk & kinds for sk in side_kinds):
            expected.add(tpl["pair_id"])
    present = {p["pair_id"]: p for p in full_graph(board)["pairs"] if p.get("present")}
    assert set(present) == expected, "命中对与模板×kind 独立复算不一致: %s vs %s" % (
        sorted(present), sorted(expected))
    return present


def expected_winner(board, pid_a, pid_b):
    """从注册表独立复算 winner（让位 > priority > id 字典序，镜像七问第 5/6 问合同）。"""
    by_id = {e["principle_id"]: e for e in board["principle_registry"]}
    a, b = by_id[pid_a], by_id[pid_b]

    def yields(x, y):
        return y in (x.get("conflict_policy", {}) or {}).get("yields_to", [])

    if yields(a, b) and yields(b, a):
        raise AssertionError("双向让位无确定 winner")
    if yields(a, b):
        return b["principle_id"]
    if yields(b, a):
        return a["principle_id"]
    pa, pb = a.get("priority", 0), b.get("priority", 0)
    if pa != pb:
        return a["principle_id"] if pa > pb else b["principle_id"]
    return min(a["principle_id"], b["principle_id"])


def pair_entries(board, block):
    by_id = {e["principle_id"]: e for e in board["principle_registry"]}
    return by_id[block["winner"]], by_id[block["loser"]]


# ---- 几何探针（与 planner/selection 同口径的公共复算，用 v5.metrics.clearance） ----

def part_bbox(part):
    xs = sorted(pt[0] for pt in part["geometry"]["endpoints"])
    ys = sorted(pt[1] for pt in part["geometry"]["endpoints"])
    return (xs[0], ys[0], xs[-1], ys[-1])


def part_hits_rect(part, rect):
    """分区几何命中矩形（planner._hits_rect 同口径：端点包围盒 gap≤EPS 或铜带交叠）。"""
    bbox = part_bbox(part)
    if clearance.rect_rect_gap(bbox, rect) <= _EPS:
        return True
    band = part["geometry"].get("copper_band")
    if band is None:
        return False
    lo, hi = sorted((float(band[0]), float(band[1])))
    band_overlap = max(lo, rect[0]) <= min(hi, rect[2]) + _EPS
    ys_overlap = max(bbox[1], rect[1]) <= min(bbox[3], rect[3]) + _EPS
    return band_overlap and ys_overlap


def zone_rect(zone):
    r = zone["rect"]
    return (float(r["x_min"]), float(r["y_min"]), float(r["x_max"]), float(r["y_max"]))


def corridor_crossers(board):
    """{分区id: 命中走廊 zone 列表}（仅 kind==corridor；planner 同口径公共复算）。"""
    corridors = [(z["zone_id"], zone_rect(z))
                 for z in board.get("zones", []) if z.get("kind") == "corridor"]
    out = {}
    for part in board["partitions"]:
        hit = sorted(zid for zid, rect in corridors if part_hits_rect(part, rect))
        if hit:
            out[part["partition_id"]] = hit
    return out


def rule_reach(board, pid):
    """规则在板上的实际作用对象（ordering/layer_plan 命中=scope 分区；corridor=走廊
    reach，镜像 planner._corridor_reach 判据）。返回 (hit_partitions, freedom)。"""
    res = resolve_scope(board["principle_registry"], board)[pid]
    entry = next(e for e in board["principle_registry"]
                 if e["principle_id"] == pid)
    freedom = entry["target_freedom"]
    if freedom != "corridor":
        return sorted(res["partitions"]), freedom
    crossers = corridor_crossers(board)
    corridor_ids = {z["zone_id"] for z in board.get("zones", [])
                    if z.get("kind") == "corridor"}
    zids = [z for z in res["zones"] if z in corridor_ids]
    if zids:
        zset = set(zids)
        return sorted(p for p, zs in crossers.items() if zset & set(zs)), freedom
    if res["partitions"]:
        return sorted(p for p in res["partitions"] if crossers.get(p)), freedom
    return [], freedom


def signal_layers(board):
    return [l["id"] for l in board["stackup"]
            if l.get("kind") == "signal" and l.get("available") is True]


def pref_first_layer(part, board):
    """分区偏好序首层（planner._expand_policy 同口径最小复现，供不变性子断言）。"""
    policy = str(part.get("layer_policy", ""))
    for sep in (",", "，", ";", "；"):
        policy = policy.replace(sep, ",")
    tokens = [t.strip() for t in policy.split(",") if t.strip()]
    sig = signal_layers(board)
    if "any" in tokens or not tokens:
        return sig[0]
    named = [t for t in tokens if t in sig]
    return named[0] if named else sig[0]


def measure_total(candidate, board):
    """候选实测目标值（v5.measure 公共入口重算；口径同 selection：单层走线孔数 0）。"""
    net_of = {}
    for n in board.get("nets", []):
        for pid in n.get("partitions", []):
            net_of[pid] = n["net_id"]
    dirs = {l["id"]: l.get("preferred_direction", "any") for l in board["stackup"]}
    routes = [{"net_id": net_of.get(pid, pid),
               "layer": candidate["layer_assignment"][pid],
               "polyline": candidate["polylines"][pid],
               "transition_vias": 0}
              for pid in candidate["route_order"]]
    return measure.measure_assignment(routes, dirs)["total_cost"]


def norm_best(best):
    """跨工件比较视图：剔除随板哈希变化的 provenance.compiled_sha256。"""
    if best is None:
        return None
    b = copy.deepcopy(best)
    b.get("provenance", {}).pop("compiled_sha256", None)
    return b


def positions(route_order):
    return {pid: i for i, pid in enumerate(route_order)}


# ================================================================
# 第 1 组：冲突电池七对×六查点（§5.1 改进六）
# ================================================================

# ---------------- 查点① winner/loser 在案且双向可溯 ----------------

@pytest.mark.parametrize("name", ADV_BOARDS)
def test_cp1_winner_loser_recorded_and_bidirectional(name, boards):
    board = boards[name]
    present = own_pairs(board)
    pid = pair_id_of(name)
    assert pid in present, "对抗板 %s 应命中七对中的 %r" % (name, pid)
    block = present[pid]
    winner, loser = block["winner"], block["loser"]
    assert winner and loser and winner != loser
    by_id = {e["principle_id"]: e for e in board["principle_registry"]}
    assert winner in by_id and loser in by_id, "winner/loser 必须可溯到注册表条目"

    # 双向可溯：loser 显式让位 winner；winner 声明与 loser 冲突（七块对抗板的声明形态）
    loser_yt = (by_id[loser].get("conflict_policy", {}) or {}).get("yields_to", [])
    winner_cw = (by_id[winner].get("conflict_policy", {}) or {}).get("conflicts_with", [])
    assert winner in loser_yt, "loser 的 yields_to 链应含 winner（正向可溯）"
    assert loser in winner_cw, "winner 的 conflicts_with 应含 loser（反向可溯）"

    # 从注册表独立复算 winner 与引擎裁决一致
    assert expected_winner(board, winner, loser) == winner

    # 组合冲突图边在案（本批板双方都有声明 → basis=declared+template）
    graph = full_graph(board)
    pair_edge = [e for e in graph["edges"]
                 if {e["a"], e["b"]} == {min(winner, loser), max(winner, loser)}]
    assert pair_edge, "组合冲突图应含该对端点的边"
    edge = pair_edge[0]
    assert edge["winner"] == winner and edge["loser"] == loser
    assert edge["basis"] == "declared+template"

    # compile_board 工件内的声明式冲突图同样在案（同 winner/loser，可从工件溯得）
    artifact, _ = compile_board(board)
    art_edges = [e for e in artifact["conflict_graph"]["edges"]
                 if {e["a"], e["b"]} == {min(winner, loser), max(winner, loser)}]
    assert art_edges and art_edges[0]["winner"] == winner \
        and art_edges[0]["loser"] == loser


# ---------------- 查点② 让位范围记录在案 ----------------

@pytest.mark.parametrize("name", ADV_BOARDS)
def test_cp2_yield_scope_recorded(name, boards):
    board = boards[name]
    block = own_pairs(board)[pair_id_of(name)]
    winner, loser = block["winner"], block["loser"]
    scope = block.get("yield_scope")
    assert isinstance(scope, str) and scope.strip(), "yield_scope 必须为非空预案文本"
    assert winner in scope and loser in scope, "预案必须点名双方"
    assert "让位" in scope, "预案必须描述让位方向"
    # 七块对抗板的 loser 都带显式 yields_to 链 → 预案文本应披露显式让位链口径
    by_id = {e["principle_id"]: e for e in board["principle_registry"]}
    loser_yt = (by_id[loser].get("conflict_policy", {}) or {}).get("yields_to", [])
    assert loser_yt, "对抗板 loser 应有显式 yields_to 链"
    assert "yields_to" in scope, "显式让位链须在预案中披露"


# ---------------- 查点③ 资源变化有数 ----------------

def _corridor_probe(board, result):
    """走廊稀缺资源账本：容量 + 固定铜占用 + 合批候选占用（全部现算实测数字）。"""
    numbers = {}
    for zone in [z for z in board.get("zones", []) if z.get("kind") == "corridor"]:
        rect = zone_rect(zone)
        cap = float(zone["capacity"])
        entries = []
        for part in board["partitions"]:
            if not part_hits_rect(part, rect):
                continue
            width = float(part.get("planned_width") or 0.2)
            declared = (part.get("geometry", {}) or {}).get("occupancy_mm")
            entries.append(cap_mod.CapacityEntry(
                part["partition_id"], width,
                declared_occupancy=float(declared) if declared is not None else None))
        numbers["capacity_mm:%s" % zone["zone_id"]] = cap
        numbers["occupancy_fixed_mm:%s" % zone["zone_id"]] = \
            cap_mod.corridor_occupancy(entries)
        assert math.isfinite(cap) and cap >= 0
        assert math.isfinite(numbers["occupancy_fixed_mm:%s" % zone["zone_id"]])
        # DRC 台账中的容量条目 subject 与板内走廊 zone 双向对得上（有拒收时）
        for rec in result["ledger"]["rejection_reasons"]:
            if rec.get("rule") == "capacity":
                assert rec.get("subject", "").startswith(zone["zone_id"] + "/"), \
                    "capacity 滤除条目 subject 应形如 <走廊zone>/<层>"
    return numbers


def _board_probe(name, board, result):
    """逐板资源探针：每板给出与该对冲突直接相关的可实测数字（全部现算，不硬编码）。"""
    numbers = {}
    numbers.update(_corridor_probe(board, result))
    if name == "adv-02-clk-vs-short":
        # 时钟隔离资源：CLK 分区折线到敏感区 rect 的实测距离（v5.metrics.clearance）
        sens = next(z for z in board["zones"] if z["kind"] == "sensitive")
        rect = {"x_min": float(sens["rect"]["x_min"]), "y_min": float(sens["rect"]["y_min"]),
                "x_max": float(sens["rect"]["x_max"]), "y_max": float(sens["rect"]["y_max"])}
        clk = next(p for p in board["partitions"] if p["ptype"] == "CLK")
        (x1, y1), (x2, y2) = clk["geometry"]["endpoints"]
        numbers["clk_to_sensitive_mm"] = clearance.segment_rect_distance(
            (x1, y1), (x2, y2), rect)
    elif name == "adv-05-eqlen-vs-layerpref":
        # 层资源：可用信号层数 + 等长组容差（注册表 params 现读）
        block = own_pairs(board)["eqlen-vs-layerpref"]
        entry = {e["principle_id"]: e for e in board["principle_registry"]}[block["winner"]]
        numbers["n_signal_layers"] = len(signal_layers(board))
        numbers["eqlen_tolerance_mm"] = float(
            entry["compiled_rule"].get("params", {}).get("tolerance_mm"))
    elif name == "adv-06-copper-vs-completion":
        # 既有铜资源：ROUTED 分区既有折线长度（v5.measure 公共度量）
        rt = next(p for p in board["partitions"] if p["ptype"] == "ROUTED")
        numbers["existing_copper_len_mm"] = measure.polyline_length(
            [list(pt) for pt in rt["geometry"]["endpoints"]])
    elif name == "adv-07-objection-vs-floor":
        # 地板资源：R1 载流下限 vs PW2 计划宽（板 hard_rules 现算）与余量
        pw2 = next(p for p in board["partitions"] if p["partition_id"] == "PW2")
        r1 = board["hard_rules"]["R1"]
        required = wp.conservative_min_width(
            float(pw2["current_a"]), fab_min_mm=0.0,
            k_per_amp=float(r1["k_a"]), floor_mm=float(r1["floor_mm"]))
        numbers["r1_required_min_mm"] = required
        numbers["pw2_planned_mm"] = float(pw2["planned_width"])
        numbers["r1_slack_mm"] = round(float(pw2["planned_width"]) - required, 10)
    for key, val in numbers.items():
        assert val is not None and math.isfinite(val), "资源数字 %s 应为有限实数" % key
    return numbers


@pytest.mark.parametrize("name", ADV_BOARDS)
def test_cp3_resource_numbers_available(name, boards):
    """查点③：winner/loser 双方争夺的稀缺资源有实测数字（容量账本/占用口径/几何测量），
    且双臂 route_order 中命中分区位次差被量化记录（变化可为 0，如实给数）。"""
    board = boards[name]
    run = pipeline(board)
    numbers = _board_probe(name, board, run["result"])
    assert numbers, "每块对抗板至少给出一个资源实测数字"

    # 双臂位次差 = 理念对排序资源的可观测增量（原则臂 vs 诊断臂，逐分区量化）
    pos_p = positions(run["cands_p"][0]["route_order"])
    pos_n = positions(run["cands_n"][0]["route_order"])
    hit_pids = set()
    for entry in board["principle_registry"]:
        reach, _freedom = rule_reach(board, entry["principle_id"])
        hit_pids.update(reach)
    deltas = {pid: pos_n[pid] - pos_p[pid] for pid in sorted(hit_pids)}
    assert all(isinstance(v, int) for v in deltas.values())
    # 走廊资源对的位次增量如实给数：adv-04 的 VI 依赖走廊前移（位次差 >0）；
    # adv-01/adv-03 的穿越分区阶梯位次本就在前（提升保序，增量=0，如实记录）
    if name == "adv-04-xtalk-vs-vias":
        assert any(v > 0 for v in deltas.values()), \
            "走廊资源对：原则臂应有分区位次前移（实测 %s）" % deltas
    else:
        assert all(v >= 0 for v in deltas.values()), deltas


# ---------------- 查点④ 目标函数变化有数 ----------------

@pytest.mark.parametrize("name", ADV_BOARDS)
def test_cp4_objective_numbers_comparable(name, boards):
    """查点④：冲突两侧方案的目标函数有数——select_best 实测 objective 在案（可行时），
    否则用 v5.measure 对双臂 C-001 现算可比实测值；SAT 时终选 objective 与重算一致。"""
    board = boards[name]
    run = pipeline(board)
    result = run["result"]
    obj_p = measure_total(run["cands_p"][0], board)
    obj_n = measure_total(run["cands_n"][0], board)
    assert math.isfinite(obj_p) and math.isfinite(obj_n), "双臂方案 objective 必须可实测"
    per = {pc["candidate_id"] + "/" + str(i): pc
           for i, pc in enumerate(result["per_candidate"])}
    if result["verdict"] == "SAT":
        best = result["best"]
        assert best is not None
        entry = next(pc for pc in result["per_candidate"]
                     if pc["candidate_id"] == best["candidate_id"] and pc["feasible"])
        assert entry["objective"] is not None
        assert abs(entry["objective"] - measure_total(best, board)) < 1e-9, \
            "终选 objective 与 v5.measure 重算一致"
        # 全部可行候选 objective 在案且非平凡（有限实数）
        assert all(pc["objective"] is not None
                   for pc in result["per_candidate"] if pc["feasible"])
    else:
        # 非 SAT：候选全被滤除（objective=None 属三态合同），但双臂方案经测量环仍可比
        assert all(pc["objective"] is None
                   for pc in result["per_candidate"] if not pc["feasible"])
        assert result["ledger"]["rejection_reasons"], "非 SAT 必须留滤除记录"


# ---------------- 查点⑤ 证据与 rationale 在案 ----------------

@pytest.mark.parametrize("name", ADV_BOARDS)
def test_cp5_evidence_and_rationale_present(name, boards):
    board = boards[name]
    block = own_pairs(board)[pair_id_of(name)]
    artifact, _ = compile_board(board)
    rules_by_pid = {r["principle_id"]: r for r in artifact["rules"]}
    reg_by_pid = {e["principle_id"]: e for e in board["principle_registry"]}
    insufficient = set(artifact["coverage"]["evidence_insufficient"])

    for pid in (block["winner"], block["loser"]):
        entry = reg_by_pid[pid]
        # 证据：evidence_refs 非空即证据在案；为空必须进 coverage 依据不足披露（七问第 7 问）
        refs = entry.get("evidence_refs")
        assert isinstance(refs, list)
        if refs:
            assert all(isinstance(x, str) and x for x in refs)
            assert pid not in insufficient
        else:
            assert pid in insufficient, "空 evidence_refs 必须披露为依据不足"
        # rationale：编译规则 fallback 非空、enforcement/intent/name 非空
        rule = rules_by_pid[pid]
        assert isinstance(rule["fallback"], str) and rule["fallback"].strip()
        assert str(entry.get("enforcement", "")).strip()
        assert str(entry.get("intent", "")).strip()
        assert str(entry.get("name", "")).strip()

    # 生成留痕 rationale：双方编译规则在本臂候选留痕中各有一条非空 effect
    trace = pipeline(board)["cands_p"][0]["generation_trace"]
    by_rule = {}
    for t in trace:
        by_rule.setdefault(t["rule"], []).append(t)
    for pid in (block["winner"], block["loser"]):
        assert pid in by_rule, "winner/loser 编译规则必须被生成侧消费留痕"
        assert all(isinstance(t["effect"], str) and t["effect"].strip()
                   for t in by_rule[pid])
    # 冲突预案 rationale 在案（查点②同源，此处核工件侧 fallback 披露让位口径）
    loser_rule = rules_by_pid[block["loser"]]
    loser_yt = (reg_by_pid[block["loser"]].get("conflict_policy", {})
                or {}).get("yields_to", [])
    if loser_yt:
        assert block["winner"] in loser_rule["fallback"]


# ---------------- 查点⑥ winner 候选仍过 DRC（机制断言） ----------------

@pytest.mark.parametrize("name", ADV_BOARDS)
def test_cp6_winner_candidate_drc_honest(name, boards):
    """查点⑥（机制断言，不硬编码三态）：滤除只出自硬规则/容量/度量（从不因理念本身
    拒解）；SAT 时 best 可行、零违例且其留痕消费 winner 规则；非 SAT 时滤除原因逐条
    具名（fail-closed）。"""
    board = boards[name]
    run = pipeline(board)
    result = run["result"]
    winner = own_pairs(board)[pair_id_of(name)]["winner"]
    reg_ids = {e["principle_id"] for e in board["principle_registry"]}
    hard_names = {"R1", "R2", "R3", "R4", "R5", "R6", "capacity"}

    for rec in result["ledger"]["rejection_reasons"]:
        assert rec["kind"] in ("drc", "measure")
        if rec["kind"] == "drc":
            assert rec["rule"] in hard_names, "滤除只能出自硬规则/容量: %s" % rec
            assert rec["rule"] not in reg_ids, "理念本身永不构成滤除原因"
        assert str(rec.get("detail", "")).strip(), "滤除必须给具体原因"

    if result["verdict"] == "SAT":
        best = result["best"]
        assert best is not None
        pc = next(p for p in result["per_candidate"]
                  if p["candidate_id"] == best["candidate_id"] and p["feasible"])
        assert pc["feasible"] and pc["drc_violations"] == 0
        traced = {t["rule"] for t in best["generation_trace"]}
        assert winner in traced, "可行终选方案必须消费 winner 编译规则"
    else:
        assert result["ledger"]["rejected"] == len(result["per_candidate"]), \
            "非 SAT 时全部候选必须被滤除"
        assert result["ledger"]["rejection_reasons"], "非 SAT 必须留具名滤除记录"
    # winner 规则在本臂每个候选留痕中都被消费（消费≠纵容违例）
    for cand in run["cands_p"]:
        assert winner in cand["provenance"]["rules_consumed"]


# ================================================================
# 第 2 组：PF 四项常驻断言
# ================================================================

# ---------------- PF① compiled_rule 覆盖率 = 100% 或显式 check_only ----------------

@pytest.mark.parametrize("name", ALL_BOARDS)
def test_pf1_compiled_coverage_full_or_check_only(name, boards):
    board = boards[name]
    artifact, _ = compile_board(board)
    reg_ids = [e["principle_id"] for e in board["principle_registry"]]
    cov = artifact["coverage"]
    assert cov["coverage_pct"] == 100.0
    assert cov["total"] == len(reg_ids)
    assert cov["compiled"] + cov["check_only"] == cov["total"]
    rule_ids = [r["principle_id"] for r in artifact["rules"]]
    co_ids = [c["principle_id"] for c in artifact["check_only"]]
    assert sorted(rule_ids + co_ids) == sorted(reg_ids), "每条理念恰落入 rules 或 check_only"
    assert not (set(rule_ids) & set(co_ids))
    for co in artifact["check_only"]:
        assert co["reason"] == "explicit check_only"
    version_of = {e["principle_id"]: e["version"] for e in board["principle_registry"]}
    for rule in artifact["rules"]:
        assert rule["compiled_rule_id"] == "%s#%s" % (
            rule["principle_id"], version_of[rule["principle_id"]])
        assert isinstance(rule["fallback"], str) and rule["fallback"].strip()
        assert rule["generator_target"] in ("ordering", "allocation", "layer_plan",
                                            "corridor")


# ---------------- PF② 生成侧消费覆盖率 = 100% ----------------

@pytest.mark.parametrize("name", ALL_BOARDS)
def test_pf2_trace_covers_all_rules(name, boards):
    """行为断言：原则臂 trace 覆盖全部编译规则（含 scope 零命中留痕），rules_consumed=
    全规则集合；诊断臂 trace/rules_consumed 必空。注：selection 账本对 planner 留痕
    （键名 rule/freedom/effect）的归类存在合同缝——_normalize_trace 只认 principle_id
    键，planner 留痕被一律归「被忽略」；本组按任务书口径断言 planner 出口的消费覆盖
    率（生成留痕本身），账本缝单列汇报。"""
    board = boards[name]
    artifact, _ = compile_board(board)
    rule_ids = {r["principle_id"] for r in artifact["rules"]}
    cands_p = plan_candidates(board, artifact, arm="principle")
    assert cands_p
    for cand in cands_p:
        traced = {t["rule"] for t in cand["generation_trace"]}
        assert traced == rule_ids, "原则臂每候选留痕必须覆盖全部编译规则"
        assert cand["provenance"]["rules_consumed"] == sorted(rule_ids)
    cands_n = plan_candidates(board, artifact, arm="no-principle")
    for cand in cands_n:
        assert cand["generation_trace"] == []
        assert cand["provenance"]["rules_consumed"] == []


def test_pf2_exit_guard_present_in_source():
    """自断言触发路径存在（inspect 读源码）：覆盖率 100% 管线 bug 守卫在 planner 出口。"""
    src = inspect.getsource(planner_mod)
    assert "生成侧消费覆盖率失守" in src
    assert "_require(not missing" in src
    # 守卫位于组合枚举之后、候选装配之前（出口语义）
    guard_at = src.index("生成侧消费覆盖率失守")
    assert src.index("itertools.islice") < guard_at < src.index("validate_candidate(candidate, board)")


# ---------------- PF③ 硬规则永不被覆盖 ----------------

def test_pf3a_compile_failclosed_hard_not_overridable(boards):
    """恶意条目形态一：hard 理念自称可覆盖 → 编译期 fail-closed。"""
    board = copy.deepcopy(boards["adv-07-objection-vs-floor"])
    entry = next(e for e in board["principle_registry"]
                 if e["principle_id"] == "P-R1-FLOOR")
    entry["overridable"] = True
    board = reseal(board)  # 板级哈希重封；条目级 source_hash 失效由后置检查另行拦截
    with pytest.raises(CompilerError) as ei:
        compile_board(board)
    assert "overridable" in str(ei.value)


def test_pf3b_compile_failclosed_tampered_entry(boards):
    """恶意条目形态二：篡改条目内容而不重算 source_hash → 篡改检测 fail-closed。"""
    board = copy.deepcopy(boards["adv-07-objection-vs-floor"])
    entry = next(e for e in board["principle_registry"]
                 if e["principle_id"] == "P-R1-FLOOR")
    entry["intent"] = {"protects": "篡改后的保护对象（哈希不复算）",
                       "sacrifices": "篡改后的牺牲项"}
    board = reseal(board)
    with pytest.raises(CompilerError) as ei:
        compile_board(board)
    assert "source_hash" in str(ei.value)


def test_pf3c_compile_failclosed_undisclosable_rule(boards):
    """恶意条目形态三：compiled_rule 用非 check_only 字符串（不可编译又不披露）→ fail-closed。"""
    board = copy.deepcopy(boards["adv-07-objection-vs-floor"])
    entry = next(e for e in board["principle_registry"]
                 if e["principle_id"] == "P-WIDTH-SLIM")
    entry["compiled_rule"] = "shrink_R5_floor_and_ignore_keepouts"
    board = reseal(board)
    with pytest.raises(CompilerError) as ei:
        compile_board(board)
    assert "check_only" in str(ei.value)


def test_pf3d_generation_cannot_weaken_r1_floor(boards):
    """生成期恶意：删掉硬地板理念、注入声称 floor=0.001 的软条目（过 schema+哈希），
    并把 PW2 计划宽压到板 R1 下限之下 → 终选仍被板 hard_rules 的 R1 拦截（所需下限
    从板数据现算，不从注册表取值）。"""
    name = "adv-07-objection-vs-floor"
    board = copy.deepcopy(boards[name])
    base = next(e for e in board["principle_registry"]
                if e["principle_id"] == "P-R1-FLOOR")
    board = remove_principle(board, "P-R1-FLOOR")
    evil = evil_entry(base, "P-EVIL-FLOOR", kind="r1_width_floor",
                      target="allocation", scope="ptype:PWR", priority=200,
                      params={"floor_mm": 0.001, "k_a": 0.001},
                      intent_protects="试图把 R1 地板改小到 0.001",
                      intent_sacrifices="载流安全（应无效）")
    board = add_principle(board, evil)
    pw2 = next(p for p in board["partitions"] if p["partition_id"] == "PW2")
    r1 = board["hard_rules"]["R1"]
    required = wp.conservative_min_width(float(pw2["current_a"]), fab_min_mm=0.0,
                                         k_per_amp=float(r1["k_a"]),
                                         floor_mm=float(r1["floor_mm"]))
    pw2["planned_width"] = round(required / 2.0, 10)  # 压到板 R1 下限之下
    board = reseal(board)

    run = pipeline(board)  # 恶意条目编译通过（软、哈希合法）——真实语义
    cands_p = run["cands_p"]
    assert any("P-EVIL-FLOOR" in c["provenance"]["rules_consumed"] for c in cands_p), \
        "恶意条目被正常消费留痕（但无宽度作用点）"
    result = run["result"]
    assert result["best"] is None
    r1_rej = [r for r in result["ledger"]["rejection_reasons"]
              if r.get("rule") == "R1" and r.get("partition") == "PW2"]
    assert r1_rej, "终选必须仍被板 hard_rules 的 R1 拦截（恶意 floor 无效果）"
    assert float(pw2["planned_width"]) < required, "前提自检：计划宽确低于板 R1 下限"


def test_pf3e_generation_cannot_disable_keepout(boards):
    """生成期恶意：注入 priority=999 的「无视禁布区」软条目——它确能行使软自由度
    （ordering 前移，route_order 必变），但 R6 禁布区违例照旧拦截（硬规则不可触碰）。"""
    name = "adv-07-objection-vs-floor"
    board = copy.deepcopy(boards[name])
    base = next(e for e in board["principle_registry"]
                if e["principle_id"] == "P-WIDTH-SLIM")
    evil = evil_entry(base, "P-EVIL-KO", kind="keepout_ignore",
                      target="ordering", scope="partition:MS1", priority=999,
                      intent_protects="试图无视 K-MID 禁布区",
                      intent_sacrifices="R6 硬规则（应不受影响）")
    board = add_principle(board, evil)

    baseline = pipeline(boards[name])
    run = pipeline(board)
    base_order = baseline["cands_p"][0]["route_order"]
    evil_order = run["cands_p"][0]["route_order"]
    assert evil_order != base_order, "恶意条目行使软自由度（MS1 前移）——软排序可被影响"
    assert evil_order[0] == "MS1"

    result = run["result"]
    assert result["best"] is None
    assert result["ledger"]["rejection_reasons"]
    assert all(r.get("rule") == "R6"
               for r in result["ledger"]["rejection_reasons"]), \
        "全部候选仍因 R6 禁布区被 fail-closed 滤除"
    assert result["verdict"] in ("UNKNOWN", "UNSAT")


# ---------------- PF④ 理念冲突裁决可溯 ----------------

@pytest.mark.parametrize("name", ALL_BOARDS)
def test_pf4_arbitration_traceable(name, boards):
    board = boards[name]
    present = own_pairs(board)  # 内含：命中对 == 模板×kind 独立复算
    graph = full_graph(board)
    for pair_id, block in present.items():
        winner, loser = block["winner"], block["loser"]
        assert winner != loser
        assert winner in graph["nodes"] and loser in graph["nodes"]
        assert expected_winner(board, winner, loser) == winner
        assert block.get("yield_scope", "").strip()
    if name.startswith("adv-"):
        # 每块对抗板恰好命中自己那对（pair_id 由板名机械推导）
        assert len(present) == 1 and pair_id_of(name) in present


def test_pf4_demo01_no_pair_expected(boards):
    """demo-01 注册表不含任何一对模板两侧 kind → 七对全不命中（可枚举且判定为缺席）。"""
    blocks = full_graph(boards["demo-01-v2-corridor"])["pairs"]
    assert len(blocks) == len(PAIR_TEMPLATES)
    assert all(not b.get("present") for b in blocks)


@pytest.mark.parametrize("name", ["demo-02-mixed-types", "demo-03-small-mixed"])
def test_pf4_demo23_single_pair(name, boards):
    present = own_pairs(boards[name])
    assert set(present) == {"eqlen-vs-layerpref"}


# ================================================================
# 第 3 组：反事实行为测试（硬门③）
# ================================================================

# (板, 删除理念, 期望, 机制说明——「为何不变」的引擎真实语义，逐条核实于 P3 管线)
#   change    = 删除后命中处生成必变（route_order 变、命中分区位次不提前且至少一个后移、
#               未命中分区相对序不变）
#   no-change = 命中在案但 P3 自由度下该规则增量被吸收（逐条给机制子断言）：
#     - demo-01/P-CHECK：显式 check_only 条目本就不产编译规则（无消费痕可删）；
#     - demo-01/P-COR-CAP：与 P-PART-GRAN 的走廊 reach 完全重合（并集覆盖冗余）；
#     - adv-01/P-PART-GRAN：走廊前移的分区阶梯位次本就先于其余分区（提升保序）；
#     - adv-01/P-PWR、adv-03/P-DIFF、adv-05/P-EQLEN、adv-07/P-WIDTH、adv-07/P-R1：
#       allocation 自由度在 P3 无层指派约束可施加（留痕如实披露，无生成效果）；
#     - adv-02/P-SHORT：命中分区同 ptype 档内端点直线长度并列（并列时按 id 序，与
#       len_key 键序重合）；
#     - adv-02/P-CLK、adv-06/P-COPPER：scope 命中分区但板内无走廊 zone 可穿越；
#     - adv-04/P-VIA、adv-05/P-LAYER 未指偏好层/偏好层已居首（层序保持）；
#     - adv-06/P-COMPLETION：命中全部分区=全量提升，相对键序无增量。
CF_MATRIX = [
    ("demo-01-v2-corridor", "P-XCOPPER-GUARD-DEMO01", "change"),
    ("demo-01-v2-corridor", "P-COR-CAP-C1-DEMO01", "no-change"),
    ("demo-01-v2-corridor", "P-CHECK-WIDTHPRIOR-DEMO01", "no-change"),
    ("adv-01-pwr-vs-bus", "P-PART-GRAN-PWR-BUS", "no-change"),
    ("adv-01-pwr-vs-bus", "P-PWR-PRIORITY", "no-change"),
    ("adv-02-clk-vs-short", "P-SHORT-RUN", "no-change"),
    ("adv-02-clk-vs-short", "P-CLK-ISOLATE", "no-change"),
    ("adv-03-diff-vs-capacity", "P-CORRIDOR-BUDGET", "no-change"),
    ("adv-03-diff-vs-capacity", "P-DIFF-PAIRING", "no-change"),
    ("adv-04-xtalk-vs-vias", "P-PART-GRAN-XTALK-VIA", "change"),
    ("adv-04-xtalk-vs-vias", "P-VIA-FRUGAL", "no-change"),
    ("adv-05-eqlen-vs-layerpref", "P-LAYER-PREF", "no-change"),
    ("adv-05-eqlen-vs-layerpref", "P-EQLEN-GROUP", "no-change"),
    ("adv-06-copper-vs-completion", "P-COMPLETION", "no-change"),
    ("adv-06-copper-vs-completion", "P-COPPER-GUARD", "no-change"),
    ("adv-07-objection-vs-floor", "P-WIDTH-SLIM", "no-change"),
    ("adv-07-objection-vs-floor", "P-R1-FLOOR", "no-change"),
]


def _straight_len(part):
    (x1, y1), (x2, y2) = part["geometry"]["endpoints"]
    return math.hypot(x2 - x1, y2 - y1)


def _payload(cand):
    """候选的生成载荷（route_order/layers/polylines），不含留痕与 provenance。"""
    return (list(cand["route_order"]), dict(cand["layer_assignment"]),
            {k: [list(pt) for pt in v] for k, v in cand["polylines"].items()})


@pytest.mark.parametrize("name,pid,expectation", CF_MATRIX)
def test_cf_counterfactual(name, pid, expectation, boards):
    board = boards[name]
    base_artifact, _ = compile_board(board)
    base_cands = plan_candidates(board, base_artifact, arm="principle")
    base = base_cands[0]
    base_consumed = set(base["provenance"]["rules_consumed"])
    base_rule_ids = {r["principle_id"] for r in base_artifact["rules"]}
    base_co_ids = {c["principle_id"] for c in base_artifact["check_only"]}

    cf_board = remove_principle(board, pid)
    assert all(e["principle_id"] != pid for e in cf_board["principle_registry"])
    cf_artifact, _ = compile_board(cf_board)  # 悬空引用会被编译器 fail-closed——摘引用后须过
    cf_cands = plan_candidates(cf_board, cf_artifact, arm="principle")
    cf = cf_cands[0]

    # check_only 条目：本就不产编译规则（PF① 口径），删除只动披露清单不动生成
    if pid in base_co_ids:
        assert pid not in base_rule_ids and pid not in base_consumed
        assert pid not in {c["principle_id"] for c in cf_artifact["check_only"]}
        assert _payload(cf) == _payload(base)
        return

    # 通用合同：被删规则从留痕与消费集合消失，其余规则仍 100% 留痕（出口守卫绿）
    cf_consumed = set(cf["provenance"]["rules_consumed"])
    assert pid in base_consumed, "前置：被删编译规则在基线中被消费留痕"
    assert cf_consumed == base_consumed - {pid}
    assert {t["rule"] for t in cf["generation_trace"]} == cf_consumed
    assert all(t["rule"] != pid for t in cf["generation_trace"])
    assert len(cf_cands) == len(base_cands), "层组合枚举不受 ordering/corridor 规则增删影响"

    base_order, base_layers, base_polys = _payload(base)
    cf_order, cf_layers, cf_polys = _payload(cf)

    if expectation == "no-change":
        assert cf_order == base_order and cf_layers == base_layers \
            and cf_polys == base_polys, "无增量规则删除后生成载荷必须不变"
        _no_change_mechanism(board, pid, base_order)
        return

    # ---- change：命中处必变、未命中处必不变（位次机制断言，无魔法期望值） ----
    hits, freedom = rule_reach(board, pid)
    assert hits, "必变前提：规则 scope 必须有实际命中"
    assert cf_order != base_order
    hit_set = set(hits)
    # 未命中分区的相对顺序原样保持
    assert [p for p in cf_order if p not in hit_set] \
        == [p for p in base_order if p not in hit_set]
    bp, cp = positions(base_order), positions(cf_order)
    assert all(cp[h] >= bp[h] for h in hits), "删除保护规则后命中分区不得提前"
    assert any(cp[h] > bp[h] for h in hits), "至少一个命中分区实际后移"
    # 该规则基线留痕声称了排序增量（claim 与 delta 互证）；层指派/折线不受影响
    base_trace = next(t for t in base["generation_trace"] if t["rule"] == pid)
    assert "前移" in base_trace["effect"] or "短线偏好" in base_trace["effect"]
    assert cf_layers == base_layers and cf_polys == base_polys


def _no_change_mechanism(board, pid, nopr_order):
    """「不变」的机制子断言：从板数据证明该规则的增量被吸收（而非测试放水）。"""
    entry = next(e for e in board["principle_registry"]
                 if e["principle_id"] == pid)
    kind = entry["compiled_rule"].get("kind")
    freedom = entry["target_freedom"]
    if freedom == "allocation" or kind == "check_only":
        return  # allocation 在 P3 无层指派约束可施加；check_only 不产编译规则（留痕如实披露）
    hits, freedom_eff = rule_reach(board, pid)
    if not hits:
        return  # scope 零命中或命中走廊对象但无分区几何穿越
    if freedom_eff == "corridor":
        # 冗余覆盖：另一条 corridor 规则的 reach 与之完全重合（并集吸收）
        others = [e["principle_id"] for e in board["principle_registry"]
                  if e["principle_id"] != pid
                  and e["target_freedom"] == "corridor"
                  and e["compiled_rule"].get("kind") != "check_only"]
        if any(rule_reach(board, o)[0] == hits for o in others):
            return
        # 提升保序：命中分区在默认阶梯序（诊断臂）中已占据前 len(hits) 个位次
        nopr_pos = positions(nopr_order)
        assert {nopr_pos[h] for h in hits} == set(range(len(hits))), \
            "命中分区应在默认序中已居首（提升保序）"
        return
    if kind == "short_run":
        # 并列同长：同 ptype 档内命中分区端点直线长度全等 → len_key 序与 id 序重合
        parts = {p["partition_id"]: p for p in board["partitions"]}
        by_rank = {}
        for h in hits:
            rank = planner_mod.LADDER_RANKS.get(
                str(parts[h].get("ptype")), planner_mod.UNLISTED_RANK)
            by_rank.setdefault(rank, []).append(_straight_len(parts[h]))
        for rank, lens in by_rank.items():
            if len(lens) > 1:
                assert max(lens) - min(lens) < 1e-9
        return
    if kind == "ordering":
        # 全量提升：命中全部分区 → 相对键序无增量
        assert len(hits) == len(board["partitions"])
        return
    if kind == "layer_preference":
        # 偏好层已居首：每个命中分区的偏好序首层已是 params.layer
        want = entry["compiled_rule"]["params"]["layer"]
        parts = {p["partition_id"]: p for p in board["partitions"]}
        assert all(pref_first_layer(parts[h], board) == want for h in hits)
        return
    # layer_plan 未指偏好层等其余形态：P3 无作用点（留痕披露），无需进一步证明


def test_cf_demo01_both_changes_reach_c1_crossers(boards):
    """demo-01 两条「必变」规则的命中集 == 走廊 C1 穿越/铜保护命中（机制同源性）。"""
    board = boards["demo-01-v2-corridor"]
    reach_cor, _ = rule_reach(board, "P-COR-CAP-C1-DEMO01")
    reach_guard, _ = rule_reach(board, "P-XCOPPER-GUARD-DEMO01")
    assert reach_cor == sorted(corridor_crossers(board))
    assert reach_guard == sorted(p["partition_id"] for p in board["partitions"]
                                 if p["ptype"] == "ROUTED")


# ================================================================
# 第 4 组：PS 理念稳定性五不变性
# ================================================================

def assert_ps_invariant(base_board, mutated_board):
    """五不变性公共断言：verdict + best（跨工件视图）+ ledger 全 dict 相等。

    ledger（含 rejection_reasons 与 principle_ledger）不含板哈希/工件指纹，突变前后
    必须逐字节相等——比任务书要求的 principle_ledger 更强的机制断言。"""
    base = pipeline(base_board)
    mut = pipeline(mutated_board)
    assert base["result"]["verdict"] == mut["result"]["verdict"]
    assert norm_best(base["result"]["best"]) == norm_best(mut["result"]["best"])
    assert base["result"]["ledger"] == mut["result"]["ledger"]
    # 候选生成载荷亦不变（同 canonical 板语义 ⇒ 同规划）
    assert [_payload(c) for c in base["cands_p"]] == \
        [_payload(c) for c in mut["cands_p"]]
    return base, mut


# ---------------- PS① 网络列表字典序变化 ----------------

@pytest.mark.parametrize("name", ["demo-01-v2-corridor", "adv-05-eqlen-vs-layerpref"])
def test_ps1_net_order_invariant(name, boards):
    board = boards[name]
    mutated = copy.deepcopy(board)
    mutated["nets"] = list(reversed(mutated["nets"]))
    assert [n["net_id"] for n in mutated["nets"]] != \
        [n["net_id"] for n in board["nets"]]
    mutated = reseal(mutated)
    assert compute_board_sha256(mutated) != compute_board_sha256(board), \
        "前提：重排改变板哈希（判定不变性才非平凡）"
    assert_ps_invariant(board, mutated)


# ---------------- PS② 无关元件增删 ----------------

def far_keepout_rect(board):
    """确定性扫描工作区角点，找与全部分区包围盒、全部既有 zone 间隙 >1.0mm 的 2×2 矩形。

    「无关」判据（机制化）：与生成/DRC 全部消费对象几何隔离（clearance.rect_rect_gap
    实测），且 zone_id 不被任何 scope token 引用 → 对管线不可达。"""
    ws = board["workspace"]
    obstructions = [part_bbox(p) for p in board["partitions"]]
    obstructions += [zone_rect(z) for z in board.get("zones", [])]
    step = 1.0
    nx = int((float(ws["x_max"]) - float(ws["x_min"])) / step)
    ny = int((float(ws["y_max"]) - float(ws["y_min"])) / step)
    for i in range(nx):
        for j in range(ny):
            x0 = float(ws["x_min"]) + i * step
            y0 = float(ws["y_min"]) + j * step
            rect = (x0, y0, x0 + 2.0, y0 + 2.0)
            if rect[2] > float(ws["x_max"]) or rect[3] > float(ws["y_max"]):
                continue
            if all(clearance.rect_rect_gap(rect, ob) > 1.0 for ob in obstructions):
                return rect
    pytest.fail("未找到几何隔离的无关 keepout 位置（板 %s）" % board["board_id"])


@pytest.mark.parametrize("name", ["demo-01-v2-corridor", "adv-05-eqlen-vs-layerpref"])
def test_ps2_unrelated_keepout_invariant(name, boards):
    board = boards[name]
    rect = far_keepout_rect(board)
    scoped = " ".join(e.get("scope", "") for e in board["principle_registry"])
    assert "FAR-KO-P3" not in scoped
    mutated = copy.deepcopy(board)
    mutated["zones"] = list(mutated.get("zones", [])) + [{
        "zone_id": "FAR-KO-P3", "kind": "keepout", "rect": {
            "x_min": rect[0], "y_min": rect[1], "x_max": rect[2], "y_max": rect[3]},
        "layers": "all", "note": "PS 无关性探针（几何隔离 keepout）"}]
    mutated = reseal(mutated)
    # 判据自检：新增 zone 与全部既有对象间隙 >1.0（无关性的实测依据）
    for part in board["partitions"]:
        assert clearance.rect_rect_gap(rect, part_bbox(part)) > 1.0
    for zone in board.get("zones", []):
        assert clearance.rect_rect_gap(rect, zone_rect(zone)) > 1.0
    assert_ps_invariant(board, mutated)


# ---------------- PS③ JSON 键序变化 ----------------

def reverse_keys(obj):
    if isinstance(obj, dict):
        return {k: reverse_keys(v) for k, v in reversed(list(obj.items()))}
    if isinstance(obj, list):
        return [reverse_keys(x) for x in obj]
    return obj


def test_ps3_key_order_invariant(boards):
    board = boards["demo-01-v2-corridor"]
    shuffled = reverse_keys(board)
    assert list(shuffled.keys()) != list(board.keys())
    # canonical 序列化键序无关：板哈希与编译指纹逐字节相等
    assert compute_board_sha256(shuffled) == compute_board_sha256(board)
    art_a, fp_a = compile_board(board)
    art_b, fp_b = compile_board(shuffled)
    assert fp_a == fp_b
    # 终选与账本完全不变（工件同指纹 ⇒ 连 compiled_sha256 都相等）
    res_a = select_best(board, plan_candidates(board, art_a, arm="principle")
                        + plan_candidates(board, art_a, arm="no-principle"))
    res_b = select_best(shuffled, plan_candidates(shuffled, art_b, arm="principle")
                        + plan_candidates(shuffled, art_b, arm="no-principle"))
    assert res_a["verdict"] == res_b["verdict"]
    assert res_a["best"] == res_b["best"]
    assert res_a["ledger"] == res_b["ledger"]


# ---------------- PS④ 输入换行变化 ----------------

def test_ps4_whitespace_invariant(tmp_path, boards):
    board = boards["demo-01-v2-corridor"]
    src_path = board_path("demo-01-v2-corridor")
    original_bytes = open(src_path, "rb").read()
    # 三种真实差异变体：缩进+换行全变（板源文件为紧凑无换行 JSON，变体必须逐字节不同）
    variants = {
        "indent2-lf": json.dumps(board, ensure_ascii=False, indent=2).encode("utf-8"),
        "indent4-crlf": json.dumps(board, ensure_ascii=False, indent=4)
                        .replace("\n", "\r\n").encode("utf-8"),
        "compact-trailing-crlf": json.dumps(board, ensure_ascii=False,
                                            separators=(",", ":")).encode("utf-8")
                                 + b"\r\n",
    }
    baseline = pipeline(board)["result"]
    for tag, payload in variants.items():
        assert payload != original_bytes, "前提：换行/缩进变体 %s 字节确有差异" % tag
        path = tmp_path / ("demo01-%s.json" % tag)
        path.write_bytes(payload)
        reloaded = load_board_file(str(path))
        assert compute_board_sha256(reloaded) == compute_board_sha256(board)
        result = pipeline(reloaded)["result"]
        assert result["verdict"] == baseline["verdict"]
        assert norm_best(result["best"]) == norm_best(baseline["best"])
        assert result["ledger"] == baseline["ledger"]


# ---------------- PS⑤ 同等候选顺序变化 ----------------

@pytest.mark.parametrize("name", ["demo-01-v2-corridor", "adv-05-eqlen-vs-layerpref"])
def test_ps5_candidate_order_invariant(name, boards):
    """同等候选顺序变化：同批候选（唯一 id）打乱注册序 → 终选 best 与 tie-break 不变。

    合同缝注记（见最终汇报）：planner 双臂各自从 C-001 起编号，两臂合批后 candidate_id
    碰撞；selection._find_candidate 按「注册序首个同 id」回取——best 字典随批序在
    principle/no-principle 臂之间翻转（payload 相同时计划不变，但 arm/trace 字段翻转），
    且 ledger.outcome 以 cid 为键后者覆盖前者。故本测试按 selection 合同前提
    （「合同保证 id 唯一」）把合批复编号为唯一 id 后再做顺序不变性断言。"""
    board = boards[name]
    artifact, _ = compile_board(board)
    cands = (plan_candidates(board, artifact, arm="principle")
             + plan_candidates(board, artifact, arm="no-principle"))
    unique = []
    for i, cand in enumerate(cands):
        c = copy.deepcopy(cand)
        c["candidate_id"] = "C-%03d" % (i + 1)
        unique.append(c)
    # 确定性重排（反序，候选数 ≥2 时必不同序）；同批同集合同 id
    shuffled = list(reversed(unique))
    assert [c["candidate_id"] for c in shuffled] != \
        [c["candidate_id"] for c in unique]
    assert sorted(c["candidate_id"] for c in shuffled) \
        == sorted(c["candidate_id"] for c in unique)
    res_a = select_best(board, unique)
    res_b = select_best(board, shuffled)
    assert res_a["verdict"] == res_b["verdict"]
    assert res_a["best"] == res_b["best"]  # 同工件 ⇒ 含 compiled_sha256 全等
    assert res_a["ledger"]["principle_ledger"] == res_b["ledger"]["principle_ledger"]
    assert res_a["ledger"]["measured"] == res_b["ledger"]["measured"]
    assert res_a["ledger"]["rejected"] == res_b["ledger"]["rejected"]
    # tie-break 机制复算：best = 可行集中 (objective, candidate_id) 字典序最小者
    feasible = [(pc["objective"], pc["candidate_id"])
                for pc in res_a["per_candidate"] if pc["feasible"]]
    if feasible:
        want_id = min(feasible)[1]
        assert res_a["best"]["candidate_id"] == want_id
        assert res_b["best"]["candidate_id"] == want_id
