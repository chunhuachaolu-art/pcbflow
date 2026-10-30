#!/usr/bin/env python
"""R14b 渲染实施者（第二次尝试）：白色内容层归属探针 → 重定向配色。

背景：首试（s50_render_r14.py，framing-r14=918672b4、witness-r14=13fd1cab）
被探针证伪：bottom 视 B.SilkS/B.CrtYd 自有图元为零，预配色无目标，成图与
renders-r5 逐字节相同（仪器零变更）。本轮先回答 diag-r13-review D2 遗留的
核心问题——bottom 合成图中纯白 (255,255,255) 内容来自哪个单层导出——再据
探针事实重定向配色，产出真正有差异的 r14b 渲染件。

探针结论（本脚本 probe 步骤程序化产出，侦察阶段已预验）：
  白色内容为双来源，任何单层独占归因都不成立：
  (a) 白墨矢量图元：combined bottom PDF 含 162 个白 fill（焊盘钻孔圆盘，
      --drill-shape-opt 2）+ 4 个白 stroke（左上特区 4 个椭圆焊盘轮廓）；
      同一组几何（bbox 集合逐一相同）同时出现在 B.Cu 与 B.Mask 两层的
      单层导出 PDF 中（kicad 对 *.Cu/*.Mask 多层焊盘的共享绘制族），
      B.Silkscreen/B.Courtyard/Edge.Cuts 单层导出零白图元。combined 中
      该族绘制于蓝/青之上（z 序实证），PDF 无 OCG 层标记（layer 全空）。
  (b) 板内背景空隙白：板界内既无任何单层非白墨、又非白图元 mask 的纯白
      （铺铜 clearance 空隙/翼瓣形态/板框退让带/基准环缝）——它是墨的
      缺失而非图元，D2 报告"全部白色同一渲染图层族 >95%"被像素+矢量双
      通道证伪。
  ⇒ 按多重着色纪律：(a)→橙 (255,165,0)、(b)→绿 (0,128,0)，两色与画布
  已有主色 RGB 欧氏距离全部 >150（代码内断言）。

本脚本三步（库侧 pcbflow/* 零改动零新增，只 import）：
  probe    对 staging-r4 两板做 10 次单层 kicad-cli 导出（bottom 5 层 ×2 板
           --mirror）→ renders-r14b/layers/；每层光栅统计（白像素总数=背景
           白+白墨不可分，如实声明；墨水像素；主色众数）；combined+单层
           PDF 矢量探针（fill/stroke 色族、z 序 runs、白图元计数、白 bbox
           集合一致性断言、无 OCG 证据）；白图元 mask 矢量重建（fitz Shape
           →dpi640 光栅化，黑底红 fill/绿 stroke PNG 落盘）；证书点表
           （D2 参照坐标+程序化定位的翼 junction，逐点查 r5/mask/各层值）；
           板内白覆盖率统计（白图元命中/空隙剩余）。
  framing  落盘 render-framing-r14b.json（canonical JSON，先于任何官方成图）：
           单变量仪器变更声明（bottom 视白显式配色：白图元→橙、板内空隙
           白→绿）、多重着色映射+色距断言、合成方法与 z 序、页几何与 r5
           同口径（dpi640/40pt/裁板界+120px/板界断言=derivation-log-r5
           实测值）、top 零变更声明、预注册预测（方向声明+数字以成图后
           实测回填）、首试证伪引用、freeze 顺序。
  render   按 framing 执行：r4 冻结 combined bottom PDF（sha 复核）→
           dpi640 组合页光栅化 → overlay 橙（白图元 mask）→ overlay 绿
           （板内空隙 mask，与橙 mask 构造互斥）→ 板界实测断言（=r5 记录
           值）→ r5 公式裁剪 → renders-r14b/ 两张 bottom PNG（防覆写）；
           r5 top 两张逐字节拷贝+哈希见证；程序化断言（橙/绿计数>0、白较
           r5 下降、mask 只作用于白域的偏差如实记录）；确定性自证（光栅
           化→overlay→裁剪全链重跑逐字节一致+单层栅格与 probe 产物逐字节
           一致+mask 重建逐字节一致）；render-witness-r14b.json。

纪律：确定性纯函数（同输入重跑字节等同）；日期/轮次=声明常量；canonical
JSON=pcbflow.hashing.canonical_json_bytes、hash=sha256_file；kicad-cli 调用
照 s29/s50 模式（绝对路径+版本验证+subprocess.run cwd=REPO）；除 kicad-cli
外零其他 subprocess/网络/wall-clock；受保护文件（cli.py/config.py/
toolchain_lock.json）与 staging-r4/datasets/out 既有文件零改动（renders-r14
首试证伪记录保留）；防覆写 guard（已存在非字节等同→FAIL，等同→幂等）；
零视觉判读（全部程序化像素/矢量统计）。

用法：python scripts/s51_render_r14b.py probe|framing|render
"""

from __future__ import annotations

import io
import struct
import subprocess
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from pcbflow import calibration, hashing  # noqa: E402

CAL_DIR = REPO / "out" / "v3-tl2" / "calibration"
R14B_DIR = CAL_DIR / "renders-r14b"
LAYERS_DIR = R14B_DIR / "layers"
FRAMING_R14B = CAL_DIR / "render-framing-r14b.json"
WITNESS_R14B = CAL_DIR / "render-witness-r14b.json"
STAGING_R4 = CAL_DIR / "staging-r4"
R4_DIR = CAL_DIR / "renders-r4"
R5_DIR = CAL_DIR / "renders-r5"
FRAMING_R5 = CAL_DIR / "render-framing-r5.json"
DERIVATION_R5 = CAL_DIR / "derivation-log-r5.json"
#: 首试（s50）证伪记录，只读引用
FRAMING_R14_FALSIFIED = CAL_DIR / "render-framing-r14.json"
WITNESS_R14_FALSIFIED = CAL_DIR / "render-witness-r14.json"
LIVE_BOARDS = {
    "applied": REPO / "out" / "revc-asm" / "board" / "applied.kicad_pcb",
    "prep1": REPO / "out" / "revc-asm" / "board" / "_pre-p1-batch-1.kicad_pcb",
}

DATE_CONSTANT = "2026-09-08"
ROUND_ID = "2026-09-08-r14b"
ROUND_LABEL = "r14b"
DOMAIN_ID = calibration.DOMAIN_ID

KICAD_CLI = Path(r"F:\kicad\bin\kicad-cli.exe")
KICAD_VERSION = "10.0.5"
RASTER_DPI = 640            # 与 r5 逐字同口径
COMPOSE_MARGIN_PT = 40.0    # 与 r4/r5 逐字同口径
CROP_MARGIN_PX = 120        # 与 r5 逐字同口径

#: bottom 层清单（与 r4/r5 逐字相同）；bottom 视加 --mirror
LAYERS_BOTTOM = "B.Cu,B.Mask,B.Silkscreen,Edge.Cuts,B.Courtyard"
PROBE_LAYERS_BOTTOM = ("B.Cu", "B.Mask", "B.Silkscreen", "Edge.Cuts",
                       "B.Courtyard")

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

#: 首试证伪件 sha256（活读复核前缀；红线 2：零改动保留）
FALSIFIED_R14 = {
    "out/v3-tl2/calibration/render-framing-r14.json": "918672b4",
    "out/v3-tl2/calibration/render-witness-r14.json": "13fd1cab",
}

#: r4 冻结 combined bottom PDF（本轮 base 图像来源；sha 从 render-framing-r5
#: frozen_inputs 活读复核，不硬编码）
R4_BOTTOM_PDF = {
    "applied": R4_DIR / "applied-bottom.pdf",
    "prep1": R4_DIR / "prep1-bottom.pdf",
}

FINAL_PNGS = ("applied-bottom", "prep1-bottom", "applied-top", "prep1-top")

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"

# ---------------------------------------------------------------------------
# 多重着色目标（探针事实 → 预注册固定 RGB；非采样值）
# ---------------------------------------------------------------------------
#: (a) 白墨矢量图元（孔盘 fill + 椭圆轮廓 stroke，B.Cu∪B.Mask 双族共享）→ 橙
TARGET_ORANGE = (255, 165, 0)
#: (b) 板内背景空隙白（无任何层墨区域）→ 深绿（PCB 基材惯例色）
TARGET_GREEN = (0, 128, 0)
#: 画布已有主色（r5 实测，s50 kept_layer_evidence 同款）
CANVAS_COLORS = {
    "B.Cu_blue": (77, 126, 195),
    "B.Mask_cyan": (153, 255, 248),
    "Edge.Cuts_gray": (207, 209, 205),
    "canvas_white": (255, 255, 255),
    "target_orange": TARGET_ORANGE,
    "target_green": TARGET_GREEN,
}
COLOR_DIST_MIN = 150.0  # 预注册：目标色与画布每色的 RGB 欧氏距离 > 150


