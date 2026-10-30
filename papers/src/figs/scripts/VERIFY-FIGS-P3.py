# -*- coding: utf-8 -*-
"""
P3 图件席程序化像素 QC（VERIFY-FIGS-P3）——像素复核通道失效（EXP-ZCODE-008，
任务书 D-4 哨兵已探明：Read 对 PNG 不呈现像素）本批判 channel-failed，本件为
非替代性程序化 QC 兜底，合并 R2 两份 QC 脚本（VERIFY-FIGS-P1.py 五道 +
_pixel_qc_supplementary.py 四道）为通用模板。

五道检查（每图全跑）：
  1. PNG 可解码＋尺寸 ≥2400×1200（300dpi 级）＋文件 >10KB
  2. 非白内容占比 ≥3%（防空白图）
  3. 顶部标题带暗像素 ≥50（中文标题存在性）
  4. 关键色存在性（每图指定 RGB 目标，全幅步进采样命中 ≥30 像素/色）
  5. 重跑生成脚本捕获缺字形警告（Glyph/missing，中文渲染完整性，须零警告）
退出码 0=全绿；非 0=存在失败项。
"""
import os
import subprocess
import sys

from PIL import Image

FIGS = "<ENGINE_ROOT>/out/paper-program-r2/figs"
SCRIPTS = FIGS + "/scripts"

FIGS_SPEC = {
    "FIG-P3-01-ENGINE-FIVE-LAYER-ARCH.png": {
        "script": "FIG-P3-01-ENGINE-FIVE-LAYER-ARCH.py",
        "colors": [(191, 216, 232), (250, 219, 216), (245, 203, 167)],  # 层盒蓝/粉/橙
    },
    "FIG-P3-02-WORLD-RESWAP-TIMELINE-FOURTREES.png": {
        "script": "FIG-P3-02-WORLD-RESWAP-TIMELINE-FOURTREES.py",
        "colors": [(245, 183, 177), (213, 245, 227), (214, 234, 248)],  # 漂移红/零漂移绿/时点头带
    },
    "FIG-P3-03-PERF-WATERFALL-EQUIV-PRESERVED.png": {
        "script": "FIG-P3-03-PERF-WATERFALL-EQUIV-PRESERVED.py",
        "colors": [(93, 173, 226), (72, 201, 176), (245, 176, 65)],  # 三口径柱色
    },
    "FIG-P3-04-KICADCLI-DRIFT-HIST-BADGELEDS6.png": {
        "script": "FIG-P3-04-KICADCLI-DRIFT-HIST-BADGELEDS6.py",
        "colors": [(93, 173, 226), (231, 76, 60), (245, 176, 65)],  # 序列蓝/极值红/分布橙
    },
    "FIG-P3-05-V7-FOUR-LAYER-PIPELINE.png": {
        "script": "FIG-P3-05-V7-FOUR-LAYER-PIPELINE.py",
        "colors": [(191, 216, 232), (254, 249, 231), (232, 218, 239)],  # 层盒/质疑环面板/紫层
    },
    "FIG-P3-06-SV1-THREE-BOARD-OVERLAP-HEATMAP.png": {
        "script": "FIG-P3-06-SV1-THREE-BOARD-OVERLAP-HEATMAP.py",
        "colors": [(31, 97, 141), (17, 122, 101), (125, 60, 152)],  # 三板条色
    },
    "FIG-P3-07-SV1-SIX-UNIQUE-TOPOLOGIES.png": {
        "script": "FIG-P3-07-SV1-SIX-UNIQUE-TOPOLOGIES.py",
        "colors": [(26, 82, 118), (30, 132, 73), (192, 57, 43)],  # 路径深蓝/S 端点红/E 端点绿
    },
}

TOL = 14          # 每通道容差
STEP = 6          # 采样步进
MIN_HITS = 30     # 关键色最少命中像素
MIN_W, MIN_H = 2400, 1200


def check_pixels(path, colors):
    img = Image.open(path).convert("RGB")
    w, h = img.size
    px = img.load()
    nonwhite = 0
    total = 0
    title_dark = 0
    hits = {c: 0 for c in colors}
    for y in range(0, h, STEP):
        for x in range(0, w, STEP):
            r, g, b = px[x, y]
            total += 1
            if r < 245 or g < 245 or b < 245:
                nonwhite += 1
            if y < h * 0.085 and (r + g + b) / 3 < 128:
                title_dark += 1
            for c in colors:
                if abs(r - c[0]) <= TOL and abs(g - c[1]) <= TOL and abs(b - c[2]) <= TOL:
                    hits[c] += 1
    return img.size, nonwhite / total, title_dark, hits


failures = []
print("=" * 100)
print("P3 图件席程序化 QC（七图）｜像素复核=channel-failed（D-4 哨兵），本件为程序化兜底")
print("=" * 100)
for fig, spec in FIGS_SPEC.items():
    path = os.path.join(FIGS, fig)
    tag = fig.replace("FIG-P3-", "P3-图")
    if not os.path.exists(path):
        failures.append(f"{tag}: 文件缺失")
        continue
    kb = os.path.getsize(path) / 1024
    if kb <= 10:
        failures.append(f"{tag}: 文件 {kb:.1f}KB ≤10KB")
        continue
    (w, h), ratio, dark, hits = check_pixels(path, spec["colors"])
    if w < MIN_W or h < MIN_H:
        failures.append(f"{tag}: 尺寸 {w}x{h} < {MIN_W}x{MIN_H}")
    if ratio < 0.03:
        failures.append(f"{tag}: 非白占比 {ratio:.3%} <3%")
    if dark < 50:
        failures.append(f"{tag}: 顶部标题带暗像素 {dark} <50")
    bad_colors = [c for c, n in hits.items() if n < MIN_HITS]
    if bad_colors:
        failures.append(f"{tag}: 关键色命中不足 {bad_colors} hits={hits}")
    # 重跑捕获缺字形警告
    r = subprocess.run([sys.executable, os.path.join(SCRIPTS, spec["script"])],
                       capture_output=True, text=True, encoding="utf-8", errors="ignore")
    glyph_issues = [ln for ln in (r.stdout + r.stderr).splitlines()
                    if "Glyph" in ln and "missing" in ln]
    if r.returncode != 0:
        failures.append(f"{tag}: 生成脚本重跑 rc={r.returncode}")
    if glyph_issues:
        failures.append(f"{tag}: 缺字形警告 {len(glyph_issues)} 条（首条: {glyph_issues[0][:90]}）")
    print(f"[{tag}] {w}x{h}｜{kb:.0f}KB｜非白 {ratio:.1%}｜标题带暗像素 {dark}｜"
          f"关键色命中 {sorted(hits.values())}｜重跑 rc={r.returncode} 缺字形=0"
          f"{'' if not glyph_issues else ' !! ' + str(len(glyph_issues))}")

print("=" * 100)
if failures:
    print("QC 结论：FAIL")
    for f in failures:
        print("  -", f)
    sys.exit(1)
print(f"QC 结论：PASS（{len(FIGS_SPEC)} 图全绿：尺寸/非白占比/标题带/关键色/缺字形捕获 五道全过）")
