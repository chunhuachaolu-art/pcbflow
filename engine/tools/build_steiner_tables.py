# -*- coding: utf-8 -*-
"""POT 表生成器（V5-R1 W-1；生成协议=本工具单源）。

分层形态枚举采样协议（确定性，重跑逐位一致；2026-09-25 修订版 v2）：
1. **网格全枚举**：度数 n 的 n×n 整数网格（0..n-1）²全部 n 点子集（去序）
   —— C(n²,n) 实例（3:84 / 4:1820 / 5:53130），含全部共线/共 x/共 y 退化
   模式与近间距区域=FLUTE 表生成的完备枚举形态。
2. **随机补充采样**：大间距随机整数坐标（独立 Random(seed)），按形态桶
   每桶 --per-shape 实例补充（稀疏远间距区域的结构切换代表）。
3. 每实例跑 v5.steiner.exact_rsmt（Dreyfus-Wagner 精确解）→ 树分解 → 秩化
   结构（H/V 段合并）→ 入该形态桶去重。
4. 验证：独立 seed 的随机对照集（每形态 --verify-per-shape 实例，span 大）
   上，查表解总长 vs DW 精确解总长逐件比对（容差 1e-9）；覆盖率/最优率
   逐度数打印。非全 100% → 退出码 1（表仍写回，缺口统计供报告如实引用）。
5. 写回 v5/steiner.py 的 _POT_TABLES 区（标记区文本替换，canonical 字面量：
   度数升序、形态键升序、桶内结构排序去重）。

用法：python tools/build_steiner_tables.py [--per-shape N] [--verify-per-shape N]
        [--seed S] [--degrees 3,4,5] [--no-grid] [--write]
"""
import argparse
import itertools
import random
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from v5 import steiner  # noqa: E402

MARK_BEGIN = "_POT_TABLES = {"
MARK_END = "}"


def gen_instance(rng, n, span=80):
    pts = set()
    guard = 0
    while len(pts) < n and guard < 10000:
        pts.add((rng.randrange(span + 1), rng.randrange(span + 1)))
        guard += 1
    return sorted(pts)


def grid_instances(n):
    """n×n 网格全部 n 点子集（去序；确定性生成序）。"""
    cells = [(x, y) for x in range(n) for y in range(n)]
    for combo in itertools.combinations(cells, n):
        yield list(combo)


def extract_structure(points, nodes, edges):
    """DW 树分解 → 秩化结构（段合并去重）。"""
    pts = list(points)
    xs = sorted({p[0] for p in pts})
    ys = sorted({p[1] for p in pts})
    xi = {v: k for k, v in enumerate(xs)}
    yi = {v: k for k, v in enumerate(ys)}
    h_segs = set()
    v_segs = set()
    for a, b in edges:
        (x0, y0), (x1, y1) = nodes[a], nodes[b]
        if abs(y0 - y1) <= steiner._EPS:
            h_segs.add((yi[y0], min(xi[x0], xi[x1]), max(xi[x0], xi[x1])))
        elif abs(x0 - x1) <= steiner._EPS:
            v_segs.add((xi[x0], min(yi[y0], yi[y1]), max(yi[y0], yi[y1])))
        else:
            raise AssertionError("树边非轴对齐（细分合同破坏）")

    def merge(segs):
        out = []
        by_line = {}
        for a, lo, hi in segs:
            by_line.setdefault(a, []).append((lo, hi))
        for line in sorted(by_line):
            ivs = sorted(by_line[line])
            cur_lo, cur_hi = ivs[0]
            for lo, hi in ivs[1:]:
                if lo <= cur_hi:      # 相接或重叠
                    cur_hi = max(cur_hi, hi)
                else:
                    out.append((line, cur_lo, cur_hi))
                    cur_lo, cur_hi = lo, hi
            out.append((line, cur_lo, cur_hi))
        return out

    return (tuple(merge(h_segs)), tuple(merge(v_segs)))


