# -*- coding: utf-8 -*-
"""
VERIFY-FIGS-P4 — 篇四 8 图程序化内容复核（像素级机器检查；沿 R2 批 VERIFY-FIGS-P1.py＋
_pixel_qc_supplementary.py 两份 QC 脚本模式合并为通用模板：尺寸/非白占比/标题带/关键色/缺字形捕获）。

背景：图像通道失效（Read 对 PNG 只返回 CDN 链接，EXP-ZCODE-008 环境级故障；批前置哨兵已探明本窗未恢复），
     目检无法进行，本脚本做可复算的像素内容检查作为补充证据（非目检替代）：
     ① PNG 可解码、尺寸=生成参数推定值、文件>10KB；② 非白内容占比（防空白图）；
     ③ 顶部标题带暗像素>50（标题存在）；④ 关键数据色像素估算≥阈值（数据主体在图）；
     ⑤ 重跑生成脚本捕获缺字形警告（中文渲染完整性，rc=0）。
"""
import os
import subprocess
import sys

from PIL import Image

FIGS = "<ENGINE_ROOT>/out/paper-program-r2/figs"
SCRIPTS = os.path.join(FIGS, "scripts")

CHECKS = [
    dict(
        png="FIG-P4-01-TRI-CLASS-DECISION-TREE.png",
        size=(3328, 1302),
        expect_colors=[((196, 78, 82), "(b) 红框", 3000),
                       ((85, 168, 104), "(a) 绿框", 2700),
                       ((76, 114, 176), "(c) 蓝框", 5500)],
        gen="FIG-P4-01-TRI-CLASS-DECISION-TREE.py",
    ),
    dict(
        png="FIG-P4-02-PADFIELD-SEAL-CHANNELS.png",
        size=(3116, 1444),
        expect_colors=[((196, 78, 82), "不足通道红柱", 60000),
                       ((221, 132, 82), "贴限橙柱", 3000),
                       ((76, 114, 176), "需求线蓝", 2500)],
        gen="FIG-P4-02-PADFIELD-SEAL-CHANNELS.py",
    ),
    dict(
        png="FIG-P4-03-TMP108-ENDPOINT-ABSTRACTION.png",
        size=(2694, 1340),
        expect_colors=[((76, 114, 176), "F.Cu 蓝焊盘", 4500),
                       ((221, 132, 82), "B.Cu 橙焊盘/旧边", 4200),
                       ((196, 78, 82), "R5 红环/标注", 1900)],
        gen="FIG-P4-03-TMP108-ENDPOINT-ABSTRACTION.py",
    ),
    dict(
        png="FIG-P4-04-PLATED-UNION-CUTPOINT.png",
        size=(2517, 1579),
        expect_colors=[((76, 114, 176), "F.Cu 段蓝", 2600),
                       ((221, 132, 82), "B.Cu 段橙", 2900),
                       ((196, 78, 82), "割点红圈", 5000),
                       ((85, 168, 104), "修复后绿", 2200)],
        gen="FIG-P4-04-PLATED-UNION-CUTPOINT.py",
    ),
    dict(
        png="FIG-P4-05-ESP32-GAPFACE.png",
        size=(2449, 1549),
        expect_colors=[((85, 168, 104), "解锁绿条", 25000),
                       ((140, 140, 140), "仍锁灰条", 25000),
                       ((221, 132, 82), "阻塞集橙柱", 8000)],
        gen="FIG-P4-05-ESP32-GAPFACE.py",
    ),
    dict(
        png="FIG-P4-06-SWDIO-SPOKE-LOCK.png",
        size=(3103, 1508),
        expect_colors=[((196, 78, 82), "J4 红端点/辐条", 2000),
                       ((76, 114, 176), "U1 蓝端点/开辐条", 700),
                       ((221, 132, 82), "封锁 cell 橙框", 850)],
        gen="FIG-P4-06-SWDIO-SPOKE-LOCK.py",
    ),
    dict(
        png="FIG-P4-07-U1-SHIFT-CUT-EXPLOSION.png",
        size=(3201, 1629),
        expect_colors=[((76, 114, 176), "基线蓝柱", 12000),
                       ((221, 132, 82), "西移1mm 橙柱", 8000),
                       ((196, 78, 82), "西移2mm 红柱", 8000)],
        gen="FIG-P4-07-U1-SHIFT-CUT-EXPLOSION.py",
    ),
    dict(
        png="FIG-P4-08-LOO-AUC-DUAL-ARM.png",
        size=(3168, 1736),
        expect_colors=[((76, 114, 176), "主LR ROC 蓝", 3000),
                       ((221, 132, 82), "主GBDT 橙", 4000),
                       ((196, 78, 82), "敏感性GBDT 红", 3400),
                       ((129, 114, 179), "敏感性LR 紫", 3200)],
        gen="FIG-P4-08-LOO-AUC-DUAL-ARM.py",
    ),
]

errs = []
for c in CHECKS:
    p = os.path.join(FIGS, c["png"])
    if not os.path.exists(p):
        errs.append(f"{p} 不存在")
        continue
    sz = os.path.getsize(p)
    if sz <= 10 * 1024:
        errs.append(f"{p} 过小 {sz}B")
    im = Image.open(p).convert("RGB")
    if im.size != c["size"]:
        errs.append(f"{c['png']} 尺寸 {im.size} != 预期 {c['size']}")
    px = im.load()
    w, h = im.size
    counts = {name: 0 for _, name, _ in c["expect_colors"]}
    step = 3
    nonwhite = 0
    total = 0
    title_dark = 0
    title_band = range(0, int(h * 0.10), 2)
    for y in range(0, h, step):
        for x in range(0, w, step):
            r, g, b = px[x, y]
            total += 1
            if not (r > 235 and g > 235 and b > 235):
                nonwhite += 1
            for (er, eg, eb), name, _ in c["expect_colors"]:
                if abs(r - er) <= 12 and abs(g - eg) <= 12 and abs(b - eb) <= 12:
                    counts[name] += 1
    for y in title_band:
        for x in range(0, w, 4):
            r, g, b = px[x, y]
            if not (r > 200 and g > 200 and b > 200):
                title_dark += 1
    for (rgb, name, thr) in c["expect_colors"]:
        est = counts[name] * step * step
        if est < thr:
            errs.append(f"{c['png']}: 色块 {name} {rgb} 估算像素 {est} < 阈值 {thr}")
        else:
            print(f"[ok] {c['png']}: {name} {rgb} 估算 {est} px ≥ {thr}")
    ink = nonwhite / total
    print(f"[ok] {c['png']}: 尺寸 {im.size}，非白占比 {ink:.1%}，标题带暗像素 {title_dark}，文件 {sz} B")
    if ink < 0.04:
        errs.append(f"{c['png']} 非白占比过低 {ink:.1%}（疑似空白图）")
    if title_dark < 50:
        errs.append(f"{c['png']} 顶部标题带暗像素 {title_dark} < 50（标题缺失疑似）")
    r = subprocess.run([sys.executable, os.path.join(SCRIPTS, c["gen"])],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    glyph_warn = [ln for ln in (r.stdout + r.stderr).splitlines() if "Glyph" in ln or "missing from font" in ln]
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
print("[verify] 篇四 8 图程序化内容复核全过（注：目检因图像通道失效未做，见 pixel_review=channel-failed；"
      "本批按任务书 D-4 前置哨兵探针判定=通道失效，未做 Read 目检、不声称复核过）")
