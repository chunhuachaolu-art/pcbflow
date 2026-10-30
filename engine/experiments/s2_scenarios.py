# -*- coding: utf-8 -*-
"""EXP-S2 规模场景生成器与引擎侧 P0 工具（n=8/12/16 × 3，档位/波次 vs 全序缩放测试）。

移植 scale_scenarios.py 的 v2 单层宽缝墙族（F/B/F 交替、边框密封、右列 ±0.5
抖动、relaxed_validate 放宽 net_id n1..n16）与 hillclimb 参照（600 评估、最陡
下降、邻域=相邻交换+单点重定位）；本文件只读复用 pcbflow.v4exp.router（零写
入 pcbflow 仓），solve 直呼 router.solve_board。

attempt 阶梯（冻结公式）：k∈{0..11}，墙缝偏移 = 2*((k%3)−1)（−2/0/+2 三缝
同偏），板尺寸偏移 = 2*(k//3)（W、H 各加同值），jitter 种子 =
sha256("sid|attempt:k") 前 4 字节。同一 sid 依次试 attempt，首个通过验收三条
件的 attempt 定为该场景快照；12 个 attempt 全不过 → void_by_population。

验收三条件（冻结）：
  ① 基线（lex 序）SAT（all_connected）
  ② headroom = 基线成本 − 参照成本 ≥ 2.0（成本口径 = sa_contrib 总和 = 引擎
     objective）
  ③ 30 条种子随机序 SAT 率 ∈ [0.10, 0.90]（过渡带，防零余量与死板两端）

参照（冻结，非 oracle 诚实口径）：
  ref = min(基线, null_best_30, hillclimb_from_baseline)
  null_best_30 = 30 条随机序（种子=sha256("sid|ref:v1") 派生）中 SAT 最小者
  hillclimb_from_baseline = 600 次邻位评估、最陡下降（SCALE-R1 同邻域），
  只跑 baseline 一个起点（起点测量不计入预算）。

产物根：E:/ZCodeData/ZCodeProject/route-v5/out/guide-exp-s2/
子命令：
  gen         9 场景 attempt 阶梯验收 → 板快照 + manifest + prescreen（逐 attempt
              记验收三值；断点续跑：已判 attempt 跳过）
  prescreen   读 prescreen.json 打印验收台账（检查用，不重算）
  ref         从 gen 结果抽取参照 → p0/reference.json（不重算）
  ceilings    TIER/WAVE 通道抽样天花板（种子均匀抽样 N=150/场景/空间，
              种子=sha256("sid|ceil:v1|space")派生；ceiling=min(sample) 上界
              口径 + sample p5 披露区间；FULL 不抽样=参照锚）
  solve_time  单解耗时统计（n8/n12/n16 分档；wall-clock 只进本文件，用于
              T_solve 阶梯预注册，永不进场景/参照/天花板数值）

确定性：全部产物数值只用种子派生随机性，无 wall-clock 参与任何实验数值。
多进程 Pool ≤ 6 worker。
"""

import argparse
import hashlib
import json
import os
import random
import sys
from multiprocessing import Pool

ROOT = "E:/ZCodeData/ZCodeProject/route-v5"
OUT = os.path.join(ROOT, "out", "guide-exp-s2")
PCBFLOW = "E:/ZCodeData/.zcode/workspace/default/tools/pcbflow"
sys.path.insert(0, PCBFLOW)
from pcbflow.v4exp import router  # noqa: E402
from pcbflow.v4exp.gen_scenarios import spaced_values  # noqa: E402

P0 = os.path.join(OUT, "p0")
MAX_PROCS = 6

#: 人口：n=8/12/16 × a/b/c。基尺寸沿用 GUIDE-SCALE-R1 已验证 SPECS（同族），
#: attempt 阶梯在此基础上偏移。a/b/c 仅通过 sid 进 jitter 种子区分（几何族同构）。
SPECS = {
    "s2-n08-a": dict(n=8, W=56.0, H=38.0),
    "s2-n08-b": dict(n=8, W=56.0, H=38.0),
    "s2-n08-c": dict(n=8, W=56.0, H=38.0),
    "s2-n12-a": dict(n=12, W=68.0, H=46.0),
    "s2-n12-b": dict(n=12, W=68.0, H=46.0),
    "s2-n12-c": dict(n=12, W=68.0, H=46.0),
    "s2-n16-a": dict(n=16, W=80.0, H=54.0),
    "s2-n16-b": dict(n=16, W=80.0, H=54.0),
    "s2-n16-c": dict(n=16, W=80.0, H=54.0),
}
WALL_GAPS_BASE = {"k1": 20.0, "k2": 22.0, "k3": 20.0}  # v2 宽缝基线
ORDERED_SIDS = sorted(SPECS)
#: gen 执行序（交错三档，进度中断时各网数档覆盖均匀）；manifest 内仍按字典序。
GEN_ORDER = ["s2-n08-a", "s2-n12-a", "s2-n16-a",
             "s2-n08-b", "s2-n12-b", "s2-n16-b",
             "s2-n08-c", "s2-n12-c", "s2-n16-c"]

