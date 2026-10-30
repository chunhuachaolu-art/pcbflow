# -*- coding: utf-8 -*-
"""EXP-S1 四层语料生成器与引擎侧工具（层计划通道 ≥4 层复测）。

只读复用 pcbflow.v4exp.router（零写入 pcbflow 仓），模式沿 scale_scenarios 先例。
4 信号层 F.Cu / In1.Cu / In2.Cu / B.Cu；高速(clock)类网限内层对
（rules.allowed_layers["clock"]=["In1.Cu","In2.Cu"]）。

引擎硬事实（router.py:158）：端点焊盘所在层必须 ∈ 允许层集——钉层不可把网
推离焊盘层，层计划=纯限制性通道。咬合面设计因此集中于三类分配问题：
  fc 内层匹配族：全部网 clock 类（限内层对），In1/In2 各留一条窄过墙窗口
    （容量 ⌈n/2⌉ 道），网→层分配=二部匹配，在线贪心≠最优。
  fa 双闸门族：F.Cu 双闸墙（横竖各一道带缝闸门）+ 少量 clock 网；普通网
    钉层空间 {null, F}，咬合主要来自 clock 内层选择对后继的影响。
  fb B 墙异构族：B.Cu 单闸墙 + 约半数网焊盘在 B.Cu（焊盘层异构），B 网
    钉 {null,B}=强制驻留 B（让出 F 逃逸），考验预留语义。

schema 偏差（沿用 scale 先例，须在预注册披露）：family="layer4"（FAMILIES 仅
f1..f8），net_id n1..n9（model._NET_ID_RE 容 n1..n9，本人口 n≤6 不越界）。

子命令：
  gen        生成 9 场景快照 + manifest（seed=sha256(sid) 前 4 字节）
  prescreen  每场景：lex 基线 + 层计划空间天花板探查（n≤4 精确枚举、n=6 抽样）
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
OUT = os.path.join(ROOT, "out", "guide-exp-s1")
P0 = os.path.join(OUT, "p0")
PCBFLOW = "E:/ZCodeData/.zcode/workspace/default/tools/pcbflow"
sys.path.insert(0, PCBFLOW)
from pcbflow.v4exp import router  # noqa: E402
from pcbflow.v4exp.gen_scenarios import spaced_values  # noqa: E402

L4 = ["F.Cu", "In1.Cu", "In2.Cu", "B.Cu"]
INNER = ["In1.Cu", "In2.Cu"]

#: 钉层字母表（预注册冻结，集值承诺）：null=自动；单层=只许该层；
#: INNER=内层对；F_I1/F_I2/F_B=焊盘层+单个逃逸层承诺。约束语义=
#: 引擎 allowed = 静态允许层 ∩ 钉集（router.py:148），焊盘层不在钉集内
#: 即 fail-stop（router.py:158）——执行器按非法提案拒绝、不落 solve。
PIN_ALPHABET = {
    None: None, "F.Cu": ["F.Cu"], "B.Cu": ["B.Cu"],
    "In1.Cu": ["In1.Cu"], "In2.Cu": ["In2.Cu"], "INNER": list(INNER),
    "F_I1": ["F.Cu", "In1.Cu"], "F_I2": ["F.Cu", "In2.Cu"],
    "F_B": ["F.Cu", "B.Cu"],
}

FAMILIES = ("fa", "fb", "fc")
SIZES = (3, 4, 6)
ORDERED_SIDS = ["l4-%s-%02d" % (f, n) for f in FAMILIES for n in SIZES]

W = 32.0
H = 22.0


def q05(v):
    return round(v * 2.0) / 2.0


def seed_for(sid):
    return int.from_bytes(hashlib.sha256(sid.encode("utf-8")).digest()[:4],
                          "big")


def net_ids_of(sid):
    return ["n%d" % (i + 1) for i in range(int(sid[-2:]))]


def net_class_of(sid, nid):
    """族内 clock 编成（内层对限类，焊盘在 In1.Cu——引擎硬约束：焊盘层必须
    ∈ 允许层集，故内层限类网的焊盘必须在内层上，预注册披露）：fc 无 clock
    （全员 default，窗口匹配问题）；fa 前 2 个（n=3 则 1 个）；fb n1。"""
    if sid.startswith("l4-fc"):
        return "default"
    n_clk = 1 if int(sid[-2:]) < 4 else 2
    if sid.startswith("l4-fa") and int(nid[1:]) <= n_clk:
        return "clock"
    if sid.startswith("l4-fb") and nid == "n1":
        return "clock"
    return "default"


def pad_layer_of(sid, nid):
    """fb 偶数号网焊盘在 B.Cu（焊盘层异构）；clock 网（fa/fb）焊盘在 In1.Cu；
    其余 F.Cu。"""
    if net_class_of(sid, nid) == "clock":
        return "In1.Cu"
    if sid.startswith("l4-fb") and int(nid[1:]) % 2 == 0:
        return "B.Cu"
    return "F.Cu"


def _walls_fa(rng):
    """双闸门：F-only 横墙 y∈[10,11] 带竖缝 + F-only 竖墙 x∈[15.5,16.5]
    带横缝；缝宽 2.0（≈2 道）。"""
    gx = q05(9.0 + rng.random() * 14.0)
    gy = q05(6.0 + rng.random() * 10.0)
    return [
        {"keepout_id": "fa-hL", "layers": ["F.Cu"],
         "rect_mm": [5.0, 10.0, q05(gx - 1.0), 11.0]},
        {"keepout_id": "fa-hR", "layers": ["F.Cu"],
         "rect_mm": [q05(gx + 1.0), 10.0, 27.0, 11.0]},
        {"keepout_id": "fa-vB", "layers": ["F.Cu"],
         "rect_mm": [15.5, 0.0, 16.5, q05(gy - 1.0)]},
        {"keepout_id": "fa-vT", "layers": ["F.Cu"],
         "rect_mm": [15.5, q05(gy + 1.0), 16.5, 22.0]},
    ]


def _walls_fb(rng):
    """B 墙单闸：B-only 竖墙 x∈[15.5,16.5]，缝宽 2.0 于种子位。"""
    gy = q05(6.0 + rng.random() * 10.0)
    return [
        {"keepout_id": "fb-bB", "layers": ["B.Cu"],
         "rect_mm": [15.5, 0.0, 16.5, q05(gy - 1.0)]},
        {"keepout_id": "fb-bT", "layers": ["B.Cu"],
         "rect_mm": [15.5, q05(gy + 1.0), 16.5, 22.0]},
    ]


def _walls_fc(n):
    """内层双窗匹配：F-only 与 B-only 全高墙同位 x∈[15.5,16.5]（F/B 皆无直穿）；
    In1-only 墙堵 y≥w（窗口 y<w）、In2-only 墙堵 y≤H−w（窗口 y>H−w），
    w=⌈n/2⌉ 道（1mm/道）。全部网必须经内层窗口过墙=网→窗口二部匹配。"""
    w = float((n + 1) // 2)
    return [
        {"keepout_id": "fc-f", "layers": ["F.Cu"],
         "rect_mm": [15.5, 0.0, 16.5, 22.0]},
        {"keepout_id": "fc-b", "layers": ["B.Cu"],
         "rect_mm": [15.5, 0.0, 16.5, 22.0]},
        {"keepout_id": "fc-i1", "layers": ["In1.Cu"],
         "rect_mm": [15.5, w, 16.5, 22.0]},
        {"keepout_id": "fc-i2", "layers": ["In2.Cu"],
         "rect_mm": [15.5, 0.0, 16.5, q05(H - w)]},
    ]


def build_board(sid):
    n = int(sid[-2:])
    fam = sid[3:5]
    seed = seed_for(sid)
    rng = random.Random(seed)
    ys = spaced_values(rng, n, 3.0, H - 3.0, 2.0)
    rng.shuffle(ys)  # 打乱网号↔y 的单调对应，制造匹配张力（否则贪心=最优）
    rules = {"grid_mm": 0.25, "clearance_mm": 0.3,
             "width_mm": {"default": 0.3, "clock": 0.4},
             "via": {"pad_mm": 0.6, "hole_mm": 0.3},
             "allowed_layers": {"default": list(L4), "clock": list(INNER)}}
    walls = {"fa": _walls_fa(rng), "fb": _walls_fb(rng),
             "fc": _walls_fc(n)}[fam]
    if fam == "fa":
        # 横闸门两端封边到 x=6/34，留 6mm 侧道；竖墙缝与横墙缝错开由 seed 定
        pass
    pin_l, pin_r = {}, {}
    pads, nets, clks = [], [], []
    for i, nid in enumerate(net_ids_of(sid)):
        cl = net_class_of(sid, nid)
        if cl == "clock":
            clks.append(nid)
        pla_layer = pad_layer_of(sid, nid)
        pl = "U%d" % (i % 4 + 1)
        pr = "J%d" % (i % 4 + 1)
        pin_l[pl] = pin_l.get(pl, 0) + 1
        pin_r[pr] = pin_r.get(pr, 0) + 1
        pads.append({"pad_id": "%s-%d" % (pl, pin_l[pl]), "net_id": nid,
                     "x_mm": 3.0, "y_mm": ys[i], "w_mm": 1.2, "h_mm": 1.2,
                     "layer": pla_layer})
        pads.append({"pad_id": "%s-%d" % (pr, pin_r[pr]), "net_id": nid,
                     "x_mm": q05(W - 3.0), "y_mm": ys[i], "w_mm": 1.2,
                     "h_mm": 1.2, "layer": pla_layer})
        nets.append({"net_id": nid, "net_class": cl,
                     "endpoints": [pads[-2]["pad_id"], pads[-1]["pad_id"]]})
    relations = []
    if clks:
        relations.append({"relation_id": "CLK-1",
                          "relation_type": "clock_group",
                          "members": sorted(clks), "parent_id": None})
    if fam == "fb" and n >= 4:
        bus = [nid for nid in net_ids_of(sid) if pad_layer_of(sid, nid) == "F.Cu"]
        relations.append({"relation_id": "BUS-1", "relation_type": "bus",
                          "members": bus, "parent_id": None})
    obj = {"schema": "pcbflow.v4exp.board/1", "scenario_id": sid,
           "split": "calibration", "family": "layer4", "seed": seed,
           "board": {"bbox_mm": [0.0, 0.0, W, H], "layers": list(L4)},
           "rules": rules, "pads": pads, "nets": nets,
           "keepouts": walls, "relations": relations,
           "label": {"fa": "layer4-double-gate", "fb": "layer4-bwall-mixedpad",
                     "fc": "layer4-inner-matching"}[fam]}
    errs = relaxed_validate(obj)
    if errs:
        raise RuntimeError("%s 校验失败: %s" % (sid, errs))
    return obj


def relaxed_validate(obj):
    """scale_scenarios.relaxed_validate 的 layer4 版：net_id n1..n9、
    family 容 layer4、pad layer ∈ 板层集，其余不变量逐条保留。"""
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
        if not (nid.startswith("n") and nid[1:].isdigit()
                and int(nid[1:]) <= 9):
            errs.append("net_id 形状 %s" % nid)
        if p["layer"] not in layer_set:
            errs.append("%s 焊盘层非法 %s" % (pid, p["layer"]))
        pad_net[pid] = nid
        for k in ("x_mm", "y_mm"):
            if not half_ok(p[k]):
                errs.append("%s.%s 非 0.5 倍数" % (pid, k))
            if not (bbox[0] <= p[k] <= bbox[2] if k == "x_mm"
                    else bbox[1] <= p[k] <= bbox[3]):
                errs.append("%s.%s 出界" % (pid, k))
    for kp in obj["pads"]:
        for k in obj["keepouts"]:
            x0, y0, x1, y1 = k["rect_mm"]
            dx = max(x0 - kp["x_mm"], 0.0, kp["x_mm"] - x1)
            dy = max(y0 - kp["y_mm"], 0.0, kp["y_mm"] - y1)
            if (dx * dx + dy * dy) ** 0.5 < 1.0:
                errs.append("pad %s 距 keepout %s 过近"
                            % (kp["pad_id"], k["keepout_id"]))
    pads = obj["pads"]
    for i in range(len(pads)):
        for j in range(i + 1, len(pads)):
            d = ((pads[i]["x_mm"] - pads[j]["x_mm"]) ** 2
                 + (pads[i]["y_mm"] - pads[j]["y_mm"]) ** 2) ** 0.5
            if d < 2.0:
                errs.append("pad %s/%s 间距 %.2f < 2mm"
                            % (pads[i]["pad_id"], pads[j]["pad_id"], d))
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
        a = next(p for p in pads if p["pad_id"] == nt["endpoints"][0])
        b = next(p for p in pads if p["pad_id"] == nt["endpoints"][1])
        dist = ((a["x_mm"] - b["x_mm"]) ** 2 + (a["y_mm"] - b["y_mm"]) ** 2) ** 0.5
        if dist < 8.0:
            errs.append("%s endpoint 间距 %.2f < 8mm" % (nid, dist))
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


# ---------------------------------------------------------------- 快照/求解

_BOARD_CACHE = {}


def load_board(sid):
    if sid not in _BOARD_CACHE:
        with open(os.path.join(P0, "board-%s.json" % sid),
                  encoding="utf-8") as f:
            _BOARD_CACHE[sid] = json.load(f)
    return _BOARD_CACHE[sid]


def pin_layers(value):
    return list(PIN_ALPHABET[value]) if value is not None else None


def static_allowed(sid, nid):
    board = load_board(sid)
    nt = next(x for x in board["nets"] if x["net_id"] == nid)
    al = board["rules"]["allowed_layers"]
    return al.get(nt["net_class"], al.get("default", L4))


def pad_layers(sid, nid):
    board = load_board(sid)
    nt = next(x for x in board["nets"] if x["net_id"] == nid)
    out = []
    for e in nt["endpoints"]:
        p = next(x for x in board["pads"] if x["pad_id"] == e)
        if p["layer"] not in out:
            out.append(p["layer"])
    return out


def pin_valid(sid, nid, value):
    """null 恒合法；钉值须 ⊇ 焊盘层集、⊆ 板层集、∩ 静态允许层 ≠ ∅。"""
    if value is None:
        return True
    if value not in PIN_ALPHABET:
        return False
    pl = pin_layers(value)
    if not set(pl) <= set(L4):
        return False
    if not set(pl) >= set(pad_layers(sid, nid)):
        return False
    return bool(set(pl) & set(static_allowed(sid, nid)))


def effective_set(sid, nid, value):
    """引擎实际生效的允许层 = 静态允许层 ∩ 钉集；null → None（自动）。"""
    if value is None:
        return None
    return frozenset(set(pin_layers(value)) & set(static_allowed(sid, nid)))


def expand_plan(sid, plan):
    """plan: {net: value|null}（缺网=null）。返回 (lex 序, layer_preferences)。
    非法钉值抛 ValueError（执行器计 invalid，不落 solve）。"""
    nets = net_ids_of(sid)
    for nid, v in (plan or {}).items():
        if nid not in nets:
            raise ValueError("未知网 %s" % nid)
        if not pin_valid(sid, nid, v):
            raise ValueError("非法钉值 %s=%s（焊盘层/静态允许层约束）"
                             % (nid, v))
    prefs = [{"net_id": nid, "layers": pin_layers(plan[nid])}
             for nid in nets if (plan or {}).get(nid) is not None]
    return list(nets), prefs


def solve_s1(sid, order, plan=None, group="S1"):
    _, prefs = expand_plan(sid, plan or {})
    req = {"route_order": [str(x) for x in order], "group": group}
    if prefs:
        req["layer_preferences"] = prefs
    run = router.solve_board(load_board(sid), req)
    m = run["metrics"]
    return {"sid": sid, "order": [str(x) for x in order],
            "plan": {k: v for k, v in (plan or {}).items() if v is not None},
            "objective": m["objective"] if m["all_connected"] else None,
            "all_connected": m["all_connected"], "status": run["status"],
            "violations": m["violations"], "nodes": m["search_nodes"],
            "run": run}


def _worker(arg):
    sid, order, plan = arg
    r = solve_s1(sid, order, plan, "S1-P0")
    r.pop("run")
    return r


def _pool_map(jobs, procs):
    with Pool(procs) as pool:
        return pool.map(_worker, jobs)


def _write(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, indent=1, sort_keys=True, ensure_ascii=False)


def plan_space(sid):
    """每网合法钉值（按引擎有效集去重：静态∩钉集相同者只留字典序最小值；
    空集有效集=必败钉直接剔除——钉后无允许层的网必 fail-stop，非模型决策）。"""
    space = {}
    for nid in net_ids_of(sid):
        by_eff = {}
        for v in PIN_ALPHABET:
            if not pin_valid(sid, nid, v):
                continue
            eff = effective_set(sid, nid, v)
            if eff is not None and not eff:
                continue
            key = None if eff is None else tuple(sorted(eff))
            if key not in by_eff or v < by_eff[key]:
                by_eff[key] = v
        space[nid] = sorted(by_eff.values(), key=lambda v: (v is not None, v))
    return space


def iter_plans(sid, cap):
    """合法层计划组合；组合数 ≤ cap 精确枚举，否则返回 None（走抽样）。"""
    space = plan_space(sid)
    total = 1
    for v in space.values():
        total *= len(v)
    if total > cap:
        return None
    combos = []
    for tup in itertools.product(*[space[n] for n in net_ids_of(sid)]):
        combos.append(dict(zip(net_ids_of(sid), tup)))
    return combos


def sample_plans(sid, count, salt):
    space = plan_space(sid)
    nets = net_ids_of(sid)
    base = seed_for(sid) ^ int.from_bytes(
        hashlib.sha256(salt.encode()).digest()[:4], "big")
    out, seen = [], set()
    rng = random.Random(base)
    tries = 0
    while len(out) < count and tries < count * 20:
        tries += 1
        plan = {n: rng.choice(space[n]) for n in nets}
        key = tuple(sorted((k, str(v)) for k, v in plan.items()))
        if key in seen:
            continue
        seen.add(key)
        out.append(plan)
    return out


# ---------------------------------------------------------------- 子命令

def cmd_gen(_):
    os.makedirs(P0, exist_ok=True)
    import pcbflow.v4exp.model as _m
    manifest = []
    for sid in ORDERED_SIDS:
        obj = build_board(sid)
        path = os.path.join(P0, "board-%s.json" % sid)
        _m.write_json(path, obj)
        manifest.append({"scenario_id": sid, "n": int(sid[-2:]),
                         "seed": obj["seed"],
                         "sha256": hashlib.sha256(
                             json.dumps(obj, sort_keys=True,
                                        ensure_ascii=False).encode("utf-8")
                         ).hexdigest()})
        print("gen: %s clocks=%s" % (sid, [x["net_id"] for x in obj["nets"]
                                           if x["net_class"] == "clock"]))
    _write(os.path.join(P0, "manifest.json"), {
        "population": ORDERED_SIDS,
        "note": "EXP-S1 四层人口；schema 偏差=family=layer4；"
                "钉层字母表=%s" % [v or "null" for v in PIN_ALPHABET],
        "scenarios": manifest})


def cmd_prescreen(args):
    cap = args.cap
    rows = []
    for sid in ORDERED_SIDS:
        nets = net_ids_of(sid)
        t0 = __import__("time").time()
        base = solve_s1(sid, nets, {}, "S1-PRE")
        dt = __import__("time").time() - t0
        plans = iter_plans(sid, cap)
        mode = "exact"
        if plans is None:
            mode = "sample%d" % args.sample_n
            plans = sample_plans(sid, args.sample_n, "prescreen")
        jobs = [(sid, nets, p) for p in plans]
        res = _pool_map(jobs, procs=args.procs)
        objs = sorted(r["objective"] for r in res if r["all_connected"])
        ceil_min = objs[0] if objs else None
        base_obj = base["objective"] if base["all_connected"] else None
        head = (round(base_obj - ceil_min, 2)
                if base_obj is not None and ceil_min is not None else None)
        rows.append({"sid": sid, "base_sat": base["all_connected"],
                     "base": base_obj, "solve_s": round(dt, 2),
                     "mode": mode, "plans": len(plans),
                     "sat_rate": round(len(objs) / float(len(res)), 3),
                     "ceiling": ceil_min, "headroom": head})
        print("%s base=%s (%.1fs) %s plans=%d sat=%.2f ceiling=%s "
              "headroom=%s" % (sid, base_obj, dt, mode, len(plans),
                               len(objs) / float(len(res)), ceil_min, head))
    _write(os.path.join(P0, "prescreen.json"), {"rows": rows})


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("gen")
    p = sub.add_parser("prescreen")
    p.add_argument("--cap", type=int, default=5000)
    p.add_argument("--sample-n", type=int, default=500)
    p.add_argument("--procs", type=int, default=10)
    args = ap.parse_args()
    {"gen": cmd_gen, "prescreen": cmd_prescreen}[args.cmd](args)


if __name__ == "__main__":
    main()
