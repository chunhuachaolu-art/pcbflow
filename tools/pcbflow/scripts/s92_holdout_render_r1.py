#!/usr/bin/env python
"""PCBFlow v3.0 holdout-r1 正式运行：渲染实施者（3 板 × 2 视 = 6 张 PNG）。

freeze 顺序：framing → render → witness（本脚本三步模式，s51 工具惯例）。
仪器=render-framing-r5.json 框架管线逐字同口径（kicad-cli 2D PDF 单页导出
→ PyMuPDF 40pt 白边组合页 dpi640 光栅化 → png_board_pixel_bounds 板界实测
→ +120px 裁剪），配色=kicad 默认（零 overlay 零重着色；r14b 白形重配为
revc 探针特化、不泛化——局限在 framing 如实预注册）。

三步：
  framing  落盘 out/v3-tl2/holdout/render-framing-holdout-r1.json（canonical
           JSON，先于任何官方 PNG；落盘前断言 renders-holdout-r1/ 不存在或
           无 *.png）：prep-record 引用（sha 前缀 b2eaad8365e33925 复核）、
           单变量声明（仪器=r5 框架原配色管线、零 overlay）、6 张目标图清单
           （板×视+输入 sha+层集）、管线参数（dpi640/40pt/120px/页数断言）、
           默认配色局限预注册（bottom 白墨/空隙歧义=弃权率潜在上推因素）、
           断言清单、freeze_order、防覆写声明、no_visual_reading。
  render   按 framing 执行 6 张：kicad-cli PDF 导出（防覆写；失败同参数重试
           至多 1 次，再败如实记录并停）→ 合成光栅裁剪（s51 _compose_raster
           逐字同口径）→ 程序化断言（PNG magic/尺寸公式/四侧恰 120px 全白）
           → 防覆写落盘 PNG → 每张确定性自证（PDF→合成→光栅→裁剪全链重跑
           逐字节等同；kicad PDF 字节不做跨运行断言）→ 中间记录落
           renders-holdout-r1/render-log-holdout-r1.json（witness 输入）。
  witness  独立复核并落盘 render-witness-holdout-r1.json：kicad-cli 版本实
           测、framing 引用+渲染期间零变动断言、受保护文件 at_start/at_end、
           板输入 sha 复核、6 张 PNG 全记录逐盘对账、确定性独立重跑、
           zero_write_declaration、degradation（无则 null）、conclusion。

纪律：日期/轮次=声明常量（2026-09-10）；canonical JSON=
pcbflow.hashing.canonical_json_bytes；防覆写 guard（已存在非字节等同→FAIL，
等同→幂等）；除 kicad-cli 外零 subprocess/网络/wall-clock；kicad-cli 调用
照 s51 模式（绝对路径执行、cwd=REPO、subprocess timeout 1200s）；受保护
文件（pcbflow/cli.py=6ed4f3fd、pcbflow/config.py=f515c348、
toolchain_lock.json=d43dad89）开工/收工各验前缀；prep-record 前缀
b2eaad8365e33925 在三步各复核一次；datasets/ 严格只读；out/ 既有文件零
改动；零视觉判读（全部程序化像素统计，不查看任何 PNG）。

新建范围=scripts/s92_holdout_render_r1.py、out/v3-tl2/holdout/
renders-holdout-r1/（含 pdfs/ 子目录）、render-framing-holdout-r1.json、
render-witness-holdout-r1.json。

用法：python scripts/s92_holdout_render_r1.py framing|render|witness
"""

from __future__ import annotations

import io
import re
import struct
import subprocess
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from pcbflow import calibration, hashing  # noqa: E402

# ---------------------------------------------------------------------------
# 路径（新建范围红线：只写以下路径）
# ---------------------------------------------------------------------------
HOLDOUT_DIR = REPO / "out" / "v3-tl2" / "holdout"
RENDERS_DIR = HOLDOUT_DIR / "renders-holdout-r1"
PDFS_DIR = RENDERS_DIR / "pdfs"
FRAMING_PATH = HOLDOUT_DIR / "render-framing-holdout-r1.json"
WITNESS_PATH = HOLDOUT_DIR / "render-witness-holdout-r1.json"
RENDER_LOG_PATH = RENDERS_DIR / "render-log-holdout-r1.json"
PREP_RECORD_PATH = HOLDOUT_DIR / "holdout-prep-record-r1.json"

FRAMING_REL = "out/v3-tl2/holdout/render-framing-holdout-r1.json"
WITNESS_REL = "out/v3-tl2/holdout/render-witness-holdout-r1.json"
RENDER_LOG_REL = ("out/v3-tl2/holdout/renders-holdout-r1/"
                  "render-log-holdout-r1.json")
PREP_REL = "out/v3-tl2/holdout/holdout-prep-record-r1.json"
RENDERS_DIR_REL = "out/v3-tl2/holdout/renders-holdout-r1"

# ---------------------------------------------------------------------------
# 声明常量（零 wall-clock）
# ---------------------------------------------------------------------------
DATE_CONSTANT = "2026-09-10"
HOLDOUT_ID = "holdout-r1"
ROUND_ID_CONSTANT = "2026-09-10-holdout-r1"
PREP_RECORD_SHA_PREFIX = "b2eaad8365e33925"