N_ATTEMPTS = 12
N_ACCEPT_ORDERS = 30
SAT_BAND = (0.10, 0.90)
HEADROOM_MIN = 2.0
HILLCLIMB_BUDGET = 600
CEIL_N = 100            # 抽样天花板 N/场景/空间。任务书缺省 150；实测算力
                        # （wave6 并跑、n16 单解 ~84s 负载价）不足降档至 100，
                        # 最终值=100（只此一个数，IMPL-REPORT 登记）
CEIL_SALT = "ceil:v1"
ACCEPT_SALT = "s2-accept30-v1"


def q05(v):
    return round(v * 2.0) / 2.0


def sha4(tok):
    return int.from_bytes(hashlib.sha256(tok.encode("utf-8")).digest()[:4],
                          "big")


def seed_for(sid, attempt):
    return sha4("%s|attempt:%d" % (sid, attempt))


def gap_offset(k):
    return 2 * ((k % 3) - 1)      # −2 / 0 / +2，三缝同偏


def size_offset(k):
    return 2 * (k // 3)           # 0 / 2 / 4 / 6，W、H 各加同值


def net_ids_of(sid):
    return ["n%d" % (i + 1) for i in range(SPECS[sid]["n"])]


def baseline_order(sid):
    """基线/R0 的 lex 序 = net_id 字典序（sorted）。n<10 时与编号序一致；
    n≥10 时两者不同，本实验全局冻结用字典序（与 TIER/WAVE/FULL 的展开
    规则『sort by (tier, net_id) / 块内字典序』自洽：FULL R0=lex=基线，
    TIER/WAVE R0=lex 切段后展开仍=lex）。"""
    return sorted(net_ids_of(sid))


def build_board(sid, attempt):
    sp = SPECS[sid]
    n = sp["n"]
    W = q05(sp["W"] + size_offset(attempt))
    H = q05(sp["H"] + size_offset(attempt))
    seed = seed_for(sid, attempt)
    rng = random.Random(seed)
    wall_gaps = {k: q05(g + gap_offset(attempt))
                 for k, g in WALL_GAPS_BASE.items()}
    rules = {"grid_mm": 0.25, "clearance_mm": 0.3,
             "width_mm": {"default": 0.3, "clock": 0.4},
             "via": {"pad_mm": 0.6, "hole_mm": 0.3},
             "allowed_layers": {"default": ["F.Cu", "B.Cu"],
                                "clock": ["F.Cu"]}}
    ys_l = spaced_values(rng, n, 3.0, H - 3.0, 2.0)
    # 右列 y = 左列 y ± 0.5mm 微抖（SCALE-R1 09-17 诊断结论保留）
    ys_r = [q05(y + rng.choice([0.0, 0.0, 0.5, -0.5])) for y in ys_l]
    clocks = {"n1", "n2"} if n >= 10 else {"n1"}
    bus_members = [nid for nid in net_ids_of(sid)
                   if nid not in clocks][:max(2, int(n * 0.4))]
    pin_l, pin_r = {}, {}
    pads, nets = [], []
    for i, nid in enumerate(net_ids_of(sid)):
        cl = "U%d" % (i % 4 + 1)
        cr = "J%d" % (i % 4 + 1)
        pin_l[cl] = pin_l.get(cl, 0) + 1
        pin_r[cr] = pin_r.get(cr, 0) + 1
        pla = "%s-%d" % (cl, pin_l[cl])
        prb = "%s-%d" % (cr, pin_r[cr])
        pads.append({"pad_id": pla, "net_id": nid, "x_mm": 3.0,
                     "y_mm": ys_l[i], "w_mm": 1.2, "h_mm": 1.2,
                     "layer": "F.Cu"})
        pads.append({"pad_id": prb, "net_id": nid, "x_mm": q05(W - 3.0),
                     "y_mm": ys_r[i], "w_mm": 1.2, "h_mm": 1.2,
                     "layer": "F.Cu"})
        nets.append({"net_id": nid,
                     "net_class": "clock" if nid in clocks else "default",
                     "endpoints": [pla, prb]})
    # 三道单层墙 F/B/F 交替（v2）+ 边框密封（1mm 双层框，防 A* 绕板外）
    walls = [
        {"keepout_id": "kFa", "layers": ["F.Cu", "B.Cu"],
         "rect_mm": [0.0, 0.0, W, 1.0]},
        {"keepout_id": "kFb", "layers": ["F.Cu", "B.Cu"],
         "rect_mm": [0.0, q05(H - 1.0), W, H]},
        {"keepout_id": "kFc", "layers": ["F.Cu", "B.Cu"],
         "rect_mm": [0.0, 0.0, 1.0, H]},
        {"keepout_id": "kFd", "layers": ["F.Cu", "B.Cu"],
         "rect_mm": [q05(W - 1.0), 0.0, W, H]},
    ]
    for kid, frac, layers in (("k1", 0.32, ["F.Cu"]), ("k2", 0.52, ["B.Cu"]),
                              ("k3", 0.72, ["F.Cu"])):
        wx = q05(W * frac)
        gap = wall_gaps[kid]
        if kid == "k1":
            gy = q05(H * (0.18 + rng.random() * 0.14))
        elif kid == "k2":
            gy = q05(H * (0.68 + rng.random() * 0.14))
        else:
            gy = q05(H * (0.42 + rng.random() * 0.16))
        lo = max(gap / 2.0 + 1.0, 1.0)
        hi = H - max(gap / 2.0 + 1.0, 1.0)
        gy = min(max(gy, lo), hi)
        below_y = q05(gy - gap / 2.0)
        above_y = q05(gy + gap / 2.0)
        if below_y > 0.5:
            walls.append({"keepout_id": kid + "a", "layers": layers,
                          "rect_mm": [wx, 0.0, q05(wx + 1.0), below_y]})
        if above_y < H - 0.5:
            walls.append({"keepout_id": kid + "b", "layers": layers,
                          "rect_mm": [wx, above_y, q05(wx + 1.0), H]})
    relations = [{"relation_id": "BUS-1", "relation_type": "bus",
                  "members": bus_members, "parent_id": None}]
    cl = sorted(clocks)
    if cl:
        relations.append({"relation_id": "CLK-1",
                          "relation_type": "clock_group",
                          "members": cl, "parent_id": None})
    obj = {"schema": "pcbflow.v4exp.board/1", "scenario_id": sid,
           "split": "calibration", "family": "scale", "seed": seed,
           "board": {"bbox_mm": [0.0, 0.0, W, H], "layers": ["F.Cu", "B.Cu"]},
           "rules": rules, "pads": pads, "nets": nets,
           "keepouts": walls, "relations": relations, "label": "satisfiable"}
    errs = relaxed_validate(obj)
    if errs:
        raise RuntimeError("%s attempt=%d 校验失败: %s" % (sid, attempt, errs))
    return obj


def relaxed_validate(obj):
    """model.validate_board 放宽版（同 scale_scenarios）：net_id 容 n1..n99、
    family 容 scale，其余不变量逐条保留。"""
    errs = []
    bbox = obj["board"]["bbox_mm"]
    layer_set = set(obj["board"]["layers"])

    def half_ok(v):
        return abs(v / 0.5 - round(v / 0.5)) <= 1e-6

    pad_ids, pad_net = set(), {}
    for p in obj["pads"]:
        pid, nid = p["pad_id"], p["net_id"]
        if pid in pad_ids:
            errs.append("pad_id 重复 %s" % pid)
        pad_ids.add(pid)
        if not (nid.startswith("n") and nid[1:].isdigit()):
            errs.append("net_id 形状 %s" % nid)
        pad_net[pid] = nid
        for k in ("x_mm", "y_mm"):
            if not half_ok(p[k]):
                errs.append("%s.%s 非 0.5 倍数" % (pid, k))
            if not (bbox[0] <= p[k] <= bbox[2] if k == "x_mm"
                    else bbox[1] <= p[k] <= bbox[3]):
                errs.append("%s.%s 出界" % (pid, k))
    net_ids = set()
    clock_nets = []
    for nt in obj["nets"]:
        nid = nt["net_id"]
        if nid in net_ids:
            errs.append("net 重复 %s" % nid)
        net_ids.add(nid)
        if nt["net_class"] == "clock":
            clock_nets.append(nid)
        if len(nt["endpoints"]) != 2:
            errs.append("%s endpoint 数" % nid)
        for e in nt["endpoints"]:
            if e not in pad_ids or pad_net.get(e) != nid:
                errs.append("%s endpoint 不一致 %s" % (nid, e))
    for k in obj["keepouts"]:
        r = k["rect_mm"]
        if not (r[0] < r[2] and r[1] < r[3]):
            errs.append("%s rect 退化" % k["keepout_id"])
        if (r[0] < bbox[0] or r[1] < bbox[1] or r[2] > bbox[2]
                or r[3] > bbox[3]):
            errs.append("%s rect 出界" % k["keepout_id"])
        if not set(k["layers"]) <= layer_set:
            errs.append("%s 层非法" % k["keepout_id"])
    related = set()
    for r in obj["relations"]:
        related |= set(r["members"])
        for m in r["members"]:
            if m not in net_ids:
                errs.append("%s 成员未知 %s" % (r["relation_id"], m))
    for nid in clock_nets:
        if nid not in related:
            errs.append("clock 网 %s 未入 relation" % nid)
    return errs


# ---------------------------------------------------------------- 求解内核

def solve_dict(board, order, group):
    """直呼 router.solve_board，返回小结果 dict（不含 run 大对象）。"""
    run = router.solve_board(board, {"route_order": [str(x) for x in order],
                                     "group": group})
    m = run["metrics"]
    return {"order": [str(x) for x in order],
            "objective": m["objective"] if m["all_connected"] else None,
            "all_connected": m["all_connected"],
            "status": run["status"], "violations": m["violations"],
            "nodes": m["search_nodes"]}


def _worker(arg):
    board, order, group = arg
    return solve_dict(board, order, group)


def pool_map(jobs, procs):
    procs = max(1, min(procs, MAX_PROCS))
    with Pool(procs) as pool:
        return pool.map(_worker, jobs)


def pool_map_fn(fn, jobs, procs):
    procs = max(1, min(procs, MAX_PROCS))
    with Pool(procs) as pool:
        return pool.map(fn, jobs)


def _orders_from_base(nets, base, count):
    out = []
    for i in range(count):
        rng = random.Random(base + i)
        v = list(nets)
        rng.shuffle(v)
        out.append(v)
    return out


def accept_orders(sid, attempt):
    """验收③的 30 条随机序（种子=attempt 种子 ⊕ 盐，逐条 +i 派生）。"""
    base = seed_for(sid, attempt) ^ sha4(ACCEPT_SALT)
    return _orders_from_base(net_ids_of(sid), base, N_ACCEPT_ORDERS)


def ref_orders(sid):
    """参照 null_best_30 的 30 条随机序（种子=sha256("sid|ref:v1") 派生，
    逐条 +i；同一 sid 全 attempt 共用，只在验收通过的快照上求解）。"""
    base = sha4("%s|ref:v1" % sid)
    return _orders_from_base(net_ids_of(sid), base, 30)


def hillclimb(board, baseline_order, baseline_result, budget=HILLCLIMB_BUDGET,
              procs=MAX_PROCS):
    """最陡下降局部搜索（SCALE-R1 同款）：邻域=相邻交换(n−1)+单点重定位
    n(n−1)；逐 pass 并行评估全部新邻位，平局取字典序；预算=budget 次邻位评估
    （起点=baseline，其测量不计入）。只跑 baseline 一个起点。"""
    seen = {}
    if baseline_result["all_connected"]:
        seen[tuple(baseline_order)] = round(baseline_result["objective"], 4)
    best_order = list(baseline_order)
    evals = 0
    while evals < budget:
        n = len(best_order)
        moves = []
        for i in range(n - 1):
            v = list(best_order)
            v[i], v[i + 1] = v[i + 1], v[i]
            moves.append(v)
        for i in range(n):
            for j in range(n):
                if j == i:
                    continue
                v = list(best_order)
                x = v.pop(i)
                v.insert(j, x)
                moves.append(v)
        fresh, seen_keys = [], set()
        for v in moves:
            k = tuple(v)
            if k not in seen and k not in seen_keys:
                seen_keys.add(k)
                fresh.append(v)
        if fresh:
            rows = pool_map([(board, v, "S2-HC") for v in fresh], procs)
            for v, r in zip(fresh, rows):
                evals += 1
                if r["all_connected"]:
                    seen[tuple(v)] = round(r["objective"], 4)
        cur_obj = seen.get(tuple(best_order))
        scored = sorted(((seen[tuple(v)], v) for v in moves
                         if tuple(v) in seen), key=lambda t: (t[0], t[1]))
        if cur_obj is None or not scored or scored[0][0] >= cur_obj - 1e-9:
            break
        best_order = scored[0][1]
        if evals >= budget:
            break
    best_obj = seen.get(tuple(best_order))
    return {"best": best_obj, "order": list(best_order), "evaluations": evals}


# ---------------------------------------------------------------- 产物读写

def _write(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, indent=1, sort_keys=True, ensure_ascii=False)


def _load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _p95(values):
    s = sorted(values)
    return s[int(0.95 * (len(s) - 1))]


def _p05(values):
    s = sorted(values)
    return s[int(0.05 * (len(s) - 1))]


_BOARD_CACHE = {}


def load_board(sid):
    if sid not in _BOARD_CACHE:
        _BOARD_CACHE[sid] = _load(os.path.join(P0, "board-%s.json" % sid))
    return _BOARD_CACHE[sid]


def solve_scale(sid, order, group="S2"):
    """对已验收快照求解（执行器经此入口；board 从 p0 快照加载）。"""
    return solve_dict(load_board(sid), order, group)


def accepted_sids():
    man = _load(os.path.join(P0, "manifest.json"))["scenarios"]
    return [s for s in ORDERED_SIDS if not man[s].get("void")]


# ---------------------------------------------------------------- gen

def _sid_file(sid):
    return os.path.join(P0, "prescreen-%s.json" % sid)


def _load_rows():
    """聚合全部 per-sid checkpoint 文件（双进程分片安全：每 sid 单文件单写者）。"""
    doc = {"rows": {}, "done_sids": []}
    if not os.path.isdir(P0):
        return doc
    for fn in os.listdir(P0):
        if not (fn.startswith("prescreen-s2-") and fn.endswith(".json")):
            continue
        sid = fn[len("prescreen-"):-len(".json")]
        with open(os.path.join(P0, fn), encoding="utf-8") as f:
            d = json.load(f)
        doc["rows"][sid] = d["rows"]
        if d.get("done"):
            doc["done_sids"].append(sid)
    doc["done_sids"].sort()
    return doc


def _save_sid(sid, rows, done):
    _write(_sid_file(sid), {"sid": sid, "rows": rows, "done": bool(done)})


def _atomic_write(path, obj):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, indent=1, sort_keys=True, ensure_ascii=False)
    os.replace(tmp, path)


