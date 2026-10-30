# -*- coding: utf-8 -*-
"""
P6-V8 图件席 程序化 QC（FIG-P6-07/08/09/10 四图；D-4 像素复核通道失效的兜底，
沿 R2 两份 QC 脚本 VERIFY-FIGS-P1.py＋_pixel_qc_supplementary.py 模式合并）：
  1) PNG 可解码＋尺寸（≥2400×1200，300dpi 级）＋文件 >10KB；
  2) 非白内容占比（防空白图，>3%）；
  3) 顶部标题带暗像素（标题存在性，>50）；
  4) 关键语义色存在性（按预期半区采样命中 ≥30 像素）；
  5) 重跑四个生成脚本捕获缺字形警告（Glyph/missing from font，应 0）；
  6) 零回改自查：figs/ 既有七件 sha16 与 figbatch-r1/figs-baseline.json 逐位一致。
Read 像素目检按任务书 D-4 记 channel-failed（本脚本非其替代，是程序化结构兜底）。
"""
import hashlib
import json
import os
import re
import subprocess
import sys

from PIL import Image

FIGS = "<ENGINE_ROOT>/out/paper-program-r2/figs"
SCRIPTS = FIGS + "/scripts"
BASELINE = "<ENGINE_ROOT>/out/paper-program-r2/figbatch-r1/figs-baseline.json"

FIGS_MINE = [
    ("FIG-P6-07-RUN5-RESOLUTION-SANKEY.png", [
        ("#2e7d32", "全幅"),   # 首波受理/首占者权威带+节点
        ("#c62828", "全幅"),   # 首波拒收带+节点
        ("#1565c0", "全幅"),   # 层消解带+节点
        ("#00838f", "右半"),   # 终态节点
    ]),
    ("FIG-P6-08-RIPUP-VS-DETOUR-COST.png", [
        ("#1565c0", "左半"),   # A 基线柱
        ("#ef6c00", "左半"),   # B 绕行柱
        ("#2e7d32", "全幅"),   # C 拆栅重布柱（左右两半各一）
        ("#c62828", "右半"),   # ∞ 截断阴影柱
    ]),
    ("FIG-P6-09-FBBOX-ESCAPE-SCHEMATIC.png", [
        ("#c62828", "全幅"),   # K1/K2 边框与拒收 bbox
        ("#6a1b9a", "右半"),   # MISC1 via-hub 链
        ("#ef6c00", "右半"),   # ETH FORCE 链
        ("#1565c0", "左半"),   # ETH 被拒 U 形路径
    ]),
    ("FIG-P6-10-V8-RUN8-13-ECON-WATERFALL.png", [
        ("#c62828", "左半"),   # (a) S4 烧损柱
        ("#1565c0", "左半"),   # (a) S6 重布柱
        ("#6a1b9a", "右半"),   # (b) 召回链/重试席柱
        ("#2e7d32", "右半"),   # (c) 常规四席柱
    ]),
]


def hex2rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def near(px, target, tol=28):
    return all(abs(a - b) <= tol for a, b in zip(px[:3], target))


def region(w, h, which):
    if which == "左半":
        return 0, w // 2, 0, h
    if which == "右半":
        return w // 2, w, 0, h
    return 0, w, 0, h


def main():
    fails = []

    for fname, checks in FIGS_MINE:
        path = os.path.join(FIGS, fname)
        tag = fname
        if not os.path.exists(path):
            fails.append(f"{tag}: 文件不存在")
            continue
        size = os.path.getsize(path)
        im = Image.open(path)
        im.load()
        w, h = im.size
        rgb = im.convert("RGB")
        px = rgb.load()
        # 1) 尺寸/大小
        if size <= 10 * 1024:
            fails.append(f"{tag}: 文件 {size}B ≤10KB")
        if w < 2400 or h < 1200:
            fails.append(f"{tag}: 尺寸 {w}×{h} < 2400×1200")
        # 2) 非白占比
        step = 7
        tot = nonwhite = 0
        for y in range(0, h, step):
            for x in range(0, w, step):
                tot += 1
                p = px[x, y]
                if not (p[0] > 245 and p[1] > 245 and p[2] > 245):
                    nonwhite += 1
        ratio = nonwhite / tot
        if ratio <= 0.03:
            fails.append(f"{tag}: 非白占比 {ratio:.3f} ≤3%")
        # 3) 顶部标题带暗像素
        dark_top = sum(1 for y in range(0, int(h * 0.18), 2) for x in range(0, w, 4)
                       if sum(px[x, y][:3]) < 420)
        if dark_top <= 50:
            fails.append(f"{tag}: 标题带暗像素 {dark_top} ≤50")
        # 4) 关键色存在性（半区采样命中）
        for hexc, half in checks:
            x0, x1, y0, y1 = region(w, h, half)
            target = hex2rgb(hexc)
            hit = 0
            for y in range(y0, y1, 5):
                for x in range(x0, x1, 5):
                    if near(px[x, y], target):
                        hit += 1
            if hit < 30:
                fails.append(f"{tag}: 关键色 {hexc}@{half} 命中 {hit} <30")
        print(f"PASS-结构 {fname}: {w}x{h} {size}B 非白{ratio:.1%} 标题带{dark_top} "
              f"色检{len(checks)}项")

    # 5) 重跑生成脚本，捕获缺字形警告
    gen_scripts = [
        "FIG-P6-07-RUN5-RESOLUTION-SANKEY.py",
        "FIG-P6-08-RIPUP-VS-DETOUR-COST.py",
        "FIG-P6-09-FBBOX-ESCAPE-SCHEMATIC.py",
        "FIG-P6-10-V8-RUN8-13-ECON-WATERFALL.py",
    ]
    for gs in gen_scripts:
        r = subprocess.run([sys.executable, os.path.join(SCRIPTS, gs)],
                           capture_output=True, text=True, encoding="utf-8", errors="replace",
                           cwd="<ENGINE_ROOT>")
        combined = (r.stdout or "") + (r.stderr or "")
        if r.returncode != 0:
            fails.append(f"{gs}: 重跑退出码 {r.returncode}\n{combined[-800:]}")
            continue
        glyph = re.findall(r"Glyph \S+ missing from font|missing from current font", combined)
        if glyph:
            fails.append(f"{gs}: 缺字形警告 {len(glyph)} 条（{glyph[:3]}）")
        else:
            print(f"PASS-字形 {gs}: 重跑绿，零缺字形警告")

    # 6) 零回改自查：既有七件 sha16 与基台账逐位一致
    base = json.load(open(BASELINE, encoding="utf-8"))
    for fname, expect in base.items():
        p = os.path.join(FIGS, fname)
        if not os.path.exists(p):
            fails.append(f"零回改: 基台账件缺失 {fname}")
            continue
        got = hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]
        if got != expect:
            fails.append(f"零回改: {fname} sha16 {got} ≠ 基台账 {expect}")
    print(f"PASS-零回改: 既有 {len(base)} 件 sha16 与 figbatch-r1/figs-baseline.json 逐位一致"
          if not any(f.startswith("零回改") for f in fails) else "FAIL-零回改")

    print("=" * 72)
    if fails:
        print(f"QC FAIL（{len(fails)} 项）：")
        for f in fails:
            print("  -", f)
        sys.exit(1)
    print("QC OK：四图结构复核+生成脚本重跑（含内建断言）+零回改自查全绿")


if __name__ == "__main__":
    main()
