# -*- coding: utf-8 -*-
"""canvas.runners.m3 -- 修整 runner（合同 CANVAS-API-CONTRACT §1 Lane-M3）。

对已布态做**不改连通**的铜层面清理规整，两层 API:
- ``plan_actions(st, budget) -> [action dicts]``: 确定性修整规划（只读消费 st，
  内部在 deepcopy scratch 上试应用；返回合同 §2 九动作形态的平铺列表，
  批以 submit 结尾分隔）。
- ``run_m3(st, budget) -> summary dict``: plan→protocol.apply_batch 应用→
  修整前后 totals 对照 + state_sha256 前后（canonical_json 可直落）。

修整动作集四类（铜层面；批序钉死 = 此序）:
1. ``dead_branch``  残段清理: ripup 落了但不参与任何端到端链的 seg。判据=
   st.chain_detail/连通账本只读分析两层: tier1=chain_detail.dangling_segs
   （台账判定: 段首/末未附着）; tier2=格点图上不在任何「端点锚-端点锚
   简单路径」上的 seg（有界 DFS 精确标注，步数上限 DFS_STEP_CAP——超限
   降级为 tier1-only，保守不误杀）。tier2 的图连接判定**不弱于也不强于**
   台账模型（终端按格点在场即连、衔接按共享格点即连）→ 比 fail-closed
   台账更宽 → 只会把更多 seg 判活（少 rip），方向保守。
2. ``redundant_via`` 冗余过孔消减: ripup 单点过渡冗余 via——衔接点两侧段
   同层且共线（判据=两侧段相邻**单位步方向相等**的格点结构算术，非 DRC
   几何判定）。共以一批表达: route 合并段(先落，同网铜 R5 豁免)→ripup via
   →ripup 两旧段。防线: 衔接点=端点锚 / 三段共点 / 异层 / 非直行 / 自环段
   / 本网带 tuning → 不规划（tuning 基线随网首段，M5 域，保守回避）。
3. ``width_unify`` 亚类宽归一: 同网 width_class 混用归一到网主导档（计数
   最大; 并列取更窄档——保守; 再并列按档名）。主导档≠widths 台账条目时
   也归一（台账补全: widths 是 route 落段 cls 的单源，merge 的合并段
   依赖此对齐）。词表外档只读忽略（不以其为候选，fail-closed）。
4. ``width_gap`` 宽度间隙规整: 段宽档位对齐 R5 余量——逐档爬升（词表 mm
   升序），**只经 canvas.validate 判定**（scratch 上 apply 后
   validate_full 违例键集差=零新增才保留，否则快照还原停爬; 禁平行实现
   几何）。每步一批。

丝印层条款（任务书钉死）: 仅当 board.v1 带丝印数据才做丝印修整。探明结论
（真板 badgeleds + 合成夹具双探）: board.v1 键集
{board_id,hard_rules,holes,nets,partitions,principle_registry,provenance,
schema_version,stackup,via_model,workspace,zones} 无丝印层/丝印数据;
schema 层 stackup.kind∈{signal,plane} 且顶层 additionalProperties=false
→ 合法 board.v1 结构上不可能携带丝印数据。故 budget["silkscreen"]=True
时: 零丝印动作规划 + run_m3 摘要登记收窄偏差（修整范围收窄至铜层面，
激活跑 prereg 转录此收窄）。

budget 形态（本 docstring 钉死; normalize_budget 规范化）::

    {
      "max_actions": int >= 0,     # 非.submit 动作总数上限（批原子: 整批
                                   # 放不下则不规划）; 缺省 24
      "categories": ["dead_branch", "redundant_via", "width_unify",
                     "width_gap"],  # 修整类别子集（缺省全四类; 未知类别/
                                   # 非法值=BudgetError fail-closed）
      "silkscreen": bool,          # 丝印修整请求; 缺省 False（board.v1
                                   # 无丝印数据 → 恒收窄登记，见上）
    }

**每接受批次连通 100% 不变量**（run_m3 逐批断言）: 修整前已连通网在每批
接受后必须仍连通; 违反=该批回退（快照还原 mutable 域）+ 记
unresolved_action。同样逐批断言 DRC 键集零新增（validate_full 差集;
归 canvas.validate/v5.drc 同源，本件零平行违例判定）。规划期在 scratch
上等价预演（同判据），run 期为纵深防御。

判定单源披露: 几何/违例判定只经 canvas.validate（内部 v5.drc 同源）;
本件自有判定均为格点结构算术（图连通/单位步方向/计数排序），非 DRC 谓词
的平行实现。无随机源; 全迭代序 sorted 钉死; deepcopy 快照确定性还原。

plan_actions 纯读约定: 不改 st 任何字段（含连通账本）; 调用方须交已
recompute_connectivity 的一致态（run_m3 入口自 recompute）。
"""
import copy
import json

