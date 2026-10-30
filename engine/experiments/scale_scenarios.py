# -*- coding: utf-8 -*-
"""GUIDE-SCALE-R1 规模场景生成器与引擎侧 P0 工具。

只读复用 pcbflow.v4exp.router（零写入 pcbflow 仓）。seat_ab_r1a 的场景查询
只覆盖 cal 语料，本模块为规模人口自建同构 board dict 直呼 router.solve_board。

schema 偏差（须在预注册件披露）：net_id 扩展为 n1..n16（model._NET_ID_RE 仅容
n1..n9）、family="scale"（FAMILIES 仅 f1..f8）。本模块自带放宽版校验
relaxed_validate（除网名/家族枚举外，model.validate_board 其余不变量逐条保留）。

产物根：E:/ZCodeData/ZCodeProject/route-v5/out/guide-scale-r1/
子命令：
  gen         生成 4 场景快照 + manifest（seed=sha256(sid[|attempt:k]) 前 4 字节）
  prescreen   基线 + 30 随机序快查（SAT 率/排序余量/单解耗时）
  null        --n N：每场景 N 条种子随机序 null 分布（多进程）
  hillclimb   每场景确定性局部搜索参照顶（相邻交换+单点重定位，首改进，预算内）
  enumerate8  scl-n08 全排列 40320 真枚举锚点（多进程，后台）

确定性：全部随机性由 seed 派生；无 wall-clock 参与任何产物数值。
"""

import argparse
import hashlib
import itertools
import json
import os
import random
import sys
from multiprocessing import Pool

ROOT = "E:/ZCodeData/ZCodeProject/route-v5"
OUT = os.path.join(ROOT, "out", "guide-scale-r1")
PCBFLOW = "E:/ZCodeData/.zcode/workspace/default/tools/pcbflow"
sys.path.insert(0, PCBFLOW)
from pcbflow.v4exp import router  # noqa: E402
from pcbflow.v4exp.gen_scenarios import spaced_values  # noqa: E402

P0 = os.path.join(OUT, "p0")

#: 人口（n=8/10/12/16 阶梯）。墙制式 v2（2026-09-17 定型）：全部单层墙
#: F/B/F 交替（语料 f6"恒可满足"原理：default 网任意排列都有开放层可换，
#: 可布性由 clock 网（锁 F.Cu，须过 k1/k3 缝）驱动；固定缝宽 12/14/12，
#: 容量非绑定）。v1 双层瓶颈墙在 n≥10 随机 SAT 率 0.06–0.5，弃。
SPECS = {
    "scl-n08": dict(n=8, W=56.0, H=38.0),
    "scl-n10": dict(n=10, W=62.0, H=42.0),
    "scl-n12": dict(n=12, W=68.0, H=46.0),
    "scl-n16": dict(n=16, W=80.0, H=54.0),
}
WALL_GAPS = {"k1": 20.0, "k2": 22.0, "k3": 20.0}  # 宽缝=降过孔稀缺（0.5H 级）
ORDERED_SIDS = sorted(SPECS)


def q05(v):
    return round(v * 2.0) / 2.0


def seed_for(sid, attempt=0):
    tok = sid if attempt == 0 else "%s|attempt:%d" % (sid, attempt)
    return int.from_bytes(hashlib.sha256(tok.encode("utf-8")).digest()[:4], "big")


def net_ids_of(sid):
    return ["n%d" % (i + 1) for i in range(SPECS[sid]["n"])]


def build_board(sid, attempt=0):
    sp = SPECS[sid]
    n, W, H = sp["n"], sp["W"], sp["H"]
    seed = seed_for(sid, attempt)
    rng = random.Random(seed)
    rules = {"grid_mm": 0.25, "clearance_mm": 0.3,
             "width_mm": {"default": 0.3, "clock": 0.4},
             "via": {"pad_mm": 0.6, "hole_mm": 0.3},
             "allowed_layers": {"default": ["F.Cu", "B.Cu"],
                                "clock": ["F.Cu"]}}
    ys_l = spaced_values(rng, n, 3.0, H - 3.0, 2.0)
    # 右列 y = 左列 y ± 0.5mm 微抖：独立随机会在右侧通道产生必然交叉扇
    # （09-17 诊断 n12/n16 基线死因），微抖保留少量逆序难度且可控
    ys_r = [q05(y + rng.choice([0.0, 0.0, 0.5, -0.5])) for y in ys_l]
    # clock 网固定编 n1/n2：编号序基线先布 clock（n1..nN 序）；
    # 2026-09-17 诊断：clock 编号靠后（n10/n12/n16 旧版）基线结构性 UNSAT
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
    # 三道单层墙 F/B/F 交替（v2 定型，f6 恒可满足原理）+ 边框密封
    # 边框密封：1mm 双层框贴 bbox 内沿——引擎的 2mm 工作区裕量对走线开放
    #（static_blocked 只含焊盘+禁布区），不密封则 A* 会从板外绕过墙（09-17 实测
    # scl-n16 n1 于 y=-0.75 越 k3 平面）。
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
        gap = WALL_GAPS[kid]
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
    """model.validate_board 的放宽版：net_id 容 n1..n99、family 容 scale，
    其余不变量逐条保留（0.5 倍数坐标、端点一致、keepout 界内、clock 入 relation）。"""
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