# ---------------------------------------------------------------------------
# 仪器参数（render-framing-r5.json 框架逐字同口径）
# ---------------------------------------------------------------------------
KICAD_CLI = Path(r"F:\kicad\bin\kicad-cli.exe")
KICAD_VERSION_EXPECTED = "10.0.5"
KICAD_TIMEOUT_S = 1200          # 大板（12 层）导出慢，任务口径 1200 秒
RASTER_DPI = 640
COMPOSE_MARGIN_PT = 40.0
CROP_MARGIN_PX = 120
LAYERS_TOP = "F.Cu,F.Mask,F.Silkscreen,Edge.Cuts,F.Courtyard"
LAYERS_BOTTOM = "B.Cu,B.Mask,B.Silkscreen,Edge.Cuts,B.Courtyard"
VIEWS = ("top", "bottom")

PROTECTED = {
    "pcbflow/cli.py": "6ed4f3fd",
    "pcbflow/config.py": "f515c348",
    "toolchain_lock.json": "d43dad89",
}

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"

# ---------------------------------------------------------------------------
# 冻结选板表（与 prep-record.board_selection.boards 逐字交叉复核；
# input_sha256 全 64 位逐字复核；活读 datasets/ 只读哈希）
# ---------------------------------------------------------------------------
FROZEN_BOARDS = [
    {
        "board_id": "kitspace_led_driver",
        "board_segment": "kitspace_led_driver",
        "input_path_rel":
            "datasets/pcbench-r1/raw/kitspace_led_driver/processed.kicad_pcb",
        "input_sha256":
            "ccc2efb5c4c0d7d1a764330f32a23851719639adfc6f0d9456678857eac02f4f",
    },
    {
        "board_id": "tiny_tapeout/tinytapeout-demo",
        "board_segment": "tiny_tapeout",
        "input_path_rel":
            "datasets/kicad-demos-r1/raw/tiny_tapeout/tinytapeout-demo.kicad_pcb",
        "input_sha256":
            "0d26bf9b6d561e32cf610d428541d6433e60b45e1838f34f73467e25b9144814",
    },
    {
        "board_id": "vme-wren/vme-wren",
        "board_segment": "vme-wren",
        "input_path_rel":
            "datasets/kicad-demos-r1/raw/vme-wren/vme-wren.kicad_pcb",
        "input_sha256":
            "1c76ac238b04babc238d2d50585858988fb3f6c4f8d0fbacc738cfe4862fff5b",
    },
]


def _fail(msg: str) -> None:
    print(f"[holdout-r1] FAIL: {msg}")
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


# ---------------------------------------------------------------------------
# 红线复核（protected / prep-record / 板输入）
# ---------------------------------------------------------------------------

def _protected_check() -> dict:
    results = {}
    for rel, prefix in PROTECTED.items():
        sha = _sha(REPO / rel)
        if not sha.startswith(prefix):
            _fail(f"受保护文件哈希不符：{rel} {sha[:8]} != {prefix}")
        results[rel] = {"sha256": sha, "expected_prefix": prefix, "match": True}
    return results


def _prep_check() -> str:
    """prep-record 前缀复核（framing/render/witness 三步各一次）。"""
    sha = _sha(PREP_RECORD_PATH)
    if not sha.startswith(PREP_RECORD_SHA_PREFIX):
        _fail(f"prep-record sha 不符：{sha[:16]} != "
              f"{PREP_RECORD_SHA_PREFIX}")
    return sha


def _load_prep_record() -> dict:
    import json
    return json.loads(PREP_RECORD_PATH.read_text(encoding="utf-8"))


def _boards_verified(prep: dict) -> list:
    """冻结选板表 ↔ prep-record 逐字交叉复核 + datasets/ 活读哈希复核。

    返回带 view 展开的 6 张目标图清单。任何不符即 FAIL。
    """
    prep_boards = {b["board_id"]: b
                   for b in prep["board_selection"]["boards"]}
    targets = []
    for fb in FROZEN_BOARDS:
        pb = prep_boards.get(fb["board_id"])
        if pb is None:
            _fail(f"prep-record 缺板：{fb['board_id']}")
        if pb["input_path_rel"] != fb["input_path_rel"]:
            _fail(f"{fb['board_id']} input_path_rel 与 prep-record 不符")
        want = pb["input_sha256"]
        if not re.fullmatch(r"[0-9a-f]{64}", want):
            _fail(f"{fb['board_id']} prep-record input_sha256 非 64 位 hex："
                  f"{want!r}")
        if want != fb["input_sha256"]:
            _fail(f"{fb['board_id']} input_sha256 与冻结表不符")
        live = _sha(REPO / fb["input_path_rel"])
        if live != want:
            _fail(f"{fb['board_id']} datasets 输入活读 sha 不符：{live}")
        for view in VIEWS:
            name = f"{fb['board_segment']}-{view}"
            targets.append({
                "name": name,
                "board_id": fb["board_id"],
                "board_segment": fb["board_segment"],
                "view": view,
                "input_path_rel": fb["input_path_rel"],
                "input_sha256": want,
                "layers": (LAYERS_TOP if view == "top" else LAYERS_BOTTOM),
                "mirror": view == "bottom",
                "pdf_output_rel":
                    f"{RENDERS_DIR_REL}/pdfs/{name}.pdf",
                "png_output_rel": f"{RENDERS_DIR_REL}/{name}.png",
            })
    return targets


