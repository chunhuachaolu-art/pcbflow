#!/usr/bin/env python
"""R17 渲染实施者：轴1 单变量仪器轮——渲染分辨率 640→1280 dpi（四图全部）。

背景：axis-experiment-plan-r17-r20.json（sha256 前缀 b6ec6467，冻结）轴 1=
渲染分辨率倍增。本轮相对 r14b 只改变一个仪器变量：光栅 dpi 640→1280（线度
×2、像素数×4，四图全部）。r14b 配色规则逐字重放：白墨图元→橙 (255,165,0)、
板内空隙白→绿 (0,128,0)（mask 在 1280 像密度下重算，规则与 z 序不变）；
top 视无配色（与既往一致——r14b top=r5 640 逐字节拷贝，本轮改为同一冻结
矢量源的 1280 原生重渲染）。渲染源与 r14b 同源：staging-r4 逐字节冻结拷贝
（sha 复核）→ renders-r4 冻结 combined PDF（sha 自 render-framing-r5.json
活读复核，r5 声明其角色=「任意 DPI 重光栅化=确定性」）。活板零写。

探针先行（r14 首试探针证伪教训；探针证伪则本轮作废，只交探针报告与
framing-证伪记录，不落正式渲染件）。探针内容（全内存+系统临时目录，
out/ 零写入）：
  1) 同源性：staging-r4 冻结 sha 复核 + r4 四冻结 PDF sha 复核（framing-r5
     frozen_inputs 活读）+ kicad-cli 从 staging-r4/applied 重导出 combined
     bottom（r4 同配方）→ 640 光栅化与冻结 applied-bottom.pdf 640 光栅化
     逐字节比对（r14b 实证：PDF 字节跨运行不同而光栅逐字节稳定，故比对
     光栅不比对 PDF 字节）；
  2) 1280 可行性：组合页 40pt+dpi1280 光栅化（全页实测尺寸/时长/峰值内存，
     时长与内存=运行观测只进 stdout，不入冻结断言）；板界 png_board_pixel_
     bounds 实测 vs 640 实测×2（容差 ±2px，AA 级）；
  3) margin 物理等值：640 的 +120px → 1280 的 +240px（120/640in=
     240/1280in=0.1875in 物理不变；换算式入 framing）；
  4) 配色语义 2× 口径：白墨 mask 矢量重建（fitz Shape，dpi1280）+板内
     空隙白重算 → 橙/绿预计 ≈4× r14b 实测（81672→≈326688、206632→
     ≈826528，容差 ±25%）；板内白=0 按构造严格成立（成图后程序化复核）。

四步（库侧 pcbflow/* 零改动零新增，只 import）：
  probe    上述 1-4 全内存执行，逐项打印 PASS/FAIL，任一 FAIL 即退出码 1。
  framing  落盘 render-framing-r17.json（canonical JSON，先于任何官方成图）：
           轴计划引用、单变量差异声明（=仅分辨率+物理等值 margin 换算）、
           探针确定性结论、多重着色映射+色距断言、合成方法与 z 序、页几何
           实测（1280 全页/板界/裁剪）、预注册预测（橙/绿 4× 带、板内白
           0、top 橙/绿=0）、诊断对照裁片方法预注册、freeze 顺序。
  render   按 framing 执行：四图（applied-top/prep1-top 1280 原生无配色；
           applied-bottom/prep1-bottom 1280+r14b 配色重放）→ renders-r17/
           （防覆写）；板界断言（=framing 实测值）、裁剪四侧白边=240px、
           调色板断言（橙/绿 4× 带内、橙绿零交集、板内白严格=0）；确定性
           自证（光栅化→配色→裁剪全链重跑逐字节一致）；render-witness-
           r17.json（四 PNG sha256+尺寸+橙/绿/白 px 实测+确定性自证）。
  diag     诊断对照裁片（供主审人工分辨力核验，非盲读件）：D1-D3 已证实
           的近触区各取一处——bottom=基准黑点-焊盘邻接区（r14b 证书点
           (282,224)c 邻域）、top=applied-top 板中部相邻 courtyard 对
           （程序化检测洋红分量、取离图幅中心最近的相邻对）——r14b（640）
           与 r17（1280）同一板面区域裁片，640 腿 2× 最近邻放大至与 1280
           腿相同显示尺寸并排拼图（top 一张、bottom 一张）+manifest
           （区域板面坐标、两版像素尺度、映射换算式）。存 diag-r17-render/。

纪律：确定性纯函数（同输入重跑字节等同；时长/内存=运行观测不入冻结件）；
日期/轮次=声明常量（date_constant="2026-09-09"）；canonical JSON=pcbflow.
hashing.canonical_json_bytes、hash=sha256_file；kicad-cli 调用照 s50/s51
模式（绝对路径+版本验证+subprocess.run cwd=REPO；探针导出输出=系统临时
目录）；除 kicad-cli 外零其他 subprocess/网络/wall-clock 依赖（perf_counter
仅用于 stdout 观测，不进任何落盘件）；受保护文件（cli.py/config.py/
toolchain_lock.json）与 staging-r4/datasets/out 既有文件零改动；防覆写
guard（已存在非字节等同→FAIL，等同→幂等）；零视觉判读（全部程序化
像素/矢量统计）。

用法：python scripts/s62_render_r17.py probe|framing|render|diag
"""

from __future__ import annotations

import ctypes
import io
import struct
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from pcbflow import calibration, hashing  # noqa: E402

#: 1280 全页 16390×12006=196,778,340 px 超出 PIL 默认 DecompressionBomb
#: 阈值（178,956,970 px）；输入=本仓冻结渲染件（非不可信来源），解除该
#: 加载守卫。像素语义零影响（仅加载期 DoS 防护）。
from PIL import Image as _PILImage  # noqa: E402

_PILImage.MAX_IMAGE_PIXELS = None

CAL_DIR = REPO / "out" / "v3-tl2" / "calibration"
R17_DIR = CAL_DIR / "renders-r17"
FRAMING_R17 = CAL_DIR / "render-framing-r17.json"
WITNESS_R17 = CAL_DIR / "render-witness-r17.json"
DIAG_DIR = CAL_DIR / "diag-r17-render"
STAGING_R4 = CAL_DIR / "staging-r4"
R4_DIR = CAL_DIR / "renders-r4"
R5_DIR = CAL_DIR / "renders-r5"
R14B_DIR = CAL_DIR / "renders-r14b"
FRAMING_R5 = CAL_DIR / "render-framing-r5.json"
FRAMING_R14B = CAL_DIR / "render-framing-r14b.json"
WITNESS_R14B = CAL_DIR / "render-witness-r14b.json"
AXIS_PLAN = CAL_DIR / "axis-experiment-plan-r17-r20.json"
LIVE_BOARDS = {
    "applied": REPO / "out" / "revc-asm" / "board" / "applied.kicad_pcb",
    "prep1": REPO / "out" / "revc-asm" / "board" / "_pre-p1-batch-1.kicad_pcb",
}

DATE_CONSTANT = "2026-09-09"
ROUND_ID = "2026-09-09-r17"
ROUND_LABEL = "r17"
DOMAIN_ID = calibration.DOMAIN_ID

KICAD_CLI = Path(r"F:\kicad\bin\kicad-cli.exe")
KICAD_VERSION = "10.0.5"

#: 本轮唯一仪器变量：光栅 dpi 640→1280（线度×2、像素数×4）
RASTER_DPI_PREV = 640
RASTER_DPI = 1280
SCALE = RASTER_DPI // RASTER_DPI_PREV          # =2
COMPOSE_MARGIN_PT = 40.0                       # 与 r4/r5/r14b 逐字同口径
CROP_MARGIN_PX_PREV = 120                      # r5/r14b 口径
CROP_MARGIN_PX = CROP_MARGIN_PX_PREV * SCALE   # =240（物理边距不变）
#: margin 物理等值换算式（framing 声明）
MARGIN_CONVERSION_FORMULA = (
    "crop_margin_px(1280) = 120px × (1280/640) = 240px；"
    "物理边距 = 120/640in = 240/1280in = 0.1875in = 13.5pt（不变）")
BOUNDS_CONVERSION_FORMULA = (
    "board_px_bounds(1280) 期望 = board_px_bounds(640 实测) × 2（像密度"
    "线度 ×2）；断言容差 ±2px（抗锯齿级；r5 先例允许 ±1px，线度加倍后"
    "裕量同步加倍）")
BOUNDS_TOL_PX = 2

#: 层清单（r4/r5/r14b 逐字同口径；仅探针同源性重导出使用，官方成图零
#: kicad 调用——图像来源=renders-r4 冻结 combined PDF）
LAYERS_BOTTOM = "B.Cu,B.Mask,B.Silkscreen,Edge.Cuts,B.Courtyard"
LAYERS_TOP = "F.Cu,F.Mask,F.Silkscreen,Edge.Cuts,F.Courtyard"

STAGED = {
    "applied": STAGING_R4 / "applied.kicad_pcb",
    "prep1": STAGING_R4 / "prep1.kicad_pcb",
}
STAGED_REL = {
    "applied": "out/v3-tl2/calibration/staging-r4/applied.kicad_pcb",
    "prep1": "out/v3-tl2/calibration/staging-r4/prep1.kicad_pcb",
}
STAGED_SHA_FROZEN = {
    "applied": "45320fbe3296a0594a3678a30ad2c1bf775e6c7e9666158abb82081fc2245d85",
    "prep1": "332c71d4362b732d0a9cdc4d82ea9f8308e4647f2e3cd2fde0bc5497fc5a62c7",
}

#: 受保护文件（红线 1：开工/收工各验；前 8 位为任务给定口径）
PROTECTED = {
    "pcbflow/cli.py": "6ed4f3fd",
    "pcbflow/config.py": "f515c348",
    "toolchain_lock.json": "d43dad89",
}

#: 轴计划冻结前缀（任务给定口径 b6ec6467）
AXIS_PLAN_PREFIX = "b6ec6467"

#: r4 冻结 combined PDF（四图唯一图像来源；sha 从 render-framing-r5.json
#: frozen_inputs 活读复核，不硬编码——r5 声明其角色=「任意 DPI 重光栅化
#: =确定性」）
R4_PDFS = {
    "applied-top": R4_DIR / "applied-top.pdf",
    "applied-bottom": R4_DIR / "applied-bottom.pdf",
    "prep1-top": R4_DIR / "prep1-top.pdf",
    "prep1-bottom": R4_DIR / "prep1-bottom.pdf",
}

FINAL_PNGS = ("applied-bottom", "prep1-bottom", "applied-top", "prep1-top")
BOTTOM_STATES = ("applied", "prep1")

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"