from .. import protocol as _protocol
from .. import validate as _validate
from .. import state as _state

RUNNER_ID = "canvas-runners-m3/1.0.0"

#: 修整类别（批序钉死: 残段清理 → 冗余过孔消减 → 亚类宽归一 → 宽度间隙规整）
CATEGORIES = ("dead_branch", "redundant_via", "width_unify", "width_gap")

#: 缺省 budget（normalize_budget 填充基准）
DEFAULT_BUDGET = {"max_actions": 24, "categories": list(CATEGORIES),
                  "silkscreen": False}

#: tier2 残段判定的 DFS 步数上限（超限=降级 tier1-only，保守不误杀）
DFS_STEP_CAP = 20000

#: 快照/还原的 mutable 域（board/lattice/anchors 为构造期冻结引用，不动）
_MUTABLE_FIELDS = ("segs", "vias", "widths", "placements", "tunings",
                   "connectivity", "chain_detail", "_seg_seq", "_tun_seq")


class BudgetError(ValueError):
    """budget 形态非法（fail-closed）。"""


class M3StateError(ValueError):
    """已布态不可修整（fail-closed）: seg/widths 带词表外 width_class——
    validate_full/instantiate（波1 件）对词表外档即抛，修整判定不可能
    成立; 显式早拒（detail 指明网与档）而非下游崩溃。"""


def _check_state_plannable(st):
    """入口 fail-closed: 词表外 width_class 早拒（segs 与 widths 双查）。"""
    vocab = _validate.width_class_vocab(st.board)
    for sid in sorted(st.segs):
        seg = st.segs[sid]
        if seg["width_class"] not in vocab:
            raise M3StateError(
                "seg %s 带词表外 width_class %r（词表 %s）——态不可修整"
                % (sid, seg["width_class"], sorted(vocab)))
    for net in sorted(st.widths):
        if st.widths[net] not in vocab:
            raise M3StateError(
                "widths[%s]=%r 词表外（词表 %s）——态不可修整"
                % (net, st.widths[net], sorted(vocab)))


# ---------------------------------------------------------------- budget

def normalize_budget(budget=None):
    """budget → 规范形（确定性; None=缺省）。非法键/值/类型 → BudgetError。"""
    nb = {"max_actions": DEFAULT_BUDGET["max_actions"],
          "categories": list(DEFAULT_BUDGET["categories"]),
          "silkscreen": DEFAULT_BUDGET["silkscreen"]}
    if budget is None:
        return nb
    if not isinstance(budget, dict):
        raise BudgetError("budget 须为 dict（得到 %s）" % type(budget).__name__)
    extra = set(budget) - {"max_actions", "categories", "silkscreen"}
    if extra:
        raise BudgetError("budget 合同外键 %s（合法键集 "
                          "{max_actions,categories,silkscreen}）"
                          % sorted(extra))
    if "max_actions" in budget:
        v = budget["max_actions"]
        if isinstance(v, bool) or not isinstance(v, int) or v < 0:
            raise BudgetError("max_actions=%r 须为 >=0 整数" % (v,))
        nb["max_actions"] = v
    if "categories" in budget:
        c = budget["categories"]
        if not isinstance(c, (list, tuple)):
            raise BudgetError("categories=%r 须为序列" % (c,))
        for name in c:
            if name not in CATEGORIES:
                raise BudgetError("未知修整类别 %r（合法集 %s）"
                                  % (name, list(CATEGORIES)))
        nb["categories"] = [k for k in CATEGORIES if k in set(c)]  # 去重+定序
    if "silkscreen" in budget:
        s = budget["silkscreen"]
        if not isinstance(s, bool):
            raise BudgetError("silkscreen=%r 须为 bool" % (s,))
        nb["silkscreen"] = s
    return nb