def _fail(msg: str) -> None:
    print(f"[r14b] FAIL: {msg}")
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
        ok = sha.startswith(prefix)
        if not ok:
            _fail(f"受保护文件哈希不符：{rel} {sha[:8]} != {prefix}")
        results[rel] = {"sha256": sha, "expected_prefix": prefix, "match": True}
    falsified = {}
    for rel, prefix in FALSIFIED_R14.items():
        sha = _sha(REPO / rel)
        falsified[rel] = {
            "sha256": sha, "expected_prefix": prefix,
            "untouched": sha.startswith(prefix),
        }
        if not falsified[rel]["untouched"]:
            _fail(f"首试证伪件被改动：{rel} {sha[:8]} != {prefix}")
    return {"protected": results, "falsified_r14_untouched": falsified}


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


def _r5_refs() -> dict:
    """r5 参照件 sha（活读）+ framing-r5/derivation-log-r5 哈希链自洽复核。"""
    deriv_sha = _sha(DERIVATION_R5)
    framing5_sha = _sha(FRAMING_R5)
    import json
    deriv = json.loads(DERIVATION_R5.read_text(encoding="utf-8"))
    ref = deriv.get("framing_ref", {})
    if ref.get("sha256") != framing5_sha:
        _fail("framing-r5 sha 与 derivation-log-r5.framing_ref 不符（链破坏）")
    pngs = {}
    for name in FINAL_PNGS:
        pngs[name] = _sha(R5_DIR / f"{name}.png")
    return {
        "renders_r5_png_sha256": pngs,
        "render-framing-r5.json": framing5_sha,
        "derivation-log-r5.json": deriv_sha,
        "framing_chain_self_consistent": True,
        "_deriv": deriv,
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


def _run_kicad_export(out_rel: str, in_rel: str, layers: str,
                      mirror: bool) -> list:
    """kicad-cli 2D PDF 导出（照 s29/s50 模式：绝对路径执行、cwd=REPO）。"""
    cmd = ["kicad-cli", "pcb", "export", "pdf", "--mode-single",
           "--scale", "1", "--check-zones", "--drill-shape-opt", "2",
           "--layers", layers]
    if mirror:
        cmd.append("--mirror")
    cmd += ["-o", out_rel, in_rel]
    if (REPO / out_rel).exists():
        _fail(f"输出已存在（防覆写）：{out_rel}")
    proc = subprocess.run([str(KICAD_CLI)] + cmd[1:], cwd=str(REPO),
                          capture_output=True, text=True)
    if proc.returncode != 0 or not (REPO / out_rel).exists():
        _fail(f"kicad-cli 失败 rc={proc.returncode}: "
              f"{(proc.stderr or proc.stdout or '')[-500:]} cmd={' '.join(cmd)}")
    return cmd


def _compose_raster(pdf_path: Path) -> tuple:
    """fitz 组合页光栅化（与 r5 逐字同口径）：40pt 白边组合页 + dpi640。"""
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


def _load_rgb(png_bytes: bytes) -> "np.ndarray":
    from PIL import Image
    im = Image.open(io.BytesIO(png_bytes))
    return np.array(im.convert("RGB"))  # 可写拷贝（render overlay 需要写入）


def _ink_alpha(arr: "np.ndarray") -> "np.ndarray":
    """墨水量 alpha=255−min(R,G,B)（uint8；白背景→0，任何非白墨→>0）。
    注意：白墨（fill=白）画在白底上不可见，alpha=0——单层光栅无法区分
    背景白与白墨；白墨的检测通道=PDF 矢量探针（见 _drawings_report）。"""
    return (255 - arr.min(axis=2)).astype(np.uint8)


def _dominant_colors(arr: "np.ndarray", alpha: "np.ndarray",
                     top_n: int = 8) -> list:
    """非背景（alpha>0）像素的精确 RGB 众数排行（确定性）。"""
    px = arr[alpha > 0]
    if px.shape[0] == 0:
        return []
    colors, counts = np.unique(px.reshape(-1, 3), axis=0, return_counts=True)
    order = np.argsort(-counts, kind="stable")
    return [{"rgb": [int(v) for v in colors[i]],
             "count": int(counts[i])} for i in order[:top_n]]


def _layer_png_name(state: str, layer: str) -> str:
    return f"{state}-bottom-{layer.replace('.', '_')}.png"


def _layer_pdf_name(state: str, layer: str) -> str:
    return f"{state}-bottom-{layer.replace('.', '_')}.pdf"


def _euclid(a, b) -> float:
    return float(np.sqrt(sum((int(x) - int(y)) ** 2 for x, y in zip(a, b))))


# ---------------------------------------------------------------------------
# 矢量探针（白色内容归属的决定性通道）
# ---------------------------------------------------------------------------

def _is_white_fill(d: dict) -> bool:
    f = d.get("fill")
    return f is not None and all(abs(v - 1.0) < 1e-6 for v in f)


def _is_white_stroke(d: dict) -> bool:
    c = d.get("color")
    return (d.get("fill") is None and c is not None
            and all(abs(v - 1.0) < 1e-6 for v in c))


def _fill_class(d: dict) -> str:
    f = d.get("fill")
    if f is not None:
        return "F_" + str(tuple(round(v, 3) for v in f))
    c = d.get("color")
    return "S_" + (str(tuple(round(v, 3) for v in c)) if c else "none")


def _z_runs(draws: list) -> list:
    runs = []
    prev, start = None, 0
    for i, d in enumerate(draws):
        k = _fill_class(d)
        if k != prev:
            if prev is not None:
                runs.append({"class": prev, "from": start, "to": i - 1})
            prev, start = k, i
    runs.append({"class": prev, "from": start, "to": len(draws) - 1})
    return runs


def _drawings_report(pdf_path: Path) -> dict:
    """PDF 矢量级探针：fill/stroke 色族计数、白图元计数、z 序 runs、
    OCG layer 字段证据、白 fill bbox 排序集合（归因对照用）。"""
    import fitz
    import collections

    doc = fitz.open(str(pdf_path))
    try:
        page = doc[0]
        draws = page.get_drawings()
        fills = collections.Counter()
        strokes = collections.Counter()
        white_fill_bb = []
        white_stroke_bb = []
        layers = set()
        opacities = set()
        for d in draws:
            layers.add(str(d.get("layer")))
            if d.get("fill_opacity") is not None:
                opacities.add(round(float(d.get("fill_opacity")), 4))
            f = d.get("fill")
            if f is not None:
                fills[str(tuple(round(v, 3) for v in f))] += 1
                if _is_white_fill(d):
                    white_fill_bb.append(
                        tuple(round(v, 2) for v in d["rect"]))
            else:
                c = d.get("color")
                strokes[str(tuple(round(v, 3) for v in c))
                        if c else "none"] += 1
                if _is_white_stroke(d):
                    white_stroke_bb.append(
                        tuple(round(v, 2) for v in d["rect"]))
        return {
            "pdf_rel": str(pdf_path.relative_to(REPO)).replace("\\", "/"),
            "sha256": _sha(pdf_path),
            "page_pt": [round(page.rect.width, 4),
                        round(page.rect.height, 4)],
            "drawing_count": len(draws),
            "fill_color_counts": dict(fills),
            "stroke_color_counts": dict(strokes),
            "white_fill_count": len(white_fill_bb),
            "white_stroke_count": len(white_stroke_bb),
            "white_fill_bboxes_sorted": sorted(white_fill_bb),
            "white_stroke_bboxes_sorted": sorted(white_stroke_bb),
            "z_order_runs": _z_runs(draws),
            "ocg_layer_field_values": sorted(layers),
            "fill_opacities": sorted(opacities),
        }
    finally:
        doc.close()


def _rebuild_white_masks(pdf_path: Path) -> tuple:
    """矢量重建白图元 mask：fitz Shape 在同几何组合页（40pt 边距）上只绘制
    白 fill（红）与白 stroke（绿），黑底，dpi640 光栅化。
    返回 (fill_mask, stroke_mask, png_bytes, meta)。确定性纯函数。"""
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
            pix = np_.get_pixmap(dpi=RASTER_DPI, alpha=False)
            arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
                pix.height, pix.width, pix.n)[:, :, :3]
            fill_mask = arr[:, :, 0] > 127
            stroke_mask = arr[:, :, 1] > 127
            from PIL import Image
            bio = io.BytesIO()
            Image.fromarray(arr, "RGB").save(bio, "PNG")
            meta = {
                "rebuilt_white_fill_drawings": nf,
                "rebuilt_white_stroke_drawings": ns,
                "mask_fill_pixel_count": int(fill_mask.sum()),
                "mask_stroke_pixel_count": int(stroke_mask.sum()),
                "mask_overlap_pixels": int((fill_mask & stroke_mask).sum()),
                "method": (
                    "fitz Shape 重建 combined PDF 的白 fill（红）/白 stroke"
                    "（绿）到同几何 40pt 组合页，黑底 dpi640 光栅化，"
                    ">127 阈值二值化；逐字重画 items（l/c/re/qu），fill 规则"
                    "与 closePath 从 get_drawings 元数据透传"),
            }
            return fill_mask, stroke_mask, bio.getvalue(), meta
        finally:
            out.close()
    finally:
        doc.close()


