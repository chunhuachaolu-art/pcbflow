"""V4exp 种子化场景生成器（50 场景 = 5 拓扑族 × 10）。

stdin 收 {"out_dir": "out/v4-experiment", "only_dev": false}；
输出 board-snapshot-<scenario_id>.json × N + scenario-manifest.json。

划分（family→split 隔离）：每族 f1..f5 内部独立 dev 6 / cal 2 / holdout 2，
序号 01-06=dev、07-08=cal、09-10=holdout；scenario_id = <split3>-<family>-<NN>。
seed = sha256(scenario_id) 前 4 字节大端整数；全部随机性由该 seed 派生，可重放。

确定性：无 wall-clock、路径只落 out/v4-experiment/、键序确定、LF 换行。
"""

from __future__ import annotations

import hashlib
import os
import random

from . import model
from .model import (Board, Keepout, Net, Pad, Relation, Rules, SPLITS)

# 历史 E0/E1 生成器固定为 f1..f5；v4cmp 的 f6..f8 仅由
# cmp_scenarios.py 消费，避免扩展 model.FAMILIES 改变历史生成器语义。
FAMILIES_LEGACY = ("f1", "f2", "f3", "f4", "f5")

SPLIT3 = {"development": "dev", "calibration": "cal", "holdout": "hol"}
SERIAL_SPLIT = [("development", range(1, 7)),
                ("calibration", range(7, 9)),
                ("holdout", range(9, 11))]
COMPONENTS = ["U1", "U2", "J2", "J3", "U3", "U4"]
PAD_W = 1.2
PAD_H = 1.2

BBOX = [0.0, 0.0, 40.0, 30.0]
LAYERS = ["F.Cu", "B.Cu"]


# ---------------------------------------------------------------- 种子与工具

def seed_for(scenario_id: str) -> int:
    digest = hashlib.sha256(scenario_id.encode("utf-8")).digest()
    return int.from_bytes(digest[:4], "big")


def scenario_ids(only_dev: bool) -> list:
    out = []
    for fam in FAMILIES_LEGACY:
        for split, serials in SERIAL_SPLIT:
            for s in serials:
                if only_dev and split != "development":
                    continue
                out.append((f"{SPLIT3[split]}-{fam}-{s:02d}", fam, split, s))
    return out


class PadAlloc:
    """组件/引脚号分配：pad_id 形如 U1-1 / J2-3，同一组件引脚号递增。"""

    def __init__(self):
        self.pin = {}

    def pad(self, comp: str, net_id: str, x, y) -> Pad:
        n = self.pin.get(comp, 0) + 1
        self.pin[comp] = n
        return Pad(f"{comp}-{n}", net_id, x, y, PAD_W, PAD_H, "F.Cu")


def spaced_values(rng: random.Random, count: int, lo: float, hi: float,
                  gap: float) -> list:
    """在 [lo,hi] 内取 count 个 0.5 倍数值，两两间距 >= gap（保证可行，
    经典有序统计法：0.5 格整数域内取有序随机数再叠加最小间距）。"""
    step = 0.5
    d = int(round(gap / step))
    mlo, mhi = int(round(lo / step)), int(round(hi / step))
    if count < 1:
        return []
    span = mhi - mlo - (count - 1) * d
    if span < 0:
        raise RuntimeError(f"spaced_values 不可行: count={count} lo={lo}"
                           f" hi={hi} gap={gap}")
    picks = sorted(rng.randint(0, span) for _ in range(count))
    return [step * (p + i * d + mlo) for i, p in enumerate(picks)]


# ---------------------------------------------------------------- 族生成

def _finish(scenario_id, split, family, seed, pads, nets, keepouts,
            relations, label) -> Board:
    board = Board(scenario_id=scenario_id, split=split, family=family,
                  seed=seed, bbox_mm=list(BBOX), layers=list(LAYERS),
                  rules=Rules(), pads=pads, nets=nets, keepouts=keepouts,
                  relations=relations, label=label)
    _post_check(board)
    return board