# ---------------------------------------------------------------------------
# 多重着色目标（r14b 逐字重放；非采样值）
# ---------------------------------------------------------------------------
#: (a) 白墨矢量图元（孔盘 fill + 椭圆轮廓 stroke，B.Cu∪B.Mask 双族共享）→ 橙
TARGET_ORANGE = (255, 165, 0)
#: (b) 板内背景空隙白（无任何层墨区域）→ 深绿（PCB 基材惯例色）
TARGET_GREEN = (0, 128, 0)
#: 画布已有主色（r5/r14b 实测口径不变）
CANVAS_COLORS = {
    "B.Cu_blue": (77, 126, 195),
    "B.Mask_cyan": (153, 255, 248),
    "Edge.Cuts_gray": (207, 209, 205),
    "canvas_white": (255, 255, 255),
    "target_orange": TARGET_ORANGE,
    "target_green": TARGET_GREEN,
}
COLOR_DIST_MIN = 150.0  # 预注册：目标色与画布每色的 RGB 欧氏距离 > 150

#: 配色 4× 预测容差（橙/绿 ≈4× r14b 实测）
PRED_TOL = 0.25
#: r14b 实测基准（witness 活读复核，非硬编码；探针/framing 双通道核对）
R14B_PALETTE_EXPECTED = {
    "orange_exact_count": 81672,
    "green_exact_count": 206632,
    "white_in_board_after": 0,
}
#: top 视 courtyard 洋红（r14 轮实测 F.Courtyard/F.B.CrtYd 目标色；诊断
#: 裁片程序化选区用，官方渲染零配色）
COURTYARD_MAGENTA = (255, 38, 226)


def _fail(msg: str) -> None:
    print(f"[r17] FAIL: {msg}")
    sys.exit(1)


def _sha(path) -> str:
    return hashing.sha256_file(str(path))


def _write_canonical_guarded(path: Path, obj) -> tuple:
    """防覆写落盘：已存在且字节等同→幂等；非等同→FAIL。返回 (sha, mode)。"""
    data = hashing.canonical_json_bytes(obj)
    if path.exists():
        if path.read_bytes() == data:
            return hashing.sha256_bytes(data), "idempotent"
        _fail(f"{path.name} 已存在且非字节等同（防覆写）")
    path.write_bytes(data)
    return hashing.sha256_bytes(data), "written"


def _guard_write_bytes(path: Path, data: bytes) -> str:
    if path.exists():
        if path.read_bytes() == data:
            return "idempotent"
        _fail(f"{path.name} 已存在且非字节等同（防覆写）")
    path.write_bytes(data)
    return "written"


def _png_size(data: bytes) -> tuple:
    if not data.startswith(PNG_MAGIC):
        _fail("不是 PNG（magic 不符）")
    w, h = struct.unpack(">II", data[16:24])
    return w, h


def _protected_check() -> dict:
    results = {}
    for rel, prefix in PROTECTED.items():
        sha = _sha(REPO / rel)
        if not sha.startswith(prefix):
            _fail(f"受保护文件哈希不符：{rel} {sha[:8]} != {prefix}")
        results[rel] = {"sha256": sha, "expected_prefix": prefix, "match": True}
    return results


def _staging_check() -> dict:
    results = {}
    for state in ("applied", "prep1"):
        p = STAGED[state]
        sha = _sha(p)
        if sha != STAGED_SHA_FROZEN[state]:
            _fail(f"staging-r4/{state} sha 不符冻结记录：{sha}")
        live = _sha(LIVE_BOARDS[state])
        results[state] = {
            "staged_path_rel": STAGED_REL[state],
            "staged_sha256": sha,
            "live_path_rel": str(LIVE_BOARDS[state].relative_to(REPO)
                                 ).replace("\\", "/"),
            "live_sha256": live,
            "staged_match_frozen": True,
            "live_prefix": live[:8],
        }
    return results


def _axis_plan_check() -> dict:
    sha = _sha(AXIS_PLAN)
    if not sha.startswith(AXIS_PLAN_PREFIX):
        _fail(f"轴计划哈希不符冻结前缀：{sha[:8]} != {AXIS_PLAN_PREFIX}")
    return {"path_rel": "out/v3-tl2/calibration/axis-experiment-plan-r17-r20.json",
            "sha256": sha, "expected_prefix": AXIS_PLAN_PREFIX, "match": True}


def _r4_pdfs_check() -> dict:
    """r4 冻结四 PDF sha（活读 framing-r5 frozen_inputs 复核）。"""
    import json
    framing5 = json.loads(FRAMING_R5.read_text(encoding="utf-8"))
    frozen = {item["state_side"]: item
              for item in framing5["frozen_inputs"]["r4_frozen_pdfs"]}
    out = {}
    for key, path in R4_PDFS.items():
        want = frozen[key]["sha256"]
        got = _sha(path)
        if got != want:
            _fail(f"r4 冻结 PDF sha 不符 framing-r5：{key} {got} != {want}")
        out[key] = {"path_rel": frozen[key]["path_rel"], "sha256": got,
                    "role": frozen[key]["role"]}
    return out


def _r14b_refs() -> dict:
    """r14b 冻结参照活读：framing/witness sha、r14b 四 PNG sha（与 witness
    记录复核）、640 板界/裁剪基准、橙/绿/白实测基准。"""
    import json
    fr_sha = _sha(FRAMING_R14B)
    wi_sha = _sha(WITNESS_R14B)
    witness = json.loads(WITNESS_R14B.read_text(encoding="utf-8"))
    framing = json.loads(FRAMING_R14B.read_text(encoding="utf-8"))
    # witness 记录的 r14b PNG sha 与盘上实际逐字复核
    pngs = {}
    for name in FINAL_PNGS:
        got = _sha(R14B_DIR / f"{name}.png")
        if name in ("applied-top", "prep1-top"):
            want = witness["top_zero_change_copies"][name]["sha256"]
        else:
            want = witness["renders"][name.removesuffix("-bottom")]["sha256"]
        if got != want:
            _fail(f"r14b PNG sha 不符 witness 记录：{name} {got} != {want}")
        pngs[name] = got
    # 配色目标活读核对（r14b 逐字重放前提）
    cm = witness["color_mapping"]
    orange = tuple(cm["white_ink_drawings"]["target_rgb"])
    green = tuple(cm["board_void_white"]["target_rgb"])
    if orange != TARGET_ORANGE or green != TARGET_GREEN:
        _fail(f"r14b 配色目标与本轮常量不符：橙{orange} 绿{green}")
    # 640 基准（bottom 两态同值；top 取 r5 实测）
    bnds = witness["renders"]["applied"]["full_page_bounds_after_overlay"]
    crop640 = witness["renders"]["applied"]["crop_box"]
    wh640 = witness["renders"]["applied"]["image_wh"]
    for s in ("prep1",):
        if witness["renders"][s]["full_page_bounds_after_overlay"] != bnds:
            _fail("r14b 两态 bottom 板界不一致（640 基准前提破坏）")
    framing5 = json.loads(FRAMING_R5.read_text(encoding="utf-8"))
    top_bounds_640 = framing5["expected_geometry"]["board_px_bounds_full_top"]
    pal = witness["renders"]["applied"]["palette"]
    for k, v in R14B_PALETTE_EXPECTED.items():
        if pal[k] != v:
            _fail(f"r14b 实测基准不符在案值：{k}={pal[k]} != {v}")
    if pal["orange_exact_count"] != 81672 or pal["green_exact_count"] != 206632:
        _fail("r14b 橙/绿实测与任务给定口径不符")
    return {
        "render-framing-r14b.json": {"sha256": fr_sha},
        "render-witness-r14b.json": {"sha256": wi_sha},
        "renders_r14b_png_sha256": pngs,
        "color_mapping_r14b": {"orange_rgb": list(TARGET_ORANGE),
                               "green_rgb": list(TARGET_GREEN)},
        "bottom_bounds_640_full_page": list(bnds),
        "bottom_crop_box_640": list(crop640),
        "bottom_cropped_wh_640": list(wh640),
        "top_bounds_640_full_page": list(top_bounds_640),
        "palette_640_measured": {
            "orange_exact_count": pal["orange_exact_count"],
            "green_exact_count": pal["green_exact_count"],
            "white_pixel_count_r14b": pal["white_pixel_count_r14b"],
            "white_in_board_after": pal["white_in_board_after"],
        },
    }


def _kicad_version() -> str:
    if not KICAD_CLI.exists():
        _fail(f"kicad-cli 不存在：{KICAD_CLI}")
    proc = subprocess.run([str(KICAD_CLI), "version"], capture_output=True,
                          text=True)
    ver = (proc.stdout or proc.stderr).strip()
    if proc.returncode != 0 or KICAD_VERSION not in ver:
        _fail(f"kicad-cli 版本验证失败：{ver!r}（预期 {KICAD_VERSION}）")
    return ver


def _provenance_check() -> dict:
    """同源性探针（probe/framing 共用）：kicad-cli 从 staging-r4/applied
    重导出 combined bottom（r4 同配方、输出=系统临时目录）→ 640 光栅化
    与冻结 applied-bottom.pdf 640 光栅化逐字节比对（r14b 实证：PDF 字节
    跨运行不同而光栅逐字节稳定，故比对光栅）。确定性断言。"""
    tmp = Path(tempfile.mkdtemp(prefix="pcbflow-r17-prov-"))
    fresh_pdf = tmp / "applied-bottom-fresh.pdf"
    t0 = time.perf_counter()
    cmd = _run_kicad_export_abs(fresh_pdf, STAGED_REL["applied"],
                                LAYERS_BOTTOM, True)
    fresh_png, fw, fh = _compose_raster(fresh_pdf, RASTER_DPI_PREV)
    frozen_png, fw2, fh2 = _compose_raster(R4_PDFS["applied-bottom"],
                                           RASTER_DPI_PREV)
    ok = bool(fresh_png == frozen_png and (fw, fh) == (fw2, fh2))
    if not ok:
        _fail("同源性探针证伪：staging-r4 重导出光栅与 r4 冻结 PDF 光栅"
              "非逐字节同（渲染源同源性不成立，本轮作废）")
    print(f"[r17] 同源性：pixmap={fw}x{fh} raster_byte_equal={ok} "
          f"export_s={time.perf_counter() - t0:.1f}（运行观测）")
    return {"method": (
                "kicad-cli 从 staging-r4/applied.kicad_pcb 重导出 combined "
                "bottom（--mode-single --scale 1 --check-zones "
                "--drill-shape-opt 2 --layers " + LAYERS_BOTTOM +
                " --mirror，输出=系统临时目录）→ 40pt 组合页 dpi640 光栅化"
                " vs 冻结 applied-bottom.pdf 同参光栅化，逐字节比对"
                "（r14b 实证口径：比对光栅不比对 PDF 字节）"),
            "raster_byte_equal": ok,
            "pixmap_wh": [fw, fh],
            "export_cmd_head": cmd[:8]}