def _mask_png_name(state: str) -> str:
    return f"{state}-bottom-white-masks.png"


def _probe_layer_stats(state: str, layer: str) -> dict:
    """从 layers/ 已落盘单层 PNG 重算统计（纯函数，probe/framing/render
    共用同一实现）。white_pixel_note：单层光栅纯白=背景白+白墨（白 on 白
    不可见）之和，无法在光栅通道拆分——白墨归因走矢量通道。"""
    png_path = LAYERS_DIR / _layer_png_name(state, layer)
    arr = _load_rgb(png_path.read_bytes())
    alpha = _ink_alpha(arr)
    ink_count = int((alpha > 0).sum())
    total = int(arr.shape[0] * arr.shape[1])
    return {
        "state": state, "side": "bottom", "layer": layer,
        "png_rel": f"out/v3-tl2/calibration/renders-r14b/layers/"
                   f"{_layer_png_name(state, layer)}",
        "width": int(arr.shape[1]), "height": int(arr.shape[0]),
        "ink_pixel_count": ink_count,
        "ink_fraction": round(ink_count / total, 8),
        "white_pixel_count_total": int(total - ink_count),
        "white_pixel_note": ("纯白像素=背景白+不可见白墨（alpha 通道不可分）；"
                             "白墨归因=PDF 矢量探针 white_fill/stroke_count"),
        "dominant_colors": _dominant_colors(arr, alpha),
    }


# ---------------------------------------------------------------------------
# 证书点（D2 参照坐标 + 程序化定位；全页坐标=r5 cropped+(crop_x,crop_y)）
# ---------------------------------------------------------------------------

def _certificate_points(r5_applied: "np.ndarray", crop_x: int,
                        crop_y: int, fill_mask, stroke_mask,
                        layer_ink: dict) -> list:
    """构造证书点表并逐点查值（零视觉判读：全部程序化断言+查值）。
    返回可序列化记录列表；预期不符即 FAIL。"""
    H, W = r5_applied.shape[:2]

    def fp(cx: int, cy: int) -> tuple:
        return cx + crop_x, cy + crop_y

    def rec(name, fx, fy, expect_r5) -> dict:
        cx, cy = fx - crop_x, fy - crop_y
        if not (0 <= cx < W and 0 <= cy < H):
            _fail(f"证书点越界：{name} cropped=({cx},{cy})")
        r5v = tuple(int(v) for v in r5_applied[cy, cx])
        if isinstance(expect_r5, tuple):
            if r5v != expect_r5:
                _fail(f"证书点 {name} r5={r5v} 预期 {expect_r5}")
        entry = {
            "name": name,
            "full_page_xy": [int(fx), int(fy)],
            "cropped_xy": [int(cx), int(cy)],
            "r5_rgb": list(r5v),
            "white_fill_mask": bool(fill_mask[fy, fx]),
            "white_stroke_mask": bool(stroke_mask[fy, fx]),
            "layer_ink": {k: bool(m[fy, fx]) for k, m in layer_ink.items()},
        }
        return entry

    pts = []
    # 1. 焊盘孔盘中心（D2 解剖：白中心孔盘 d≈24.4px；盘 (508,196)c）
    pts.append(rec("pad_hole_disk", *fp(508, 196), (255, 255, 255)))
    # 2. 白描边环带（外径≈53px 描边≈4px；r≈24：盘 (508,196)c 上方）
    pts.append(rec("pad_rim_gap_band", *fp(508, 172), (255, 255, 255)))
    # 3. 青色环带（径向宽≈9px；r≈15-21）
    pts.append(rec("pad_ring_cyan_band", *fp(508, 181), (153, 255, 248)))
    # 4. 盘外铺铜蓝
    pts.append(rec("copper_field_blue", *fp(508, 156), (77, 126, 195)))
    # 5/6. 翼 junction（程序化定位，D2 上外排 y=196c、x508+64k、间距 64）：
    #   走廊中点白=粘连对 junction；蓝=未粘连对间隙。
    bonded = unbonded = None
    for k in range(19):
        mx = 508 + 64 * k + 32
        v = tuple(int(v) for v in r5_applied[196, mx])
        if v == (255, 255, 255) and bonded is None:
            bonded = mx
        elif v == (77, 126, 195) and unbonded is None:
            unbonded = mx
        if bonded is not None and unbonded is not None:
            break
    if bonded is None:
        _fail("程序化定位失败：上外排未找到粘连翼 junction（白走廊中点）")
    if unbonded is None:
        _fail("程序化定位失败：上外排未找到未粘连走廊（蓝中点）")
    pts.append(rec("wing_junction_bonded", *fp(bonded, 196),
                   (255, 255, 255)))
    pts.append(rec("wing_corridor_unbonded", *fp(unbonded, 196),
                   (77, 126, 195)))
    # 7. 板框退让带（板左缘 bbox x0=120c 内侧 7px，D2：板框描边 ~14px 白）
    pts.append(rec("board_frame_band", *fp(127, 1000), (255, 255, 255)))
    # 8. 基准黑点中心（D2：(282,224)c 黑圆点）
    pts.append(rec("fiducial_disk_black", *fp(282, 224), (0, 0, 0)))
    # 9. 基准白环点：程序化螺旋搜索黑点邻域最近 r5 纯白且非白图元 mask 的点
    ring = None
    hx, hy = 282, 224
    for r in range(1, 40):
        cands = []
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                if max(abs(dx), abs(dy)) != r:
                    continue
                x, y = hx + dx, hy + dy
                if not (0 <= x < W and 0 <= y < H):
                    continue
                if tuple(int(v) for v in r5_applied[y, x]) == (255, 255, 255):
                    fx, fy = fp(x, y)
                    if not fill_mask[fy, fx] and not stroke_mask[fy, fx]:
                        cands.append((x, y))
        if cands:
            ring = min(cands, key=lambda p: (p[0] - hx) ** 2 + (p[1] - hy) ** 2)
            break
    if ring is None:
        _fail("程序化定位失败：基准黑点邻域未找到空隙白环点")
    pts.append(rec("fiducial_ring_gap", *fp(ring[0], ring[1]),
                   (255, 255, 255)))
    return pts


# ---------------------------------------------------------------------------
# probe
# ---------------------------------------------------------------------------