# ---------------------------------------------------------------------------
# kicad-cli（s51 模式：绝对路径执行、cwd=REPO、版本验证、timeout 1200s）
# ---------------------------------------------------------------------------

def _kicad_version() -> str:
    if not KICAD_CLI.exists():
        _fail(f"kicad-cli 不存在：{KICAD_CLI}")
    proc = subprocess.run([str(KICAD_CLI), "version"], capture_output=True,
                          text=True)
    ver = (proc.stdout or proc.stderr).strip()
    if proc.returncode != 0 or KICAD_VERSION_EXPECTED not in ver:
        _fail(f"kicad-cli 版本验证失败：{ver!r}"
              f"（预期含 {KICAD_VERSION_EXPECTED}）")
    return ver


def _export_cmd(out_rel: str, in_rel: str, layers: str, mirror: bool) -> list:
    cmd = ["kicad-cli", "pcb", "export", "pdf", "--mode-single",
           "--scale", "1", "--check-zones", "--drill-shape-opt", "2",
           "--layers", layers]
    if mirror:
        cmd.append("--mirror")
    cmd += ["-o", out_rel, in_rel]
    return cmd


def _run_kicad_attempt(cmd: list, out_rel: str) -> dict:
    """单次导出尝试（防覆写 guard 先行；同参数重试至多 1 次由调用方控制）。"""
    if (REPO / out_rel).exists():
        return {"returncode": -1,
                "stderr_tail": "输出已存在（防覆写 guard，未执行）",
                "guard_blocked": True}
    try:
        proc = subprocess.run([str(KICAD_CLI)] + cmd[1:], cwd=str(REPO),
                              capture_output=True, text=True,
                              timeout=KICAD_TIMEOUT_S)
    except subprocess.TimeoutExpired:
        return {"returncode": -3,
                "stderr_tail": f"timeout>{KICAD_TIMEOUT_S}s",
                "guard_blocked": False}
    tail = ((proc.stderr or "") + (proc.stdout or ""))[-500:]
    if proc.returncode != 0:
        return {"returncode": proc.returncode, "stderr_tail": tail,
                "guard_blocked": False}
    if not (REPO / out_rel).exists():
        return {"returncode": -2,
                "stderr_tail": "kicad rc=0 但输出缺失",
                "guard_blocked": False}
    return {"returncode": 0, "stderr_tail": tail, "guard_blocked": False}


# ---------------------------------------------------------------------------
# 合成 + 光栅 + 裁剪（s51 _compose_raster / r5 框架逐字同口径）
# ---------------------------------------------------------------------------

def _compose_raster(pdf_path: Path) -> tuple:
    """fitz 组合页光栅化：断言页数=1 → 40pt 白边组合页 → dpi640 alpha=False。"""
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
            pix = page.get_pixmap(dpi=RASTER_DPI, alpha=False)
            return pix.tobytes("png"), pix.width, pix.height
        finally:
            out.close()
    finally:
        src.close()


def _bounds_of(full_png_bytes: bytes) -> dict:
    return calibration.png_board_pixel_bounds(full_png_bytes)


def _crop_full(full_png_bytes: bytes, bounds: dict) -> tuple:
    """r5 裁剪公式：box=(x0-120, y0-120, x1+1+120, y1+1+120)。"""
    from PIL import Image
    x0, y0 = bounds["x0"], bounds["y0"]
    x1, y1 = bounds["x1"], bounds["y1"]
    box = (x0 - CROP_MARGIN_PX, y0 - CROP_MARGIN_PX,
           x1 + 1 + CROP_MARGIN_PX, y1 + 1 + CROP_MARGIN_PX)
    im = Image.open(io.BytesIO(full_png_bytes))
    cropped = im.crop(box)
    bio = io.BytesIO()
    cropped.save(bio, "PNG")
    return bio.getvalue(), list(box)


def _assert_cropped(png_bytes: bytes, bounds: dict, name: str) -> dict:
    """成图程序化断言：PNG magic、尺寸公式、四侧恰 120px 全白边。"""
    w, h = _png_size(png_bytes)
    exp_w = bounds["x1"] - bounds["x0"] + 241  # (x1+1+120)-(x0-120)
    exp_h = bounds["y1"] - bounds["y0"] + 241
    if (w, h) != (exp_w, exp_h):
        _fail(f"{name}: 尺寸断言失败 {(w, h)} != {(exp_w, exp_h)}"
              "（=(bounds宽+241, bounds高+241)，bounds 含端）")
    arr = _load_rgb(png_bytes)
    bands = {
        "left": arr[:, :CROP_MARGIN_PX, :],
        "right": arr[:, arr.shape[1] - CROP_MARGIN_PX:, :],
        "top": arr[:CROP_MARGIN_PX, :, :],
        "bottom": arr[arr.shape[0] - CROP_MARGIN_PX:, :, :],
    }
    nonwhite = {k: int((~np.all(v == 255, axis=2)).sum())
                for k, v in bands.items()}
    if any(nonwhite.values()):
        _fail(f"{name}: 裁剪后边缘带存在非白像素（四侧应恰 120px 全白）："
              f"{nonwhite}")
    return {"width": w, "height": h, "edge_band_nonwhite": nonwhite,
            "edge_band_px": CROP_MARGIN_PX}


