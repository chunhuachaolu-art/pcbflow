# -*- coding: utf-8 -*-
"""
VERIFY-FIGS-P6-V6 — P6-V6 席（P6 图 1–6）程序化像素 QC（沿 R2 批 VERIFY-FIGS-P1.py 与
_pixel_qc_supplementary.py 两份 QC 脚本模式合并）。
背景：本批像素复核通道失效（D-4 哨兵已探明，EXP-ZCODE-008），目检不做、不声称复核过；
     本脚本做可复算的像素内容检查兜底：
     ① PNG 可解码＋尺寸锚（±3px）；② 关键色像素计数阈值（数据系列存在性）；
     ③ 非白内容占比（防空白图）；④ 顶部标题带暗像素（标题存在）；
     ⑤ 重跑生成脚本捕获缺字形警告（中文渲染完整性）＋断言全过。
"""
import os
import subprocess
import sys

from PIL import Image

FIGS = "<ENGINE_ROOT>/out/paper-program-r2/figs"
SCRIPTS = os.path.join(FIGS, "scripts")

CHECKS = [
    dict(
        png="FIG-P6-01-ACTION-CONTRACT-V6-V8.png",
        gen="FIG-P6-01-ACTION-CONTRACT-V6-V8.py",
        size=(3225, 1960),
        expect_colors=[(((234, 242, 251), "V6 左栏底 #eaf2fb", 40000)),
                       ((251, 234, 234), "FORCE 面板 #fbeaea", 8000),
                       ((232, 245, 233), "共享验证核 #e8f5e9", 4000)],
        ink=0.03,
    ),
    dict(
        png="FIG-P6-02-TRACK-SWITCH-8VS37.png",
        gen="FIG-P6-02-TRACK-SWITCH-8VS37.py",
        size=(4464, 1841),
        expect_colors=[((196, 78, 82), "模型臂红线", 400),
                       ((76, 114, 176), "确定性臂蓝线", 400),
                       ((85, 168, 104), "m5 残差绿线", 400)],
        ink=0.03,
    ),
    dict(
        png="FIG-P6-03-VOTE-FAMINE-COMPOSITE-VS-INDIVIDUAL.png",
        gen="FIG-P6-03-VOTE-FAMINE-COMPOSITE-VS-INDIVIDUAL.py",
        size=(5706, 1927),
        expect_colors=[((196, 78, 82), "合票红柱", 8000),
                       ((85, 168, 104), "个体绿柱", 8000),
                       ((76, 114, 176), "badgeleds 重放点", 300),
                       ((221, 132, 82), "bme280 重放点", 300)],
        ink=0.03,
    ),
    dict(
        png="FIG-P6-04-THREE-BOARD-CONNECTIVITY-CLIMB.png",
        gen="FIG-P6-04-THREE-BOARD-CONNECTIVITY-CLIMB.py",
        size=(6517, 1766),
        expect_colors=[((76, 114, 176), "badgeleds 折线", 800),
                       ((221, 132, 82), "bme280 折线", 800),
                       ((85, 168, 104), "crypto 折线", 800)],
        ink=0.03,
    ),
    dict(
        png="FIG-P6-05-STALL-CAUSE-FUNNEL.png",
        gen="FIG-P6-05-STALL-CAUSE-FUNNEL.py",
        size=(3332, 1769),
        expect_colors=[((215, 230, 247), "漏斗顶层 #d7e6f7", 40000),
                       ((227, 239, 217), "漏斗二层 #e3efd9", 30000),
                       ((247, 232, 207), "漏斗三层 #f7e8cf", 20000),
                       ((242, 215, 215), "漏斗底层 #f2d7d7", 10000)],
        ink=0.03,
    ),
    dict(
        png="FIG-P6-06-SEAT-SWITCH-DURATION-QUALITY-SCATTER.png",
        gen="FIG-P6-06-SEAT-SWITCH-DURATION-QUALITY-SCATTER.py",
        size=(5543, 1992),
        expect_colors=[((221, 132, 82), "SWA 点", 300),
                       ((196, 78, 82), "SWB 点", 300),
                       ((76, 114, 176), "SWC 点", 300),
                       ((129, 114, 178), "基线道点", 200)],
        ink=0.03,
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
    if (abs(im.size[0] - c["size"][0]) > 3 or abs(im.size[1] - c["size"][1]) > 3):
        errs.append(f"{c['png']} 尺寸 {im.size} != 预期 {c['size']}（±3）")
    px = im.load()
    w, h = im.size
    counts = {name: 0 for _, name, _ in c["expect_colors"]}
    step = 3
    nonwhite = 0
    total = 0
    title_dark = 0
    for y in range(0, h, step):
        for x in range(0, w, step):
            r, g, b = px[x, y]
            total += 1
            if not (r > 235 and g > 235 and b > 235):
                nonwhite += 1
            if y < h * 0.12 and (r < 120 and g < 120 and b < 120):
                title_dark += 1
            for (er, eg, eb), name, _ in c["expect_colors"]:
                if abs(r - er) <= 12 and abs(g - eg) <= 12 and abs(b - eb) <= 12:
                    counts[name] += 1
    for (rgb, name, thr), _ in zip(c["expect_colors"], c["expect_colors"]):
        est = counts[name] * step * step
        if est < thr:
            errs.append(f"{c['png']}: 色块 {name} {rgb} 估算像素 {est} < 阈值 {thr}")
        else:
            print(f"[ok] {c['png']}: {name} 估算 {est} px ≥ {thr}")
    ink = nonwhite / total
    print(f"[ok] {c['png']}: 尺寸 {im.size}，非白占比 {ink:.1%}，标题带暗像素 {title_dark}，文件 {sz} B")
    if ink < c["ink"]:
        errs.append(f"{c['png']} 内容占比过低 {ink:.1%}（疑似空白图）")
    if title_dark < 50:
        errs.append(f"{c['png']} 顶部标题带暗像素 {title_dark} < 50（标题缺失？）")
    # 重跑生成脚本：断言全过＋捕获缺字形警告
    r = subprocess.run([sys.executable, os.path.join(SCRIPTS, c["gen"])],
                       capture_output=True, text=True, encoding="utf-8", errors="replace",
                       cwd="<ENGINE_ROOT>")
    glyph_warn = [ln for ln in (r.stdout + r.stderr).splitlines()
                  if "Glyph" in ln or "missing" in ln.lower()]
    if r.returncode != 0:
        errs.append(f"{c['gen']} 重跑失败 rc={r.returncode}: {r.stderr[-300:]}")
    elif glyph_warn:
        errs.append(f"{c['gen']} 存在缺字形警告: {glyph_warn[:3]}")
    else:
        print(f"[ok] {c['gen']} 重跑通过（内建断言全过、无缺字形警告=中文渲染完整）")

if errs:
    for e in errs:
        print("CHECK FAIL:", e)
    raise SystemExit(2)
print("[verify] P6-V6 席六图程序化像素 QC 全过（注：Read 目检因图像通道失效未做，"
      "pixel_review=channel-failed，见 D-4 哨兵结论）")