def _run_kicad_export_abs(out_path: Path, in_rel: str, layers: str,
                          mirror: bool) -> list:
    """kicad-cli 2D PDF 导出（探针同源性专用；照 s50/s51 模式：绝对路径
    执行、cwd=REPO；输出=调用方给定的仓库外临时路径）。"""
    cmd = ["pcb", "export", "pdf", "--mode-single", "--scale", "1",
           "--check-zones", "--drill-shape-opt", "2", "--layers", layers]
    if mirror:
        cmd.append("--mirror")
    cmd += ["-o", str(out_path), in_rel]
    proc = subprocess.run([str(KICAD_CLI)] + cmd, cwd=str(REPO),
                          capture_output=True, text=True)
    if proc.returncode != 0 or not out_path.exists():
        _fail(f"kicad-cli 失败 rc={proc.returncode}: "
              f"{(proc.stderr or proc.stdout or '')[-500:]}")
    return cmd


def _compose_raster(pdf_path: Path, dpi: int) -> tuple:
    """fitz 组合页光栅化（与 r5 逐字同口径，dpi 参数化）：40pt 白边组合页。
    返回 (png_bytes, pix_w, pix_h)。"""
    import fitz

    src = fitz.open(str(pdf_path))
    try:
        if src.page_count != 1:
            _fail(f"{pdf_path.name}: 页数 {src.page_count} != 1（mode-single）")
        src_page = src[0]
        w, h = src_page.rect.width, src_page.rect.height
        m = COMPOSE_MARGIN_PT
        out = fitz.open()
        try:
            page = out.new_page(width=w + 2 * m, height=h + 2 * m)
            page.show_pdf_page(fitz.Rect(m, m, m + w, m + h), src, 0)
            pix = page.get_pixmap(dpi=dpi, alpha=False)
            return pix.tobytes("png"), pix.width, pix.height
        finally:
            out.close()
    finally:
        src.close()


def _load_rgb(png_bytes: bytes) -> "np.ndarray":
    from PIL import Image
    im = Image.open(io.BytesIO(png_bytes))
    return np.asarray(im.convert("RGB"))  # 只读视图（调用方按需拷贝）


def _bounds_of(png_bytes: bytes) -> dict:
    return calibration.png_board_pixel_bounds(png_bytes)


def _peak_working_set_mb() -> int:
    """当前进程峰值工作集（Windows；观测值，只进 stdout，不入冻结件）。"""
    try:
        import ctypes.wintypes as wt

        class PMC(ctypes.Structure):
            _fields_ = [
                ("cb", wt.DWORD), ("PageFaultCount", wt.DWORD),
                ("PeakWorkingSetSize", ctypes.c_size_t),
                ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t),
                ("PeakPagefileUsage", ctypes.c_size_t),
            ]
        pmc = PMC()
        pmc.cb = ctypes.sizeof(PMC)
        k32 = ctypes.windll.kernel32
        k32.GetCurrentProcess.restype = wt.HANDLE
        k32.K32GetProcessMemoryInfo.argtypes = [wt.HANDLE,
                                                ctypes.POINTER(PMC),
                                                wt.DWORD]
        h = k32.GetCurrentProcess()
        ok = k32.K32GetProcessMemoryInfo(h, ctypes.byref(pmc), pmc.cb)
        return int(pmc.PeakWorkingSetSize // 1048576) if ok else -1
    except Exception:
        return -1


# ---------------------------------------------------------------------------
# 白墨矢量图元 mask 重建（r14b 规则逐字重放，dpi 参数化）
# ---------------------------------------------------------------------------

def _is_white_fill(d: dict) -> bool:
    f = d.get("fill")
    return f is not None and all(abs(v - 1.0) < 1e-6 for v in f)


def _is_white_stroke(d: dict) -> bool:
    c = d.get("color")
    return (d.get("fill") is None and c is not None
            and all(abs(v - 1.0) < 1e-6 for v in c))


def _rebuild_white_masks(pdf_path: Path, dpi: int):
    """矢量重建白图元 mask（r14b 规则，dpi 参数化）：fitz Shape 在同几何
    组合页（40pt 边距）上只绘制白 fill（红）与白 stroke（绿），黑底，
    dpi 光栅化。返回 (fill_mask, stroke_mask, meta)。确定性纯函数。"""
    import fitz

    doc = fitz.open(str(pdf_path))
    try:
        page = doc[0]
        w, h = page.rect.width, page.rect.height
        draws = page.get_drawings()
        m = COMPOSE_MARGIN_PT
        out = fitz.open()
        try:
            np_ = out.new_page(width=w + 2 * m, height=h + 2 * m)
            np_.draw_rect(fitz.Rect(0, 0, w + 2 * m, h + 2 * m),
                          color=None, fill=(0, 0, 0))
            shape = np_.new_shape()
            nf = ns = 0
            for d in draws:
                items = d["items"]
                if _is_white_fill(d):
                    nf += 1
                    color, width = (1, 0, 0), 1.0
                elif _is_white_stroke(d):
                    ns += 1
                    color, width = (0, 1, 0), d.get("width") or 1.0
                else:
                    continue
                for it in items:
                    if it[0] == "l":
                        shape.draw_line(it[1] + (m, m), it[2] + (m, m))
                    elif it[0] == "c":
                        shape.draw_bezier(it[1] + (m, m), it[2] + (m, m),
                                          it[3] + (m, m), it[4] + (m, m))
                    elif it[0] == "re":
                        shape.draw_rect(it[1] + (m, m, m, m))
                    elif it[0] == "qu":
                        shape.draw_quad(it[1] + (m, m))
                if _is_white_fill(d):
                    shape.finish(fill=color, color=None,
                                 even_odd=bool(d.get("even_odd", False)),
                                 closePath=bool(d.get("closePath", True)))
                else:
                    shape.finish(color=color, fill=None, width=width,
                                 closePath=bool(d.get("closePath", True)))
            shape.commit()
            pix = np_.get_pixmap(dpi=dpi, alpha=False)
            arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
                pix.height, pix.width, pix.n)[:, :, :3]
            fill_mask = np.ascontiguousarray(arr[:, :, 0] > 127)
            stroke_mask = np.ascontiguousarray(arr[:, :, 1] > 127)
            meta = {
                "rebuilt_white_fill_drawings": nf,
                "rebuilt_white_stroke_drawings": ns,
                "mask_fill_pixel_count": int(fill_mask.sum()),
                "mask_stroke_pixel_count": int(stroke_mask.sum()),
                "mask_overlap_pixels": int((fill_mask & stroke_mask).sum()),
                "method": (
                    "fitz Shape 重建 combined PDF 的白 fill（红）/白 stroke"
                    "（绿）到同几何 40pt 组合页，黑底 dpi1280 光栅化，"
                    ">127 阈值二值化；逐字重画 items（l/c/re/qu），fill 规则"
                    "与 closePath 从 get_drawings 元数据透传（r14b 规则逐字"
                    "重放，dpi 参数化）"),
            }
            del arr, pix
            return fill_mask, stroke_mask, meta
        finally:
            out.close()
    finally:
        doc.close()


def _euclid(a, b) -> float:
    return float(np.sqrt(sum((int(x) - int(y)) ** 2 for x, y in zip(a, b))))


def _color_distance_table() -> dict:
    table = {}
    ok = True
    for tname, tRGB in (("target_orange", TARGET_ORANGE),
                        ("target_green", TARGET_GREEN)):
        for cname, cRGB in CANVAS_COLORS.items():
            if cname == tname:
                continue
            d = _euclid(tRGB, cRGB)
            table[f"{tname}_vs_{cname}"] = round(d, 2)
            if d <= COLOR_DIST_MIN:
                ok = False
    return {"distances": table, "min_required": COLOR_DIST_MIN,
            "all_above_threshold": ok}


# ---------------------------------------------------------------------------
# 每态确定性测量（1280；probe/framing/render 共用同一实现）
# ---------------------------------------------------------------------------

def _bottom_bounds_expectation() -> list:
    """640 实测板界×2 的 1280 期望值（r14b witness 活读）。"""
    b = _r14b_refs()
    return [v * SCALE for v in b["bottom_bounds_640_full_page"]]


def _top_bounds_expectation() -> list:
    b = _r14b_refs()
    return [v * SCALE for v in b["top_bounds_640_full_page"]]


def _assert_bounds_2x(got: dict, exp: list, tag: str) -> dict:
    gv = [got["x0"], got["y0"], got["x1"], got["y1"]]
    deltas = [g - e for g, e in zip(gv, exp)]
    for d in deltas:
        if abs(d) > BOUNDS_TOL_PX:
            _fail(f"{tag} 板界 ×2 断言失败（±{BOUNDS_TOL_PX}px）：{gv} vs "
                  f"{exp} deltas={deltas}")
    return {"measured_1280": gv, "expected_2x_of_640": exp,
            "deltas_px": deltas, "tolerance_px": BOUNDS_TOL_PX,
            "pass": True}


def _crop_box(bounds: dict) -> tuple:
    return (bounds["x0"] - CROP_MARGIN_PX, bounds["y0"] - CROP_MARGIN_PX,
            bounds["x1"] + 1 + CROP_MARGIN_PX, bounds["y1"] + 1 + CROP_MARGIN_PX)