# ---------------------------------------------------------------- 快照与求解

_BOARD_CACHE = {}


def load_board(sid):
    if sid not in _BOARD_CACHE:
        with open(os.path.join(P0, "board-%s.json" % sid),
                  encoding="utf-8") as f:
            _BOARD_CACHE[sid] = json.load(f)
    return _BOARD_CACHE[sid]


def solve_scale(sid, order, group="SCALE"):
    run = router.solve_board(load_board(sid),
                             {"route_order": [str(x) for x in order],
                              "group": group})
    m = run["metrics"]
    return {"sid": sid, "order": [str(x) for x in order],
            "objective": m["objective"] if m["all_connected"] else None,
            "all_connected": m["all_connected"],
            "status": run["status"], "violations": m["violations"],
            "nodes": m["search_nodes"], "run": run}


def _worker(arg):
    sid, order = arg
    r = solve_scale(sid, order, "SCALE-P0")
    r.pop("run")
    return r


def _pool_map(jobs, procs):
    with Pool(procs) as pool:
        return pool.map(_worker, jobs)


def _random_orders(sid, count, salt):
    nets = net_ids_of(sid)
    base = seed_for(sid) ^ int.from_bytes(
        hashlib.sha256(salt.encode()).digest()[:4], "big")
    out = []
    for i in range(count):
        rng = random.Random(base + i)
        v = list(nets)
        rng.shuffle(v)
        out.append(v)
    return out


def _write(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, indent=1, sort_keys=True, ensure_ascii=False)


def _p95(values):
    s = sorted(values)
    return s[int(0.95 * (len(s) - 1))]


# ---------------------------------------------------------------- 子命令

def cmd_gen(args):
    os.makedirs(P0, exist_ok=True)
    attempts = dict(a.split("=") for a in args.attempts) if args.attempts else {}
    manifest = []
    for sid in ORDERED_SIDS:
        attempt = int(attempts.get(sid, "0"))
        obj = build_board(sid, attempt)
        import pcbflow.v4exp.model as _m  # 只用其确定性 write_json/sha256
        path = os.path.join(P0, "board-%s.json" % sid)
        _m.write_json(path, obj)
        manifest.append({"scenario_id": sid, "attempt": attempt,
                         "n": SPECS[sid]["n"],
                         "seed": obj["seed"],
                         "sha256": hashlib.sha256(
                             json.dumps(obj, sort_keys=True,
                                        ensure_ascii=False).encode("utf-8")
                         ).hexdigest()})
    _write(os.path.join(P0, "manifest.json"), {
        "population": ORDERED_SIDS,
        "note": "GUIDE-SCALE-R1 人口；schema 偏差=net_id n1..n16 + family=scale",
        "scenarios": manifest})
    print("gen: %d scenarios -> %s" % (len(manifest), P0))