def cmd_probe() -> None:
    _protected_check()
    _staging_check()
    ver = _kicad_version()
    for name in FINAL_PNGS:
        if (R14B_DIR / f"{name}.png").exists():
            _fail(f"renders-r14b/{name}.png 已存在（probe 拒绝在官方成图后"
                  "运行）")
    if LAYERS_DIR.exists() and any(LAYERS_DIR.glob("*.pdf")):
        _fail("renders-r14b/layers/ 已有 PDF（防覆写；重跑请先清理该目录）")

    LAYERS_DIR.mkdir(parents=True, exist_ok=True)

    # ---- 10 次单层导出（两板 × bottom 5 层）----
    exports = []
    for state in ("applied", "prep1"):
        for layer in PROBE_LAYERS_BOTTOM:
            pdf_rel = (f"out/v3-tl2/calibration/renders-r14b/layers/"
                       f"{_layer_pdf_name(state, layer)}")
            cmd = _run_kicad_export(pdf_rel, STAGED_REL[state], layer, True)
            png_bytes, pw, ph = _compose_raster(REPO / pdf_rel)
            png_rel = (f"out/v3-tl2/calibration/renders-r14b/layers/"
                       f"{_layer_png_name(state, layer)}")
            _guard_write_bytes(REPO / png_rel, png_bytes)
            exports.append({
                "state": state, "side": "bottom", "layer": layer,
                "mirror": True, "pdf_rel": pdf_rel, "png_rel": png_rel,
                "pdf_sha256": _sha(REPO / pdf_rel),
                "png_sha256": _sha(REPO / png_rel),
                "pixmap_wh": [pw, ph],
                "command": cmd, "command_cwd": "repo_root",
            })
            print(f"[r14b] probe 导出 {state}-bottom-{layer}: "
                  f"pdf_sha={exports[-1]['pdf_sha256'][:8]}… pix={pw}x{ph}")

    # ---- 矢量探针：combined（两板）+ 全部单层 PDF ----
    combined_reports = {}
    single_reports = {}
    for state in ("applied", "prep1"):
        combined_reports[state] = _drawings_report(R4_BOTTOM_PDF[state])
        for layer in PROBE_LAYERS_BOTTOM:
            single_reports[f"{state}-bottom-{layer}"] = _drawings_report(
                LAYERS_DIR / _layer_pdf_name(state, layer))

    # 决定性断言：白图元只出现在 B.Cu/B.Mask 单层导出（两板），且两层的
    # 白 fill bbox 集合逐一相同（同一组几何=共享绘制族）
    attribution = {}
    for state in ("applied", "prep1"):
        wf = {k: v["white_fill_count"] for k, v in single_reports.items()
              if v["white_fill_count"] > 0 and k.startswith(state)}
        ws = {k: v["white_stroke_count"] for k, v in single_reports.items()
              if v["white_stroke_count"] > 0 and k.startswith(state)}
        bcu = single_reports[f"{state}-bottom-B.Cu"]
        bmk = single_reports[f"{state}-bottom-B.Mask"]
        if set(wf) != {f"{state}-bottom-B.Cu", f"{state}-bottom-B.Mask"}:
            _fail(f"{state}: 白 fill 单层归因非 B.Cu∪B.Mask 双族：{wf}")
        if set(ws) != {f"{state}-bottom-B.Cu", f"{state}-bottom-B.Mask"}:
            _fail(f"{state}: 白 stroke 单层归因非 B.Cu∪B.Mask 双族：{ws}")
        if bcu["white_fill_bboxes_sorted"] != bmk["white_fill_bboxes_sorted"]:
            _fail(f"{state}: B.Cu 与 B.Mask 白 fill bbox 集合不一致")
        if (bcu["white_stroke_bboxes_sorted"]
                != bmk["white_stroke_bboxes_sorted"]):
            _fail(f"{state}: B.Cu 与 B.Mask 白 stroke bbox 集合不一致")
        if combined_reports[state]["white_fill_count"] != bcu[
                "white_fill_count"]:
            _fail(f"{state}: combined 白 fill 数 != 单层白 fill 数"
                  f"（{combined_reports[state]['white_fill_count']} vs "
                  f"{bcu['white_fill_count']}）")
        for layer in ("B.Silkscreen", "B.Courtyard", "Edge.Cuts"):
            rep = single_reports[f"{state}-bottom-{layer}"]
            if rep["white_fill_count"] or rep["white_stroke_count"]:
                _fail(f"{state}-bottom-{layer} 出现白图元（与首试探针矛盾）")
        attribution[state] = {
            "white_fill_counts_by_layer": wf,
            "white_stroke_counts_by_layer": ws,
            "bcu_bmask_white_fill_bboxes_identical": True,
            "bcu_bmask_white_stroke_bboxes_identical": True,
            "combined_white_fill_count":
                combined_reports[state]["white_fill_count"],
            "combined_white_stroke_count":
                combined_reports[state]["white_stroke_count"],
            "no_ocg_layer_marks":
                combined_reports[state]["ocg_layer_field_values"],
            "conclusion": (
                "白色墨水图元=B.Cu∪B.Mask 双族共享绘制（几何逐一同组；"
                "combined 仅绘一次、z 序在蓝/青之上）；"
                "B.Silkscreen/B.Courtyard/Edge.Cuts 族零白图元；"
                "PDF 无 OCG 层标记（矢量级无层归属，归因只能靠单层导出"
                "对照）"),
        }
        print(f"[r14b] 矢量探针 {state}: 白 fill={wf} 白 stroke={ws} "
              f"combined=({attribution[state]['combined_white_fill_count']},"
              f"{attribution[state]['combined_white_stroke_count']})")

    # ---- 白图元 mask 矢量重建（两板）+ 落盘中间件 PNG ----
    masks = {}
    mask_meta = {}
    for state in ("applied", "prep1"):
        fm, sm, png_bytes, meta = _rebuild_white_masks(R4_BOTTOM_PDF[state])
        _guard_write_bytes(LAYERS_DIR / _mask_png_name(state), png_bytes)
        masks[state] = (fm, sm)
        mask_meta[state] = meta
        print(f"[r14b] mask 重建 {state}: fill={meta['mask_fill_pixel_count']}"
              f"px stroke={meta['mask_stroke_pixel_count']}px")

    # ---- r5 图加载 + 板界/裁剪参数活读 ----
    import json
    deriv = json.loads(DERIVATION_R5.read_text(encoding="utf-8"))
    images = {im["state_side"]: im for im in deriv["renders_r5"]["images"]}
    im0 = images["applied-bottom"]
    crop_x, crop_y = im0["crop_box"][0], im0["crop_box"][1]
    bounds = im0["board_px_bounds_full"]

    r5_bottoms = {}
    for state in ("applied", "prep1"):
        r5_bottoms[state] = _load_rgb(
            (R5_DIR / f"{state}-bottom.png").read_bytes())
    if r5_bottoms["applied"].tobytes() != r5_bottoms["prep1"].tobytes():
        _fail("r5 两张 bottom 非逐像素相同（与 D2 记录不符；证书点表复用"
              "前提破坏）")

    # ---- 覆盖率统计（板内白 = 白图元命中 + 空隙剩余）----
    coverage = {}
    for state in ("applied", "prep1"):
        fm, sm = masks[state]
        r5c = r5_bottoms[state]
        Wm = np.all(r5c == 255, axis=2)
        board = np.zeros(Wm.shape, dtype=bool)
        board[bounds["y0"] - crop_y: bounds["y1"] + 1 - crop_y,
              bounds["x0"] - crop_x: bounds["x1"] + 1 - crop_x] = True
        board_white = Wm & board
        any_ink_full = np.zeros((6003, 8195), dtype=bool)
        for layer in PROBE_LAYERS_BOTTOM:
            arr = _load_rgb((LAYERS_DIR
                             / _layer_png_name(state, layer)).read_bytes())
            any_ink_full |= _ink_alpha(arr) > 0
        any_ink_c = any_ink_full[crop_y:crop_y + r5c.shape[0],
                                 crop_x:crop_x + r5c.shape[1]]
        void = board & ~any_ink_c & ~(
            fm[crop_y:crop_y + r5c.shape[0],
               crop_x:crop_x + r5c.shape[1]]
            | sm[crop_y:crop_y + r5c.shape[0],
                 crop_x:crop_x + r5c.shape[1]])
        coverage[state] = {
            "r5_white_total": int(Wm.sum()),
            "board_region_white": int(board_white.sum()),
            "board_white_on_white_fill_mask": int((board_white
                                                   & fm[crop_y:crop_y
                                                        + r5c.shape[0],
                                                        crop_x:crop_x
                                                        + r5c.shape[1]]
                                                   ).sum()),
            "board_white_on_void_mask": int(void.sum()),
            "unaccounted_board_white": int(
                (board_white
                 & ~fm[crop_y:crop_y + r5c.shape[0],
                       crop_x:crop_x + r5c.shape[1]]
                 & ~void).sum()),
            "outside_board_white": int(Wm.sum() - board_white.sum()),
            "board_rect_full_page": [bounds["x0"], bounds["y0"],
                                     bounds["x1"], bounds["y1"]],
        }
        print(f"[r14b] 覆盖率 {state}: 板内白={coverage[state]['board_region_white']}"
              f" 图元命中={coverage[state]['board_white_on_white_fill_mask']}"
              f" 空隙={coverage[state]['board_white_on_void_mask']}"
              f" 未计入={coverage[state]['unaccounted_board_white']}")

    # ---- 证书点表（applied 板）----
    fm, sm = masks["applied"]
    layer_ink = {}
    for layer in PROBE_LAYERS_BOTTOM:
        arr = _load_rgb((LAYERS_DIR / _layer_png_name(
            "applied", layer)).read_bytes())
        layer_ink[layer] = _ink_alpha(arr) > 0
    certs = _certificate_points(r5_bottoms["applied"], crop_x, crop_y,
                                fm, sm, layer_ink)
    print(f"[r14b] 证书点 {len(certs)} 个全部命中预期")

    print(f"[r14b] probe 完成：10 次单层导出 + 矢量探针 + mask 重建；"
          f"kicad-cli {ver}")
    print("[r14b] recompute 提示：framing/render 从 layers/ 产物重算统计"
          "（纯函数）")


# ---------------------------------------------------------------------------
# framing（从 layers/ 产物重算探针统计的纯函数块）
# ---------------------------------------------------------------------------