def _save_manifest():
    rows_doc = _load_rows()
    man = {"protocol": {
        "attempt_ladder": "k∈{0..11}: gap_off=2*((k%3)-1) 三缝同偏; "
                          "size_off=2*(k//3) 加于 W 与 H; "
                          "seed=sha256('sid|attempt:k')[:4]",
        "acceptance": ["baseline_lex_sat", "headroom>=2.0 (sa_contrib sum)",
                       "30-seed random SAT rate in [0.10,0.90]"],
        "reference": "min(baseline, null_best_30(seed sha256('sid|ref:v1')), "
                     "hillclimb_from_baseline(600 evals, steepest descent, "
                     "adjacent-swap + single-relocation))",
        "salts": {"accept30": ACCEPT_SALT, "ref": "ref:v1",
                  "ceil": CEIL_SALT},
        "n_attempts": N_ATTEMPTS, "headroom_min": HEADROOM_MIN,
        "sat_band": list(SAT_BAND), "hillclimb_budget": HILLCLIMB_BUDGET,
        "ceil_n": CEIL_N,
        "baseline": "lex=net_id 字典序（sorted）；n<10 时与编号序一致",
        "note": "schema 偏差=net_id n1..n16 + family=scale（relaxed_validate）",
    }, "population": ORDERED_SIDS, "scenarios": {}}
    for sid in ORDERED_SIDS:
        rows = rows_doc["rows"].get(sid) or []
        acc = next((r for r in rows if r.get("accepted")), None)
        if acc is None:
            done = sid in rows_doc.get("done_sids", [])
            man["scenarios"][sid] = {
                "sid": sid, "n": SPECS[sid]["n"],
                "attempts_tried": len([r for r in rows if r.get("done")]),
                "void": True,
                "void_reason": "void_by_population"
                if done else "gen_incomplete",
                "accepted_attempt": None}
        else:
            man["scenarios"][sid] = {
                "sid": sid, "n": SPECS[sid]["n"],
                "attempts_tried": len([r for r in rows if r.get("done")]),
                "void": False, "accepted_attempt": acc["attempt"],
                "seed": acc["seed"], "gap_off": acc["gap_off"],
                "size_off": acc["size_off"],
                "baseline_obj": acc["baseline_obj"],
                "accept_sat_rate": acc["sat_rate"],
                "headroom": acc["headroom"], "ref": acc["ref"]}
    _atomic_write(os.path.join(P0, "manifest.json"), man)