def _build_bottom(state: str) -> tuple:
    """bottom 单态全链（r14b 配色规则重放 @1280；确定性纯函数）。
    返回 (crop_bytes, record, rerun_closure)。"""
    import json
    from PIL import Image

    base_pdf = R4_PDFS[f"{state}-bottom"]
    t0 = time.perf_counter()
    png_full, pw, ph = _compose_raster(base_pdf, RASTER_DPI)
    t_raster = time.perf_counter() - t0
    t0 = time.perf_counter()
    bounds = _bounds_of(png_full)
    t_bounds = time.perf_counter() - t0
    full_wh = [pw, ph]
    exp_full_wh = [2 * v for v in (8195, 6003)]
    if full_wh != exp_full_wh:
        _fail(f"{state}-bottom 1280 全页尺寸 {full_wh} != 640 实测×2 "
              f"{exp_full_wh}")
    bounds_check = _assert_bounds_2x(bounds, _bottom_bounds_expectation(),
                                     f"{state}-bottom")

    fm, sm, mask_meta = _rebuild_white_masks(base_pdf, RASTER_DPI)
    wink_full = fm | sm
    del fm, sm

    box = _crop_box(bounds)
    im = Image.open(io.BytesIO(png_full))
    cropped = im.crop(box)
    del im, png_full
    arr = np.array(cropped.convert("RGB"), dtype=np.uint8)  # 可写窗口拷贝
    del cropped
    H, W = arr.shape[:2]

    white_m = np.all(arr == 255, axis=2)
    board_m = np.zeros((H, W), dtype=bool)
    bx0, by0 = bounds["x0"] - box[0], bounds["y0"] - box[1]
    bx1, by1 = bounds["x1"] - box[0], bounds["y1"] - box[1]
    board_m[by0:by1 + 1, bx0:bx1 + 1] = True
    wink_c = wink_full[box[1]:box[1] + H, box[0]:box[0] + W]
    del wink_full

    pre_white = int(white_m.sum())
    # overlay1：白墨图元 mask → 橙（限板界内；r14b 规则）
    sel_o = wink_c & board_m
    # overlay2：板内空隙白 mask → 绿（=板内纯白且非白墨 mask；与橙构造互斥）
    sel_g = white_m & board_m & ~wink_c
    orange = np.array(TARGET_ORANGE, dtype=np.uint8)
    green = np.array(TARGET_GREEN, dtype=np.uint8)
    arr[sel_o] = orange
    arr[sel_g] = green
    white_after_m = np.all(arr == 255, axis=2)
    white_in_board_after = int((white_after_m & board_m).sum())
    white_after = int(white_after_m.sum())
    out_im = Image.fromarray(arr, "RGB")
    del arr, white_m, board_m, wink_c, white_after_m, sel_o, sel_g
    bio = io.BytesIO()
    out_im.save(bio, "PNG")
    crop_bytes = bio.getvalue()

    # 裁剪 sanity：png_board_pixel_bounds 对成图实测（白边恰 240px）
    cbounds = _bounds_of(crop_bytes)
    if [cbounds["x0"], cbounds["y0"], cbounds["x1"], cbounds["y1"]] != [
            bx0, by0, bx1, by1]:
        _fail(f"{state}-bottom 裁剪板界不符（白边≠240px）："
              f"{[cbounds['x0'], cbounds['y0'], cbounds['x1'], cbounds['y1']]} "
              f"vs {[bx0, by0, bx1, by1]}")

    record = {
        "image_wh": [W, H],
        "full_page_wh": full_wh,
        "board_bounds_full_1280": bounds_check,
        "crop_box": list(box),
        "white_pre_overlay_cropped": pre_white,
        "timings_observed_only": {
            "raster_compose_s": round(t_raster, 2),
            "bounds_full_page_s": round(t_bounds, 2),
            "note": "运行观测，只进 stdout/探针记录，不入冻结断言",
        },
        "_mask_meta": mask_meta,
        "_crop_bounds_cropped": [bx0, by0, bx1, by1],
    }
    # 调色板实测（成图字节上重算——确定性）
    carr = _load_rgb(crop_bytes)
    om = np.all(carr == orange, axis=2)
    gm = np.all(carr == green, axis=2)
    palette = {
        "orange_exact_count": int(om.sum()),
        "green_exact_count": int(gm.sum()),
        "orange_green_mix_count": int((om & gm).sum()),
        "white_pixel_count_r17": white_after,
        "white_in_board_after": white_in_board_after,
        "white_outside_board_after": white_after - white_in_board_after,
        "white_fraction_r17": round(white_after / (W * H), 8),
    }
    del om, gm, carr
    record["palette"] = palette

    def rerun() -> bytes:
        again, rec, _ = _build_bottom(state)
        return again

    return crop_bytes, record, rerun


def _build_top(state: str) -> tuple:
    """top 单态全链（1280 原生无配色；确定性纯函数）。"""
    from PIL import Image

    base_pdf = R4_PDFS[f"{state}-top"]
    png_full, pw, ph = _compose_raster(base_pdf, RASTER_DPI)
    full_wh = [pw, ph]
    exp_full_wh = [2 * v for v in (8195, 6003)]
    if full_wh != exp_full_wh:
        _fail(f"{state}-top 1280 全页尺寸 {full_wh} != 640 实测×2 "
              f"{exp_full_wh}")
    bounds = _bounds_of(png_full)
    bounds_check = _assert_bounds_2x(bounds, _top_bounds_expectation(),
                                     f"{state}-top")
    box = _crop_box(bounds)
    im = Image.open(io.BytesIO(png_full))
    cropped = im.crop(box)
    del im, png_full
    bio = io.BytesIO()
    cropped.save(bio, "PNG")
    crop_bytes = bio.getvalue()
    del cropped

    carr = _load_rgb(crop_bytes)
    W, H = carr.shape[1], carr.shape[0]
    orange = np.array(TARGET_ORANGE, dtype=np.uint8)
    green = np.array(TARGET_GREEN, dtype=np.uint8)
    palette = {
        "orange_exact_count": int(np.all(carr == orange, axis=2).sum()),
        "green_exact_count": int(np.all(carr == green, axis=2).sum()),
        "white_pixel_count_r17": int(np.all(carr == 255, axis=2).sum()),
        "white_fraction_r17": round(
            int(np.all(carr == 255, axis=2).sum()) / (W * H), 8),
    }
    del carr
    cb = _bounds_of(crop_bytes)
    bx0, by0 = bounds["x0"] - box[0], bounds["y0"] - box[1]
    bx1, by1 = bounds["x1"] - box[0], bounds["y1"] - box[1]
    if [cb["x0"], cb["y0"], cb["x1"], cb["y1"]] != [bx0, by0, bx1, by1]:
        _fail(f"{state}-top 裁剪板界不符（白边≠240px）")
    record = {
        "image_wh": [W, H],
        "full_page_wh": full_wh,
        "board_bounds_full_1280": bounds_check,
        "crop_box": list(box),
        "palette": palette,
        "coloring": "none（top 无配色，与既往一致；kicad 原生层色）",
    }

    def rerun() -> bytes:
        again, rec, _ = _build_top(state)
        return again

    return crop_bytes, record, rerun


# ---------------------------------------------------------------------------
# probe
# ---------------------------------------------------------------------------

def cmd_probe() -> None:
    _protected_check()
    _staging_check()
    _axis_plan_check()
    _r4_pdfs_check()
    _r14b_refs()
    ver = _kicad_version()
    for name in FINAL_PNGS:
        if (R17_DIR / f"{name}.png").exists():
            _fail(f"renders-r17/{name}.png 已存在（probe 拒绝在官方成图后"
                  "运行；如需重跑探针请先确认成图件冻结状态）")

    print("=== [r17 probe] 1) 同源性：kicad-cli 从 staging-r4 重导出 "
          "combined bottom（r4 配方）vs 冻结 applied-bottom.pdf 640 光栅 ===")
    prov = _provenance_check()
    print(f"    pixmap={prov['pixmap_wh']} "
          f"raster_byte_equal={prov['raster_byte_equal']}")

    print("=== [r17 probe] 2) 1280 可行性：全页尺寸/板界×2/时长/内存 ===")
    ws0 = _peak_working_set_mb()
    t0 = time.perf_counter()
    png_b, pw, ph = _compose_raster(R4_PDFS["applied-bottom"], RASTER_DPI)
    t_raster = time.perf_counter() - t0
    t0 = time.perf_counter()
    bounds_b = _bounds_of(png_b)
    t_bounds = time.perf_counter() - t0
    del png_b
    ws1 = _peak_working_set_mb()
    print(f"    bottom 全页 {pw}x{ph}（640 实测×2=[16390,12006]）"
          f"raster_s={t_raster:.1f} bounds_s={t_bounds:.1f} "
          f"peakWS_delta_MB={ws1 - ws0}")
    bb = _assert_bounds_2x(bounds_b, _bottom_bounds_expectation(),
                           "probe applied-bottom")
    print(f"    bottom 板界 1280={bb['measured_1280']} "
          f"期望640×2={bb['expected_2x_of_640']} deltas={bb['deltas_px']}px")

    png_t, pw2, ph2 = _compose_raster(R4_PDFS["applied-top"], RASTER_DPI)
    bounds_t = _bounds_of(png_t)
    del png_t
    tb = _assert_bounds_2x(bounds_t, _top_bounds_expectation(),
                           "probe applied-top")
    print(f"    top 全页 {pw2}x{ph2} 板界 1280={tb['measured_1280']} "
          f"deltas={tb['deltas_px']}px")

    print("=== [r17 probe] 3) margin 物理等值 ===")
    print(f"    {MARGIN_CONVERSION_FORMULA}")

    print("=== [r17 probe] 4) 配色语义 2× 口径（橙/绿 ≈4× r14b，±25%）===")
    refs = _r14b_refs()
    pal640 = refs["palette_640_measured"]
    bottom_full_rasters = {}
    probe_facts = {}
    for state in BOTTOM_STATES:
        crop_bytes, rec, _ = _build_bottom(state)
        p = rec["palette"]
        o, g = p["orange_exact_count"], p["green_exact_count"]
        o4 = pal640["orange_exact_count"] * SCALE ** 2
        g4 = pal640["green_exact_count"] * SCALE ** 2
        ro, rg = o / o4, g / g4
        ok_o = abs(ro - 1.0) <= PRED_TOL
        ok_g = abs(rg - 1.0) <= PRED_TOL
        print(f"    {state}-bottom: 橙={o}（4×预期≈{o4}，ratio={ro:.3f}，"
              f"{'PASS' if ok_o else 'FAIL'}）绿={g}（4×预期≈{g4}，"
              f"ratio={rg:.3f}，{'PASS' if ok_g else 'FAIL'}）"
              f"板内白={p['white_in_board_after']}（必须=0）"
              f"白(板外边距)={p['white_outside_board_after']} "
              f"裁后尺寸={rec['image_wh']}")
        if p["white_in_board_after"] != 0:
            _fail(f"{state}: 板内白 {p['white_in_board_after']} != 0"
                  "（配色重放语义失败）")
        if not (ok_o and ok_g):
            _fail(f"{state}: 橙/绿 4× 预测越出 ±25% 带（ratio 橙={ro:.3f} "
                  f"绿={rg:.3f}）——探针如实证伪，本轮作废")
        probe_facts[state] = {
            "image_wh": rec["image_wh"],
            "board_bounds_full_1280": rec["board_bounds_full_1280"],
            "crop_box": rec["crop_box"],
            "palette": {k: v for k, v in p.items()},
            "mask_rebuild": rec["_mask_meta"],
        }
        bottom_full_rasters[state] = crop_bytes
    if bottom_full_rasters["applied"] != bottom_full_rasters["prep1"]:
        _fail("两板 bottom 1280 成图非逐字节同（与 r5/r14b 两态 bottom "
              "逐字节同的既证事实矛盾）")
    print("    两板 bottom 1280 成图逐字节同（与 r5/r14b 一致性延续）")

    for state in BOTTOM_STATES:
        crop_bytes, rec, _ = _build_top(state)
        probe_facts[f"{state}-top"] = {
            "image_wh": rec["image_wh"],
            "board_bounds_full_1280": rec["board_bounds_full_1280"],
            "palette": rec["palette"],
        }
        print(f"    {state}-top: 裁后={rec['image_wh']} "
              f"白={rec['palette']['white_pixel_count_r17']} "
              f"橙/绿（须=0）=({rec['palette']['orange_exact_count']},"
              f"{rec['palette']['green_exact_count']})")
        if rec["palette"]["orange_exact_count"] or \
                rec["palette"]["green_exact_count"]:
            _fail(f"{state}-top 出现橙/绿（top 无配色被破坏）")
    print(f"=== [r17 probe] 结论：1280 管线可行；峰值工作集观测 "
          f"{_peak_working_set_mb()} MB（运行观测）；kicad-cli {ver} ===")
    print("[r17] probe 完成：同源性 PASS、尺寸/板界 ×2 PASS、配色 4× PASS、"
          "板内白=0；时长/内存=运行观测（不入冻结件）")