def _probe_block() -> dict:
    """从 layers/ 产物重算全部探针统计（纯函数；probe/framing/render 共用）。"""
    import json
    deriv = json.loads(DERIVATION_R5.read_text(encoding="utf-8"))
    images = {im["state_side"]: im for im in deriv["renders_r5"]["images"]}
    im0 = images["applied-bottom"]
    crop_x, crop_y = im0["crop_box"][0], im0["crop_box"][1]
    bounds = im0["board_px_bounds_full"]

    per_layer = {}
    for state in ("applied", "prep1"):
        for layer in PROBE_LAYERS_BOTTOM:
            per_layer[f"{state}-bottom-{layer}"] = _probe_layer_stats(
                state, layer)

    combined_reports = {}
    single_reports = {}
    for state in ("applied", "prep1"):
        combined_reports[state] = _drawings_report(R4_BOTTOM_PDF[state])
        for layer in PROBE_LAYERS_BOTTOM:
            single_reports[f"{state}-bottom-{layer}"] = _drawings_report(
                LAYERS_DIR / _layer_pdf_name(state, layer))

    attribution = {}
    for state in ("applied", "prep1"):
        wf = {k: v["white_fill_count"] for k, v in single_reports.items()
              if v["white_fill_count"] > 0 and k.startswith(state)}
        ws = {k: v["white_stroke_count"] for k, v in single_reports.items()
              if v["white_stroke_count"] > 0 and k.startswith(state)}
        bcu = single_reports[f"{state}-bottom-B.Cu"]
        bmk = single_reports[f"{state}-bottom-B.Mask"]
        if set(wf) != {f"{state}-bottom-B.Cu", f"{state}-bottom-B.Mask"}:
            _fail(f"{state}: 白 fill 单层归因非 B.Cu∪B.Mask 双族：{wf}")
        if set(ws) != {f"{state}-bottom-B.Cu", f"{state}-bottom-B.Mask"}:
            _fail(f"{state}: 白 stroke 单层归因非 B.Cu∪B.Mask 双族：{ws}")
        if bcu["white_fill_bboxes_sorted"] != bmk["white_fill_bboxes_sorted"]:
            _fail(f"{state}: B.Cu 与 B.Mask 白 fill bbox 集合不一致")
        if (bcu["white_stroke_bboxes_sorted"]
                != bmk["white_stroke_bboxes_sorted"]):
            _fail(f"{state}: B.Cu 与 B.Mask 白 stroke bbox 集合不一致")
        if combined_reports[state]["white_fill_count"] != bcu[
                "white_fill_count"]:
            _fail(f"{state}: combined 白 fill 数 != 单层白 fill 数")
        for layer in ("B.Silkscreen", "B.Courtyard", "Edge.Cuts"):
            rep = single_reports[f"{state}-bottom-{layer}"]
            if rep["white_fill_count"] or rep["white_stroke_count"]:
                _fail(f"{state}-bottom-{layer} 出现白图元")
        attribution[state] = {
            "white_fill_counts_by_layer": wf,
            "white_stroke_counts_by_layer": ws,
            "bcu_bmask_white_fill_bboxes_identical": True,
            "bcu_bmask_white_stroke_bboxes_identical": True,
            "combined_white_fill_count":
                combined_reports[state]["white_fill_count"],
            "combined_white_stroke_count":
                combined_reports[state]["white_stroke_count"],
            "no_ocg_layer_marks":
                combined_reports[state]["ocg_layer_field_values"],
            "conclusion": (
                "白色墨水图元=B.Cu∪B.Mask 双族共享绘制（几何逐一同组；"
                "combined 仅绘一次、z 序在蓝/青之上）；"
                "B.Silkscreen/B.Courtyard/Edge.Cuts 族零白图元；"
                "PDF 无 OCG 层标记（归因只能靠单层导出对照）"),
        }

    masks = {}
    mask_meta = {}
    for state in ("applied", "prep1"):
        fm, sm, png_bytes, meta = _rebuild_white_masks(R4_BOTTOM_PDF[state])
        saved = LAYERS_DIR / _mask_png_name(state)
        if png_bytes != saved.read_bytes():
            _fail(f"mask 重建确定性失败：{saved.name}")
        masks[state] = (fm, sm)
        mask_meta[state] = meta

    r5_bottoms = {}
    for state in ("applied", "prep1"):
        r5_bottoms[state] = _load_rgb(
            (R5_DIR / f"{state}-bottom.png").read_bytes())
    r5_bottoms_equal = bool(r5_bottoms["applied"].tobytes()
                            == r5_bottoms["prep1"].tobytes())

    coverage = {}
    void_masks = {}
    for state in ("applied", "prep1"):
        fm, sm = masks[state]
        r5c = r5_bottoms[state]
        Wm = np.all(r5c == 255, axis=2)
        board = np.zeros(Wm.shape, dtype=bool)
        board[bounds["y0"] - crop_y: bounds["y1"] + 1 - crop_y,
              bounds["x0"] - crop_x: bounds["x1"] + 1 - crop_x] = True
        any_ink_full = np.zeros((6003, 8195), dtype=bool)
        for layer in PROBE_LAYERS_BOTTOM:
            arr = _load_rgb((LAYERS_DIR
                             / _layer_png_name(state, layer)).read_bytes())
            any_ink_full |= _ink_alpha(arr) > 0
        any_ink_c = any_ink_full[crop_y:crop_y + r5c.shape[0],
                                 crop_x:crop_x + r5c.shape[1]]
        fm_c = fm[crop_y:crop_y + r5c.shape[0],
                  crop_x:crop_x + r5c.shape[1]]
        sm_c = sm[crop_y:crop_y + r5c.shape[0],
                  crop_x:crop_x + r5c.shape[1]]
        # 空隙白 = 板界内 r5 纯白 且 非白图元 mask；两种口径都记录：
        #   strict：另要求无任何单层非白墨（纯背景空隙）
        #   final：不排除抗锯齿过渡白（成图用——保证板内白清零）
        board_white = Wm & board
        white_ink_mask = fm_c | sm_c
        void_final = board_white & ~white_ink_mask
        void_strict = board & ~any_ink_c & ~white_ink_mask
        void_masks[state] = void_final
        wm_full = fm | sm
        board_full = np.zeros((6003, 8195), dtype=bool)
        board_full[bounds["y0"]:bounds["y1"] + 1,
                   bounds["x0"]:bounds["x1"] + 1] = True
        coverage[state] = {
            "r5_white_total": int(Wm.sum()),
            "board_region_white": int(board_white.sum()),
            "board_white_on_white_ink_mask":
                int((board_white & white_ink_mask).sum()),
            "board_white_on_void_strict": int(void_strict.sum()),
            "board_white_on_void_final": int(void_final.sum()),
            "board_white_unaccounted_strict": int(
                (board_white & ~white_ink_mask & ~void_strict).sum()),
            "outside_board_white": int(Wm.sum() - board_white.sum()),
            "white_ink_mask_total_fullpage": int(wm_full.sum()),
            "white_ink_mask_outside_board_fullpage": int(
                (wm_full & ~board_full).sum()),
        }

    fm, sm = masks["applied"]
    layer_ink = {}
    for layer in PROBE_LAYERS_BOTTOM:
        arr = _load_rgb((LAYERS_DIR / _layer_png_name(
            "applied", layer)).read_bytes())
        layer_ink[layer] = _ink_alpha(arr) > 0
    certs = _certificate_points(r5_bottoms["applied"], crop_x, crop_y,
                                fm, sm, layer_ink)

    return {
        "per_layer_default_colors": per_layer,
        "vector_attribution": {
            "combined_reports": combined_reports,
            "single_layer_reports": single_reports,
            "attribution_table": attribution,
        },
        "white_mask_rebuild": mask_meta,
        "r5_bottoms_pixel_equal": r5_bottoms_equal,
        "board_white_coverage": coverage,
        "certificate_points": certs,
        "method_note": (
            "白色内容归属探针三通道：1) 单层导出光栅 alpha 通道（背景白与"
            "白墨不可分——如实声明局限）；2) PDF 矢量探针（fill/stroke 色"
            "族+z 序+白图元计数+单层归因对照，决定性通道）；3) 白图元矢量"
            "重建 mask 与 r5 板内白的覆盖率分解。无视觉判读。"),
        "_masks": masks,
        "_void": void_masks,
        "_crop": (crop_x, crop_y),
        "_bounds": [bounds["x0"], bounds["y0"], bounds["x1"], bounds["y1"]],
    }


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


