# -*- coding: utf-8 -*-
"""
VERIFY-FIGS-P1 — 篇一新增两图的程序化内容复核（像素级机器检查，非目检替代）
背景：图像通道失效（Read 对 PNG 只返回 CDN 链接，EXP-ZCODE-008 环境级故障），
     目检无法进行，本脚本做可复算的像素内容检查作为补充证据：
     ① PNG 可解码、尺寸正确；② 关键数据色在图中按预期出现（柱/矩阵/条带色）；
     ③ 图像非空白（有效内容占比）；④ 重跑生成脚本 stderr 无缺字形警告（中文渲染完整性）。
"""
import os
import subprocess
import sys

from PIL import Image

FIGS = "<ENGINE_ROOT>/out/paper-program-r2/figs"
SCRIPTS = os.path.join(FIGS, "scripts")

CHECKS = [
    dict(
        png=os.path.join(FIGS, "FIG-P1-R55-3P-FOUR-GATES-R1.png"),
        size=(2720, 1639),
        expect_colors=[((196, 78, 82), "修复前红柱", 20000),    # #c44e52 至少 2 万像素（两根 55 柱）
                       ((85, 168, 104), "SAT/修复后绿", 60000)],  # #55a868 柱+矩阵+条带
        gen="FIG-P1-R55-3P-FOUR-GATES-R1.py",
    ),
    dict(
        png=os.path.join(FIGS, "FIG-P1-B1-SHORTS57-FAMILY-R1.png"),
        size=(2640, 1520),
        expect_colors=[((76, 114, 176), "C1 蓝", 30000),        # #4c72b0（31 段）
                       ((221, 132, 82), "C2 橙", 15000),        # #dd8452（18 段+柱）
                       ((147, 120, 96), "C3 棕", 8000)],        # #937860（8 段+柱）
        gen="FIG-P1-B1-SHORTS57-FAMILY-R1.py",
    ),
]

errs = []
for c in CHECKS:
    p = c["png"]
    if not os.path.exists(p):
        errs.append(f"{p} 不存在")
        continue
    sz = os.path.getsize(p)
    if sz <= 10 * 1024:
        errs.append(f"{p} 过小 {sz}B")
    im = Image.open(p).convert("RGB")
    if im.size != c["size"]:
        errs.append(f"{os.path.basename(p)} 尺寸 {im.size} != 预期 {c['size']}")
    px = im.load()
    w, h = im.size
    counts = {name: 0 for _, name, _ in c["expect_colors"]}
    step = 3  # 抽样步长（全量 400 万像素级，抽样足够判定色块存在）
    nonwhite = 0
    total = 0
    for y in range(0, h, step):
        for x in range(0, w, step):
            r, g, b = px[x, y]
            total += 1
            if not (r > 235 and g > 235 and b > 235):
                nonwhite += 1
            for (er, eg, eb), name, _ in c["expect_colors"]:
                if abs(r - er) <= 12 and abs(g - eg) <= 12 and abs(b - eb) <= 12:
                    counts[name] += 1
    for (rgb, name, thr), _ in zip(c["expect_colors"], c["expect_colors"]):
        est = counts[name] * step * step  # 抽样还原估
        if est < thr:
            errs.append(f"{os.path.basename(p)}: 色块 {name} {rgb} 估算像素 {est} < 阈值 {thr}")
        else:
            print(f"[ok] {os.path.basename(p)}: {name} {rgb} 估算 {est} px ≥ {thr}")
    ink = nonwhite / total
    print(f"[ok] {os.path.basename(p)}: 尺寸 {im.size}，非白内容占比 {ink:.1%}，文件 {sz} B")
    if ink < 0.05:
        errs.append(f"{os.path.basename(p)} 内容占比过低 {ink:.1%}（疑似空白图）")
    # 重跑生成脚本捕获缺字形警告（中文渲染完整性）
    r = subprocess.run([sys.executable, os.path.join(SCRIPTS, c["gen"])],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    glyph_warn = [ln for ln in (r.stdout + r.stderr).splitlines() if "Glyph" in ln or "missing" in ln.lower()]
    if r.returncode != 0:
        errs.append(f"{c['gen']} 重跑失败 rc={r.returncode}: {r.stderr[-300:]}")
    elif glyph_warn:
        errs.append(f"{c['gen']} 存在缺字形警告: {glyph_warn[:3]}")
    else:
        print(f"[ok] {c['gen']} 重跑通过（断言全过、无缺字形警告=中文渲染完整）")

if errs:
    for e in errs:
        print("CHECK FAIL:", e)
    raise SystemExit(2)
print("[verify] 两图程序化内容复核全过（注：目检因图像通道失效未做，见 pixel_review=channel-failed）")