def cmd_prescreen(args):
    import time
    rows = []
    for sid in ORDERED_SIDS:
        nets = net_ids_of(sid)
        t = time.time()
        base = solve_scale(sid, nets, "SCALE-PRE")
        dt = time.time() - t
        rnd = _pool_map([(sid, o) for o in _random_orders(sid, args.n,
                                                          "prescreen")],
                        procs=args.procs)
        objs = [r["objective"] for r in rnd if r["all_connected"]]
        sat = len(objs) / float(len(rnd))
        rows.append((sid, base, dt, sat, objs, len(rnd)))
        print("%s base=%s (%.1fs) rand_sat=%.2f rand_min=%s rand_med=%s "
              "p95=%s spread_med=%.3f" % (
                  sid, base["objective"], dt, sat,
                  min(objs) if objs else "-",
                  sorted(objs)[len(objs) // 2] if objs else "-",
                  _p95(objs) if objs else "-",
                  (sorted(objs)[len(objs) // 2] / base["objective"] - 1)
                  if objs else -1))


def _null_jobs(sid, count):
    return [(sid, o) for o in _random_orders(sid, count, "null")]


def cmd_null(args):
    per = {}
    orders_all = []
    for sid in ORDERED_SIDS:
        rows = _pool_map(_null_jobs(sid, args.n), procs=args.procs)
        objs = sorted(r["objective"] for r in rows if r["all_connected"])
        per[sid] = {"n_orders": len(rows),
                    "sat_count": len(objs),
                    "sat_rate": len(objs) / float(len(rows)),
                    "objective_p95": _p95(objs) if objs else None,
                    "objective_min": objs[0] if objs else None,
                    "objective_max": objs[-1] if objs else None}
        for r in rows:
            orders_all.append({"scenario_id": sid, "order": r["order"],
                               "objective": r["objective"],
                               "all_connected": r["all_connected"]})
        print(sid, per[sid])
    _write(os.path.join(P0, "null-orders.json"), {"rows": orders_all})
    _write(os.path.join(P0, "null-summary.json"),
           {"n_per_scenario": args.n, "salt": "null", "per": per})


def _hillclimb_worker(sid):
    nets = net_ids_of(sid)
    with open(os.path.join(P0, "null-orders.json"), encoding="utf-8") as f:
        rows = [r for r in json.load(f)["rows"] if r["scenario_id"] == sid]
    seen = {}
    for r in rows:
        if r["all_connected"]:
            seen[tuple(r["order"])] = round(r["objective"], 4)
    base = solve_scale(sid, nets, "SCALE-HILL")
    if base["all_connected"]:
        seen.setdefault(tuple(nets), round(base["objective"], 4))
    best_obj, best_order = min(
        ((v, list(k)) for k, v in seen.items()), key=lambda t: (t[0], t[1]))
    budget = 600
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
        for v, r in zip(fresh, _pool_map([(sid, v) for v in fresh],
                                         procs=8)):
            evals += 1
            if r["all_connected"]:
                seen[tuple(v)] = round(r["objective"], 4)
        cur_obj = seen[tuple(best_order)]
        scored = sorted(
            ((seen[tuple(v)], v) for v in moves if tuple(v) in seen),
            key=lambda t: (t[0], t[1]))
        if not scored or scored[0][0] >= cur_obj - 1e-9:
            break
        best_obj, best_order = scored[0][0], scored[0][1]
    return {"scenario_id": sid, "reference_best": best_obj,
            "reference_order": best_order, "evaluations": evals}


def cmd_hillclimb(args):
    out = {}
    for sid in ORDERED_SIDS:
        r = _hillclimb_worker(sid)
        out[sid] = r
        print(sid, r)
    _write(os.path.join(P0, "reference-ceiling.json"),
           {"method": "null 最优 + 最陡下降局部搜索（邻域=相邻交换 n-1 + 单点重定位 "
                      "n(n-1)，逐 pass 并行评估、最优邻位平局取字典序，确定性）；"
                      "预算 600 次评估；近似顶非真最优（n=8 另有全枚举锚点）",
            "per": out})


def cmd_enumerate8(args):
    sid = "scl-n08"
    nets = net_ids_of(sid)
    perms = list(itertools.permutations(nets))
    hist = {}
    best = None
    sat_count = 0
    CH = 512
    for i in range(0, len(perms), CH):
        rows = _pool_map([(sid, list(p)) for p in perms[i:i + CH]],
                         procs=args.procs)
        for r in rows:
            if r["all_connected"]:
                sat_count += 1
                o = round(r["objective"], 4)
                hist[o] = hist.get(o, 0) + 1
                if best is None or o < best[0]:
                    best = (o, r["order"])
        print("enumerate8: %d/%d perms, best=%s" % (min(i + CH, len(perms)),
                                                    len(perms),
                                                    best[0] if best else "-"))
    top = sorted(hist.items())[:100]
    _write(os.path.join(P0, "oracle-scl-n08.json"), {
        "scenario_id": sid, "permutations": len(perms),
        "sat_order_count": sat_count, "best_objective": best[0],
        "best_order": best[1], "histogram_top100": top})


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("gen")
    g.add_argument("--attempts", nargs="*", default=[])
    p = sub.add_parser("prescreen")
    p.add_argument("--n", type=int, default=30)
    p.add_argument("--procs", type=int, default=10)
    nu = sub.add_parser("null")
    nu.add_argument("--n", type=int, default=400)
    nu.add_argument("--procs", type=int, default=10)
    sub.add_parser("hillclimb")
    e8 = sub.add_parser("enumerate8")
    e8.add_argument("--procs", type=int, default=10)
    args = ap.parse_args()
    {"gen": cmd_gen, "prescreen": cmd_prescreen, "null": cmd_null,
     "hillclimb": cmd_hillclimb, "enumerate8": cmd_enumerate8}[args.cmd](args)


if __name__ == "__main__":
    main()