def _load_rgb(png_bytes: bytes) -> "np.ndarray":
    from PIL import Image
    im = Image.open(io.BytesIO(png_bytes))
    return np.array(im.convert("RGB"))


def _render_chain(pdf_path: Path) -> tuple:
    """「PDF→合成→光栅→板界实测→裁剪」全链（确定性纯函数链）。"""
    full_png, pw, ph = _compose_raster(pdf_path)
    bounds = _bounds_of(full_png)
    cropped, box = _crop_full(full_png, bounds)
    return cropped, bounds, box, (pw, ph)


# ---------------------------------------------------------------------------
# framing
# ---------------------------------------------------------------------------

def cmd_framing() -> None:
    _protected_check()
    _prep_check()

    # freeze 顺序：本文件落盘时 renders-holdout-r1/ 尚无任何 PNG
    if RENDERS_DIR.exists() and any(RENDERS_DIR.glob("*.png")):
        _fail("renders-holdout-r1/ 已有 PNG（freeze 顺序破坏：framing 须"
              "先于任何官方 PNG 落盘）")
    if WITNESS_PATH.exists():
        _fail("render-witness-holdout-r1.json 已存在（状态不一致：witness"
              "不得先于 framing）")

    prep_sha = _sha(PREP_RECORD_PATH)
    prep = _load_prep_record()
    targets = _boards_verified(prep)

    doc = {
        "schema_version": "3.0",
        "kind": "tl2_holdout_r1_render_framing",
        "holdout_id": HOLDOUT_ID,
        "round_id_constant": ROUND_ID_CONSTANT,
        "date_constant": DATE_CONSTANT,
        "evaluation_split": {
            "declared": "development",
            "basis": (
                "holdout-prep-record-r1.json evaluation_domain.declared="
                "development（in_calibrated_range=False 直到正式采纳；本轮"
                "产物=独立泛化证据，不构成采纳/晋升）"),
        },
        "no_visual_reading": True,
        "prep_record": {
            "path_rel": PREP_REL,
            "sha256": prep_sha,
            "expected_prefix": PREP_RECORD_SHA_PREFIX,
            "prefix_match": True,
            "declared_date": prep["declared_date"],
            "render_plan_output_dir": prep["render_plan"]["output_dir"],
            "render_plan_pngs": prep["render_plan"]["pngs"],
        },
        "single_variable_declaration": (
            "本轮仪器=r5 框架原配色管线（render-framing-r5.json 口径逐字同："
            "kicad-cli pcb export pdf --mode-single --scale 1 --check-zones "
            "--drill-shape-opt 2 → PyMuPDF 40pt 白边组合页 dpi640 "
            "alpha=False 光栅化 → pcbflow.calibration.png_board_pixel_bounds "
            "板界实测 → +120px 裁剪），零 overlay 零重着色，全部 6 图=kicad "
            "默认配色。r14b 的白形重配（橙/绿 overlay）为 revc 探针特化、"
            "不泛化到本轮；相对 r5 校准仪器本轮零仪器变量变更。"),
        "target_images": targets,
        "pipeline_parameters": {
            "kicad_cli_version_expected": KICAD_VERSION_EXPECTED,
            "export_flags": ("pcb export pdf --mode-single --scale 1 "
                             "--check-zones --drill-shape-opt 2 --layers "
                             "<层集> [--mirror] -o <pdf> <输入板>"),
            "layers_top": LAYERS_TOP,
            "layers_bottom": LAYERS_BOTTOM,
            "mirror": {"top": False, "bottom": True},
            "rasterization": {
                "tool": "PyMuPDF (fitz) get_pixmap(dpi=640, alpha=False)",
                "dpi": RASTER_DPI,
                "compose_margin_pt": COMPOSE_MARGIN_PT,
                "compose_page_formula": (
                    "new_page(width=W+80, height=H+80) + show_pdf_page"
                    "(Rect(40,40,W+40,H+40))；断言源 PDF 页数=1"),
            },
            "crop": {
                "bounds_function":
                    "pcbflow.calibration.png_board_pixel_bounds（dpi640 "
                    "全页组合页实测；r5 框架同款函数）",
                "crop_box_formula": (
                    "(x0-120, y0-120, x1+1+120, y1+1+120)，(x0,y0,x1,y1)="
                    "含端板像素界"),
                "margin_px": CROP_MARGIN_PX,
                "expected_size_formula": (
                    "w = x1-x0+241, h = y1-y0+241（即 bounds宽+241/"
                    "bounds高+241，bounds 含端；= 板像素宽高 + 2×120px 白边）"),
            },
        },
        "default_palette_limitation_preregistration": (
            "默认配色局限如实预注册：bottom 视在 kicad 默认配色下，白墨"
            "图元（焊盘孔盘 --drill-shape-opt 2 白 fill 等）与板内背景"
            "空隙白在白底上不可见/不可分（calibration r14b 探针实证该"
            "现象于 revc 板；外部板同仪器预期同构）。本轮按单变量纪律"
            "不修仪器（r14b 重配为 revc 探针特化、不泛化）。该歧义="
            "bottom 视判读的弃权率潜在上推因素，holdout 弃权率解读时"
            "如实计入，不得事后归咎于仪器。"),
        "assertions": [
            "A1 输入复核：每板 input_sha256 全 64 位 hex，prep-record 逐字"
            "一致，datasets/ 活读一致（render 步导出前再验一次）",
            "A2 页数断言：每个导出 PDF page_count == 1（mode-single）",
            "A3 PNG magic：每张成图 \\x89PNG\\r\\n\\x1a\\n",
            "A4 尺寸公式：w == x1-x0+241 且 h == y1-y0+241（bounds 含端；"
            "= bounds宽高+241）",
            "A5 白边断言：裁剪后四侧各恰 120px、边缘带全白像素（非白计数"
            "=0）",
            "A6 确定性自证：每张图 PDF→合成→光栅→裁剪全链重跑一次，两次"
            "字节逐同（kicad PDF 字节本身不承诺跨运行等同，只断言光栅链内"
            "一致）",
            "A7 防覆写：全部输出（PDF/PNG/JSON）已存在非字节等同→FAIL，"
            "等同→幂等；kicad 导出目标已存在→拒绝执行",
            "A8 prep-record 前缀 b2eaad8365e33925 在 framing/render/witness"
            " 三步各复核一次；framing 文件在 render 期间零变动断言",
            "A9 受保护文件前缀（cli.py=6ed4f3fd/config.py=f515c348/"
            "toolchain_lock.json=d43dad89）每步开工/收工各验",
        ],
        "failure_policy": {
            "kicad_cli_failure": (
                "vme-wren（或任一板）kicad-cli 导出失败：同参数重试至多 "
                "1 次；再败→如实报告并停止渲染（不许换板、不许降参数），"
                "已成功产物与失败记录如实写入 witness 的 degradation 字段"),
            "assertion_failure": (
                "任一程序化断言失败即停止并如实报告，不得静默改参数"),
        },
        "freeze_order": {
            "declaration": (
                "本文件先于本轮任何官方 PNG 落盘（prep-record → framing → "
                "render → witness → 盲读）；落盘前断言 renders-holdout-r1/ "
                "不存在或无 *.png（本文件落盘时该目录尚不存在）。"),
            "render_step_outputs": (
                "render 步新建：6 张 PNG + pdfs/ 6 个 PDF + "
                "render-log-holdout-r1.json 中间记录（全部在 "
                "renders-holdout-r1/ 新建范围内）"),
        },
        "overwrite_guard": (
            "目标文件已存在非字节等同→FAIL；字节等同→幂等（防覆写）"),
        "zero_write_discipline": (
            "datasets/ 严格只读（仅 3 块输入板的只读哈希与 kicad-cli 读"
            "取）；out/ 既有文件零改动；活板（out/revc-asm/*）零涉及；"
            "pcbflow/ 与 tests/ 零改动（仅 import）。本轮新建范围="
            "scripts/s92_holdout_render_r1.py、out/v3-tl2/holdout/"
            "renders-holdout-r1/（含 pdfs/ 子目录）、"
            "render-framing-holdout-r1.json、render-witness-holdout-r1.json"),
        "protected_files_frozen_prefixes": PROTECTED,
    }

    sha, mode = _write_canonical_guarded(FRAMING_PATH, doc)
    print(f"[holdout-r1] framing 落盘：render-framing-holdout-r1.json "
          f"sha256={sha[:16]}… ({mode})")
    print(f"[holdout-r1] 目标 6 图："
          f"{', '.join(t['name'] for t in targets)}")