def cmd_gen(args):
    os.makedirs(P0, exist_ok=True)
    doc = _load_rows()
    rows_map = doc["rows"]
    done_sids = set(doc["done_sids"])
    only = set(args.sids.split(",")) if args.sids else None
    order = [s for s in GEN_ORDER if not only or s in only]
    import pcbflow.v4exp.model as _m  # 只用其确定性 write_json
    for sid in order:
        if sid in done_sids:
            print("gen: %s 已完成，跳过（断点续跑）" % sid, flush=True)
            continue
        rows = rows_map.setdefault(sid, [])
        by_k = {r["attempt"]: r for r in rows}
        accepted = None
        for k in range(N_ATTEMPTS):
            old = by_k.get(k)
            if old is not None and old.get("done"):
                if old.get("accepted"):
                    accepted = old
                print("gen: %s attempt %d 已判（%s），跳过"
                      % (sid, k, old.get("reject") or "accepted"), flush=True)
                continue
            board = build_board(sid, k)
            row = {"attempt": k, "gap_off": gap_offset(k),
                   "size_off": size_offset(k), "seed": board["seed"],
                   "done": False, "accepted": False, "reject": None,
                   "baseline_sat": None, "baseline_obj": None,
                   "sat_rate": None, "sat_count": None,
                   "null_best_30": None, "hillclimb_best": None,
                   "hillclimb_evals": None, "ref": None, "headroom": None}
            rows[:] = [r for r in rows if r["attempt"] != k]
            rows.append(row)
            rows.sort(key=lambda r: r["attempt"])
            # ① 基线（lex=net_id 字典序）SAT —— 单解内联
            base_r = solve_dict(board, baseline_order(sid), "S2-GEN-ACC")
            row["baseline_sat"] = base_r["all_connected"]
            row["baseline_obj"] = base_r["objective"]
            if not base_r["all_connected"]:
                row["reject"] = "baseline_unsat"
            else:
                # ③ 30 条种子随机序 SAT 率
                acc_rows = pool_map(
                    [(board, o, "S2-GEN-ACC") for o in accept_orders(sid, k)],
                    args.procs)
                sat_n = sum(1 for r in acc_rows if r["all_connected"])
                row["sat_count"] = sat_n
                row["sat_rate"] = round(sat_n / float(N_ACCEPT_ORDERS), 4)
                if not (SAT_BAND[0] <= row["sat_rate"] <= SAT_BAND[1]):
                    row["reject"] = "sat_rate_out_of_band"
            if row["reject"] is None:
                # ② 参照与 headroom（只在 ①③ 通过后花算力）
                ref30 = pool_map([(board, o, "S2-GEN-REF")
                                  for o in ref_orders(sid)], args.procs)
                sat30 = [r for r in ref30 if r["all_connected"]]
                null_best = min((r["objective"] for r in sat30), default=None)
                row["null_best_30"] = null_best
                hc = hillclimb(board, baseline_order(sid), base_r,
                               procs=args.procs)
                row["hillclimb_best"] = hc["best"]
                row["hillclimb_evals"] = hc["evaluations"]
                comp = [base_r["objective"]]
                if null_best is not None:
                    comp.append(null_best)
                if hc["best"] is not None:
                    comp.append(hc["best"])
                row["ref"] = round(min(comp), 4)
                row["headroom"] = round(base_r["objective"] - row["ref"], 4)
                if row["headroom"] < HEADROOM_MIN:
                    row["reject"] = "headroom_lt_2"
            if row["reject"] is None:
                row["accepted"] = True
                path = os.path.join(P0, "board-%s.json" % sid)
                _m.write_json(path, board)
                row["board_sha256"] = hashlib.sha256(
                    json.dumps(board, sort_keys=True,
                               ensure_ascii=False).encode("utf-8")
                ).hexdigest()
                accepted = row
            row["done"] = True
            _save_sid(sid, rows, done=False)
            _save_manifest()
            print("gen: %s attempt %d -> %s%s" % (
                sid, k, "ACCEPTED" if row["accepted"] else "reject",
                "" if row["accepted"] else
                " (%s sat_rate=%s headroom=%s)" % (row["reject"],
                                                   row["sat_rate"],
                                                   row["headroom"])), flush=True)
            if accepted is not None:
                break
        if accepted is None:
            print("gen: %s 全部 12 attempt 未过验收 -> void_by_population"
                  % sid, flush=True)
        _save_sid(sid, rows, done=True)
        _save_manifest()
    _save_manifest()
    man = _load(os.path.join(P0, "manifest.json"))
    ok = [s for s in ORDERED_SIDS if not man["scenarios"][s]["void"]]
    print("gen: 完成（本批 %d sid）；accepted=%d void=%d -> %s"
          % (len(order), len(ok), len(ORDERED_SIDS) - len(ok),
             os.path.join(P0, "manifest.json")), flush=True)