def cmd_framing() -> None:
    _protected_check()
    _staging_check()
    refs = _r5_refs()
    deriv = refs.pop("_deriv")
    import json

    # r4 冻结 combined bottom PDF sha（从 framing-r5 活读并复核）
    framing5 = json.loads(FRAMING_R5.read_text(encoding="utf-8"))
    frozen_pdfs = {item["state_side"]: item for item
                   in framing5["frozen_inputs"]["r4_frozen_pdfs"]}
    r4_base = {}
    for state, path in R4_BOTTOM_PDF.items():
        want = frozen_pdfs[f"{state}-bottom"]["sha256"]
        got = _sha(path)
        if got != want:
            _fail(f"r4 冻结 base PDF sha 不符：{state}-bottom {got} != {want}")
        r4_base[state] = {"path_rel": frozen_pdfs[f"{state}-bottom"]["path_rel"],
                          "sha256": got}

    # r5 实测板界与裁剪基准（逐字活读）
    images = {im["state_side"]: im for im in deriv["renders_r5"]["images"]}
    expected = {}
    for state in ("applied", "prep1"):
        im = images[f"{state}-bottom"]
        expected[state] = {
            "full_page_wh": im["full_page_wh"],
            "board_px_bounds_full": [im["board_px_bounds_full"]["x0"],
                                     im["board_px_bounds_full"]["y0"],
                                     im["board_px_bounds_full"]["x1"],
                                     im["board_px_bounds_full"]["y1"]],
            "cropped_image_wh": im["image_wh"],
            "crop_box": im["crop_box"],
            "output_png_sha256_r5": im["sha256"],
        }

    if not FRAMING_R14_FALSIFIED.exists() or not WITNESS_R14_FALSIFIED.exists():
        _fail("首试证伪件缺失（framing-r14/witness-r14 须保留在案）")
    falsified = {rel: _sha(REPO / rel) for rel in FALSIFIED_R14}
    for rel, sha in falsified.items():
        if not sha.startswith(FALSIFIED_R14[rel]):
            _fail(f"首试证伪件哈希不符：{rel}")

    probe = _probe_block()
    cov = probe["board_white_coverage"]["applied"]
    cd = _color_distance_table()
    if not cd["all_above_threshold"]:
        _fail(f"色距断言失败：{cd}")

    doc = {
        "schema_version": "3.0",
        "kind": "tl2_calibration_render_framing_r14b_preregistration",
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
        "falsified_first_attempt_reference": {
            "framing_r14_sha256": falsified[
                "out/v3-tl2/calibration/render-framing-r14.json"],
            "witness_r14_sha256": falsified[
                "out/v3-tl2/calibration/render-witness-r14.json"],
            "falsification_record": (
                "首试（s50_render_r14.py）：探针实证 bottom 视 B.SilkS/"
                "B.CrtYd 自有图元为零（单层导出逐字节相同、墨水⊂Edge.Cuts "
                "墨水=跨层上下文剪影；板文件普查图元=0）⇒ B.Silkscreen/B."
                "Courtyard 预配色无着色目标，overlay 应用 0 像素，r14 成图"
                "与 renders-r5 逐字节相同（仪器零变更，如实记录在案）。"
                "本轮为第二次尝试：先探明白色内容真正归属层，再重定向配色。"),
        },
        "probe_finding": {
            "core_question": (
                "diag-r13-review D2：r5 bottom 合成图纯白 (255,255,255) "
                "1,185,926 px（29.5%）来自哪个单层导出？候选：B.Mask 开窗"
                "白绘 / B.Cu / Edge.Cuts / 跨层上下文剪影。"),
            "answer_multi_source": (
                "探针（像素+矢量双通道）实证：白色内容为双来源，任何单层"
                "独占归因不成立——"
                "(a) 白墨矢量图元：combined bottom PDF 含 162 个白 fill"
                "（焊盘钻孔圆盘，--drill-shape-opt 2）+4 个白 stroke（左上"
                "特区 4 个椭圆焊盘轮廓）；同一组几何（bbox 集合逐一相同）"
                "同时出现于 B.Cu 与 B.Mask 两层的单层导出 PDF（kicad 对 "
                "*.Cu/*.Mask 多层焊盘的共享绘制族）；combined 中该族仅绘"
                "一次、z 序在蓝/青之上；B.Silkscreen/B.Courtyard/Edge.Cuts"
                " 单层导出零白图元；PDF 无 OCG 层标记（layer 字段全空）。"
                "板内白被该族命中 73,050 px（r5 纯白域内）。"
                "(b) 板内背景空隙白 206,052 px（严格口径；final 口径 "
                "207,836 px 含抗锯齿过渡白）：板界内无任何单层非白墨、亦"
                "非白图元的纯白——铺铜 clearance 空隙（D2 的白描边环）、"
                "翼瓣形态、板框退让带、基准环缝。它是墨的缺失而非图元，"
                "无法归属到任何单层导出的绘制。"
                "⇒ D2「全部白色同一渲染图层族（>95%）」被证伪：白墨图元"
                "仅解释板内白的 26.0%，其余 74.0% 为背景空隙白。"),
            "board_white_decomposition_applied": cov,
            "attribution_table": probe["vector_attribution"][
                "attribution_table"],
            "certificate_points": probe["certificate_points"],
        },
        "single_variable_change": {
            "declaration": (
                "本轮相对 R5 只改变一个仪器变量：bottom 视白的显式配色"
                "（多重着色，探针事实驱动）——"
                "(a) 白墨矢量图元 mask（162 孔盘 fill+4 椭圆轮廓 stroke，"
                "归属=B.Cu∪B.Mask 双族共享绘制）→ 橙 (255,165,0)；"
                "(b) 板界内空隙白 mask（板内 r5 纯白且非白图元；语义=铺铜"
                "clearance/翼瓣空隙/板框退让带/基准环缝的基材露白）→ 绿 "
                "(0,128,0)。层清单/dpi/组合页/裁剪公式/页几何与 R5 逐字同"
                "口径；top 视两图零变更（逐字节拷贝自 renders-r5）。"),
            "multi_color_justification": (
                "红线 5（多重着色纪律）执行：白色内容分布在 B.Cu/B.Mask "
                "双族共享的白墨图元（几何同组、像素级不可再分层）+无墨背景"
                "空隙两类来源；对 (a) 双族共享的同一像素集合不存在逐层可分"
                "的两组像素，故按图元类别给橙一色并在 witness 如实记录双族"
                "归属；对 (b) 空隙白给绿一色。两类可区分色共同消除 bottom "
                "视全部板内歧义白。"),
            "color_mapping": {
                "white_ink_drawings": {
                    "target_rgb": list(TARGET_ORANGE),
                    "semantics": "焊盘钻孔圆盘+椭圆焊盘轮廓白填充（B.Cu∪"
                                 "B.Mask 双族共享）",
                },
                "board_void_white": {
                    "target_rgb": list(TARGET_GREEN),
                    "semantics": "板界内空隙白（铺铜 clearance/翼瓣空隙/"
                                 "板框退让带/基准环缝的基材露白；PCB 基材"
                                 "惯例色）",
                },
                "kept_layers": {
                    "B.Cu": "kicad 原配色不变",
                    "B.Mask": "kicad 原配色不变",
                    "Edge.Cuts": "kicad 原配色不变",
                    "B.Silkscreen": "kicad 原配色不变（自有图元=0，首试"
                                    "探针实证）",
                    "B.Courtyard": "kicad 原配色不变（自有图元=0，首试"
                                   "探针实证）",
                },
            },
            "color_distance_assertion": cd,
        },
        "synthesis_method": {
            "declaration": (
                "base=renders-r4 冻结 combined bottom PDF（r5 唯一图像来"
                "源，sha 复核）经 40pt 组合页+dpi640 光栅化；overlay1=橙，"
                "作用于白图元重建 mask（probe 矢量重建，黑底红 fill/绿 "
                "stroke PNG 落盘于 renders-r14b/layers/）；overlay2=绿，"
                "作用于板界内空隙白 mask（=板内 r5 纯白 且 非白图元 mask；"
                "与 overlay1 构造互斥）。两 overlay 均为二值 mask 全量替换"
                "（out[mask]=color；mask 阈值>127），不做 alpha 混合——"
                "孔盘边缘抗锯齿过渡像素随 mask 一并着色，板内歧义白清零。"
                "z 序=base→overlay1 橙→overlay2 绿（构造互斥，序无实质）。"),
            "z_order": ["base(combined B.Cu,B.Mask,B.Silkscreen,Edge.Cuts,"
                        "B.Courtyard)", "overlay1:white_ink_drawings→orange",
                        "overlay2:board_void_white→green"],
            "blend_math": "out[mask]=color（布尔 mask 全量替换；mask=重建"
                          "光栅通道 >127）",
            "base_inputs": r4_base,
            "determinism_scope": (
                "kicad-cli PDF 字节不做跨运行确定性断言（r4 实证：两板 "
                "PDF sha 不同而栅格逐字节同；probe 两次运行 PDF sha 亦不同"
                "而光栅 PNG 逐字节同）；确定性断言范围=PDF→栅格化→overlay"
                "→裁剪→PNG 字节全链重跑逐字节一致 + 单层栅格与 probe 落盘"
                "产物逐字节一致 + mask 重建与 probe 落盘产物逐字节一致。"),
        },
        "compose_and_crop_same_as_r5": {
            "dpi": RASTER_DPI,
            "compose_margin_pt": COMPOSE_MARGIN_PT,
            "crop_margin_px": CROP_MARGIN_PX,
            "crop_box_formula": "(x0-120, y0-120, x1+1+120, y1+1+120)，"
                                "(x0,y0,x1,y1)=dpi640 全页 "
                                "png_board_pixel_bounds 实测板界",
            "rasterization_tool": "PyMuPDF (fitz) get_pixmap(dpi=640, "
                                  "alpha=False) + PIL Image.crop/save('PNG')",
            "expected_from_r5_derivation_log": expected,
            "board_bounds_assertion": (
                "着色后合成页板界像素界须逐字等于 derivation-log-r5.json "
                "renders_r5.images[<state>-bottom].board_px_bounds_full"
                "（活读复核）；crop 后四侧白边须恰为 120px。着色仅作用于"
                "板界内白域，不移动非白 bbox。"),
        },
        "top_zero_change": {
            "declaration": (
                "renders-r14b/applied-top.png 与 prep1-top.png 自 renders-r5 "
                "逐字节拷贝（零重渲染）；sha256 见证见 witness。"),
            "source_sha256": {
                "applied-top": refs["renders_r5_png_sha256"]["applied-top"],
                "prep1-top": refs["renders_r5_png_sha256"]["prep1-top"],
            },
        },
        "palette_assertions": {
            "formulas": (
                "对每张 r14b bottom PNG：a) 橙 (255,165,0) 精确像素计数>0；"
                "b) 绿 (0,128,0) 精确像素计数>0；c) 橙绿零交集；d) 纯白"
                "像素数较 renders-r5 同名图显著下降（下降量入 witness）；"
                "e) 板界内纯白像素=0（板内歧义白清零）；f) 剩余纯白全部"
                "位于板界外（裁剪边距，仪器口径保留）——f 以程序化位置"
                "统计如实记录。"),
            "preregistered_prediction": {
                "direction_only_before_render": True,
                "orange_pixel_count_expected_approx":
                    cov["board_white_on_white_ink_mask"],
                "green_pixel_count_expected_approx":
                    cov["board_white_on_void_final"],
                "white_after_expected_approx":
                    cov["r5_white_total"]
                    - cov["board_region_white"],
                "prediction_basis": (
                    "探针实测：板内白 280,886 = 白图元命中 73,050 + 空隙"
                    "207,836（final 口径）⇒ 预测橙≈73,050、绿≈207,836、"
                    "白从 1,185,926 降至≈905,040（板外裁剪边距白，含 "
                    "120px 边距带）。方向断言先于成图落盘：橙>0、绿>0、"
                    "白显著下降、板内白清零。精确数字以成图后实测回填"
                    "（witness），不修改本预测字段。"),
            },
        },
        "fallback": {
            "board_bounds_fail": (
                "板界断言/裁剪 sanity 任一失败即停止并如实报告，不得静默"
                "改参数。"),
            "mask_mismatch": (
                "mask 重建或单层栅格与 probe 落盘产物非逐字节同即停止。"),
        },
        "freeze_order": {
            "declaration": (
                "本文件先于本轮任何官方成图落盘（probe→framing→render→"
                "witness）；renders-r14b/ 根目录四张 PNG 在本文件落盘时"
                "尚不存在；probe 仅产出 layers/ 中间件。"),
            "probe_artifacts_policy": (
                "probe 单层 PDF/PNG 与 mask PNG 为一次性中间件（kicad PDF"
                "字节不承诺跨运行等同）；render 重跑复用之并逐字节复核，"
                "不重导出。"),
        },
        "overwrite_guard": (
            "目标文件已存在非字节等同→FAIL；字节等同→幂等。"),
        "zero_write_discipline": (
            "out/ 既有文件零改动（staging-r4/renders-r4/renders-r5/"
            "renders-r14/derivation-log-r5.json/render-framing-r5.json/"
            "首试证伪件等只读）；datasets/ 零写入；pcbflow/ 与 tests/ "
            "零改动（仅 import）；活板文件全程只读（witness 收尾 sha "
            "见证）。新建范围=scripts/s51_render_r14b.py、renders-r14b/"
            "（含 layers/）、render-framing-r14b.json、"
            "render-witness-r14b.json。"),
        "protected_files_frozen_prefixes": PROTECTED,
        "probe_block": {k: v for k, v in probe.items()
                        if not k.startswith("_")},
        "input_board_witness": {
            "applied": STAGED_SHA_FROZEN["applied"],
            "prep1": STAGED_SHA_FROZEN["prep1"],
        },
    }
    sha, mode = _write_canonical_guarded(FRAMING_R14B, doc)
    print(f"[r14b] framing 落盘：render-framing-r14b.json sha256={sha[:16]}… "
          f"({mode})")
    print(f"[r14b] 预注册预测：橙≈{cov['board_white_on_white_ink_mask']}、"
          f"绿≈{cov['board_white_on_void_final']}、白→"
          f"≈{cov['r5_white_total'] - cov['board_region_white']}"
          f"（方向断言；精确数字成图后实测回填）")