def _post_check(board: Board) -> None:
    """生成期自检：pad 中心到各 keepout 矩形的平面距离 >= 1.0mm
    （= pad 半宽 0.6 + 0.4 间隙 >= clearance 0.3；f5 环心 pad 到环内缘
    恰为 1.0mm，有意为之且 pad 本体不落入任何 keepout 矩形）、
    endpoint 间距 >= 8mm、pad 两两中心距 >= 2.0mm。
    违反即生成器 bug（响失败）。"""
    for p in board.pads:
        for k in board.keepouts:
            x0, y0, x1, y1 = k.rect_mm
            dx = max(x0 - p.x_mm, 0.0, p.x_mm - x1)
            dy = max(y0 - p.y_mm, 0.0, p.y_mm - y1)
            if (dx * dx + dy * dy) ** 0.5 < 1.0:
                raise RuntimeError(
                    f"{board.scenario_id}: pad {p.pad_id} 距 keepout"
                    f" {k.keepout_id} 过近")
    by_id = {p.pad_id: p for p in board.pads}
    for n in board.nets:
        a, b = (by_id[e] for e in n.endpoints)
        dist = ((a.x_mm - b.x_mm) ** 2 + (a.y_mm - b.y_mm) ** 2) ** 0.5
        if dist < 8.0:
            raise RuntimeError(f"{board.scenario_id}: net {n.net_id}"
                               f" endpoint 间距 {dist:.2f} < 8mm")
    pads = board.pads
    for i in range(len(pads)):
        for j in range(i + 1, len(pads)):
            d = ((pads[i].x_mm - pads[j].x_mm) ** 2
                 + (pads[i].y_mm - pads[j].y_mm) ** 2) ** 0.5
            if d < 2.0:
                raise RuntimeError(f"{board.scenario_id}: pad"
                                   f" {pads[i].pad_id}/{pads[j].pad_id}"
                                   f" 间距 {d:.2f} < 2mm")


def gen_f1(sid, split, seed, rng) -> Board:
    """f1 简单点对点：3-4 net，无 keepout，同层可达。"""
    alloc = PadAlloc()
    n = rng.choice([3, 4])
    lys = spaced_values(rng, n, 4.0, 26.0, 3.0)
    rys = spaced_values(rng, n, 4.0, 26.0, 3.0)
    pads, nets = [], []
    for i in range(n):
        nid = f"n{i + 1}"
        ca, cb = COMPONENTS[2 * i % 6], COMPONENTS[(2 * i + 1) % 6]
        pads.append(alloc.pad(ca, nid, rng.choice([3.0, 5.0]), lys[i]))
        pads.append(alloc.pad(cb, nid, rng.choice([35.0, 37.0]), rys[i]))
        nets.append(Net(nid, "default", [pads[-2].pad_id, pads[-1].pad_id]))
    return _finish(sid, split, "f1", seed, pads, nets, [], [],
                   "satisfiable")


def gen_f2(sid, split, seed, rng) -> Board:
    """f2 拥挤通道：4-6 net，两侧双层 keepout 纵向贯穿夹出中央走廊。

    布局保证玩具布线器可全部连通且走廊为唯一通道：net 按序分上/下组
    （上组 pad y <= 10，下组 y >= 20），每侧每槽位（左 x in {1,2,3}mm，
    右 x in {37,38,39}mm）组内唯一，通道竖段互不重叠；上行 net 从走廊
    下沿取行、下行从上沿取行，行间距 >= 1.0mm（走廊高 h = n+1mm）。
    顺序敏感性体现在后布的 net 只能拿更靠中的行。"""
    alloc = PadAlloc()
    n = rng.choice([4, 5, 6])
    h = n + 1.0
    cy = 15.0
    k1y1, k2y0 = cy - h / 2, cy + h / 2
    a = (n + 1) // 2
    b = n - a
    slot_l = [1.0, 2.0, 3.0]
    slot_r = [37.0, 38.0, 39.0]
    lys_a = spaced_values(rng, a, 3.0, 10.0, 2.0)
    rys_a = spaced_values(rng, a, 3.0, 10.0, 2.0)
    lys_b = spaced_values(rng, b, 20.0, 27.0, 2.0)
    rys_b = spaced_values(rng, b, 20.0, 27.0, 2.0)
    pads, nets = [], []
    for i in range(n):
        nid = f"n{i + 1}"
        if i < a:
            k, ly, ry = i, lys_a[i], rys_a[i]
        else:
            k, ly, ry = i - a, lys_b[i - a], rys_b[i - a]
        ca, cb = COMPONENTS[2 * i % 6], COMPONENTS[(2 * i + 1) % 6]
        pads.append(alloc.pad(ca, nid, slot_l[k], ly))
        pads.append(alloc.pad(cb, nid, slot_r[k], ry))
        nets.append(Net(nid, "default", [pads[-2].pad_id, pads[-1].pad_id]))
    keepouts = [Keepout("k1", [4.0, 0.0, 36.0, k1y1], list(LAYERS)),
                Keepout("k2", [4.0, k2y0, 36.0, 30.0], list(LAYERS))]
    return _finish(sid, split, "f2", seed, pads, nets, keepouts, [],
                   "satisfiable")