# ---------------------------------------------------------------------------
# framing
# ---------------------------------------------------------------------------

def _probe_block() -> dict:
    """确定性探针块（probe/framing/render 共用同一实现；纯函数）。
    bottom 两态成图逐字节同在块内断言（r5/r14b 既证事实的 1280 延续）。"""
    facts = {"bottom": {}, "top": {}, "two_states_bottom_byte_equal": None}
    bottom_bytes = {}
    for state in BOTTOM_STATES:
        crop_bytes, rec, _ = _build_bottom(state)
        facts["bottom"][state] = rec
        bottom_bytes[state] = crop_bytes
    if bottom_bytes["applied"] != bottom_bytes["prep1"]:
        _fail("两板 bottom 1280 成图非逐字节同（与 r5/r14b 两态 bottom "
              "逐字节同的既证事实矛盾）")
    facts["two_states_bottom_byte_equal"] = True
    for state in BOTTOM_STATES:
        _, rec, _ = _build_top(state)
        facts["top"][state] = rec
    return facts


def cmd_framing() -> None:
    _protected_check()
    _staging_check()
    _axis_plan_check()
    r4 = _r4_pdfs_check()
    refs = _r14b_refs()
    import json

    for name in FINAL_PNGS:
        if (R17_DIR / f"{name}.png").exists():
            print(f"[r17] 注意：renders-r17/{name}.png 已存在（framing 重跑"
                  "模式——确定性复算，防覆写守卫保证幂等）")

    facts = _probe_block()
    prov = _provenance_check()
    b_ap = facts["bottom"]["applied"]
    pal = b_ap["palette"]
    pal640 = refs["palette_640_measured"]
    o4 = pal640["orange_exact_count"] * SCALE ** 2
    g4 = pal640["green_exact_count"] * SCALE ** 2
    cd = _color_distance_table()
    if not cd["all_above_threshold"]:
        _fail(f"色距断言失败：{cd}")
    # 配色 4× 一致性（applied 与 prep1 相同——成图逐字节同）
    for s in BOTTOM_STATES:
        p = facts["bottom"][s]["palette"]
        if p["white_in_board_after"] != 0:
            _fail(f"{s}: 板内白 {p['white_in_board_after']} != 0")
        if abs(p["orange_exact_count"] / o4 - 1.0) > PRED_TOL or \
                abs(p["green_exact_count"] / g4 - 1.0) > PRED_TOL:
            _fail(f"{s}: 橙/绿 4× 预测越出 ±25% 带")

    doc = {
        "schema_version": "3.0",
        "kind": "tl2_calibration_render_framing_r17_preregistration",
        "round_label": ROUND_LABEL,
        "round_id_constant": ROUND_ID,
        "date_constant": DATE_CONSTANT,
        "domain_id": DOMAIN_ID,
        "evaluation_split": {
            "declared": "development",
            "basis": "evaluation-protocol-v1.md §1/§4（同域迭代校准轮预备；"
                     "全部产物仅作 development 证据）",
        },
        "no_visual_reading": True,
        "axis_reference": {
            "path_rel": "out/v3-tl2/calibration/axis-experiment-plan-r17-r20.json",
            "sha256": _sha(AXIS_PLAN),
            "expected_prefix": AXIS_PLAN_PREFIX,
            "declaration": (
                "轴 1=渲染分辨率倍增（640→1280 dpi，四图全部）；本渲染包"
                "=轴 1 单变量仪器轮实施，产物供 R17 盲读。"),
        },
        "single_variable_change": {
            "declaration": (
                "本轮相对 r14b 只改变一个仪器变量：光栅分辨率 dpi 640→1280"
                "（线度×2、像素数×4，四图全部）。bottom 视 r14b 配色规则"
                "逐字重放（白墨图元→橙 (255,165,0)、板内空隙白→绿 "
                "(0,128,0)；mask 在 1280 像密度下重算，规则/z 序/色值不变）；"
                "top 视无配色（与既往一致——r14b top 为 r5 640 逐字节拷贝，"
                "本轮改为同一冻结矢量源的 1280 原生重渲染，属同一单变量"
                "（分辨率）在 top 的应用）。其余口径（组合页 40pt、层清单、"
                "冻结矢量源、png_board_pixel_bounds 板界仪器、裁剪公式）与 "
                "r5/r14b 逐字同。"),
            "margin_conversion": {
                "formula": MARGIN_CONVERSION_FORMULA,
                "px_640": CROP_MARGIN_PX_PREV,
                "px_1280": CROP_MARGIN_PX,
                "physical_inch": 0.1875,
            },
            "bounds_conversion": {
                "formula": BOUNDS_CONVERSION_FORMULA,
                "tolerance_px": BOUNDS_TOL_PX,
            },
            "color_rules_replay": (
                "r14b 配色规则逐字重放声明：目标 RGB、mask 语义（白墨矢量"
                "图元=fitz Shape 矢量重建 fill∪stroke、板内空隙白=板内纯白"
                "且非白墨 mask）、z 序（base→橙→绿，构造互斥）、混合数学"
                "（二值 mask 全量替换 out[mask]=color，阈值>127）全部与 "
                "r14b 逐字相同；唯一差异=mask 与 base 光栅在 1280 像密度"
                "下重算（同矢量几何、同 40pt 组合页）。"),
        },
        "render_source_same_as_r14b": {
            "declaration": (
                "渲染源与 r14b 同源：staging-r4 逐字节冻结拷贝（sha 复核）"
                "→ renders-r4 冻结 combined PDF 四件（sha 自 render-framing-"
                "r5.json frozen_inputs 活读复核；r5 声明其角色=任意 DPI 重"
                "光栅化=确定性）。探针以 kicad-cli 从 staging-r4/applied 重"
                "导出 combined bottom（r4 同配方）并与冻结 PDF 640 光栅逐"
                "字节比对通过（PDF 字节跨运行不承诺等同而光栅逐字节稳定，"
                "r14b 实证口径）。官方成图零 kicad 调用。"),
            "frozen_pdfs": r4,
        },
        "probe_conclusion": {
            "feasible": True,
            "deterministic_facts": {
                "full_page_wh_1280": b_ap["full_page_wh"],
                "bottom_board_bounds_1280": b_ap["board_bounds_full_1280"],
                "top_board_bounds_1280":
                    facts["top"]["applied"]["board_bounds_full_1280"],
                "bottom_cropped_wh_1280": b_ap["image_wh"],
                "top_cropped_wh_1280":
                    facts["top"]["applied"]["image_wh"],
                "two_states_bottom_byte_equal":
                    facts["two_states_bottom_byte_equal"],
                "mask_rebuild_applied":
                    facts["bottom"]["applied"]["_mask_meta"],
                "provenance_reexport": prov,
            },
            "runtime_observations_not_frozen": (
                "时长/峰值内存=探针运行观测（stdout 记录：1280 全页光栅化"
                "约 5s、全页板界扫描约 40s/次、裁后扫描约 3s/次量级；峰值"
                "工作集约 1.5-2GB 量级），非确定性量，不入冻结断言；可行性"
                "判据=全部确定性断言 PASS+进程正常完成。"),
        },
        "synthesis_method": {
            "declaration": (
                "base=renders-r4 冻结 combined PDF（四图唯一图像来源，sha "
                "复核）经 40pt 组合页+dpi1280 光栅化；bottom：overlay1=橙"
                "（白墨矢量重建 mask ∩ 板界）、overlay2=绿（板内纯白且非白"
                "墨 mask，与橙构造互斥）；top：零 overlay。裁剪=板界实测 "
                "png_board_pixel_bounds ±240px。配色与裁剪次序等价性：逐像"
                "素重配色与裁剪可交换（r14b 先在整页配色后裁剪，本轮先取"
                "窗口后在窗口坐标系配色，作用像素集逐一相同）。"),
            "z_order": ["base(combined 层清单见 render-framing-r5.json)",
                        "overlay1:white_ink_drawings→orange（仅 bottom）",
                        "overlay2:board_void_white→green（仅 bottom）"],
            "blend_math": "out[mask]=color（布尔 mask 全量替换；mask 阈值"
                          ">127）",
            "base_inputs": r4,
            "determinism_scope": (
                "kicad-cli PDF 字节不做跨运行确定性断言（r4/r14b 实证口径）；"
                "确定性断言范围=冻结 PDF→组合页光栅化→配色→裁剪→PNG 字节"
                "全链重跑逐字节一致（四图各一次重跑自证）。"),
        },
        "compose_and_crop": {
            "dpi": RASTER_DPI,
            "dpi_previous": RASTER_DPI_PREV,
            "compose_margin_pt": COMPOSE_MARGIN_PT,
            "crop_margin_px": CROP_MARGIN_PX,
            "crop_margin_px_previous": CROP_MARGIN_PX_PREV,
            "crop_box_formula": "(x0-240, y0-240, x1+1+240, y1+1+240)，"
                                "(x0,y0,x1,y1)=dpi1280 全页 "
                                "png_board_pixel_bounds 实测板界",
            "rasterization_tool": "PyMuPDF (fitz) get_pixmap(dpi=1280, "
                                  "alpha=False) + PIL Image.crop/save('PNG')",
            "measured_1280": {
                "bottom_applied": {
                    k: b_ap[k] for k in ("image_wh", "full_page_wh",
                                         "board_bounds_full_1280",
                                         "crop_box") if k in b_ap},
                "bottom_prep1": {
                    k: facts["bottom"]["prep1"][k]
                    for k in ("image_wh", "full_page_wh",
                              "board_bounds_full_1280", "crop_box")
                    if k in facts["bottom"]["prep1"]},
                "top_applied": {
                    k: facts["top"]["applied"][k]
                    for k in ("image_wh", "full_page_wh",
                              "board_bounds_full_1280", "crop_box")
                    if k in facts["top"]["applied"]},
                "top_prep1": {
                    k: facts["top"]["prep1"][k]
                    for k in ("image_wh", "full_page_wh",
                              "board_bounds_full_1280", "crop_box")
                    if k in facts["top"]["prep1"]},
            },
            "board_bounds_assertion": (
                "成图板界（裁后坐标）=全页板界−裁剪原点，且四侧白边恰为 "
                "240px；全页板界=640 实测×2 ±2px（framing measured_1280 "
                "逐字断言）。配色仅作用于板界内白域，不移动非白 bbox。"),
        },
        "palette_assertions": {
            "formulas": (
                "对每张 r17 bottom PNG：a) 橙 (255,165,0) 精确像素计数>0 且"
                "在 4× r14b 实测 ±25% 带内；b) 绿 (0,128,0) 同理；c) 橙绿"
                "零交集；d) 板界内纯白像素=0（严格）；e) 剩余纯白全部位于"
                "板界外（240px 裁剪边距带，仪器口径保留）。对每张 r17 top "
                "PNG：橙/绿精确计数=0（无配色）。"),
            "preregistered_prediction": {
                "orange_pixel_count_expected_4x": o4,
                "green_pixel_count_expected_4x": g4,
                "tolerance_relative": PRED_TOL,
                "orange_band": [round(o4 * (1 - PRED_TOL)),
                                round(o4 * (1 + PRED_TOL))],
                "green_band": [round(g4 * (1 - PRED_TOL)),
                               round(g4 * (1 + PRED_TOL))],
                "white_in_board_after": 0,
                "prediction_basis": (
                    "r14b 实测（witness 活读复核）：橙=81672、绿=206632、"
                    "板内白=0。像密度×2 ⇒ 线度×2 ⇒ 同名色像素数≈×4（抗锯齿"
                    "边界占比变化仅致百分之几级偏离）。方向断言先于成图落盘："
                    "橙>0、绿>0、4× 带内、板内白清零、top 橙/绿=0。"),
            },
            "color_distance_assertion": cd,
        },
        "diag_plan": {
            "declaration": (
                "诊断对照裁片（成图后产出；供主审人工分辨力核验，非盲读件）："
                "D1-D3 已证实的近触区各取一处，r14b（640）与 r17（1280）"
                "同一板面区域各一裁片，640 腿 2× 最近邻放大至与 1280 腿"
                "相同显示尺寸并排拼图。bottom=基准黑点-焊盘邻接区（r14b "
                "证书点 (282,224)c 邻域）；top=applied-top 板中部相邻 "
                "courtyard 对（程序化检测洋红 (255,38,226) 精确色分量，"
                "scipy.ndimage.label 连通域 bbox，边缘间隙 ≤8px(1280) 的"
                "相邻对中取对中点离图幅中心最近者，平局取 (min_x,min_y) "
                "字典序）。区域坐标在 640 裁剪系整数定义，1280 腿=×2+"
                "crop 原点差映射（像素精确对应）；manifest 记录区域板面"
                "坐标、两版像素尺度、映射换算式。"),
            "regions": {
                "bottom": {
                    "anchor_r14b_cropped_xy": [282, 224],
                    "half_size_640_px": 80,
                    "basis": "diag-r13-review D1/D2：左上小足迹区基准黑点 "
                             "(0,0,0) ⌀≈23px + 白 C 形轮廓环抱 + 焊盘邻接",
                },
                "top": {
                    "selection": "programmatic_courtyard_pair_nearest_center",
                    "basis": "任务指定：applied-top 中部相邻 courtyard 对"
                             "（D1-D3 近触形态的 top 视对应物）",
                },
            },
        },
        "fallback": {
            "bounds_fail": (
                "板界 ×2 断言/裁剪白边=240px 断言任一失败即停止并如实报告，"
                "不得静默改参数。"),
            "palette_fail": (
                "橙/绿 4× 带断言或板内白=0 断言失败即停止并如实报告（探针"
                "已预验通过；成图阶段失败=证伪，如实记录，不得硬造）。"),
        },
        "freeze_order": {
            "declaration": (
                "本文件先于本轮任何官方成图落盘（probe→framing→render→"
                "witness→diag）；renders-r17/ 四张 PNG 在本文件落盘时尚不"
                "存在；probe 零 out/ 写入（临时目录+全内存）。"),
        },
        "overwrite_guard": (
            "目标文件已存在非字节等同→FAIL；字节等同→幂等。"),
        "zero_write_discipline": (
            "out/ 既有文件零改动（staging-r4/renders-r4/renders-r5/"
            "renders-r14b/render-framing-r5.json/render-framing-r14b.json/"
            "render-witness-r14b.json/axis-experiment-plan-r17-r20.json 等"
            "只读）；datasets/ 零写入；pcbflow/ 与 tests/ 零改动（仅 "
            "import）；活板文件全程只读（witness 收尾 sha 见证）。新建范围="
            "scripts/s62_render_r17.py、renders-r17/（四 PNG）、"
            "render-framing-r17.json、render-witness-r17.json、"
            "diag-r17-render/（两张对照裁片+manifest）。"),
        "protected_files_frozen_prefixes": PROTECTED,
        "r14b_references": {k: v for k, v in refs.items()
                            if k != "color_mapping_r14b"},
        "input_board_witness": {
            "applied": STAGED_SHA_FROZEN["applied"],
            "prep1": STAGED_SHA_FROZEN["prep1"],
        },
    }
    sha, mode = _write_canonical_guarded(FRAMING_R17, doc)
    print(f"[r17] framing 落盘：render-framing-r17.json sha256={sha[:16]}… "
          f"({mode})")
    lo_o = round(o4 * (1 - PRED_TOL))
    hi_o = round(o4 * (1 + PRED_TOL))
    lo_g = round(g4 * (1 - PRED_TOL))
    hi_g = round(g4 * (1 + PRED_TOL))
    print("[r17] 预注册预测：橙≈", o4, "（带 [", lo_o, ",", hi_o, "]）、",
          "绿≈", g4, "（带 [", lo_g, ",", hi_g, "]）、板内白=0、top 橙/绿=0",
          sep="")


