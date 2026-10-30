"""pcbflow.v4exp.cmp_scenarios -- v4cmp 扩量场景生成器（112 场景）。

在 gen_scenarios.py 的 f1..f5 族函数之上（seed 策略、_post_check、PadAlloc、
spaced_values 全部复用；随机性一律 sha256(sid) 派生的确定性种子，供可重放
实验使用，非加密用途）新增：

* 每族 serial 扩量：dev 01-12 / cal 13-16 / hol 17-20（serial 决定
  scenario_id，seed=sha256(sid) 前 4 字节，故与上一轮 serial 01-10 的
  场景逐实例不同）；
* 新拓扑族 f6/f7/f8 只出现在 holdout（serial 01-04），dev/cal 零样本
  ——满足任务书 §7.5 "真正未见拓扑族"留出；
* canonical_geometry_hash：对 (bbox, layers, rules, pads, nets, keepouts,
  relations) 剔除 scenario_id/split/family/seed/label 后的 canonical JSON
  取 sha256 ——纯几何，跨 split 查重用。

CLI（stdin JSON -> stdout；无 argv、无 wall-clock）：
  {"out_dir": "out/v4-comparative-experiment"}
另提供 generate_scenario(sid) 纯函数（runner 消费）。

确定性：无时钟、无网络；同 out_dir 重跑逐字节一致。
"""

from __future__ import annotations

import hashlib
import os
import random

from . import gen_scenarios, model
from .gen_scenarios import (BBOX, COMPONENTS, LAYERS, PadAlloc, _post_check,
                            seed_for, spaced_values)
from .model import Keepout, Net, Relation, Rules

FAMILIES_V2 = ("f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8")

#: family -> [(split3, serial range)]
SERIALS_V2 = {
    "f1": [("dev", range(1, 13)), ("cal", range(13, 17)),
           ("hol", range(17, 21))],
    "f2": [("dev", range(1, 13)), ("cal", range(13, 17)),
           ("hol", range(17, 21))],
    "f3": [("dev", range(1, 13)), ("cal", range(13, 17)),
           ("hol", range(17, 21))],
    "f4": [("dev", range(1, 13)), ("cal", range(13, 17)),
           ("hol", range(17, 21))],
    "f5": [("dev", range(1, 13)), ("cal", range(13, 17)),
           ("hol", range(17, 21))],
    "f6": [("hol", range(1, 5))],
    "f7": [("hol", range(1, 5))],
    "f8": [("hol", range(1, 5))],
}
SPLIT_NAME = {"dev": "development", "cal": "calibration",
              "hol": "holdout"}


def _finish_v2(scenario_id, split, family, seed, pads, nets, keepouts,
               relations, label) -> model.Board:
    board = model.Board(scenario_id=scenario_id, split=split, family=family,
                        seed=seed, bbox_mm=list(BBOX), layers=list(LAYERS),
                        rules=Rules(), pads=pads, nets=nets,
                        keepouts=keepouts, relations=relations, label=label)
    _post_check(board)
    return board


# ---------------------------------------------------------------- 族扩展/新族

def gen_f3_v2(sid, split, seed, rng) -> model.Board:
    """f3 参数扩展版（族语义不变：3 bus + 1 clock(F.Cu only) + 1 default，
    BUS-1/CLK-1 两 relation）。原 gen_f3 仅 12 组合，撑不起每族 20 实例；
    扩展 j/xl/xr/行距 d 至 5×3×3×2=90 组合。"""
    from .model import Net as _Net
    alloc = PadAlloc()
    j = rng.choice([0.0, 0.5, 1.0, 1.5, 2.0])
    xl = rng.choice([4.0, 5.0, 6.0])
    xr = rng.choice([34.0, 35.0, 36.0])
    d = rng.choice([2.0, 2.5])
    y0 = 4.0 + j
    rows = {"n1": y0, "n2": y0 + d, "n3": y0 + 2.0 * d,
            "n4": y0 + 2.0 * d + 5.0, "n5": y0 + 2.0 * d + 8.0}
    classes = {"n1": "default", "n2": "default", "n3": "default",
               "n4": "clock", "n5": "default"}
    comps = {"n1": ("U1", "U2"), "n2": ("J2", "J3"), "n3": ("U3", "U4"),
             "n4": ("U1", "J3"), "n5": ("U2", "U4")}
    pads, nets = [], []
    for nid in ("n1", "n2", "n3", "n4", "n5"):
        ca, cb = comps[nid]
        pads.append(alloc.pad(ca, nid, xl, rows[nid]))
        pads.append(alloc.pad(cb, nid, xr, rows[nid]))
        nets.append(_Net(nid, classes[nid],
                         [pads[-2].pad_id, pads[-1].pad_id]))
    relations = [Relation("BUS-1", "bus", ["n1", "n2", "n3"], None),
                 Relation("CLK-1", "clock_group", ["n4"], None)]
    return _finish_v2(sid, split, "f3", seed, pads, nets, [], relations,
                      "satisfiable")