# ---------------------------------------------------------------- prescreen/ref

def cmd_prescreen(_):
    doc = _load_rows()
    _atomic_write(os.path.join(P0, "prescreen.json"), doc)
    print("== EXP-S2 验收台账（三条件逐 attempt）==")
    for sid in ORDERED_SIDS:
        rows = (doc["rows"].get(sid) or [])
        acc = next((r for r in rows if r.get("accepted")), None)
        print("%s: %s" % (sid, "accepted@%d" % acc["attempt"] if acc
                          else ("void_by_population"
                                if sid in doc.get("done_sids", [])
                                else "gen_incomplete")))
        for r in rows:
            print("  k=%2d gap%+d size%+d base_sat=%s base_obj=%s "
                  "sat_rate=%s null30=%s hc=%s(%s evals) ref=%s "
                  "headroom=%s -> %s"
                  % (r["attempt"], r["gap_off"], r["size_off"],
                     r["baseline_sat"], r["baseline_obj"], r["sat_rate"],
                     r["null_best_30"], r["hillclimb_best"],
                     r["hillclimb_evals"], r["ref"], r["headroom"],
                     "ACCEPTED" if r["accepted"] else (r["reject"] or "?")))


def cmd_ref(_):
    doc = _load_rows()
    out = {}
    for sid in accepted_sids():
        rows = doc["rows"].get(sid) or []
        acc = next((r for r in rows if r.get("accepted")), None)
        if acc is None:
            continue
        comps = {"baseline": acc["baseline_obj"],
                 "null_best_30": acc["null_best_30"],
                 "hillclimb": acc["hillclimb_best"]}
        out[sid] = {"ref": acc["ref"], "components": comps,
                    "accepted_attempt": acc["attempt"],
                    "hillclimb_evals": acc["hillclimb_evals"],
                    "headroom": acc["headroom"],
                    "baseline_obj": acc["baseline_obj"]}
    _write(os.path.join(P0, "reference.json"), {
        "note": "非 oracle 诚实口径：ref=min(基线, null_best_30, "
                "hillclimb_from_baseline)；hillclimb 只跑 baseline 起点，600 "
                "邻位评估最陡下降；null_best_30 种子=sha256('sid|ref:v1')；"
                "参照≠全局最优（n=8 全枚举锚点见 GUIDE-SCALE-R1）",
        "per": out})
    print("ref: %d scenarios -> %s" % (len(out),
                                       os.path.join(P0, "reference.json")))