# ---------------------------------------------------------------------------
# render
# ---------------------------------------------------------------------------

def cmd_render() -> None:
    protected_start = _protected_check()
    prep_sha_start = _prep_check()
    if not FRAMING_PATH.exists():
        _fail("render-framing-holdout-r1.json 缺失（先跑 framing）")
    framing_sha_start = _sha(FRAMING_PATH)
    import json
    framing = json.loads(FRAMING_PATH.read_text(encoding="utf-8"))
    if framing["kind"] != "tl2_holdout_r1_render_framing":
        _fail("framing kind 不符")
    targets = _boards_verified(_load_prep_record())
    ver = _kicad_version()

    if RENDER_LOG_PATH.exists() and any(RENDERS_DIR.glob("*.png")):
        _fail("renders-holdout-r1/ 已有 PNG 且 render-log 存在（渲染一次"
              "成型纪律：重跑须先清理 renders-holdout-r1/ 整目录）")

    PDFS_DIR.mkdir(parents=True, exist_ok=True)

    renders = []
    failures = []
    degraded = False
    determinism = {}

    for t in targets:
        if degraded:
            break
        # A1 导出前输入再验
        live = _sha(REPO / t["input_path_rel"])
        if live != t["input_sha256"]:
            _fail(f"{t['name']}: 导出前输入 sha 复核失败：{live}")

        cmd = _export_cmd(t["pdf_output_rel"], t["input_path_rel"],
                          t["layers"], t["mirror"])
        attempts = []
        ok = False
        for attempt_no in (1, 2):  # 首次 + 同参数重试至多 1 次
            res = _run_kicad_attempt(cmd, t["pdf_output_rel"])
            attempts.append({"attempt": attempt_no, **res})
            print(f"[holdout-r1] 导出 {t['name']} attempt{attempt_no} "
                  f"rc={res['returncode']}")
            if res["returncode"] == 0:
                ok = True
                break
            if res["guard_blocked"]:
                break  # 防覆写 guard 命中即停，不重试
        if not ok:
            failures.append({
                "name": t["name"], "board_id": t["board_id"],
                "view": t["view"], "command": cmd,
                "pdf_output_rel": t["pdf_output_rel"],
                "attempts": attempts,
                "policy": "同参数重试至多 1 次已执行；如实报告并停止渲染",
            })
            degraded = True
            break  # 停止渲染（不许换板、不许降参数）

        pdf_path = REPO / t["pdf_output_rel"]
        pdf_sha = _sha(pdf_path)

        cropped, bounds, crop_box, pix_wh = _render_chain(pdf_path)
        checks = _assert_cropped(cropped, bounds, t["name"])

        png_path = REPO / t["png_output_rel"]
        mode = _guard_write_bytes(png_path, cropped)

        # A6 确定性自证：全链重跑一次，字节逐同
        cropped2, bounds2, _, _ = _render_chain(pdf_path)
        det_ok = cropped2 == cropped and bounds2 == bounds
        determinism[t["name"]] = bool(det_ok)
        if not det_ok:
            _fail(f"{t['name']}: 确定性自证失败（重跑非逐字节同）")

        renders.append({
            "name": t["name"],
            "board_id": t["board_id"],
            "view": t["view"],
            "png_rel": t["png_output_rel"],
            "sha256": _sha(png_path),
            "bytes": png_path.stat().st_size,
            "width": checks["width"],
            "height": checks["height"],
            "board_px_bounds_full": {
                "x0": bounds["x0"], "y0": bounds["y0"],
                "x1": bounds["x1"], "y1": bounds["y1"],
            },
            "pdf_sha256": pdf_sha,
            "pdf_rel": t["pdf_output_rel"],
            "command": cmd,
            "command_cwd": "repo_root",
            "crop_box": crop_box,
            "full_pixmap_wh": list(pix_wh),
            "edge_band_nonwhite": checks["edge_band_nonwhite"],
            "png_write_mode": mode,
            "determinism_rerun_byte_identical": bool(det_ok),
        })
        print(f"[holdout-r1] 成图 {t['name']}.png {checks['width']}x"
              f"{checks['height']} 板界=({bounds['x0']},{bounds['y0']})-"
              f"({bounds['x1']},{bounds['y1']}) "
              f"sha={renders[-1]['sha256'][:16]}… ({mode})")

    # A8 framing / prep-record 渲染期间零变动
    if _sha(FRAMING_PATH) != framing_sha_start:
        _fail("render-framing-holdout-r1.json 在 render 期间变动（冻结"
              "纪律破坏）")
    if _sha(PREP_RECORD_PATH) != prep_sha_start:
        _fail("holdout-prep-record-r1.json 在 render 期间变动")
    framing_unchanged = True
    protected_end = _protected_check()

    log = {
        "schema_version": "3.0",
        "kind": "tl2_holdout_r1_render_log",
        "holdout_id": HOLDOUT_ID,
        "round_id_constant": ROUND_ID_CONSTANT,
        "date_constant": DATE_CONSTANT,
        "no_visual_reading": True,
        "framing": {"path_rel": FRAMING_REL,
                    "sha256": framing_sha_start},
        "framing_unchanged_during_render": framing_unchanged,
        "prep_record_sha256_at_render": prep_sha_start,
        "prep_record_unchanged_during_render": True,
        "kicad_cli_version": ver,
        "protected_files": {"at_start": protected_start,
                            "at_end": protected_end},
        "renders": renders,
        "failures": failures,
        "determinism_rerun_byte_identical": determinism,
        "completed": len(renders) == 6 and len(failures) == 0,
        "degradation": (None if not degraded else {
            "kind": "kicad_cli_export_failure",
            "failed": [f["name"] for f in failures],
            "rendered_count": len(renders),
            "expected_count": 6,
            "policy_applied": ("同参数重试至多 1 次；失败后停止渲染，"
                               "不换板、不降参数；已成功产物保留并如实"
                               "记录"),
        }),
    }
    sha, mode = _write_canonical_guarded(RENDER_LOG_PATH, log)
    print(f"[holdout-r1] render 完成：{len(renders)}/6 张，失败 "
          f"{len(failures)}；render-log 落盘 sha256={sha[:16]}… ({mode})")
    if degraded:
        print(f"[holdout-r1] DEGRADED：{[f['name'] for f in failures]} "
              "导出失败（详见 render-log failures/degradation）")