# ---------------------------------------------------------------- 丝印探针

def silkscreen_scope(st):
    """board 丝印数据探针（只读）。-> {"available": bool, "reason", "evidence"}。

    探明口径: stackup 层 id/kind 丝印匹配 + 顶层键丝印名匹配。board.v1
    schema（stackup.kind∈{signal,plane}、additionalProperties=false）下
    合法板恒 available=False——结构上不可能携带丝印数据（本车道 REPORT
    登记此收窄，prereg 转录）。"""
    board = st.board
    stackup = board.get("stackup") or []

    def _silkish(text):
        return "silk" in str(text).lower() or "overlay" in str(text).lower()

    silk_layers = [s for s in stackup
                   if _silkish(s.get("id", "")) or _silkish(s.get("kind", ""))]
    silk_keys = sorted(k for k in board if _silkish(k))
    evidence = {
        "stackup_kinds": sorted({str(s.get("kind")) for s in stackup}),
        "stackup_ids": [str(s.get("id")) for s in stackup],
        "board_keys": sorted(board),
        "silk_layers": [str(s.get("id")) for s in silk_layers],
        "silk_keys": silk_keys,
    }
    available = bool(silk_layers or silk_keys)
    if available:
        reason = "board 携带丝印数据（%s）——丝印修整可规划" % (
            evidence["silk_layers"] + evidence["silk_keys"],)
    else:
        reason = ("board.v1 无丝印数据（stackup.kind∈%s、键集无丝印层——"
                  "schema 层合法板结构上不可能携带）→ 修整范围收窄至铜层面"
                  % (evidence["stackup_kinds"],))
    return {"available": available, "reason": reason, "evidence": evidence}


# ---------------------------------------------------------------- 内部工具

def _snapshot(st):
    """mutable 域 deepcopy 快照（回退用）。"""
    return {f: copy.deepcopy(getattr(st, f)) for f in _MUTABLE_FIELDS}


def _restore(st, snap):
    """快照还原（含账本重算，幂等）。"""
    for f in _MUTABLE_FIELDS:
        setattr(st, f, snap[f])
    st.recompute_connectivity()


def _viol_key(v):
    """v5.drc.Violation → 可比对键（与 canvas.validate._vkey 同形: 本件仅
    作键化比对，判定本体仍归 validate/v5.drc）。"""
    return (v.rule, str(v.subject_a), str(v.subject_b),
            json.dumps(v.data, sort_keys=True))


def _viol_keys(st):
    """全态违例键集（canvas.validate.validate_full 同源单调用）。"""
    return {_viol_key(v) for v in _validate.validate_full(st).violations}


def _width_mix(st):
    """{net_id -> {width_class: seg 计数}}（网序/档名序钉死）。"""
    out = {}
    for sid in sorted(st.segs):
        seg = st.segs[sid]
        net = seg["net_id"]
        out.setdefault(net, {})
        cls = seg["width_class"]
        out[net][cls] = out[net].get(cls, 0) + 1
    return {net: dict(sorted(out[net].items())) for net in sorted(out)}