# ---------------------------------------------------------------- ceilings

def _expand_tier_order(nets, tup):
    return sorted(nets, key=lambda n: (tup[nets.index(n)], n))


def _expand_wave_order(nets, assign):
    blocks = [[] for _ in range(max(assign) + 1)]
    for nid, wi in zip(nets, assign):
        blocks[wi].append(nid)
    order = []
    for b in blocks:
        order.extend(sorted(b))
    return order


def _sample_space(sid, space, n_sample):
    """种子均匀抽样（冻结）：tier=每网 iid∈{1,2,3} 拒非满射；wave=先均匀取
    k∈{2,3} 再每网 iid 块号、拒空块。按展开序去重（通道表达=可达序集合）。"""
    nets = net_ids_of(sid)
    rng = random.Random(sha4("%s|%s|%s" % (sid, CEIL_SALT, space)))
    picks, seen_orders, tries = [], set(), 0
    while len(picks) < n_sample and tries < n_sample * 40:
        tries += 1
        if space == "tier":
            assign = [rng.randint(1, 3) for _ in nets]
            if set(assign) != {1, 2, 3}:
                continue
            order = _expand_tier_order(nets, assign)
            prop = {"tiers": dict(zip(nets, assign))}
        else:
            k = rng.choice((2, 3))
            assign = [rng.randrange(k) for _ in nets]
            blocks = [[] for _ in range(k)]
            for nid, wi in zip(nets, assign):
                blocks[wi].append(nid)
            if any(not b for b in blocks):
                continue
            order = _expand_wave_order(nets, assign)
            prop = {"waves": blocks}
        key = tuple(order)
        if key in seen_orders:
            continue
        seen_orders.add(key)
        picks.append({"proposal": prop, "order": order})
    return picks, tries