def main(argv=None):
    ap = argparse.ArgumentParser(description="分层形态枚举 POT 表生成器")
    ap.add_argument("--per-shape", type=int, default=8)
    ap.add_argument("--verify-per-shape", type=int, default=3)
    ap.add_argument("--seed", type=int, default=20260925)
    ap.add_argument("--degrees", default="3,4,5")
    ap.add_argument("--no-grid", action="store_true",
                    help="跳过网格全枚举（只随机采样）")
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args(argv)
    degrees = [int(x) for x in args.degrees.split(",")]

    tables = {}
    for n in degrees:
        rng = random.Random(args.seed * 1000 + n)
        bucket = {}          # 形态键 -> set(结构)
        count = {}           # 形态键 -> 已采实例数（随机补充计数）

        def feed(pts):
            total, nodes, edges = steiner.exact_rsmt(pts)
            if not edges:
                return
            key = steiner._shape_key(pts)
            bucket.setdefault(key, set()).add(extract_structure(pts, nodes, edges))

        inst_grid = 0
        if not args.no_grid:
            for pts in grid_instances(n):
                feed(pts)
                inst_grid += 1
        inst_rand = 0
        while inst_rand < 400000:
            pts = gen_instance(rng, n)
            inst_rand += 1
            key = steiner._shape_key(pts)
            if count.get(key, 0) >= args.per_shape:
                continue
            count[key] = count.get(key, 0) + 1
            feed(pts)
        tables[n] = bucket
        print("degree=%d grid=%d rand=%d shapes=%d structs=%d"
              % (n, inst_grid, inst_rand, len(bucket),
                 sum(len(s) for s in bucket.values())), flush=True)

    # 内存注入 → 分层验证（独立 seed 偏移）
    steiner._POT_TABLES = {
        n: {k: [[list(s[0]), list(s[1])] for s in sorted(v)]
            for k, v in tables[n].items()} for n in degrees}
    ok_all = True
    for n in degrees:
        rng = random.Random(args.seed * 77 + n)
        cover = opt = total_v = 0
        worst_gap = 0.0
        seen = {}
        max_verify = max(20000, args.per_shape * max(1, len(tables[n])) * 4)
        while total_v < max_verify:
            if len(seen) >= len(tables[n]) and \
                    all(c >= args.verify_per_shape for c in seen.values()):
                break                             # 全部已知形态验够早停
            pts = gen_instance(rng, n)
            key = steiner._shape_key(pts)
            if seen.get(key, 0) >= args.verify_per_shape:
                continue
            seen[key] = seen.get(key, 0) + 1
            total_v += 1
            dw_len, _nn, _ee = steiner.exact_rsmt(pts)
            pot = steiner._pot_solve(pts)
            if pot is not None:
                cover += 1
                if pot[2] <= dw_len + 1e-9:
                    opt += 1
                else:
                    worst_gap = max(worst_gap, pot[2] - dw_len)
        print("degree=%d verify_instances=%d cover=%d/%d optimal=%d/%d "
              "worst_gap=%.3g" % (n, total_v, cover, total_v, opt, total_v,
                                  worst_gap), flush=True)
        if cover != total_v or opt != total_v:
            ok_all = False

    # 写回
    lines = ["_POT_TABLES = {"]
    for n in sorted(tables):
        lines.append("    %d: {" % n)
        for key in sorted(tables[n]):
            structs = sorted(tables[n][key])
            sx = "".join(str(i) for i in key[0])
            sy = "".join(str(i) for i in key[1])
            lines.append("        (%r, %r): [" % (tuple(key[0]), tuple(key[1])))
            for s in structs:
                h = ", ".join("(%d, %d, %d)" % t for t in s[0])
                v = ", ".join("(%d, %d, %d)" % t for t in s[1])
                lines.append("            ([%s], [%s])," % (h, v))
            lines.append("        ],")
        lines.append("    },")
    lines.append("}")
    block = "\n".join(lines) + "\n"

    src_path = os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "v5", "steiner.py")
    src = open(src_path, encoding="utf-8").read()
    i = src.index(MARK_BEGIN)
    # 表区=文件末块整替（嵌套花括号使首个 '}' 锚不可靠）
    new_src = src[:i] + block.rstrip("\n") + "\n"
    if args.write:
        open(src_path, "w", encoding="utf-8", newline="\n").write(new_src)
        print("WRITTEN: %s（表区 %d 字节）" % (src_path, len(block)))
    else:
        print("DRY-RUN（--write 写回；表区 %d 字节）" % len(block))
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