def _totals(st):
    """修整前后对照元组（canonical_json 可直落）。"""
    return {
        "segs_n": len(st.segs),
        "vias_n": len(st.vias),
        "tunings_n": len(st.tunings),
        "routed_nets": st.routed_nets(),
        "widths": {net: st.widths[net] for net in sorted(st.widths)},
        "width_mix": _width_mix(st),
        "connectivity": {net: bool(st.connectivity[net])
                         for net in sorted(st.connectivity)},
    }


def _net_terminals(st, net_id):
    pts = set()
    for pid in st.net_partitions(net_id):
        for a in st.effective_anchors(pid):
            pts.add(tuple(a))
    return pts


# ---------------------------------------------------------------- 残段判定

def _dfs_mark(adj, src, dst, live, budget):
    """src→dst 全体简单路径途经边所属 seg 标记 live（有界 DFS，确定性:
    邻接序=构建序=seg shape_id 序+路径序）。budget[0]<=0 即止。"""
    on_path = {src}
    edge_stack = []

    def dfs(u):
        if budget[0] <= 0:
            return
        budget[0] -= 1
        if u == dst:
            live.update(edge_stack)
            return
        for v, sid in adj.get(u, ()):
            if v in on_path:
                continue
            on_path.add(v)
            edge_stack.append(sid)
            dfs(v)
            edge_stack.pop()
            on_path.remove(v)

    dfs(src)


def _net_dead_segs(st, net_id):
    """不参与任何端到端链的 seg（shape_id 集）。tier1=台账 dangling_segs;
    tier2=有界 DFS 精确标注后的补集。超限降级 tier1-only（保守）。"""
    detail = st.chain_detail.get(net_id) or {}
    tier1 = set(detail.get("dangling_segs") or [])
    net_sids = [sid for sid in sorted(st.segs)
                if st.segs[sid]["net_id"] == net_id]
    if not net_sids:
        return set(tier1)
    adj = {}
    for sid in net_sids:
        pts = [tuple(p) for p in st.segs[sid]["grid"]]
        for a, b in zip(pts[:-1], pts[1:]):
            if a == b:
                continue
            adj.setdefault(a, []).append((b, sid))
            adj.setdefault(b, []).append((a, sid))
    terms = sorted(_net_terminals(st, net_id))
    live = set()
    budget = [DFS_STEP_CAP]
    for i in range(len(terms)):
        for j in range(i + 1, len(terms)):
            a, b = terms[i], terms[j]
            if a not in adj or b not in adj:
                continue
            _dfs_mark(adj, a, b, live, budget)
            if budget[0] <= 0:
                return set(tier1)   # 降级: 只认台账判定
    dead = set(net_sids) - live
    return dead | set(tier1)


# ---------------------------------------------------------------- 过孔消减

def _via_merge_candidates(st, net_id):
    """冗余过孔消减候选（确定性序=via shape_id 序）。

    候选判据（全部满足）: 本网 via 格点 P 处 ①恰 2 段本网 seg 含 P
    ②两段 head-tail 直通衔接于 P（无自环段） ③同层 ④共线（P 两侧相邻
    单位步同向直行） ⑤P 非本网端点锚 ⑥本网无 tuning。"""
    if any(t["net_id"] == net_id for t in st.tunings.values()):
        return []
    seg_pts = {}
    for sid in sorted(st.segs):
        seg = st.segs[sid]
        if seg["net_id"] != net_id:
            continue
        for p in set(tuple(q) for q in seg["grid"]):
            seg_pts.setdefault(p, []).append(seg)
    terms = _net_terminals(st, net_id)
    out = []
    for vsid in sorted(st.vias):
        via = st.vias[vsid]
        if via["net_id"] != net_id:
            continue
        P = tuple(via["grid"])
        if P in terms:
            continue
        at = seg_pts.get(P) or []
        if len(at) != 2:
            continue
        A, B = at
        ga = [tuple(q) for q in A["grid"]]
        gb = [tuple(q) for q in B["grid"]]
        if len(ga) < 2 or len(gb) < 2:
            continue
        if ga[0] == ga[-1] or gb[0] == gb[-1]:
            continue
        if ga[-1] == P and gb[0] == P:
            s1, g1, s2, g2 = A, ga, B, gb
        elif gb[-1] == P and ga[0] == P:
            s1, g1, s2, g2 = B, gb, A, ga
        else:
            continue
        if s1["layer"] != s2["layer"]:
            continue
        d_in = (P[0] - g1[-2][0], P[1] - g1[-2][1])
        d_out = (g2[1][0] - P[0], g2[1][1] - P[1])
        if d_in != d_out:
            continue
        out.append({
            "net_id": net_id,
            "via_shape_id": vsid,
            "seg_shape_ids": [s1["shape_id"], s2["shape_id"]],
            "layer": s1["layer"],
            "waypoints": [list(p) for p in g1 + g2[1:]],
        })
    return out