def gen_f3(sid, split, seed, rng) -> Board:
    """f3 总线+时钟：3 net bus + 1 clock（F.Cu only, 0.4mm）+ 1 普通 net。"""
    alloc = PadAlloc()
    j = rng.choice([0.0, 0.5, 1.0])
    xl = rng.choice([4.0, 5.0])
    xr = rng.choice([35.0, 36.0])
    y0 = 5.0 + j
    rows = {"n1": y0, "n2": y0 + 2.0, "n3": y0 + 4.0,
            "n4": y0 + 9.0, "n5": y0 + 12.0}
    classes = {"n1": "default", "n2": "default", "n3": "default",
               "n4": "clock", "n5": "default"}
    comps = {"n1": ("U1", "U2"), "n2": ("J2", "J3"), "n3": ("U3", "U4"),
             "n4": ("U1", "J3"), "n5": ("U2", "U4")}
    pads, nets = [], []
    for nid in ("n1", "n2", "n3", "n4", "n5"):
        ca, cb = comps[nid]
        pads.append(alloc.pad(ca, nid, xl, rows[nid]))
        pads.append(alloc.pad(cb, nid, xr, rows[nid]))
        nets.append(Net(nid, classes[nid],
                       [pads[-2].pad_id, pads[-1].pad_id]))
    relations = [Relation("BUS-1", "bus", ["n1", "n2", "n3"], None),
                 Relation("CLK-1", "clock_group", ["n4"], None)]
    return _finish(sid, split, "f3", seed, pads, nets, [], relations,
                   "satisfiable")


def gen_f4(sid, split, seed, rng) -> Board:
    """f4 keepout 迷宫：3-4 net，2-3 个 F.Cu keepout 迫使绕行或换层。"""
    alloc = PadAlloc()
    n = rng.choice([3, 4])
    wx = rng.choice([14.0, 16.0, 18.0])
    wy1 = rng.choice([18.0, 20.0, 22.0])
    lys = spaced_values(rng, n, 4.0, 26.0, 2.5)
    rys = spaced_values(rng, n, 4.0, 26.0, 2.5)
    keepouts = [Keepout("k1", [wx, 4.0, wx + 1.0, wy1], ["F.Cu"]),
                Keepout("k2", [wx + 6.0, 8.0, wx + 14.0, 9.0], ["F.Cu"])]
    if rng.random() < 0.5:
        keepouts.append(Keepout("k3", [10.0, 24.0, 14.0, 25.0], ["F.Cu"]))
    pads, nets = [], []
    for i in range(n):
        nid = f"n{i + 1}"
        ca, cb = COMPONENTS[2 * i % 6], COMPONENTS[(2 * i + 1) % 6]
        pads.append(alloc.pad(ca, nid, rng.choice([3.0, 5.0]), lys[i]))
        pads.append(alloc.pad(cb, nid, rng.choice([35.0, 37.0]), rys[i]))
        nets.append(Net(nid, "default", [pads[-2].pad_id, pads[-1].pad_id]))
    return _finish(sid, split, "f4", seed, pads, nets, keepouts, [],
                   "satisfiable")