# ---------------------------------------------------------------------------
# witness
# ---------------------------------------------------------------------------

def cmd_witness() -> None:
    protected_start = _protected_check()
    prep_sha = _prep_check()
    if not FRAMING_PATH.exists() or not RENDER_LOG_PATH.exists():
        _fail("framing 或 render-log 缺失（先跑 framing、render）")
    framing_sha = _sha(FRAMING_PATH)
    import json
    framing = json.loads(FRAMING_PATH.read_text(encoding="utf-8"))
    log = json.loads(RENDER_LOG_PATH.read_text(encoding="utf-8"))

    if log["framing"]["sha256"] != framing_sha:
        _fail("framing 在 render 期间变动（render-log 记录的 framing sha "
              "与活读不符）")
    if log["prep_record_sha256_at_render"] != prep_sha:
        _fail("prep-record 在 render 期间变动")
    if not log["framing_unchanged_during_render"]:
        _fail("render-log 记录 framing 期间变动")

    ver = _kicad_version()

    # 板输入 sha 复核（witness 独立再验）
    board_inputs = []
    for fb in FROZEN_BOARDS:
        live = _sha(REPO / fb["input_path_rel"])
        if live != fb["input_sha256"]:
            _fail(f"{fb['board_id']} 输入 sha witness 复核失败：{live}")
        board_inputs.append({"board_id": fb["board_id"],
                             "input_path_rel": fb["input_path_rel"],
                             "input_sha256": live,
                             "verified": True})

    # 6 张 PNG 逐盘对账 + 确定性独立重跑（witness 通道）
    expected_names = [t["name"] for t in
                      _boards_verified(_load_prep_record())]
    logged = {r["name"]: r for r in log["renders"]}
    failed_names = [f["name"] for f in log["failures"]]

    pngs_on_disk = sorted(p.name for p in RENDERS_DIR.glob("*.png"))
    if log["completed"]:
        if pngs_on_disk != sorted(f"{n}.png" for n in expected_names):
            _fail(f"成图集合与 6 张目标不符：{pngs_on_disk}")
    else:
        missing = [n for n in expected_names
                   if f"{n}.png" not in pngs_on_disk]
        if sorted(missing) != sorted(failed_names):
            _fail(f"缺失成图与失败记录不符：缺={missing} 败={failed_names}")

    renders_verified = []
    det_witness = {}
    for name in expected_names:
        if name not in logged:
            continue
        rec = logged[name]
        png_path = REPO / rec["png_rel"]
        data = png_path.read_bytes()
        if _sha_bytes(data) != rec["sha256"]:
            _fail(f"{name}: PNG sha 与 render-log 不符")
        if png_path.stat().st_size != rec["bytes"]:
            _fail(f"{name}: PNG 字节数不符")
        w, h = _png_size(data)
        if [w, h] != [rec["width"], rec["height"]]:
            _fail(f"{name}: PNG 尺寸不符")
        b = _bounds_of_checked(data, rec)
        if b is False:
            _fail(f"{name}: 板界宽高与记录不符")
        # 确定性独立重跑（witness 通道）：PDF→合成→光栅→裁剪 字节逐同
        pdf_path = REPO / rec["pdf_rel"]
        if _sha(pdf_path) != rec["pdf_sha256"]:
            _fail(f"{name}: PDF sha 与 render-log 不符")
        cropped2, bounds2, _, _ = _render_chain(pdf_path)
        bound_keys = ("x0", "y0", "x1", "y1")
        det_ok = (cropped2 == data
                  and all(bounds2[k] == b[k] for k in bound_keys))
        det_witness[name] = bool(det_ok)
        if not det_ok:
            _fail(f"{name}: witness 确定性独立重跑非逐字节同")
        renders_verified.append({
            "name": name,
            "png_rel": rec["png_rel"],
            "sha256": rec["sha256"],
            "bytes": rec["bytes"],
            "width": rec["width"],
            "height": rec["height"],
            "board_px_bounds_full": rec["board_px_bounds_full"],
            "pdf_rel": rec["pdf_rel"],
            "pdf_sha256": rec["pdf_sha256"],
            "command": rec["command"],
            "disk_verified": True,
        })
        print(f"[holdout-r1] witness 对账 {name}: sha={rec['sha256'][:16]}… "
              f"{rec['width']}x{rec['height']} 确定性重跑=OK")

    # pdfs/ 目录对账
    pdfs_on_disk = sorted(p.name for p in PDFS_DIR.glob("*.pdf"))
    if len(pdfs_on_disk) != len(logged):
        _fail(f"pdfs/ 数量不符：{len(pdfs_on_disk)} != {len(logged)}")

    import fitz
    import PIL

    degraded = log["degradation"]
    n = len(renders_verified)
    bounds_txt = "; ".join(
        f"{r['name']}=({r['board_px_bounds_full']['x0']},"
        f"{r['board_px_bounds_full']['y0']})-"
        f"({r['board_px_bounds_full']['x1']},"
        f"{r['board_px_bounds_full']['y1']})"
        for r in renders_verified)

    doc = {
        "schema_version": "3.0",
        "kind": "tl2_holdout_r1_render_witness",
        "holdout_id": HOLDOUT_ID,
        "round_id_constant": ROUND_ID_CONSTANT,
        "date_constant": DATE_CONSTANT,
        "no_visual_reading": True,
        "instrument": (
            f"kicad-cli {ver} pcb export pdf --mode-single --scale 1 "
            "--check-zones --drill-shape-opt 2（top=F.Cu,F.Mask,"
            "F.Silkscreen,Edge.Cuts,F.Courtyard；bottom=B.Cu,B.Mask,B."
            "Silkscreen,Edge.Cuts,B.Courtyard + --mirror）→ PyMuPDF "
            f"{fitz.version[0]} 40pt 组合页 get_pixmap(dpi=640, alpha="
            "False) → pcbflow.calibration.png_board_pixel_bounds 板界实测 "
            f"→ +120px 裁剪（Pillow {PIL.__version__} crop/save）；kicad "
            "默认配色、零 overlay（=render-framing-holdout-r1.json 预注册）"),
        "kicad_cli_version_measured": ver,
        "framing": {
            "path_rel": FRAMING_REL,
            "sha256": framing_sha,
            "unchanged_during_render": log["framing_unchanged_during_render"],
            "unchanged_at_witness": True,
        },
        "prep_record": {
            "path_rel": PREP_REL,
            "sha256": prep_sha,
            "expected_prefix": PREP_RECORD_SHA_PREFIX,
            "prefix_verified_all_three_steps": True,
            "unchanged_during_render":
                log["prep_record_unchanged_during_render"],
        },
        "protected_files": {
            "at_start": protected_start,
            "at_end": _protected_check(),
        },
        "board_inputs_verified": board_inputs,
        "renders": renders_verified,
        "render_log": {
            "path_rel": RENDER_LOG_REL,
            "sha256": _sha(RENDER_LOG_PATH),
            "completed": log["completed"],
        },
        "determinism": {
            "scope": (
                "kicad PDF 字节不做跨运行确定性断言（工具不承诺）；确定性"
                "断言范围=「PDF→40pt 合成→dpi640 光栅→板界实测→+120px "
                "裁剪→PNG 字节」全链重跑逐字节一致"),
            "render_step_rerun": log["determinism_rerun_byte_identical"],
            "witness_independent_rerun": det_witness,
        },
        "zero_write_declaration": {
            "datasets_zero_write": True,
            "datasets_note": "3 块输入板只读（sha 复核+导出读取），零写入",
            "live_boards_zero_involvement": True,
            "out_existing_files_untouched": True,
            "new_files_scope": [
                "scripts/s92_holdout_render_r1.py",
                RENDERS_DIR_REL + "/",
                RENDERS_DIR_REL + "/pdfs/",
                FRAMING_REL,
                WITNESS_REL,
            ],
        },
        "degradation": degraded,
        "conclusion": (
            f"holdout-r1 渲染完成：{n}/6 张成图（3 板 × top/bottom，kicad "
            "默认配色、r5 框架管线逐字同口径、零 overlay）。全部成图通过"
            "程序化断言（PNG magic、尺寸公式 bounds+241、四侧恰 120px 全"
            f"白边）；确定性自证 render 步与 witness 独立重跑全部逐字节一"
            f"致。板界实测：{bounds_txt}。受保护文件前缀三步全程复核通过；"
            "framing/prep-record 渲染期间零变动。degradation="
            f"{None if degraded is None else degraded['failed']}。"
            "默认配色局限已预注册：bottom 视白墨/空隙歧义=弃权率潜在"
            "上推因素，解读时如实计入。"),
    }
    sha, mode = _write_canonical_guarded(WITNESS_PATH, doc)
    print(f"[holdout-r1] witness 落盘：render-witness-holdout-r1.json "
          f"sha256={sha[:16]}… ({mode})")


def _sha_bytes(data: bytes) -> str:
    return hashing.sha256_bytes(data)


def _bounds_of_checked(data: bytes, rec: dict) -> dict:
    """盘上 PNG 的尺寸一致性已有断言；板界以 render-log 记录为准
    （board_px_bounds_full 是全页组合页上的实测，witness 经独立重跑复核，
    见 _render_chain 调用处）。此处仅做宽高口径一致性检查。"""
    b = rec["board_px_bounds_full"]
    w = b["x1"] - b["x0"] + 241
    h = b["y1"] - b["y0"] + 241
    if [rec["width"], rec["height"]] != [w, h]:
        return False
    return {"x0": b["x0"], "y0": b["y0"], "x1": b["x1"], "y1": b["y1"]}


def main() -> None:
    step = sys.argv[1] if len(sys.argv) > 1 else ""
    if step == "framing":
        cmd_framing()
    elif step == "render":
        cmd_render()
    elif step == "witness":
        cmd_witness()
    else:
        _fail("用法：s92_holdout_render_r1.py framing|render|witness")


if __name__ == "__main__":
    main()