def _merge_batch(cand):
    """合并候选 → 批动作（route 合并段先行，同网铜 R5 豁免; ripup 序钉死）。"""
    s1, s2 = sorted(cand["seg_shape_ids"])
    return [
        {"action": "route", "net_id": cand["net_id"],
         "waypoints": cand["waypoints"], "layer": cand["layer"]},
        {"action": "ripup", "shape_id": cand["via_shape_id"]},
        {"action": "ripup", "shape_id": s1},
        {"action": "ripup", "shape_id": s2},
        {"action": "submit"},
    ]


# ---------------------------------------------------------------- 宽度档

def _dominant_class(st, net_id, vocab):
    """网主导档（计数最大; 并列取更窄 mm; 再并列按档名）。词表外档忽略。"""
    counts = {}
    for sid in sorted(st.segs):
        seg = st.segs[sid]
        if seg["net_id"] == net_id and seg["width_class"] in vocab:
            cls = seg["width_class"]
            counts[cls] = counts.get(cls, 0) + 1
    if not counts:
        return None
    return sorted(counts, key=lambda c: (-counts[c], vocab[c], c))[0]


def _width_unify_action(st, net_id, vocab):
    """亚类宽归一动作（无 seg/词表外-only/已对齐且无混用 → None）。"""
    dominant = _dominant_class(st, net_id, vocab)
    if dominant is None:
        return None
    classes = set()
    for sid in sorted(st.segs):
        seg = st.segs[sid]
        if seg["net_id"] == net_id and seg["width_class"] in vocab:
            classes.add(seg["width_class"])
    mixed = len(classes) > 1
    if st.widths.get(net_id) == dominant and not mixed:
        return None
    return {"action": "width_class", "net_id": net_id, "class": dominant}


def _ladder(scratch, net_id, vocab):
    """宽度间隙规整逐档爬升（scratch 上试应用+validate_full 键差判定;
    返回批列表，每批一个 width_class 动作+submit）。"""
    ladder = sorted(vocab, key=lambda c: (vocab[c], c))
    net_sids = [sid for sid in sorted(scratch.segs)
                if scratch.segs[sid]["net_id"] == net_id]
    if not net_sids:
        return []
    cur = scratch.segs[net_sids[0]]["width_class"]
    if cur not in ladder:
        return []
    batches = []
    idx = ladder.index(cur)
    while idx + 1 < len(ladder):
        nxt = ladder[idx + 1]
        snap = _snapshot(scratch)
        pre_keys = _viol_keys(scratch)
        _protocol.apply_batch(scratch, [
            {"action": "width_class", "net_id": net_id, "class": nxt},
            {"action": "submit"}])
        post_keys = _viol_keys(scratch)
        if post_keys - pre_keys:
            _restore(scratch, snap)      # 只经 validate 判定的爬停（禁平行几何）
            break
        batches.append([{"action": "width_class", "net_id": net_id,
                         "class": nxt}, {"action": "submit"}])
        idx += 1
    return batches


# ---------------------------------------------------------------- 规划