# ---------------------------------------------------------------------------
# render
# ---------------------------------------------------------------------------

def cmd_render() -> None:
    _protected_check()
    _staging_check()
    refs = _r5_refs()
    deriv = refs.pop("_deriv")
    import json
    if not FRAMING_R14B.exists():
        _fail("render-framing-r14b.json 缺失（先落盘 framing）")
    framing_sha_start = _sha(FRAMING_R14B)
    framing = json.loads(FRAMING_R14B.read_text(encoding="utf-8"))
    ver = _kicad_version()

    if WITNESS_R14B.exists():
        for name in FINAL_PNGS:
            if not (R14B_DIR / f"{name}.png").exists():
                _fail("render-witness-r14b.json 已存在但成图不全（状态不一致）")

    expected = framing["compose_and_crop_same_as_r5"][
        "expected_from_r5_derivation_log"]
    orange = np.array(framing["single_variable_change"]["color_mapping"]
                      ["white_ink_drawings"]["target_rgb"], dtype=np.uint8)
    green = np.array(framing["single_variable_change"]["color_mapping"]
                     ["board_void_white"]["target_rgb"], dtype=np.uint8)

    # probe 中间件复核 + 单层栅格确定性 + mask 重建确定性
    for state in ("applied", "prep1"):
        for layer in PROBE_LAYERS_BOTTOM:
            pdf = LAYERS_DIR / _layer_pdf_name(state, layer)
            if not pdf.exists():
                _fail(f"probe 中间件缺失：{pdf.name}（先跑 probe）")
            png_bytes, _, _ = _compose_raster(pdf)
            saved = LAYERS_DIR / _layer_png_name(state, layer)
            if png_bytes != saved.read_bytes():
                _fail(f"单层栅格确定性失败：{saved.name}")
        fm, sm, mask_bytes, _ = _rebuild_white_masks(R4_BOTTOM_PDF[state])
        saved_mask = LAYERS_DIR / _mask_png_name(state)
        if mask_bytes != saved_mask.read_bytes():
            _fail(f"mask 重建确定性失败：{saved_mask.name}")

    probe = _probe_block()
    masks, void_masks, (crop_x, crop_y) = (probe["_masks"], probe["_void"],
                                           probe["_crop"])
    bounds_ref = probe["_bounds"]
    del probe

    R14B_DIR.mkdir(parents=True, exist_ok=True)
    results = {}
    determinism = {}
    for state in ("applied", "prep1"):
        base_pdf = R4_BOTTOM_PDF[state]
        want = framing["synthesis_method"]["base_inputs"][state]["sha256"]
        if _sha(base_pdf) != want:
            _fail(f"base PDF sha 不符 framing：{state} {_sha(base_pdf)}")

        def build(state=state):
            fm, sm = masks[state]
            void = void_masks[state]
            # 着色语义=板界内的白色内容；板界外（画布边距）零着色
            board_full = np.zeros((6003, 8195), dtype=bool)
            board_full[bounds_ref[1]:bounds_ref[3] + 1,
                       bounds_ref[0]:bounds_ref[2] + 1] = True
            png_full, pw, ph = _compose_raster(base_pdf)
            arr = _load_rgb(png_full)
            arr_c = arr[crop_y:crop_y + void.shape[0],
                        crop_x:crop_x + void.shape[1]]
            pre_white = int(np.all(arr_c == 255, axis=2).sum())
            # overlay1：白图元 mask → 橙（限板界内）
            sel_o = (fm | sm) & board_full
            arr[sel_o] = orange
            # overlay2：板内空隙白 mask → 绿（cropped 坐标系作用）
            arr_c2 = arr[crop_y:crop_y + void.shape[0],
                         crop_x:crop_x + void.shape[1]]
            arr_c2[void] = green
            full2 = Image_fromarray(arr)
            bio = io.BytesIO()
            full2.save(bio, "PNG")
            full_bytes = bio.getvalue()
            b = _bounds_of(full_bytes)
            box = (b["x0"] - CROP_MARGIN_PX, b["y0"] - CROP_MARGIN_PX,
                   b["x1"] + 1 + CROP_MARGIN_PX, b["y1"] + 1 + CROP_MARGIN_PX)
            from PIL import Image
            im = Image.open(io.BytesIO(full_bytes))
            cropped = im.crop(box)
            bio2 = io.BytesIO()
            cropped.save(bio2, "PNG")
            return (full_bytes, b, box, bio2.getvalue(), (pw, ph),
                    pre_white)

        full_bytes, bounds_got, box, crop_bytes, pix_wh, pre_white = build()

        # 板界断言（=derivation-log-r5 实测值，逐字；着色不得移动 bbox）
        exp = expected[state]["board_px_bounds_full"]
        got = [bounds_got["x0"], bounds_got["y0"],
               bounds_got["x1"], bounds_got["y1"]]
        if got != exp:
            _fail(f"{state} 板界断言失败：着色后 {got} != r5 实测 {exp}")
        if [pix_wh[0], pix_wh[1]] != expected[state]["full_page_wh"]:
            _fail(f"{state} 全页尺寸断言失败：{pix_wh} != "
                  f"{expected[state]['full_page_wh']}")

        out_path = R14B_DIR / f"{state}-bottom.png"
        mode = _guard_write_bytes(out_path, crop_bytes)

        # 程序化断言（客观数字）
        carr = _load_rgb(crop_bytes)
        r5arr = _load_rgb((R5_DIR / f"{state}-bottom.png").read_bytes())
        orange_m = np.all(carr == orange, axis=2)
        green_m = np.all(carr == green, axis=2)
        white_after_m = np.all(carr == 255, axis=2)
        white_after = int(white_after_m.sum())
        white_r5 = int(np.all(r5arr == 255, axis=2).sum())
        total = int(carr.shape[0] * carr.shape[1])
        bx0, by0 = expected[state]["board_px_bounds_full"][0] - crop_x, \
            expected[state]["board_px_bounds_full"][1] - crop_y
        bx1, by1 = expected[state]["board_px_bounds_full"][2] - crop_x, \
            expected[state]["board_px_bounds_full"][3] - crop_y
        board_m = np.zeros(white_after_m.shape, dtype=bool)
        board_m[by0:by1 + 1, bx0:bx1 + 1] = True
        white_in_board_after = int((white_after_m & board_m).sum())
        white_outside = white_after - white_in_board_after
        assertions_pass = bool(int(orange_m.sum()) > 0
                               and int(green_m.sum()) > 0
                               and int((orange_m & green_m).sum()) == 0
                               and white_after < white_r5
                               and white_in_board_after == 0)
        results[state] = {
            "output_png_rel": f"out/v3-tl2/calibration/renders-r14b/"
                              f"{state}-bottom.png",
            "sha256": _sha(out_path),
            "bytes": out_path.stat().st_size,
            "image_wh": list(_png_size(crop_bytes)),
            "full_page_bounds_after_overlay": got,
            "full_page_bounds_expected_r5": exp,
            "full_page_wh_asserted": expected[state]["full_page_wh"],
            "crop_box": list(box),
            "base_pre_overlay_white_cropped": pre_white,
            "palette": {
                "orange_exact_count": int(orange_m.sum()),
                "green_exact_count": int(green_m.sum()),
                "orange_green_mix_count": int((orange_m & green_m).sum()),
                "white_pixel_count_r14b": white_after,
                "white_pixel_count_r5": white_r5,
                "white_reduction": white_r5 - white_after,
                "white_fraction_r14b": round(white_after / total, 8),
                "white_fraction_r5": round(white_r5 / total, 8),
                "white_in_board_after": white_in_board_after,
                "white_outside_board_after": white_outside,
                "assertions_pass": assertions_pass,
                "assertion_note": (
                    "预注册方向断言：橙>0、绿>0、橙绿零交集、白较 r5 显著"
                    "下降、板内白清零；剩余白=板外裁剪边距（仪器口径）"
                    "——以 white_outside_board_after 记录。"),
            },
        }
        print(f"[r14b] render {state}-bottom.png {results[state]['bytes']}B "
              f"{results[state]['image_wh']} 板界(全页){got} "
              f"橙={results[state]['palette']['orange_exact_count']} "
              f"绿={results[state]['palette']['green_exact_count']} "
              f"白 {white_r5}→{white_after} 断言={assertions_pass}")
        determinism[state] = build

    # 确定性自证：全链重跑逐字节一致
    det = {}
    for state in ("applied", "prep1"):
        again = determinism[state]()
        det[state] = again[3] == (R14B_DIR / f"{state}-bottom.png").read_bytes()
        if not det[state]:
            _fail(f"确定性自证失败：{state} 重跑非逐字节同")
    print(f"[r14b] 确定性自证：重跑全链逐字节一致={det}")

    # top 零变更拷贝（逐字节+哈希见证）
    tops = {}
    for name in ("applied-top", "prep1-top"):
        src = R5_DIR / f"{name}.png"
        data = src.read_bytes()
        if _sha(src) != framing["top_zero_change"]["source_sha256"][name]:
            _fail(f"r5 top 源 sha 不符 framing：{name}")
        mode = _guard_write_bytes(R14B_DIR / f"{name}.png", data)
        tops[name] = {"sha256": _sha(src), "bytes": len(data),
                      "source_rel": f"out/v3-tl2/calibration/renders-r5/"
                                    f"{name}.png"}
        print(f"[r14b] top 拷贝 {name}.png {len(data)}B ({mode})")

    # framing 运行期间零改动复核 + 收工复核
    if _sha(FRAMING_R14B) != framing_sha_start:
        _fail("render-framing-r14b.json 在 render 期间变动（冻结纪律破坏）")
    protected_end = _protected_check()
    staging_end = _staging_check()
    refs_end = _r5_refs()
    refs_end.pop("_deriv")

    pal = results["applied"]["palette"]
    doc = {
        "schema_version": "3.0",
        "kind": "tl2_calibration_render_witness_r14b",
        "round_label": ROUND_LABEL,
        "round_id_constant": ROUND_ID,
        "date_constant": DATE_CONSTANT,
        "domain_id": DOMAIN_ID,
        "no_visual_reading": True,
        "instrument": (
            f"kicad-cli {KICAD_VERSION} pcb export pdf（probe 单层导出）+ "
            "PyMuPDF get_pixmap(dpi=640, alpha=False) 40pt 组合页光栅化 + "
            "fitz Shape 白图元矢量重建 + PIL crop/save；base=renders-r4 "
            "冻结 combined bottom PDF（预注册=render-framing-r14b.json）"),
        "kicad_cli_version": ver,
        "framing": {
            "path_rel": "out/v3-tl2/calibration/render-framing-r14b.json",
            "sha256": framing_sha_start,
            "unchanged_during_render": True,
        },
        "falsified_first_attempt_reference": {
            "framing_r14_sha256": _sha(FRAMING_R14_FALSIFIED),
            "witness_r14_sha256": _sha(WITNESS_R14_FALSIFIED),
            "relationship": (
                "首试仪器零变更（证伪）在案；本轮先探明白色内容归属（双来"
                "源）再重定向配色，产出与 r5 有实质差异的渲染件。"),
        },
        "protected_files": {
            "at_start": _protected_check(),
            "at_end": protected_end,
        },
        "staging_and_live_boards": {
            "at_start": _staging_check(),
            "at_end": staging_end,
            "zero_write_declaration": (
                "staging-r4 与活板全程只读；probe 导出输入=staging-r4 逐字"
                "节冻结拷贝。"),
        },
        "r5_references": refs_end,
        "probe_artifacts": {
            "layers_dir_rel": "out/v3-tl2/calibration/renders-r14b/layers",
            "layer_png_sha256": {
                f"{s}-bottom-{l}": _sha(LAYERS_DIR / _layer_png_name(s, l))
                for s in ("applied", "prep1")
                for l in PROBE_LAYERS_BOTTOM},
            "white_mask_png_sha256": {
                s: _sha(LAYERS_DIR / _mask_png_name(s))
                for s in ("applied", "prep1")},
            "probe_block": framing["probe_block"],
        },
        "color_mapping": framing["single_variable_change"]["color_mapping"],
        "renders": results,
        "top_zero_change_copies": tops,
        "determinism_rerun_byte_identical": det,
        "determinism_scope": framing["synthesis_method"]["determinism_scope"],
        "palette_assertion_summary": {s: results[s]["palette"]
                                      for s in results},
        "conclusion": (
            "探针（像素+矢量双通道）实证白色内容双来源：(a) 白墨矢量图元"
            "162 fill+4 stroke=B.Cu∪B.Mask 双族共享绘制（几何同组；"
            "B.SilkS/B.CrtYd/Edge.Cuts 族零白图元；combined 仅绘一次、z 序"
            "在蓝/青之上；无 OCG）；(b) 板界内空隙白 206,052 px（严格口径）"
            "=无任何单层墨的背景白（铺铜 clearance 翼瓣空隙/板框退让带/"
            "基准环缝）——D2「全部白色同一图层族>95%」证伪（白墨图元仅解"
            "释板内白 26.0%）。多重着色执行：白图元→橙 (255,165,0)、板内"
            f"空隙白→绿 (0,128,0)。成图实测：橙={pal['orange_exact_count']}、"
            f"绿={pal['green_exact_count']}、白 {pal['white_pixel_count_r5']}"
            f"→{pal['white_pixel_count_r14b']}（板内白清零="
            f"{pal['white_in_board_after'] == 0}；剩余白=板外裁剪边距），"
            "板界断言=r5 实测值逐字相同，确定性自证逐字节一致。r14b bottom "
            "与 r5 具有实质仪器差异（板内歧义白全部消除、层语义可判读）。"),
        "degradation": None,
    }
    sha, mode = _write_canonical_guarded(WITNESS_R14B, doc)
    print(f"[r14b] witness 落盘：render-witness-r14b.json sha256={sha[:16]}… "
          f"({mode})")


def _bounds_of(png_bytes: bytes) -> dict:
    return calibration.png_board_pixel_bounds(png_bytes)


def Image_fromarray(arr):
    from PIL import Image
    return Image.fromarray(arr, "RGB")


def main() -> None:
    step = sys.argv[1] if len(sys.argv) > 1 else ""
    if step == "probe":
        cmd_probe()
    elif step == "framing":
        cmd_framing()
    elif step == "render":
        cmd_render()
    else:
        _fail("用法：s51_render_r14b.py probe|framing|render")


if __name__ == "__main__":
    main()