# ---------------------------------------------------------------------------
# render
# ---------------------------------------------------------------------------

def cmd_render() -> None:
    _protected_check()
    _staging_check()
    _axis_plan_check()
    refs = _r14b_refs()
    import json
    if not FRAMING_R17.exists():
        _fail("render-framing-r17.json 缺失（先落盘 framing）")
    framing_sha_start = _sha(FRAMING_R17)
    framing = json.loads(FRAMING_R17.read_text(encoding="utf-8"))
    ver = _kicad_version()

    if WITNESS_R17.exists():
        for name in FINAL_PNGS:
            if not (R17_DIR / f"{name}.png").exists():
                _fail("render-witness-r17.json 已存在但成图不全（状态不一致）")

    pred = framing["palette_assertions"]["preregistered_prediction"]

    R17_DIR.mkdir(parents=True, exist_ok=True)
    results = {}
    determinism = {}
    for state in BOTTOM_STATES:
        crop_bytes, rec, rerun = _build_bottom(state)

        # 板界断言（=framing measured_1280 逐字）
        exp = framing["compose_and_crop"]["measured_1280"][
            f"bottom_{state}"]["board_bounds_full_1280"]["measured_1280"]
        got = rec["board_bounds_full_1280"]["measured_1280"]
        if got != exp:
            _fail(f"{state} 板界断言失败：{got} != framing 实测 {exp}")
        if rec["image_wh"] != framing["compose_and_crop"]["measured_1280"][
                f"bottom_{state}"]["image_wh"]:
            _fail(f"{state} 裁后尺寸断言失败")

        p = rec["palette"]
        # 预注册断言：4× 带、板内白=0、橙绿零交集
        in_band_o = (pred["orange_band"][0] <= p["orange_exact_count"]
                     <= pred["orange_band"][1])
        in_band_g = (pred["green_band"][0] <= p["green_exact_count"]
                     <= pred["green_band"][1])
        assertions_pass = bool(
            p["orange_exact_count"] > 0 and p["green_exact_count"] > 0
            and p["orange_green_mix_count"] == 0
            and p["white_in_board_after"] == 0
            and in_band_o and in_band_g)
        if not assertions_pass:
            _fail(f"{state} 调色板预注册断言失败：{p} bands={pred}")

        out_path = R17_DIR / f"{state}-bottom.png"
        mode = _guard_write_bytes(out_path, crop_bytes)
        ratio_o = round(p["orange_exact_count"]
                        / pred["orange_pixel_count_expected_4x"], 4)
        ratio_g = round(p["green_exact_count"]
                        / pred["green_pixel_count_expected_4x"], 4)
        results[state] = {
            "output_png_rel": f"out/v3-tl2/calibration/renders-r17/"
                              f"{state}-bottom.png",
            "sha256": _sha(out_path),
            "bytes": out_path.stat().st_size,
            "image_wh": rec["image_wh"],
            "full_page_wh": rec["full_page_wh"],
            "board_bounds_full_1280": got,
            "board_bounds_expected_2x_of_640":
                rec["board_bounds_full_1280"]["expected_2x_of_640"],
            "board_bounds_deltas_px":
                rec["board_bounds_full_1280"]["deltas_px"],
            "crop_box": rec["crop_box"],
            "white_pre_overlay_cropped": rec["white_pre_overlay_cropped"],
            "palette": {
                **p,
                "orange_ratio_vs_4x": ratio_o,
                "green_ratio_vs_4x": ratio_g,
                "assertions_pass": assertions_pass,
                "assertion_note": (
                    "预注册断言：橙>0 且 4× 带内、绿>0 且 4× 带内、橙绿零"
                    "交集、板内白严格=0；剩余白=板外 240px 裁剪边距（仪器"
                    "口径）——以 white_outside_board_after 记录。"),
            },
            "mask_rebuild": rec["_mask_meta"],
        }
        print(f"[r17] render {state}-bottom.png "
              f"{results[state]['bytes']}B {rec['image_wh']} "
              f"板界(全页){got} 橙={p['orange_exact_count']}"
              f"(×4 比={ratio_o}) 绿={p['green_exact_count']}"
              f"(×4 比={ratio_g}) 板内白={p['white_in_board_after']} "
              f"({mode})")
        determinism[state] = rerun

    for state in BOTTOM_STATES:
        crop_bytes, rec, rerun = _build_top(state)
        exp = framing["compose_and_crop"]["measured_1280"][
            f"top_{state}"]["board_bounds_full_1280"]["measured_1280"]
        got = rec["board_bounds_full_1280"]["measured_1280"]
        if got != exp:
            _fail(f"{state}-top 板界断言失败：{got} != framing 实测 {exp}")
        p = rec["palette"]
        if p["orange_exact_count"] or p["green_exact_count"]:
            _fail(f"{state}-top 出现橙/绿（top 无配色被破坏）")
        out_path = R17_DIR / f"{state}-top.png"
        mode = _guard_write_bytes(out_path, crop_bytes)
        results[f"{state}-top"] = {
            "output_png_rel": f"out/v3-tl2/calibration/renders-r17/"
                              f"{state}-top.png",
            "sha256": _sha(out_path),
            "bytes": out_path.stat().st_size,
            "image_wh": rec["image_wh"],
            "full_page_wh": rec["full_page_wh"],
            "board_bounds_full_1280": got,
            "board_bounds_expected_2x_of_640":
                rec["board_bounds_full_1280"]["expected_2x_of_640"],
            "board_bounds_deltas_px":
                rec["board_bounds_full_1280"]["deltas_px"],
            "crop_box": rec["crop_box"],
            "palette": p,
            "coloring": "none（top 无配色，与既往一致）",
        }
        print(f"[r17] render {state}-top.png {results[f'{state}-top']['bytes']}"
              f"B {rec['image_wh']} 板界(全页){got} "
              f"白={p['white_pixel_count_r17']} ({mode})")
        determinism[f"{state}-top"] = rerun

    # 确定性自证：全链重跑逐字节一致（四图各一）
    det = {}
    for key, rerun in determinism.items():
        name = (f"{key}-bottom.png" if key in ("applied", "prep1")
                else f"{key}.png")
        det[key] = rerun() == (R17_DIR / name).read_bytes()
        if not det[key]:
            _fail(f"确定性自证失败：{key} 重跑非逐字节同")
    print(f"[r17] 确定性自证：重跑全链逐字节一致={det}")

    # framing 运行期间零改动复核 + 收工复核
    if _sha(FRAMING_R17) != framing_sha_start:
        _fail("render-framing-r17.json 在 render 期间变动（冻结纪律破坏）")
    protected_end = _protected_check()
    staging_end = _staging_check()
    axis_end = _axis_plan_check()

    pal_b = results["applied"]["palette"]
    doc = {
        "schema_version": "3.0",
        "kind": "tl2_calibration_render_witness_r17",
        "round_label": ROUND_LABEL,
        "round_id_constant": ROUND_ID,
        "date_constant": DATE_CONSTANT,
        "domain_id": DOMAIN_ID,
        "no_visual_reading": True,
        "axis_reference": {
            "path_rel": "out/v3-tl2/calibration/axis-experiment-plan-r17-r20.json",
            "sha256": axis_end["sha256"],
        },
        "instrument": (
            f"renders-r4 冻结 combined PDF（sha 复核）+ PyMuPDF "
            f"get_pixmap(dpi=1280, alpha=False) 40pt 组合页光栅化 + fitz "
            f"Shape 白图元矢量重建（dpi1280）+ PIL crop/save；bottom 配色="
            f"r14b 规则逐字重放（mask 1280 重算）；top 无配色；官方成图零 "
            f"kicad 调用（预注册=render-framing-r17.json）"),
        "kicad_cli_version": ver,
        "framing": {
            "path_rel": "out/v3-tl2/calibration/render-framing-r17.json",
            "sha256": framing_sha_start,
            "unchanged_during_render": True,
        },
        "protected_files": {
            "at_start": _protected_check(),
            "at_end": protected_end,
        },
        "staging_and_live_boards": {
            "at_start": _staging_check(),
            "at_end": staging_end,
            "zero_write_declaration": (
                "staging-r4 与活板全程只读；渲染源=staging-r4 冻结字节的 "
                "r4 冻结 PDF（同源性探针逐字节核验）。"),
        },
        "r14b_references": refs,
        "renders": results,
        "determinism_rerun_byte_identical": det,
        "determinism_scope": framing["synthesis_method"]["determinism_scope"],
        "palette_assertion_summary": {
            k: v["palette"] for k, v in results.items()},
        "conclusion": (
            "轴1 单变量仪器轮执行完成：四图 dpi 640→1280（线度×2、像素数"
            f"×4），其余口径与 r14b 逐字同。成图实测：bottom 橙="
            f"{pal_b['orange_exact_count']}（4× 预期 "
            f"{pred['orange_pixel_count_expected_4x']}，比 "
            f"{pal_b['orange_ratio_vs_4x']}）、绿={pal_b['green_exact_count']}"
            f"（4× 预期 {pred['green_pixel_count_expected_4x']}，比 "
            f"{pal_b['green_ratio_vs_4x']}）、板内白严格清零="
            f"{pal_b['white_in_board_after'] == 0}（剩余白=板外 240px 裁剪"
            "边距带）；top 无配色（橙/绿=0）。两板 bottom 成图逐字节同"
            "（r5/r14b 一致性延续）。板界=640 实测×2 在 ±2px 内（逐图 "
            "deltas 入 renders）。确定性自证四图全链重跑逐字节一致。产物供 "
            "R17 盲读。"),
        "degradation": None,
    }
    sha, mode = _write_canonical_guarded(WITNESS_R17, doc)
    print(f"[r17] witness 落盘：render-witness-r17.json sha256={sha[:16]}… "
          f"({mode})")