def _plan_batches(st, budget):
    """-> [(kind, [action, ..., submit]), ...]（确定性; 只读 st，
    scratch deepcopy 上试应用预演各批）。"""
    nb = normalize_budget(budget)
    _check_state_plannable(st)
    scratch = copy.deepcopy(st)
    vocab = _validate.width_class_vocab(st.board)
    remaining = [nb["max_actions"]]

    def n_actions(batch):
        return sum(1 for a in batch if a.get("action") != "submit")

    def fits(batch):
        return n_actions(batch) <= remaining[0]

    def rehearse(batch):
        """scratch 上试演一批: 全非-submit 动作 accepted 且连通保持且
        （宽度批）DRC 键差零新增 → True 并扣预算; 否则快照还原 False。"""
        snap = _snapshot(scratch)
        conn_pre = {n: bool(scratch.connectivity[n])
                    for n in scratch.connectivity}
        pre_keys = _viol_keys(scratch)
        results = _protocol.apply_batch(scratch, batch)
        conn_ok = all(not conn_pre[n] or scratch.connectivity[n]
                      for n in conn_pre)
        has_width = any(a.get("action") == "width_class" for a in batch)
        drc_ok = (not has_width) or not (_viol_keys(scratch) - pre_keys)
        all_ok = all(r.get("accepted") for r in results) and conn_ok and drc_ok
        if not all_ok:
            _restore(scratch, snap)
            return False
        remaining[0] -= n_actions(batch)
        return True

    planned = []
    nets = [n for n in sorted(st.known_nets())]
    for kind in nb["categories"]:
        if remaining[0] <= 0:
            break
        if kind == "dead_branch":
            for net in nets:
                if remaining[0] <= 0:
                    break
                for sid in sorted(_net_dead_segs(scratch, net)):
                    if remaining[0] <= 0:
                        break
                    batch = [{"action": "ripup", "shape_id": sid},
                             {"action": "submit"}]
                    if fits(batch) and rehearse(batch):
                        planned.append((kind, batch))
        elif kind == "redundant_via":
            for net in nets:
                if remaining[0] <= 0:
                    break
                for cand in _via_merge_candidates(scratch, net):
                    if remaining[0] <= 0:
                        break
                    batch = _merge_batch(cand)
                    if fits(batch) and rehearse(batch):
                        planned.append((kind, batch))
        elif kind == "width_unify":
            for net in nets:
                if remaining[0] <= 0:
                    break
                act = _width_unify_action(scratch, net, vocab)
                if act is None:
                    continue
                batch = [act, {"action": "submit"}]
                if fits(batch) and rehearse(batch):
                    planned.append((kind, batch))
        elif kind == "width_gap":
            for net in nets:
                if remaining[0] <= 0:
                    break
                for batch in _ladder(scratch, net, vocab):
                    if remaining[0] <= 0:
                        break
                    if fits(batch) and rehearse(batch):
                        planned.append((kind, batch))
    return planned


def plan_actions(st, budget=None):
    """确定性修整规划 → 平铺动作列表（批以 submit 结尾; 合同 §2 形态）。

    只读 st（含连通账本快照）; 内部 scratch deepcopy 预演。丝印条款:
    board.v1 无丝印数据 → 丝印修整恒零动作（收窄登记在 run_m3 摘要，
    plan 层即 fail-closed 不产丝印动作）。"""
    out = []
    for _kind, batch in _plan_batches(st, budget):
        out.extend(batch)
    return out


def _split_batches(actions):
    """平铺动作 → 批列表（submit 分隔; 尾部无 submit 的残批丢弃=防御）。"""
    batches = []
    cur = []
    for a in actions:
        cur.append(a)
        if a.get("action") == "submit":
            batches.append(cur)
            cur = []
    return batches


# ---------------------------------------------------------------- 运行