def gen_f6(sid, split, seed, rng) -> model.Board:
    """f6 交错双层墙：3 道窄墙 F.Cu/B.Cu 交替、缝隙上下错开。

    default 类 net 两层皆可，跨墙需在缝间换层，产生真实 via 决策；
    任一缝对双层并集都开放，恒可满足。"""
    alloc = PadAlloc()
    n = rng.choice([3, 4, 5])
    x_a = rng.choice([10.0, 11.0])
    y_b = rng.choice([16.0, 17.0])
    x_b = rng.choice([19.0, 20.0, 21.0])
    x_c = rng.choice([28.0, 29.0])
    keepouts = [
        Keepout("k1", [x_a, 3.0, x_a + 1.0, 20.0], ["F.Cu"]),
        Keepout("k2", [x_b, y_b, x_b + 1.0, 27.0], ["B.Cu"]),
        Keepout("k3", [x_c, 3.0, x_c + 1.0, 20.0], ["F.Cu"]),
    ]
    lys = spaced_values(rng, n, 4.0, 26.0, 3.0)
    rys = spaced_values(rng, n, 4.0, 26.0, 3.0)
    pads, nets = [], []
    for i in range(n):
        nid = f"n{i + 1}"
        ca, cb = COMPONENTS[2 * i % 6], COMPONENTS[(2 * i + 1) % 6]
        pads.append(alloc.pad(ca, nid, 4.0, lys[i]))
        pads.append(alloc.pad(cb, nid, 36.0, rys[i]))
        nets.append(Net(nid, "default", [pads[-2].pad_id, pads[-1].pad_id]))
    return _finish_v2(sid, split, "f6", seed, pads, nets, keepouts, [],
                      "satisfiable")


def gen_f7(sid, split, seed, rng) -> model.Board:
    """f7 层级关系：主总线 4 成员 + 子总线（parent 指向主总线，成员交叠
    n3/n4）+ 差分对 + 时钟组（8 net）。无 keepout——难度在关系/从属
    语义而非几何。"""
    alloc = PadAlloc()
    xl = rng.choice([3.0, 4.0])
    xr = rng.choice([36.0, 37.0])
    y0 = rng.choice([3.0, 3.5, 4.0])
    ys = [round(y0 + 3.0 * i, 2) for i in range(8)]  # 行距 3mm，末行 ≤25
    specs = [  # (net_id, class, component pair)
        ("n1", "default", ("U1", "U2")), ("n2", "default", ("J2", "J3")),
        ("n3", "default", ("U3", "U4")), ("n4", "default", ("U1", "J2")),
        ("n5", "default", ("J3", "U3")), ("n6", "default", ("U4", "U1")),
        ("n7", "default", ("U2", "J2")), ("n8", "clock", ("U3", "J3")),
    ]
    pads, nets = [], []
    for i, (nid, cls, (ca, cb)) in enumerate(specs):
        pads.append(alloc.pad(ca, nid, xl, ys[i]))
        pads.append(alloc.pad(cb, nid, xr, ys[i]))
        nets.append(Net(nid, cls, [pads[-2].pad_id, pads[-1].pad_id]))
    relations = [
        Relation("BUS-MAIN", "bus", ["n1", "n2", "n3", "n4"], None),
        Relation("BUS-SUB", "bus", ["n3", "n4", "n5"], "BUS-MAIN"),
        Relation("DP-1", "differential_pair", ["n6", "n7"], None),
        Relation("CLK-1", "clock_group", ["n8"], None),
    ]
    return _finish_v2(sid, split, "f7", seed, pads, nets, [], relations,
                      "satisfiable")