# ---------------------------------------------------------------------------
# diag（诊断对照裁片；非盲读件）
# ---------------------------------------------------------------------------

def _pair_png(left: "np.ndarray", right: "np.ndarray") -> bytes:
    """并排拼图：左=640 腿（已 2× 最近邻放大）、右=1280 腿（1:1），中缝
    4px 黑色分隔。确定性纯函数。"""
    from PIL import Image
    h = max(left.shape[0], right.shape[0])
    sep = 4
    W = left.shape[1] + sep + right.shape[1]
    canvas = np.zeros((h, W, 3), dtype=np.uint8)
    canvas[:left.shape[0], :left.shape[1]] = left
    canvas[:right.shape[0], left.shape[1] + sep:] = right
    im = Image.fromarray(canvas, "RGB")
    bio = io.BytesIO()
    im.save(bio, "PNG")
    return bio.getvalue()


def _nearest2x(arr: "np.ndarray") -> "np.ndarray":
    """2× 最近邻放大（确定性；等价于 np.repeat 轴 0/1 各 ×2）。"""
    return np.repeat(np.repeat(arr, 2, axis=0), 2, axis=1)


def cmd_diag() -> None:
    _protected_check()
    _staging_check()
    import json
    import scipy.ndimage  # 连通域（确定性）

    if not FRAMING_R17.exists() or not WITNESS_R17.exists():
        _fail("framing/witness 缺失（diag 在成图与 witness 之后运行）")
    for name in FINAL_PNGS:
        if not (R17_DIR / f"{name}.png").exists():
            _fail(f"renders-r17/{name}.png 缺失（先跑 render）")
    framing = json.loads(FRAMING_R17.read_text(encoding="utf-8"))
    wit14b = json.loads(
        (CAL_DIR / "render-witness-r14b.json").read_text(encoding="utf-8"))

    # 裁剪原点与映射（region 在 640 裁剪系整数定义；1280 = ×2 + 原点差）
    crop640_bottom = wit14b["renders"]["applied"]["crop_box"]
    import json as _json
    framing5 = _json.loads(
        (CAL_DIR / "render-framing-r5.json").read_text(encoding="utf-8"))
    tb640 = framing5["expected_geometry"]["board_px_bounds_full_top"]
    crop640_top = (tb640[0] - CROP_MARGIN_PX_PREV,
                   tb640[1] - CROP_MARGIN_PX_PREV,
                   tb640[2] + 1 + CROP_MARGIN_PX_PREV,
                   tb640[3] + 1 + CROP_MARGIN_PX_PREV)
    crop1280_bottom = framing["compose_and_crop"]["measured_1280"][
        "bottom_applied"]["crop_box"]
    crop1280_top = framing["compose_and_crop"]["measured_1280"][
        "top_applied"]["crop_box"]
    dx_bottom = crop1280_bottom[0] - SCALE * crop640_bottom[0]
    dy_bottom = crop1280_bottom[1] - SCALE * crop640_bottom[1]
    dx_top = crop1280_top[0] - SCALE * crop640_top[0]
    dy_top = crop1280_top[1] - SCALE * crop640_top[1]

    DIAG_DIR.mkdir(parents=True, exist_ok=True)

    # ---- bottom：基准黑点-焊盘邻接区（r14b 证书点 (282,224)c 邻域）----
    half = 80  # 640 腿半宽 → 160×160 区域
    cx, cy = 282, 224
    b640 = (cx - half, cy - half, cx + half, cy + half)
    img640 = _load_rgb((R14B_DIR / "applied-bottom.png").read_bytes())
    H6, W6 = img640.shape[:2]
    b640 = (max(0, b640[0]), max(0, b640[1]),
            min(W6, b640[2]), min(H6, b640[3]))
    leg640 = _nearest2x(img640[b640[1]:b640[3], b640[0]:b640[2]])
    b1280 = (SCALE * b640[0] + dx_bottom, SCALE * b640[1] + dy_bottom,
             SCALE * b640[2] + dx_bottom, SCALE * b640[3] + dy_bottom)
    img1280 = _load_rgb((R17_DIR / "applied-bottom.png").read_bytes())
    H1, W1 = img1280.shape[:2]
    if not (0 <= b1280[0] < b1280[2] <= W1 and 0 <= b1280[1] < b1280[3] <= H1):
        _fail(f"bottom 诊断区域越界：{b1280} vs {W1}x{H1}")
    leg1280 = np.ascontiguousarray(
        img1280[b1280[1]:b1280[3], b1280[0]:b1280[2]])
    if leg1280.shape != leg640.shape:
        _fail(f"bottom 两腿显示尺寸不一致：{leg1280.shape} vs {leg640.shape}")
    # 非退化断言：区域含基准黑点（640 腿 (0,0,0)>0）与 r17 腿橙/绿>0
    black640 = int(np.all(img640[b640[1]:b640[3], b640[0]:b640[2]]
                          == 0, axis=2).sum())
    orange_m = int(np.all(leg1280 == np.array(TARGET_ORANGE,
                                              dtype=np.uint8), axis=2).sum())
    green_m = int(np.all(leg1280 == np.array(TARGET_GREEN,
                                             dtype=np.uint8), axis=2).sum())
    if black640 <= 0 or orange_m <= 0 or green_m <= 0:
        _fail(f"bottom 诊断区域退化：黑={black640} 橙={orange_m} "
              f"绿={green_m}")
    png_b = _pair_png(leg640, leg1280)
    mode_b = _guard_write_bytes(DIAG_DIR / "compare-bottom-fiducial.png",
                                png_b)
    print(f"[r17] diag bottom 对照：640 区域 {b640}（×2 最近邻）vs 1280 "
          f"区域 {b1280}；黑={black640} 橙={orange_m} 绿={green_m} "
          f"({mode_b})")

    # ---- top：板中部相邻 courtyard 对（程序化选区）----
    top1280 = _load_rgb((R17_DIR / "applied-top.png").read_bytes())
    mag = np.all(top1280 == np.array(COURTYARD_MAGENTA, dtype=np.uint8),
                 axis=2)
    lab, n = scipy.ndimage.label(mag)
    boxes = scipy.ndimage.find_objects(lab)
    comps = []
    for i, sl in enumerate(boxes):
        if sl is None:
            continue
        y0, y1 = sl[0].start, sl[0].stop - 1
        x0, x1 = sl[1].start, sl[1].stop - 1
        comps.append((x0, y0, x1, y1))
    # 最小尺寸过滤（≥16px @1280）：排除细描边精确色抗混叠残段（碎片），
    # 使配对对象为可辨识的 courtyard 矩形轮廓
    comps = [c for c in comps if c[2] - c[0] + 1 >= 16 and c[3] - c[1] + 1 >= 16]
    H, W = top1280.shape[:2]
    ccx, ccy = W / 2.0, H / 2.0
    best = None
    for i in range(len(comps)):
        for j in range(i + 1, len(comps)):
            a, b = comps[i], comps[j]
            # 相邻判定：一维投影间隙 ≤8px(1280) 且另一维投影重叠
            gap_x = max(a[0] - b[2], b[0] - a[2], 0)
            gap_y = max(a[1] - b[3], b[1] - a[3], 0)
            overlap_x = not (a[2] < b[0] or b[2] < a[0])
            overlap_y = not (a[3] < b[1] or b[3] < a[1])
            adjacent = ((gap_x <= 8 and overlap_y)
                        or (gap_y <= 8 and overlap_x))
            if not adjacent:
                continue
            ux0, uy0 = min(a[0], b[0]), min(a[1], b[1])
            ux1, uy1 = max(a[2], b[2]), max(a[3], b[3])
            mx, my = (ux0 + ux1) / 2.0, (uy0 + uy1) / 2.0
            d2 = (mx - ccx) ** 2 + (my - ccy) ** 2
            key = (d2, ux0, uy0, ux1, uy1)
            if best is None or key < best[0]:
                best = (key, (ux0, uy0, ux1, uy1), (a, b))
    if best is None:
        _fail("top 诊断选区失败：未找到相邻 courtyard 对")
    (ux0, uy0, ux1, uy1), pair = best[1], best[2]
    pad = 40
    # 区域在 1280 裁剪系先定，再折算到 640 裁剪系整数框（2 对齐）
    r1280 = (max(0, ux0 - pad), max(0, uy0 - pad),
             min(W - 1, ux1 + pad), min(H - 1, uy1 + pad))
    t640 = _load_rgb((R14B_DIR / "applied-top.png").read_bytes())
    H6t, W6t = t640.shape[:2]

    def to640_lo(v, d):
        # x1280 = 2*x640 + d ⇒ x640 下界 = ceil((x1280 - d)/2)
        return -(-(v - d) // 2)

    x6_lo = to640_lo(r1280[0], dx_top)
    y6_lo = to640_lo(r1280[1], dy_top)
    x6_hi = (r1280[2] - dx_top) // 2
    y6_hi = (r1280[3] - dy_top) // 2
    x6_lo, y6_lo = max(0, x6_lo), max(0, y6_lo)
    x6_hi, y6_hi = min(W6t - 1, x6_hi), min(H6t - 1, y6_hi)
    # 重推 1280 框（像素精确对应：640 像素 x ↔ 1280 像素 {2x+d, 2x+d+1}，
    # 故闭区间上界 = 2*hi + d + 1）
    r1280b = (2 * x6_lo + dx_top, 2 * y6_lo + dy_top,
              2 * x6_hi + dx_top + 1, 2 * y6_hi + dy_top + 1)
    leg640_t = _nearest2x(
        t640[y6_lo:y6_hi + 1, x6_lo:x6_hi + 1])
    leg1280_t = np.ascontiguousarray(
        top1280[r1280b[1]:r1280b[3] + 1, r1280b[0]:r1280b[2] + 1])
    if leg1280_t.shape != leg640_t.shape:
        _fail(f"top 两腿显示尺寸不一致：{leg1280_t.shape} vs "
              f"{leg640_t.shape}")
    mag1280_in = int(np.all(leg1280_t == np.array(COURTYARD_MAGENTA,
                                                  dtype=np.uint8),
                            axis=2).sum())
    mag640_in = int(np.all(t640[y6_lo:y6_hi + 1, x6_lo:x6_hi + 1]
                           == np.array(COURTYARD_MAGENTA, dtype=np.uint8),
                           axis=2).sum())
    if mag1280_in <= 0 or mag640_in <= 0:
        _fail(f"top 诊断区域退化：洋红 640={mag640_in} 1280={mag1280_in}")
    png_t = _pair_png(leg640_t, leg1280_t)
    mode_t = _guard_write_bytes(DIAG_DIR / "compare-top-courtyard-pair.png",
                                png_t)
    print(f"[r17] diag top 对照：640 区域 ({x6_lo},{y6_lo})-({x6_hi},{y6_hi})"
          f"（×2 最近邻）vs 1280 区域 {r1280b}；courtyard 对 bbox={pair}；"
          f"洋红 640={mag640_in} 1280={mag1280_in} ({mode_t})")

    manifest = {
        "schema_version": "3.0",
        "kind": "tl2_calibration_render_diag_r17_manifest",
        "round_label": ROUND_LABEL,
        "round_id_constant": ROUND_ID,
        "date_constant": DATE_CONSTANT,
        "domain_id": DOMAIN_ID,
        "purpose": (
            "诊断对照裁片：供主审人工分辨力核验（非盲读件、非判读输入）；"
            "r14b（640 dpi）与 r17（1280 dpi）同一板面区域并排对照，640 腿"
            "2× 最近邻放大至与 1280 腿相同显示尺寸。"),
        "layout": {
            "left": "r14b 640 dpi 裁片，2× 最近邻（NEAREST/np.repeat）放大",
            "right": "r17 1280 dpi 裁片 1:1",
            "separator_px": 4,
            "separator_color": [0, 0, 0],
            "display_size_per_leg": list(leg640.shape[:2][::-1]),
        },
        "mapping": {
            "formula": "x1280_cropped = 2 × x640_cropped + d，d = 裁剪原点"
                       "差 = crop_origin(1280) − 2 × crop_origin(640)",
            "bottom_d": [dx_bottom, dy_bottom],
            "top_d": [dx_top, dy_top],
            "bottom_crop_origin_640": crop640_bottom[:2],
            "bottom_crop_origin_1280": crop1280_bottom[:2],
            "top_crop_origin_640": list(crop640_top[:2]),
            "top_crop_origin_1280": crop1280_top[:2],
        },
        "regions": {
            "bottom": {
                "file": "compare-bottom-fiducial.png",
                "anchor": "基准黑点-焊盘邻接区（diag-r13-review D1/D2 左上"
                          "小足迹区；r14b 证书点 (282,224)c 为黑点中心）",
                "box_640_cropped": list(b640),
                "box_1280_cropped": list(b1280),
                "box_640_full_page": [b640[0] + crop640_bottom[0],
                                      b640[1] + crop640_bottom[1],
                                      b640[2] + crop640_bottom[0],
                                      b640[3] + crop640_bottom[1]],
                "box_1280_full_page": [b1280[0] + crop1280_bottom[0],
                                       b1280[1] + crop1280_bottom[1],
                                       b1280[2] + crop1280_bottom[0],
                                       b1280[3] + crop1280_bottom[1]],
                "pixel_scales": {"r14b_leg": "640 dpi ×2",
                                 "r17_leg": "1280 dpi 1:1"},
                "nondegeneracy_counts": {
                    "black_640_leg": black640,
                    "orange_1280_leg": orange_m,
                    "green_1280_leg": green_m,
                },
            },
            "top": {
                "file": "compare-top-courtyard-pair.png",
                "selection_rule": (
                    "applied-top 洋红 (255,38,226) 精确色连通域（scipy."
                    "ndimage.label）bbox（两维 ≥16px 过滤抗混叠碎片）；"
                    "边缘间隙 ≤8px(1280) 且另一维投影重叠的相邻对中，取对"
                    "中点离图幅中心最近者（平局取 (min_x,min_y) 字典序）；"
                    "区域=对并集 bbox 外扩 40px，在 640 裁剪系取 2 对齐"
                    "整数框（1280 腿上界=2×上+映射差+1，闭区间）"),
                "courtyard_pair_bboxes_1280_cropped": [list(pair[0]),
                                                       list(pair[1])],
                "box_640_cropped": [x6_lo, y6_lo, x6_hi, y6_hi],
                "box_1280_cropped": list(r1280b),
                "box_640_full_page": [x6_lo + crop640_top[0],
                                      y6_lo + crop640_top[1],
                                      x6_hi + crop640_top[0],
                                      y6_hi + crop640_top[1]],
                "box_1280_full_page": [r1280b[0] + crop1280_top[0],
                                       r1280b[1] + crop1280_top[1],
                                       r1280b[2] + crop1280_top[0],
                                       r1280b[3] + crop1280_top[1]],
                "pixel_scales": {"r14b_leg": "640 dpi ×2",
                                 "r17_leg": "1280 dpi 1:1"},
                "nondegeneracy_counts": {
                    "magenta_640_leg": mag640_in,
                    "magenta_1280_leg": mag1280_in,
                },
            },
        },
        "sources": {
            "r14b_png_sha256": {
                "applied-bottom": _sha(R14B_DIR / "applied-bottom.png"),
                "applied-top": _sha(R14B_DIR / "applied-top.png"),
            },
            "r17_png_sha256": {
                "applied-bottom": _sha(R17_DIR / "applied-bottom.png"),
                "applied-top": _sha(R17_DIR / "applied-top.png"),
            },
            "witness_r17_sha256": _sha(WITNESS_R17),
        },
        "outputs": {
            "compare-bottom-fiducial.png": {
                "sha256": hashing.sha256_bytes(png_b)},
            "compare-top-courtyard-pair.png": {
                "sha256": hashing.sha256_bytes(png_t)},
        },
        "no_visual_reading": (
            "选区与拼图全程程序化（连通域/固定锚点/确定性重采样）；零视觉"
            "判读参与产物生成。"),
    }
    sha_m, mode_m = _write_canonical_guarded(DIAG_DIR / "manifest.json",
                                             manifest)
    print(f"[r17] diag manifest 落盘：diag-r17-render/manifest.json "
          f"sha256={sha_m[:16]}… ({mode_m})")


def main() -> None:
    step = sys.argv[1] if len(sys.argv) > 1 else ""
    if step == "probe":
        cmd_probe()
    elif step == "framing":
        cmd_framing()
    elif step == "render":
        cmd_render()
    elif step == "diag":
        cmd_diag()
    else:
        _fail("用法：s62_render_r17.py probe|framing|render|diag")


if __name__ == "__main__":
    main()