def _ceil_worker(arg):
    sid, order = arg
    r = solve_scale(sid, order, "S2-CEIL")
    return {"order": r["order"], "objective": r["objective"],
            "all_connected": r["all_connected"]}


def _ceil_file(sid):
    return os.path.join(P0, "ceilings-%s.json" % sid)


def _load_ceil_parts():
    out = {}
    if not os.path.isdir(P0):
        return out
    for fn in sorted(os.listdir(P0)):
        if not (fn.startswith("ceilings-s2-") and fn.endswith(".json")):
            continue
        sid = fn[len("ceilings-"):-len(".json")]
        with open(os.path.join(P0, fn), encoding="utf-8") as f:
            d = json.load(f)
        if d.get("complete"):
            out[sid] = {k: v for k, v in d.items() if k != "complete"}
    return out


def _ceil_worker(arg):
    sid, order = arg
    r = solve_scale(sid, order, "S2-CEIL")
    return {"order": r["order"], "objective": r["objective"],
            "all_connected": r["all_connected"]}


def cmd_ceilings(args):
    n_sample = args.n if args.n else CEIL_N
    parts = _load_ceil_parts()
    only = set(args.sids.split(",")) if args.sids else None
    todo = [s for s in accepted_sids()
            if (not only or s in only)
            and not (s in parts and set(parts[s]) == {"tier", "wave"})]
    for sid in todo:
        entry = {"complete": False}
        for space in ("tier", "wave"):
            picks, tries = _sample_space(sid, space, n_sample)
            jobs = [(sid, p["order"]) for p in picks]
            rows = pool_map_fn(_ceil_worker, jobs, args.procs)
            sat = [r for r in rows if r["all_connected"]]
            e = {"n_sample": len(picks), "n_tries": tries,
                 "n_sat": len(sat), "space": space}
            if sat:
                best = min(sat, key=lambda r: (r["objective"], r["order"]))
                e["ceiling"] = best["objective"]
                e["ceiling_order"] = best["order"]
                prop = next(p["proposal"] for p in picks
                            if p["order"] == best["order"])
                e["argmin_proposal"] = prop
                objs = [r["objective"] for r in sat]
                e["sample_p5"] = _p05(objs)
                e["sample_min"] = min(objs)
                e["sample_median"] = sorted(objs)[len(objs) // 2]
            else:
                e["ceiling"] = None
            entry[space] = e
            print("ceil %s %s: N=%d sat=%d ceiling=%s p5=%s"
                  % (sid, space, len(picks), len(sat),
                     e.get("ceiling"), e.get("sample_p5")), flush=True)
        entry["complete"] = True
        _atomic_write(_ceil_file(sid), entry)
        parts = _load_ceil_parts()
        _atomic_write(os.path.join(P0, "ceilings.json"), {
            "note": "抽样天花板（种子均匀抽样，种子=sha256('sid|ceil:v1|"
                    "space')派生；N=%d/场景/空间，任务书缺省 150 因实测算力"
                    "降档，最终值=100）。上界口径：ceiling=min(sample) 为通道"
                    "天花板保守上界（真天花板 ≤ 该值）；[ceiling, sample_p5] "
                    "为披露区间。FULL 不抽样（16! 不可达），参照即其分母锚。"
                    % n_sample,
            "n_per_space": n_sample, "per": parts})
    print("ceilings: done（todo=%d）-> %s"
          % (len(todo), os.path.join(P0, "ceilings.json")))


# ---------------------------------------------------------------- solve_time

def cmd_solve_time(args):
    import time
    per_sid = {}
    tier_rows = {}
    for sid in accepted_sids():
        nets = net_ids_of(sid)
        base = seed_for(sid, 0) ^ sha4("s2-solvetime-v1")
        orders = [baseline_order(sid)] + _orders_from_base(nets, base,
                                                           args.n - 1)
        rows = []
        for o in orders:
            t0 = time.perf_counter()
            r = solve_scale(sid, o, "S2-TIME")
            dt = time.perf_counter() - t0
            rows.append({"order": r["order"], "sat": r["all_connected"],
                         "objective": r["objective"],
                         "seconds": round(dt, 3)})
            print("solve_time %s: %.2fs sat=%s" % (sid, dt,
                                                   r["all_connected"]),
                  flush=True)
        per_sid[sid] = rows
        tier = sid.split("-")[1]
        tier_rows.setdefault(tier, []).extend(rows)
    summary = {}
    for tier, rows in sorted(tier_rows.items()):
        sec = sorted(r["seconds"] for r in rows)
        summary[tier] = {"n": len(sec), "min": sec[0],
                         "mean": round(sum(sec) / len(sec), 3),
                         "median": sec[len(sec) // 2],
                         "p95": round(_p95(sec), 3), "max": sec[-1]}
    _write(os.path.join(P0, "solve-time.json"), {
        "note": "wall-clock 只进本文件：单解耗时仅用于 T_solve 阶梯预注册与"
                "运行风险披露（brief §3 停机条款），永不进入场景/参照/天花板"
                "等实验数值。orders=基线+种子派生随机序。",
        "n_per_sid": args.n, "per_sid": per_sid, "per_tier": summary})
    print("solve_time: %s" % json.dumps(summary))


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("gen")
    g.add_argument("--procs", type=int, default=MAX_PROCS)
    g.add_argument("--sids", default="",
                   help="逗号分隔 sid 子集（分片并行用；默认全部）")
    sub.add_parser("prescreen")
    sub.add_parser("ref")
    c = sub.add_parser("ceilings")
    c.add_argument("--procs", type=int, default=MAX_PROCS)
    c.add_argument("--sids", default="",
                   help="逗号分隔 sid 子集（增量续算用；已完成 sid 跳过）")
    c.add_argument("--n", type=int, default=0,
                   help="抽样 N（默认冻结常量 CEIL_N=%d）" % CEIL_N)
    st = sub.add_parser("solve_time")
    st.add_argument("--n", type=int, default=12)
    st.add_argument("--procs", type=int, default=MAX_PROCS)
    args = ap.parse_args()
    {"gen": cmd_gen, "prescreen": cmd_prescreen, "ref": cmd_ref,
     "ceilings": cmd_ceilings, "solve_time": cmd_solve_time}[args.cmd](args)


if __name__ == "__main__":
    main()