def gen_f8(sid, split, seed, rng) -> model.Board:
    """f8 交错竖墙挤流：3 道双层竖墙（k1/k3 封底留顶缝、k2 封顶留底缝），
    6-7 net 左右横穿。相邻缝的开放带互不贯通，全部 net 争夺错开的
    上/下缝区，拥挤度显著高于 f2；缝宽 >=12mm，恒可满足。"""
    alloc = PadAlloc()
    n = rng.choice([6, 7])
    keepouts = [
        Keepout("k1", [13.0, 0.0, 14.0, 18.0], list(LAYERS)),
        Keepout("k2", [20.0, 12.0, 21.0, 30.0], list(LAYERS)),
        Keepout("k3", [27.0, 0.0, 28.0, 18.0], list(LAYERS)),
    ]
    lys = spaced_values(rng, n, 3.0, 27.0, 3.0)
    rys = spaced_values(rng, n, 3.0, 27.0, 3.0)
    pads, nets = [], []
    for i in range(n):
        nid = f"n{i + 1}"
        ca, cb = COMPONENTS[2 * i % 6], COMPONENTS[(2 * i + 1) % 6]
        pads.append(alloc.pad(ca, nid, 2.0, lys[i]))
        pads.append(alloc.pad(cb, nid, 38.0, rys[i]))
        nets.append(Net(nid, "default", [pads[-2].pad_id, pads[-1].pad_id]))
    return _finish_v2(sid, split, "f8", seed, pads, nets, keepouts, [],
                      "satisfiable")


GENS_V2 = {"f1": gen_scenarios.gen_f1, "f2": gen_scenarios.gen_f2,
           "f3": gen_f3_v2, "f4": gen_scenarios.gen_f4,
           "f5": gen_scenarios.gen_f5, "f6": gen_f6, "f7": gen_f7,
           "f8": gen_f8}


# ---------------------------------------------------------------- 查询与 hash

def all_scenario_ids() -> list:
    out = []
    for fam in FAMILIES_V2:
        for split3, serials in SERIALS_V2[fam]:
            for s in serials:
                out.append("%s-%s-%02d" % (split3, fam, s))
    return sorted(out)


MAX_DEDUP_ATTEMPTS = 64


def seed_for_attempt(sid: str, attempt: int) -> int:
    """attempt 0 = sha256(sid) 前 4 字节（与上一轮同策略）；
    attempt >0 = sha256(sid|attempt:k) 前 4 字节（去重重生成盐）。"""
    if attempt == 0:
        return seed_for(sid)
    token = "%s|attempt:%d" % (sid, attempt)
    return int.from_bytes(hashlib.sha256(token.encode("utf-8")).digest()[:4],
                          "big")


def generate_scenario(sid: str, attempt: int = 0) -> dict:
    """按 scenario_id + attempt 生成板对象（校验通过）；与批量生成一致。"""
    split3, fam, _serial = sid.split("-", 2)
    if split3 not in SPLIT_NAME or fam not in GENS_V2:
        raise ValueError("未知 scenario_id: %s" % sid)
    seed = seed_for_attempt(sid, attempt)
    # board.split 合同要求全名（model.SPLITS），sid 前缀只是缩写
    board = GENS_V2[fam](sid, SPLIT_NAME[split3], seed, random.Random(seed))
    obj = board.to_obj()
    errs = model.validate_board(obj)
    if errs:
        raise RuntimeError("%s 生成校验失败: %s" % (sid, errs))
    return obj


def _norm(v):
    return round(v, 3) if isinstance(v, float) else v