def _apply_gated(st, kind, batch, batch_index):
    """一批受控应用: 逐批断言 ①连通不变量（修整前已连通网仍连通）
    ②DRC 键集零新增; 违反=快照回退 + unresolved 记录。"""
    snap = _snapshot(st)
    sha_pre = _state.state_sha256(st)
    conn_pre = {n: bool(st.connectivity[n]) for n in st.connectivity}
    pre_keys = _viol_keys(st)
    results = _protocol.apply_batch(st, batch)
    st.recompute_connectivity()
    conn_ok = all(not conn_pre[n] or st.connectivity[n] for n in conn_pre)
    drc_ok = not (_viol_keys(st) - pre_keys)
    rolled_back = False
    unresolved = []
    if not conn_ok or not drc_ok:
        _restore(st, snap)
        rolled_back = True
        reason = ("connectivity_invariant" if not conn_ok
                  else "drc_new_violation")
        unresolved.append({"batch_index": batch_index, "kind": kind,
                           "actions": [a for a in batch
                                       if a.get("action") != "submit"],
                           "reason": reason})
    return {
        "index": batch_index,
        "kind": kind,
        "actions": [a for a in batch if a.get("action") != "submit"],
        "results": results,
        "connectivity_ok": conn_ok,
        "drc_ok": drc_ok,
        "rolled_back": rolled_back,
        "sha256_after": _state.state_sha256(st),
        "sha256_before": sha_pre,
        "unresolved": unresolved,
    }


def run_m3(st, budget=None):
    """修整 runner 入口: plan → 逐批 apply_batch（受控）→ 前后对照摘要。

    摘要（canonical_json 可直落）: budget/scope（丝印探针+偏差登记）/
    totals_before/after（各含 segs_n/vias_n/width_mix/routed_nets/widths/
    connectivity）/state_sha256 前后/逐批记录（accepted 结果+双不变量+
    回退）/unresolved_actions/drc（前后违例数+新增键数）/connectivity
    （preserved + routed 前后计数）。"""
    nb = normalize_budget(budget)
    _check_state_plannable(st)
    st.recompute_connectivity()
    silk = silkscreen_scope(st)
    deviations = []
    if nb["silkscreen"] and not silk["available"]:
        deviations.append({
            "code": "M3-SILK-SCOPE-NARROW",
            "detail": ("budget 请求丝印修整但 board.v1 无丝印数据（%s）——"
                       "修整范围收窄至铜层面; 激活跑 prereg 转录此收窄"
                       % silk["reason"]),
        })
    sha_before = _state.state_sha256(st)
    totals_before = _totals(st)
    conn_before = dict(totals_before["connectivity"])
    keys_before = _viol_keys(st)

    planned = _plan_batches(st, nb)
    batches = []
    unresolved = []
    for i, (kind, batch) in enumerate(planned):
        rec = _apply_gated(st, kind, batch, i)
        batches.append(rec)
        unresolved.extend(rec["unresolved"])

    sha_after = _state.state_sha256(st)
    totals_after = _totals(st)
    keys_after = _viol_keys(st)
    preserved = all(not conn_before[n] or totals_after["connectivity"][n]
                    for n in conn_before)
    return {
        "runner": RUNNER_ID,
        "board_id": st.board["board_id"],
        "board_sha256": st.board_sha256,
        "budget": {"max_actions": nb["max_actions"],
                   "categories": list(nb["categories"]),
                   "silkscreen": nb["silkscreen"]},
        "scope": {"silkscreen": {"requested": nb["silkscreen"],
                                 "available": silk["available"],
                                 "reason": silk["reason"]},
                  "deviations": deviations},
        "totals_before": totals_before,
        "totals_after": totals_after,
        "state_sha256_before": sha_before,
        "state_sha256_after": sha_after,
        "plan_actions_n": sum(len(r["actions"]) for r in batches),
        "batches": batches,
        "unresolved_actions": unresolved,
        "drc": {"violations_before_n": len(keys_before),
                "violations_after_n": len(keys_after),
                "new_violation_keys_n": len(keys_after - keys_before)},
        "connectivity": {"preserved": preserved,
                         "routed_before_n": totals_before["routed_nets"],
                         "routed_after_n": totals_after["routed_nets"]},
    }