def gen_f5(sid, split, seed, rng) -> Board:
    """f5 不可满足构造：n1 的一个 endpoint 被环形 keepout（双层）围死。"""
    alloc = PadAlloc()
    n = rng.choice([2, 3])
    ex = rng.choice([16.0, 18.0, 20.0, 22.0])
    ey = rng.choice([16.0, 18.0])
    ys = spaced_values(rng, 1 + 2 * (n - 1), 4.0, 12.0, 2.0)
    pads = [alloc.pad("U1", "n1", ex, ey),
            alloc.pad("J2", "n1", 5.0, ys[0])]
    nets = [Net("n1", "default", ["U1-1", "J2-1"])]
    k = 1
    for i in range(n - 1):
        nid = f"n{i + 2}"
        ca, cb = COMPONENTS[2 * (i + 1) % 6], COMPONENTS[(2 * (i + 1) + 1) % 6]
        pads.append(alloc.pad(ca, nid, 5.0, ys[k]))
        pads.append(alloc.pad(cb, nid, 35.0, ys[k + 1]))
        nets.append(Net(nid, "default", [pads[-2].pad_id, pads[-1].pad_id]))
        k += 2
    keepouts = [
        Keepout("k1", [ex - 3.0, ey - 3.0, ex + 3.0, ey - 1.0], list(LAYERS)),
        Keepout("k2", [ex - 3.0, ey + 1.0, ex + 3.0, ey + 3.0], list(LAYERS)),
        Keepout("k3", [ex - 3.0, ey - 1.0, ex - 1.0, ey + 1.0], list(LAYERS)),
        Keepout("k4", [ex + 1.0, ey - 1.0, ex + 3.0, ey + 1.0], list(LAYERS))]
    return _finish(sid, split, "f5", seed, pads, nets, keepouts, [],
                   "unsatisfiable")


GENS = {"f1": gen_f1, "f2": gen_f2, "f3": gen_f3, "f4": gen_f4,
        "f5": gen_f5}


# ---------------------------------------------------------------- 主流程

def generate(out_dir: str, only_dev: bool) -> dict:
    os.makedirs(out_dir, exist_ok=True)
    entries = []
    for sid, fam, split, serial in scenario_ids(only_dev):
        seed = seed_for(sid)
        board = GENS[fam](sid, split, seed, random.Random(seed))
        obj = board.to_obj()
        errs = model.validate_board(obj)
        if errs:
            raise RuntimeError(f"{sid} 生成校验失败: {errs}")
        path = os.path.join(out_dir, f"board-snapshot-{sid}.json")
        model.write_json(path, obj)
        entries.append({"scenario_id": sid, "family": fam, "split": split,
                        "label": board.label,
                        "board_snapshot_sha256": model.sha256_of(obj)})
    entries.sort(key=lambda e: e["scenario_id"])
    families = {}
    for fam in FAMILIES_LEGACY:
        families[fam] = {s: [e["scenario_id"] for e in entries
                             if e["family"] == fam and e["split"] == s]
                         for s in SPLITS}
    manifest = {
        "schema": model.SCHEMA_SCENARIO_MANIFEST,
        "seed_policy": "seed = sha256(scenario_id) 前 4 字节大端整数；"
                       "场景随机性全部由该 seed 派生，可重放",
        "split_policy": {
            "isolation": "per-family",
            "declaration": "划分在每族 f1..f5 内部独立进行"
                           "（development 6 / calibration 2 / holdout 2）；"
                           "同一 scenario_id 只属于一个 split，"
                           "不存在跨族混合板或变体泄漏",
            "per_family_counts": {"development": 6, "calibration": 2,
                                  "holdout": 2}},
        "families": families,
        "scenarios": entries}
    model.write_json(os.path.join(out_dir, "scenario-manifest.json"),
                     manifest)
    return {"scenarios": len(entries), "out_dir": out_dir,
            "boards_written": len(entries), "manifest": "scenario-manifest.json"}


def main() -> None:
    cfg = model.read_stdin_json()
    summary = generate(cfg.get("out_dir") or "out/v4-experiment",
                       bool(cfg.get("only_dev")))
    import json as _json
    import sys
    sys.stdout.write(_json.dumps(summary, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