def _to_plain(obj):
    if isinstance(obj, dict):
        return {k: _to_plain(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_plain(v) for v in obj]
    return obj


def canonical_geometry_hash(board_obj: dict) -> str:
    """纯几何 canonical hash（剔除实例元数据与 split/family/seed/label；
    net 端点以坐标对表达，不依赖 pad_id 组件命名）。"""
    pad_geom = {p["pad_id"]: (_norm(p["x_mm"]), _norm(p["y_mm"]))
                for p in board_obj["pads"]}
    pad_net = {p["pad_id"]: p["net_id"] for p in board_obj["pads"]}
    geom = {
        "bbox": [[_norm(x) for x in board_obj["board"]["bbox_mm"]],
                 list(board_obj["board"]["layers"])],
        "rules": {k: _to_plain(v)
                  for k, v in board_obj["rules"].items()
                  if k != "grid_mm"},
        "pads": sorted(
            (_norm(p["x_mm"]), _norm(p["y_mm"]), _norm(p["w_mm"]),
             _norm(p["h_mm"]), p["layer"], p["net_id"])
            for p in board_obj["pads"]),
        "nets": sorted(
            (sorted(pad_geom[e] for e in n["endpoints"]), n["net_class"],
             n["net_id"])
            for n in board_obj["nets"]),
        "keepouts": sorted(
            (_norm(k["rect_mm"][0]), _norm(k["rect_mm"][1]),
             _norm(k["rect_mm"][2]), _norm(k["rect_mm"][3]),
             sorted(k["layers"]))
            for k in board_obj.get("keepouts", [])),
        "relations": sorted(
            (r["relation_type"],
             sorted(r["members"]), r.get("parent_id"))
            for r in board_obj.get("relations", [])),
    }
    del pad_net  # 仅备注：pad_id 身份不参与 hash
    text = model.canonical_json(_to_plain(geom))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------- 主流程

def generate(out_dir: str) -> dict:
    os.makedirs(out_dir, exist_ok=True)
    entries = []
    seen_hashes = {}
    for sid in all_scenario_ids():
        obj = None
        gh = None
        attempt = None
        for attempt in range(MAX_DEDUP_ATTEMPTS):
            cand = generate_scenario(sid, attempt)
            cand_gh = canonical_geometry_hash(cand)
            if cand_gh in seen_hashes:
                continue  # 确定性盐重生成，直到几何唯一
            obj, gh = cand, cand_gh
            break
        if obj is None:
            raise RuntimeError(
                "%s 在 %d 次 attempt 内未获得唯一几何"
                % (sid, MAX_DEDUP_ATTEMPTS))
        seen_hashes[gh] = sid
        path = os.path.join(out_dir, "board-snapshot-%s.json" % sid)
        model.write_json(path, obj)
        split3, fam, _serial = sid.split("-", 2)
        entries.append({"scenario_id": sid, "family": fam,
                        "split": SPLIT_NAME[split3],
                        "label": obj["label"],
                        "dedup_attempt": attempt,
                        "board_snapshot_sha256": model.sha256_of(obj),
                        "canonical_geometry_hash": gh})
    entries.sort(key=lambda e: e["scenario_id"])
    families = {}
    for fam in FAMILIES_V2:
        fam_splits = {SPLIT_NAME[s3]: sorted(
            e["scenario_id"] for e in entries
            if e["family"] == fam and e["split"] == SPLIT_NAME[s3])
            for s3 in SPLIT_NAME}
        families[fam] = {k: v for k, v in fam_splits.items() if v}
    counts = {sp: sum(1 for e in entries if e["split"] == sp)
              for sp in ("development", "calibration", "holdout")}
    manifest = {
        "schema": "pcbflow.v4cmp.scenario-manifest/2",
        "seed_policy": "attempt 0: seed = sha256(scenario_id) 前 4 字节大端整数"
                       "（与上一轮同策略）；窄参数空间族（如 f3 仅 12 组合）"
                       "在族内 16 实例下必然碰撞，故按确定性盐"
                       " sha256(sid|attempt:k) 重生成直至 canonical 几何唯一"
                       "（上限 64 次），每场景 attempt 数记入 manifest；"
                       "全部随机性由 seed 派生，可重放，非加密用途",
        "split_policy": {
            "isolation": "per-family",
            "declaration": "f1..f5 每族 dev 12 / cal 4 / hol 4（serial 与上一轮"
                           "错开：dev 01-12、cal 13-16、hol 17-20；"
                           "seed 由 sid 决定故逐实例不同）；f6/f7/f8 仅 holdout"
                           "（hol serial 01-04）——dev/cal 对未见拓扑族零样本；"
                           "上一轮 serial 01-10 的场景不在本 manifest 内，"
                           "不得复用。族定义：f1/f2/f4/f5 逐字节复用上一轮"
                           " gen_scenarios 族函数；f3 参数空间扩展"
                           "（gen_f3_v2，语义不变：3 bus + clock + default，"
                           " BUS-1/CLK-1 relation；原 12 组合撑不起每族 20"
                           " 实例，扩至 90）；f7 行起点加抖动（xl/xr/y0 共"
                           " 12 组合）。全部扩展仅作用于本轮新 serial。",
            "per_family_counts": {
                fam: {SPLIT_NAME[s3]: len(list(sr))
                      for s3, sr in SERIALS_V2[fam]}
                for fam in FAMILIES_V2}},
        "counts": counts,
        "families": families,
        "scenarios": entries}
    model.write_json(os.path.join(out_dir, "scenario-manifest.json"),
                     manifest)
    return {"scenarios": len(entries), "counts": counts,
            "out_dir": out_dir, "manifest": "scenario-manifest.json"}


def main():
    import json as _json
    import sys
    cfg = model.read_stdin_json()
    summary = generate(cfg.get("out_dir")
                       or "out/v4-comparative-experiment")
    sys.stdout.write(_json.dumps(summary, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
