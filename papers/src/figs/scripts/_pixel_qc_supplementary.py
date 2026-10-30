# -*- coding: utf-8 -*-
"""
补充 QC（非 Read 像素复核的替代品——Read 通道本批失效，像素级目检按纪律记 channel-failed）：
对三张成图做程序化结构复核：
  1) 尺寸/模式/大小；
  2) 数据系列颜色是否真的出现在画布的预期半区（bar/line 色存在性）；
  3) 标题带是否存在文本像素（暗像素密度）；
  4) 画布非空白（非白像素占比）。
"""
import os

from PIL import Image

FIGS = "<ENGINE_ROOT>/out/paper-program-r2/figs"
CHECKS = {
    "FIG-P5-01-SCALE-R1-N8-HIST-N16-GAMBIT.png": [
        ("#2e7d32", "左半"),   # (a) 474.5 绿色柱
        ("#9e9e9e", "左半"),   # (a) 475.5 灰柱
        ("#1565c0", "右半"),   # (b) SB 蓝线
    ],
    "FIG-P5-02-EXP-S1-FC06-REVERSAL.png": [
        ("#1565c0", "全幅"),   # TIER 蓝线
        ("#ef6c00", "全幅"),   # FULL 橙线
        ("#2e7d32", "全幅"),   # oracle 绿虚线
    ],
    "FIG-P5-03-SEATB-THREE-BATCH-ZERO-INCREMENT.png": [
        ("#1565c0", "左半"),   # (a) RESTORE 蓝柱
        ("#5e35b1", "左半"),   # (a) SUPPLEMENT 紫柱
        ("#90a4ae", "右半"),   # (b) ③==② 灰柱
        ("#c62828", "右半"),   # (b) 零增量红柱（零高度，取红标签像素）
    ],
}


def hex2rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def near(px, target, tol=28):
    return all(abs(a - b) <= tol for a, b in zip(px[:3], target))


for fname, checks in CHECKS.items():
    path = os.path.join(FIGS, fname)
    im = Image.open(path).convert("RGB")
    w, h = im.size
    px = im.load()
    # 非白像素占比
    step = 7
    tot = nonwhite = 0
    for y in range(0, h, step):
        for x in range(0, w, step):
            tot += 1
            p = px[x, y]
            if not (p[0] > 245 and p[1] > 245 and p[2] > 245):
                nonwhite += 1
    # 标题带暗像素（顶部 0..18% 高度，覆盖 suptitle 与 axes title 两种版式）
    dark_top = sum(
        1 for y in range(0, int(h * 0.18), 2) for x in range(0, w, 4)
        if sum(px[x, y][:3]) < 300
    )
    print(f"{fname}: {w}x{h} mode=RGB size={os.path.getsize(path)}B "
          f"非白占比={nonwhite / tot:.3f} 顶部文本暗像素={dark_top}")
    assert w >= 2400 and h >= 1200, "300dpi 尺寸不符"
    assert nonwhite / tot > 0.03, "画布近乎空白"
    assert dark_top > 50, "顶部标题带无文本像素"
    for hexc, region in checks:
        target = hex2rgb(hexc)
        hits = 0
        x0, x1 = (0, w // 2) if region == "左半" else ((w // 2, w) if region == "右半" else (0, w))
        for y in range(0, h, 3):
            for x in range(x0, x1, 3):
                if near(px[x, y], target):
                    hits += 1
                    if hits >= 30:
                        break
            if hits >= 30:
                break
        print(f"   系列 {hexc}（{region}）命中采样像素 {hits}")
        assert hits >= 30, f"系列色 {hexc} 未出现于{region}"
print("[QC] 三图结构复核全过（尺寸/非空白/标题文本/系列色存在性）")
