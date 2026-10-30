#!/usr/bin/env python
"""R14 渲染实施者：bottom 视分层着色仪器变更轮（只渲染；不写 prep-record、
不盲读、不 close、不写轮测试）。

背景：diag-r13-review D1-D3 提出 bottom 视多语义压成同一纯白→层语义不可判；
用户拍板路线 A（占位轮廓层与焊盘体可区分颜色）：bottom 视 B.Silkscreen→丝印黄、
B.Courtyard→洋红，其余层保持 kicad 原配色，其余一切与 r5 逐字同口径。

本脚本三步（库侧 pcbflow/* 零改动零新增，只 import）：

  probe    对 staging-r4 两板做 12 次单层 kicad-cli 导出（bottom 5 层 ×2 板
           --mirror + applied 板 F.Silkscreen/F.Courtyard 2 層种子归层导出），
           逐层 fitz dpi640 组合页光栅化 → renders-r14/layers/；统计每层默认
           主色（非背景像素 RGB 众数）与 own-mask 证据（silk/court 导出栅格
           是否逐字节相同、其墨水是否为 Edge.Cuts 墨水子集=kicad 跨层上下文）；
           从 renders-r5/applied-top.png 程序化采样目标 RGB（丝印黄/洋红众数）。
           纯客观像素统计，无视觉判读。
  framing  落盘 render-framing-r14.json（canonical JSON，先于任何官方成图）：
           单变量仪器变更声明、层→颜色映射表（实测 RGB）、合成方法声明
           （r4 冻结 combined PDF 为 base + 指定色 overlay + z 序 + 上下文
           归属规则）、页几何与 r5 同口径声明（dpi640/40pt 组合/裁板界
           +120px 公式/板界断言=derivation-log-r5 实测值）、top 零变更声明
           （逐字节拷贝+哈希见证）、空层 fallback 与调色板断言预注册预测、
           freeze 顺序声明。
  render   按 framing 执行：r4 冻结 bottom PDF（sha 复核）→ dpi640 组合页
           光栅化 → own-mask overlay（空则按 fallback 跳过+witness 记录）→
           板界实测断言（=r5 记录值）→ r5 公式裁剪 → renders-r14/ 两张
           bottom PNG（硬断言与 renders-r5 同名件逐字节同=r5 同口径证明）；
           r5 top 两张逐字节拷贝+哈希见证；调色板断言（客观数字，如实记录
           pass/fail）；确定性自证（栅格化→overlay→裁剪全链重跑逐字节一致
           + 单层栅格与 probe 产物逐字节一致）；render-witness-r14.json。

纪律：确定性纯函数（同输入重跑字节等同）；日期/轮次=声明常量；canonical
JSON=pcbflow.hashing.canonical_json_bytes、hash=sha256_file；kicad-cli 调用
照 s29 模式（绝对路径+存在性验证+subprocess.run cwd=REPO；渲染脚本的
subprocess 豁免同理），除 kicad-cli 外零其他 subprocess/网络/wall-clock；
受保护文件（cli.py/config.py/toolchain_lock.json）与 staging-r4/datasets/
out/ 既有文件零改动；防覆写 guard（已存在非字节等同→FAIL，等同→幂等）。

用法：python scripts/s50_render_r14.py probe|framing|render
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
R14_DIR = CAL_DIR / "renders-r14"
LAYERS_DIR = R14_DIR / "layers"
FRAMING_R14 = CAL_DIR / "render-framing-r14.json"
WITNESS_R14 = CAL_DIR / "render-witness-r14.json"
STAGING_R4 = CAL_DIR / "staging-r4"
R4_DIR = CAL_DIR / "renders-r4"
R5_DIR = CAL_DIR / "renders-r5"
FRAMING_R5 = CAL_DIR / "render-framing-r5.json"
DERIVATION_R5 = CAL_DIR / "derivation-log-r5.json"
LIVE_BOARDS = {
    "applied": REPO / "out" / "revc-asm" / "board" / "applied.kicad_pcb",
    "prep1": REPO / "out" / "revc-asm" / "board" / "_pre-p1-batch-1.kicad_pcb",
}

DATE_CONSTANT = "2026-09-08"
ROUND_ID = "2026-09-08-r14"
ROUND_LABEL = "r14"
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
#: 种子归层导出（applied 板 top 视，无 mirror）：目标色归层证据
SEED_LAYERS_TOP = ("F.Silkscreen", "F.Courtyard")

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

#: r4 冻结 bottom PDF（base 图像来源；sha 记录于 render-framing-r5.json
#: frozen_inputs，本脚本从该文件活读并复核，不硬编码）
R4_BOTTOM_PDF = {
    "applied": R4_DIR / "applied-bottom.pdf",
    "prep1": R4_DIR / "prep1-bottom.pdf",
}

FINAL_PNGS = ("applied-bottom", "prep1-bottom", "applied-top", "prep1-top")

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
#: 目标色采样容差（Chebyshev 距离，8/255；framing 声明）
TARGET_TOL = 8


def _fail(msg: str) -> None:
    print(f"[r14] FAIL: {msg}")
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
    """kicad-cli 2D PDF 导出（照 s29 模式：绝对路径执行、cwd=REPO、
    命令逐字记录时以 'kicad-cli' 开头）。"""
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
    """fitz 组合页光栅化（与 r5 逐字同口径）：40pt 白边组合页 + dpi640。
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
            pix = page.get_pixmap(dpi=RASTER_DPI, alpha=False)
            return pix.tobytes("png"), pix.width, pix.height
        finally:
            out.close()
    finally:
        src.close()


def _load_rgb(png_bytes: bytes) -> "np.ndarray":
    from PIL import Image
    im = Image.open(io.BytesIO(png_bytes))
    return np.asarray(im.convert("RGB"))


def _ink_alpha(arr: "np.ndarray") -> "np.ndarray":
    """墨水量 alpha=255−min(R,G,B)（uint8；白背景→0，任何非白墨→>0）。
    纯函数，整数运算，确定性。"""
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


def _mode_near(arr: "np.ndarray", seed, tol: int) -> dict:
    """arr 中与 seed Chebyshev 距离 ≤tol 的像素的精确 RGB 众数。"""
    d = np.max(np.abs(arr.astype(np.int16) - np.array(seed, dtype=np.int16)),
               axis=2)
    sel = arr[d <= tol]
    if sel.shape[0] == 0:
        return {"seed_rgb": list(seed), "tolerance": tol,
                "pixel_count": 0, "mode_rgb": None, "mode_count": 0}
    colors, counts = np.unique(sel.reshape(-1, 3), axis=0, return_counts=True)
    i = int(np.argmax(counts))
    return {"seed_rgb": list(seed), "tolerance": tol,
            "pixel_count": int(sel.shape[0]),
            "mode_rgb": [int(v) for v in colors[i]],
            "mode_count": int(counts[i])}


def _layer_png_name(state: str, side: str, layer: str) -> str:
    return f"{state}-{side}-{layer.replace('.', '_')}.png"


def _layer_pdf_name(state: str, side: str, layer: str) -> str:
    return f"{state}-{side}-{layer.replace('.', '_')}.pdf"


def _probe_layer_stats(state: str, side: str, layer: str) -> dict:
    """从 layers/ 已落盘单层 PNG 重算统计（纯函数；probe/framing/render
    三处共用同一实现保证口径一致）。"""
    png_path = LAYERS_DIR / _layer_png_name(state, side, layer)
    arr = _load_rgb(png_path.read_bytes())
    alpha = _ink_alpha(arr)
    ink_count = int((alpha > 0).sum())
    total = int(arr.shape[0] * arr.shape[1])
    return {
        "state": state, "side": side, "layer": layer,
        "png_rel": f"out/v3-tl2/calibration/renders-r14/layers/"
                   f"{_layer_png_name(state, side, layer)}",
        "width": int(arr.shape[1]), "height": int(arr.shape[0]),
        "ink_pixel_count": ink_count,
        "ink_fraction": round(ink_count / total, 8),
        "dominant_colors": _dominant_colors(arr, alpha),
        "_arr": arr, "_alpha": alpha,
    }


def _own_mask_evidence() -> dict:
    """B.Silkscreen/B.Courtyard own-mask 证据（纯客观像素统计）：
    context := B.Silkscreen 单层导出墨水（板文件普查 B.SilkS 件数=0 的
    佐证下，该导出墨水 100% 为 kicad 跨层上下文：168 个 *.Cu/*.Mask 多层
    焊盘剪影+板框）；own(L) = ink(L) 且 非context。逐层加载不驻留。"""
    silk = _probe_layer_stats("applied", "bottom", "B.Silkscreen")
    silk_arr, silk_ink = silk.pop("_arr"), silk.pop("_alpha") > 0
    court = _probe_layer_stats("applied", "bottom", "B.Courtyard")
    court_arr, court_ink = court.pop("_arr"), court.pop("_alpha") > 0
    edge = _probe_layer_stats("applied", "bottom", "Edge.Cuts")
    edge_ink = edge.pop("_alpha") > 0
    raster_equal_silk_court = bool(np.array_equal(silk_arr, court_arr))
    silk_outside_edge = int((silk_ink & ~edge_ink).sum())
    court_outside_edge = int((court_ink & ~edge_ink).sum())
    own_silk = (int((silk_ink & ~court_ink).sum())
                if not raster_equal_silk_court else 0)
    own_court = (int((court_ink & ~silk_ink).sum())
                 if not raster_equal_silk_court else 0)
    return {
        "silk_court_rasters_byte_equal": raster_equal_silk_court,
        "silk_ink_subset_of_edge_ink": silk_outside_edge == 0,
        "silk_ink_pixels_outside_edge_ink": silk_outside_edge,
        "court_ink_pixels_outside_edge_ink": court_outside_edge,
        "own_mask_counts": {
            "B.Silkscreen": own_silk,
            "B.Courtyard": own_court,
        },
        "context_rule": ("own(L)=ink(L) 减另一语义层 ink（两导出逐字节相同"
                         "⇒ own 双零）；且 silk ink ⊆ Edge.Cuts ink（上下文"
                         "实证）。own-mask 与 combined 栅格像素对齐（同一"
                         "组合页/dpi/--mirror 口径）。"),
    }


def _board_census() -> dict:
    """两板 B 侧 silk/courtyard 图元件数普查（字符串计数+解释锚定）。"""
    out = {}
    for state, path in STAGED.items():
        txt = path.read_text(encoding="utf-8")
        out[state] = {
            "token_counts": {
                "B.SilkS": txt.count("B.SilkS"),
                "B.CrtYd": txt.count("B.CrtYd"),
                "F.SilkS": txt.count("F.SilkS"),
                "F.CrtYd": txt.count("F.CrtYd"),
                "*.Cu": txt.count("*.Cu"),
                "*.Mask": txt.count("*.Mask"),
            },
            "note": ("板文件 layers 表自身含每个层名 1 次 ⇒ B.SilkS/B.CrtYd "
                     "计数=1 表示零图元（对照 F.SilkS=512/F.CrtYd=173）；"
                     "*.Cu/*.Mask=168 个多层焊盘（跨层上下文来源）。"),
        }
    return out


def _sample_targets_from_r5_top() -> dict:
    """目标 RGB 程序化采样：种子=applied 板 F.Silkscreen/F.Courtyard 单层
    导出 **own-mask** 主色（own=该层导出墨水减另一语义层导出墨水——排除
    kicad 跨层上下文剪影；与 bottom own-mask 同一规则），在 renders-r5/
    applied-top.png 内取容差内众数。"""
    top_png = (R5_DIR / "applied-top.png").read_bytes()
    top_arr = _load_rgb(top_png)
    targets = {}
    pair = {}
    for layer in SEED_LAYERS_TOP:
        st = _probe_layer_stats("applied", "top", layer)
        pair[layer] = (st["_arr"], st["_alpha"] > 0)
    for layer, key in (("F.Silkscreen", "silkscreen_yellow"),
                       ("F.Courtyard", "courtyard_magenta")):
        other = "F.Courtyard" if layer == "F.Silkscreen" else "F.Silkscreen"
        arr, ink = pair[layer]
        _, other_ink = pair[other]
        own = ink & ~other_ink
        own_px = arr[own]
        if own_px.shape[0] == 0:
            _fail(f"目标色归层失败：{layer} own-mask 为空")
        colors, counts = np.unique(own_px.reshape(-1, 3), axis=0,
                                   return_counts=True)
        i = int(np.argmax(counts))
        seed = [int(v) for v in colors[i]]
        m = _mode_near(top_arr, seed, TARGET_TOL)
        if m["mode_rgb"] is None:
            _fail(f"目标色采样失败：{layer} 种子 {seed} 在 renders-r5/"
                  f"applied-top.png 容差 {TARGET_TOL} 内零像素")
        targets[key] = {
            "layer_semantic": layer,
            "seed_method": ("own-mask 主色（own=该层单层导出墨水减另一语义层"
                            "导出墨水；排除 kicad 跨层上下文剪影）"),
            "own_mask_pixel_count": int(own.sum()),
            "seed_single_layer_dominant_rgb": seed,
            "sampled_from": "out/v3-tl2/calibration/renders-r5/applied-top.png",
            **m,
        }
    return targets


# ---------------------------------------------------------------------------
# probe
# ---------------------------------------------------------------------------

def cmd_probe() -> None:
    _protected_check()
    _staging_check()
    ver = _kicad_version()
    for name in FINAL_PNGS:
        if (R14_DIR / f"{name}.png").exists():
            _fail(f"renders-r14/{name}.png 已存在（probe 拒绝在官方成图后运行）")
    if LAYERS_DIR.exists() and any(LAYERS_DIR.glob("*.pdf")):
        _fail("renders-r14/layers/ 已有 PDF（防覆写；重跑请先清理该目录）")

    plan = []
    for state in ("applied", "prep1"):
        for layer in PROBE_LAYERS_BOTTOM:
            plan.append((state, "bottom", layer, True))
    for layer in SEED_LAYERS_TOP:
        plan.append(("applied", "top", layer, False))

    LAYERS_DIR.mkdir(parents=True, exist_ok=True)
    exports = []
    for state, side, layer, mirror in plan:
        pdf_rel = (f"out/v3-tl2/calibration/renders-r14/layers/"
                   f"{_layer_pdf_name(state, side, layer)}")
        cmd = _run_kicad_export(pdf_rel, STAGED_REL[state],
                                layer, mirror)
        png_bytes, pw, ph = _compose_raster(REPO / pdf_rel)
        png_rel = (f"out/v3-tl2/calibration/renders-r14/layers/"
                   f"{_layer_png_name(state, side, layer)}")
        _guard_write_bytes(REPO / png_rel, png_bytes)
        exports.append({
            "state": state, "side": side, "layer": layer, "mirror": mirror,
            "pdf_rel": pdf_rel, "png_rel": png_rel,
            "pdf_sha256": _sha(REPO / pdf_rel),
            "png_sha256": _sha(REPO / png_rel),
            "pixmap_wh": [pw, ph],
            "command": cmd, "command_cwd": "repo_root",
        })
        print(f"[r14] probe 导出 {state}-{side}-{layer}: "
              f"pdf_sha={exports[-1]['pdf_sha256'][:8]}… pix={pw}x{ph}")

    print(f"[r14] probe 完成：{len(exports)} 次单层导出；kicad-cli {ver}")
    print("recompute 提示：framing/render 从 layers/ 产物重算统计（纯函数）")


# ---------------------------------------------------------------------------
# framing
# ---------------------------------------------------------------------------

def _layer_stats_serializable(state: str, side: str, layer: str) -> dict:
    st = _probe_layer_stats(state, side, layer)
    st.pop("_arr")
    st.pop("_alpha")
    return st


def _probe_block() -> dict:
    """从 layers/ 产物重算全部探针统计（纯函数；逐层处理不驻留大数组）。"""
    bottom_block = {}
    for state in ("applied", "prep1"):
        for layer in PROBE_LAYERS_BOTTOM:
            bottom_block[f"{state}-bottom-{layer}"] = _layer_stats_serializable(
                state, "bottom", layer)
    evidence = _own_mask_evidence()
    census = _board_census()
    targets = _sample_targets_from_r5_top()
    return {
        "per_layer_default_colors": bottom_block,
        "own_mask_evidence": evidence,
        "board_file_census": census,
        "target_color_sampling": targets,
        "method_note": ("每层主色=单层导出 dpi640 组合页栅格非背景像素"
                        "（alpha=255−min(R,G,B)>0）精确 RGB 众数；无视觉判读。"),
    }


def cmd_framing() -> None:
    _protected_check()
    _staging_check()
    refs = _r5_refs()
    deriv = refs.pop("_deriv")

    # r4 冻结 bottom PDF sha（从 framing-r5 活读并复核）
    frozen_pdfs = {item["state_side"]: item for item
                   in json_loads(FRAMING_R5)["frozen_inputs"]
                   ["r4_frozen_pdfs"]}
    r4_base = {}
    for state, path in R4_BOTTOM_PDF.items():
        want = frozen_pdfs[f"{state}-bottom"]["sha256"]
        got = _sha(path)
        if got != want:
            _fail(f"r4 冻结 base PDF sha 不符：{state}-bottom {got} != {want}")
        r4_base[state] = {"path_rel": frozen_pdfs[f"{state}-bottom"]["path_rel"],
                          "sha256": got}

    # r5 实测板界（全页）与裁剪后板界（断言基准，逐字读取）
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
            "board_px_bounds_cropped": [im["board_px_bounds"]["x0"],
                                        im["board_px_bounds"]["y0"],
                                        im["board_px_bounds"]["x1"],
                                        im["board_px_bounds"]["y1"]],
            "output_png_sha256_r5": im["sha256"],
        }

    probe = _probe_block()
    own = probe["own_mask_evidence"]["own_mask_counts"]
    targets = probe["target_color_sampling"]

    doc = {
        "schema_version": "3.0",
        "kind": "tl2_calibration_render_framing_r14_preregistration",
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
        "revision_note": (
            "本文件为修订重写（先于本轮任何官方成图，成图未开始）：首写版"
            "（sha256 前缀 7eaab9335a3385e1，写后即删）将 B.Courtyard 目标色"
            "误采样为 (0,0,0)——原因=种子取自单层导出全墨水主色，被 kicad "
            "跨层上下文剪影（黑色焊盘圆盘，像素数多于洋红描边）污染；修订="
            "种子改取 own-mask（该层墨水减另一语义层墨水，排除上下文）主色。"
            "修订仅动目标色采样过程，其余声明不变。"),
        "single_variable_change": {
            "declaration": (
                "本轮相对 R5 只改变一个仪器变量：bottom 视 B.Silkscreen 与 "
                "B.Courtyard 的显式配色（路线 A，用户 2026-09-08 拍板：占位"
                "轮廓层与焊盘体可区分颜色）。层清单/dpi/组合页/裁剪公式/页"
                "几何与 R5 逐字同口径；top 视两图零变更（逐字节拷贝自 "
                "renders-r5）。"),
            "probe_finding": (
                "探针实证：两板 B.Silkscreen 与 B.Courtyard 单层导出栅格"
                "逐字节相同，且其墨水为 Edge.Cuts 导出墨水的子集（kicad 对"
                "每层导出绘制的跨层上下文=168 个 *.Cu/*.Mask 多层焊盘剪影+"
                "板框）；板文件普查 B.SilkS/B.CrtYd 图元件数=0（仅 layers "
                "表条目）。即：两板 bottom 视的丝印/courtyard 自有内容为空，"
                "「同色压扁」的实体是 kicad 上下文剪影，而非丝印/courtyard "
                "图元。"),
            "attribution_rejection": (
                "拒绝将跨层上下文剪影（焊盘体圆盘）着丝印黄/洋红：那是焊盘"
                "体/多层焊盘语义，不是占位轮廓或丝印语义；着色将破坏 B.Cu/"
                "B.Mask 层的 r5 同口径并制造伪语义。按任务 fallback 纪律"
                "处理空层（跳过该层合成+witness 记录），不静默造数。"),
        },
        "color_mapping": {
            "B.Silkscreen": {
                "target_rgb": targets["silkscreen_yellow"]["mode_rgb"],
                "alignment": "与 top 视 F.Silkscreen 同 RGB（丝印黄）",
                "sampling": targets["silkscreen_yellow"],
            },
            "B.Courtyard": {
                "target_rgb": targets["courtyard_magenta"]["mode_rgb"],
                "alignment": "与 top 视 F.Courtyard 同 RGB（courtyard 洋红）",
                "sampling": targets["courtyard_magenta"],
            },
            "B.Cu": {"keep": "kicad 原配色不变"},
            "B.Mask": {"keep": "kicad 原配色不变"},
            "Edge.Cuts": {"keep": "kicad 原配色不变"},
            "kept_layers_evidence": kept_layer_evidence(),
        },
        "synthesis_method": {
            "declaration": (
                "base=renders-r4 冻结 combined bottom PDF（r5 唯一图像来源，"
                "sha 复核）经 40pt 组合页+dpi640 光栅化；overlay=按映射表对 "
                "B.Silkscreen/B.Courtyard 的 own-mask 以指定色合成（z 序 "
                "B.Silkscreen→B.Courtyard，叠于 base 之上、Edge.Cuts 语义"
                "不涉）；own-mask=该层单层导出墨水（alpha=255−min(R,G,B)>0）"
                "减去另一语义层墨水（像素对齐：同组合页/dpi/--mirror 口径）。"
                "own-mask 为空（探针实证=0）时按 fallback 跳过着色——此为"
                "声明路径而非异常。"),
            "z_order": ["base(combined B.Cu,B.Mask,B.Silkscreen,Edge.Cuts,"
                        "B.Courtyard)", "overlay:B.Silkscreen",
                        "overlay:B.Courtyard"],
            "blend_math": "out=round((base*(255−a)+color*a)/255)，a=own-mask "
                          "alpha（uint8 整数运算，确定性纯函数）",
            "base_inputs": r4_base,
            "determinism_scope": (
                "kicad-cli PDF 字节不做跨运行确定性断言（r4 实证：applied-"
                "bottom.pdf 与 prep1-bottom.pdf sha 不同而栅格逐字节同）;"
                "确定性断言范围=PDF→栅格化→overlay→裁剪→PNG 字节全链重跑"
                "逐字节一致 + 单层栅格与 probe 落盘产物逐字节一致。"),
        },
        "compose_and_crop_same_as_r5": {
            "dpi": RASTER_DPI,
            "compose_margin_pt": COMPOSE_MARGIN_PT,
            "crop_margin_px": CROP_MARGIN_PX,
            "crop_box_formula": "(x0-120, y0-120, x1+1+120, y1+1+120)，"
                                "(x0,y0,x1,y1)=dpi640 全页 png_board_pixel_"
                                "bounds 实测板界",
            "rasterization_tool": "PyMuPDF (fitz) get_pixmap(dpi=640, "
                                  "alpha=False) + PIL Image.crop/save('PNG')",
            "expected_from_r5_derivation_log": expected,
            "board_bounds_assertion": (
                "合成页板界像素界须逐字等于 derivation-log-r5.json "
                "renders_r5.images[<state>-bottom].board_px_bounds_full "
                "（活读复核）；crop 后四侧白边须恰为 120px。"),
        },
        "top_zero_change": {
            "declaration": (
                "renders-r14/applied-top.png 与 prep1-top.png 自 renders-r5 "
                "逐字节拷贝（零重渲染）；sha256 见证见 renders_plan。"),
            "source_sha256": {
                "applied-top": refs["renders_r5_png_sha256"]["applied-top"],
                "prep1-top": refs["renders_r5_png_sha256"]["prep1-top"],
            },
        },
        "palette_assertions": {
            "formulas": (
                "对每张 r14 bottom PNG：a) 目标黄 (color_mapping.B.Silkscreen."
                "target_rgb) 精确像素计数>0 且容差 8 内计数>0；b) 目标洋红同"
                "理；c) 两色容差 8 内交集像素=0（互不相混）；d) 纯白像素占比 "
                "相对 renders-r5 同名图显著下降（下降量入 witness）。"),
            "preregistered_prediction": {
                "yellow_pixel_count": 0,
                "magenta_pixel_count": 0,
                "white_fraction_delta": 0,
                "prediction_basis": (
                    "探针实证 own-mask 双零 ⇒ overlay 应用 0 像素 ⇒ r14 "
                    "bottom 与 r5 逐字节相同 ⇒ 调色板断言将如实记为 "
                    "fail（计数 0），同时 r5 同口径逐字节断言为 pass。"
                    "本预测先于任何官方成图落盘。"),
            },
        },
        "fallback": {
            "empty_own_mask": (
                "own-mask 为空的语义层：跳过其着色合成+witness 记录计数与"
                "原因（本轮 B.Silkscreen/B.Courtyard 探针实证为空）；不得"
                "静默造数、不得以上下文剪影冒充层内容。"),
            "assertion_fail": (
                "板界断言/裁剪 sanity/r5 同口径逐字节断言任一失败即停止"
                "并如实报告，不得静默改参数。"),
        },
        "freeze_order": {
            "declaration": (
                "本文件先于本轮任何官方成图落盘（framing→render→witness）；"
                "renders-r14/ 根目录四张 PNG 在本文件落盘时尚不存在；probe "
                "仅产出 layers/ 中间件（单层 PDF/PNG），先于本文件。"),
            "probe_artifacts_policy": (
                "probe 单层 PDF/PNG 为一次性中间件（kicad PDF 字节不承诺跨"
                "运行等同）；render 重跑复用之，不重导出。"),
        },
        "overwrite_guard": (
            "目标文件已存在非字节等同→FAIL；字节等同→幂等。"),
        "zero_write_discipline": (
            "out/ 既有文件零改动（staging-r4/renders-r4/renders-r5/"
            "derivation-log-r5.json/render-framing-r5.json 等只读）；"
            "datasets/ 零写入；pcbflow/ 与 tests/ 零改动（仅 import）；"
            "活板文件全程只读（witness 收尾 sha 见证）。"),
        "protected_files_frozen_prefixes": PROTECTED,
        "probe_block": probe,
        "input_board_witness": {
            "applied": STAGED_SHA_FROZEN["applied"],
            "prep1": STAGED_SHA_FROZEN["prep1"],
        },
    }
    sha, mode = _write_canonical_guarded(FRAMING_R14, doc)
    print(f"[r14] framing 落盘：render-framing-r14.json sha256={sha[:16]}… "
          f"({mode})")
    print(f"[r14] 预注册预测：黄/洋红像素计数=0（own-mask 双零）；"
          f"r14 bottom 将与 renders-r5 同名件逐字节相同")


def json_loads(path: Path) -> dict:
    import json
    return json.loads(path.read_text(encoding="utf-8"))


def kept_layer_evidence() -> dict:
    """kept 层（B.Cu/B.Mask/Edge.Cuts）的 r5 原配色证据：renders-r5/
    applied-bottom.png 精确色计数（活读）。"""
    arr = _load_rgb((R5_DIR / "applied-bottom.png").read_bytes())
    out = {}
    for rgb in ((77, 126, 195), (153, 255, 248), (207, 209, 205),
                (255, 255, 255)):
        out[str(rgb)] = int(np.all(arr == np.array(rgb, dtype=np.uint8),
                                   axis=2).sum())
    out["note"] = ("B.Cu 蓝/B.Mask 青/Edge.Cuts 灰(207,209,205)/白 的精确"
                   "像素计数（renders-r5/applied-bottom.png 活读实测）。")
    return out


# ---------------------------------------------------------------------------
# render
# ---------------------------------------------------------------------------

def _bounds_of(png_bytes: bytes) -> dict:
    return calibration.png_board_pixel_bounds(png_bytes)


def cmd_render() -> None:
    _protected_check()
    _staging_check()
    refs = _r5_refs()
    deriv = refs.pop("_deriv")
    if not FRAMING_R14.exists():
        _fail("render-framing-r14.json 缺失（先落盘 framing）")
    framing_sha_start = _sha(FRAMING_R14)
    framing = json_loads(FRAMING_R14)
    ver = _kicad_version()

    for name in FINAL_PNGS:
        if not (R14_DIR / f"{name}.png").exists() and WITNESS_R14.exists():
            _fail("render-witness-r14.json 已存在但成图不全（状态不一致）")

    # framing 冻结值复核
    own_pred = framing["probe_block"]["own_mask_evidence"]["own_mask_counts"]
    expected = framing["compose_and_crop_same_as_r5"][
        "expected_from_r5_derivation_log"]
    targets = {
        "B.Silkscreen": framing["color_mapping"]["B.Silkscreen"]["target_rgb"],
        "B.Courtyard": framing["color_mapping"]["B.Courtyard"]["target_rgb"],
    }
    tol = TARGET_TOL

    # probe 中间件复核 + 单层栅格确定性（与 probe 落盘产物逐字节比较）
    layer_png_sha = {}
    for state in ("applied", "prep1"):
        for layer in PROBE_LAYERS_BOTTOM:
            pdf = LAYERS_DIR / _layer_pdf_name(state, "bottom", layer)
            if not pdf.exists():
                _fail(f"probe 中间件缺失：{pdf.name}（先跑 probe）")
            png_bytes, _, _ = _compose_raster(pdf)
            saved = LAYERS_DIR / _layer_png_name(state, "bottom", layer)
            if png_bytes != saved.read_bytes():
                _fail(f"单层栅格确定性失败：{saved.name}（与 probe 产物"
                      "非逐字节同）")
            layer_png_sha[f"{state}-bottom-{layer}"] = _sha(saved)

    # own-mask 重算（与 framing 记录一致性断言）
    evidence = _own_mask_evidence()
    own_now = evidence["own_mask_counts"]
    if own_now != own_pred:
        _fail(f"own-mask 重算不符 framing 预注册：{own_now} != {own_pred}")
    del evidence

    R14_DIR.mkdir(parents=True, exist_ok=True)
    results = {}
    determinism = {}
    for state in ("applied", "prep1"):
        base_pdf = R4_BOTTOM_PDF[state]
        want = framing["synthesis_method"]["base_inputs"][state]["sha256"]
        if _sha(base_pdf) != want:
            _fail(f"base PDF sha 不符 framing：{state} {_sha(base_pdf)}")

        def build() -> tuple:
            png_full, pw, ph = _compose_raster(base_pdf)
            arr = _load_rgb(png_full)
            # overlay（z 序 silk→court；own-mask 空则按 fallback 跳过）
            overlay_skipped = {}
            silk_png = LAYERS_DIR / _layer_png_name(
                state, "bottom", "B.Silkscreen")
            court_png = LAYERS_DIR / _layer_png_name(
                state, "bottom", "B.Courtyard")
            silk_arr = _load_rgb(silk_png.read_bytes())
            court_arr = _load_rgb(court_png.read_bytes())
            if np.array_equal(silk_arr, court_arr):
                # 两语义层导出逐字节相同 ⇒ own 双零（fallback：跳过着色）
                overlay_skipped = {"B.Silkscreen": 0, "B.Courtyard": 0}
            else:
                a_s = _ink_alpha(silk_arr)
                a_c = _ink_alpha(court_arr)
                for layer, alpha, other_a in (
                        ("B.Silkscreen", a_s, a_c),
                        ("B.Courtyard", a_c, a_s)):
                    own = (alpha > 0) & ~(other_a > 0)
                    n = int(own.sum())
                    overlay_skipped[layer] = n
                    if n == 0:
                        continue
                    a = alpha.astype(np.uint16)
                    c = np.array(targets[layer], dtype=np.uint16)
                    base16 = arr.astype(np.uint16)
                    blended = ((base16 * (255 - a)[..., None]
                                + c * a[..., None] + 127)
                               // 255).astype(np.uint8)
                    arr[own] = blended[own]
            del silk_arr, court_arr
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
            return (full_bytes, b, box, bio2.getvalue(), overlay_skipped,
                    (pw, ph))

        full_bytes, bounds_full2, box, crop_bytes, skipped, pix_wh = build()

        # 板界断言（=derivation-log-r5 实测值，逐字）
        exp = expected[state]["board_px_bounds_full"]
        got = [bounds_full2["x0"], bounds_full2["y0"],
               bounds_full2["x1"], bounds_full2["y1"]]
        if got != exp:
            _fail(f"{state} 板界断言失败：合成页 {got} != r5 实测 {exp}")
        if [pix_wh[0], pix_wh[1]] != expected[state]["full_page_wh"]:
            _fail(f"{state} 全页尺寸断言失败：{pix_wh} != "
                  f"{expected[state]['full_page_wh']}")

        # r5 同口径硬断言：overlay 应用 0 像素 ⇒ 与 renders-r5 逐字节同
        r5_bytes = (R5_DIR / f"{state}-bottom.png").read_bytes()
        parity = crop_bytes == r5_bytes
        if not parity and sum(skipped.values()) == 0:
            _fail(f"{state}: overlay 为空但成图与 renders-r5 非逐字节同"
                  "（同口径破坏）")

        out_path = R14_DIR / f"{state}-bottom.png"
        mode = _guard_write_bytes(out_path, crop_bytes)

        # 调色板断言（客观数字；如实记录 pass/fail）
        carr = _load_rgb(crop_bytes)
        r5arr = _load_rgb(r5_bytes)
        yellow = _mode_near(carr, targets["B.Silkscreen"], tol)
        magenta = _mode_near(carr, targets["B.Courtyard"], tol)
        yd = np.max(np.abs(carr.astype(np.int16)
                           - np.array(targets["B.Silkscreen"],
                                      dtype=np.int16)), axis=2)
        md = np.max(np.abs(carr.astype(np.int16)
                           - np.array(targets["B.Courtyard"],
                                      dtype=np.int16)), axis=2)
        mix_count = int(((yd <= tol) & (md <= tol)).sum())
        white_r14 = int(np.all(carr == 255, axis=2).sum())
        white_r5 = int(np.all(r5arr == 255, axis=2).sum())
        total = int(carr.shape[0] * carr.shape[1])
        results[state] = {
            "output_png_rel": f"out/v3-tl2/calibration/renders-r14/"
                              f"{state}-bottom.png",
            "sha256": _sha(out_path),
            "bytes": out_path.stat().st_size,
            "image_wh": list(_png_size(crop_bytes)),
            "full_page_bounds": got,
            "full_page_wh_asserted": expected[state]["full_page_wh"],
            "crop_box": list(box),
            "overlay_applied_pixels": {k: v for k, v in skipped.items()},
            "r5_parity_byte_equal": parity,
            "r5_sha256": refs["renders_r5_png_sha256"][f"{state}-bottom"],
            "palette": {
                "yellow_exact_count": yellow["mode_count"]
                if yellow["mode_rgb"] == targets["B.Silkscreen"] else 0,
                "yellow_tol8_count": yellow["pixel_count"],
                "magenta_exact_count": magenta["mode_count"]
                if magenta["mode_rgb"] == targets["B.Courtyard"] else 0,
                "magenta_tol8_count": magenta["pixel_count"],
                "two_color_tol8_mix_count": mix_count,
                "white_pixel_count_r14": white_r14,
                "white_pixel_count_r5": white_r5,
                "white_fraction_r14": round(white_r14 / total, 8),
                "white_fraction_r5": round(
                    white_r5 / int(r5arr.shape[0] * r5arr.shape[1]), 8),
                "white_fraction_delta": round(
                    white_r14 / total - white_r5
                    / int(r5arr.shape[0] * r5arr.shape[1]), 8),
                "assertions_pass": bool(
                    yellow["pixel_count"] > 0 and magenta["pixel_count"] > 0
                    and mix_count == 0
                    and white_r14 < white_r5),
                "assertion_note": (
                    "预注册预测=计数 0（own-mask 双零）；如实记录 fail，"
                    "同时 r5_parity_byte_equal=true 证明同口径未被破坏；"
                    "不静默造数。"),
            },
        }
        print(f"[r14] render {state}-bottom.png {results[state]['bytes']}B "
              f"{results[state]['image_wh']} 板界(全页){got} "
              f"r5_parity={parity} 调色板断言="
              f"{results[state]['palette']['assertions_pass']}")
        determinism[state] = build

    # 确定性自证：全链重跑（栅格化→overlay→裁剪→PNG 字节）逐字节一致
    det = {}
    for state in ("applied", "prep1"):
        again = determinism[state]()
        det[state] = again[3] == (R14_DIR / f"{state}-bottom.png").read_bytes()
        if not det[state]:
            _fail(f"确定性自证失败：{state} 重跑非逐字节同")
    print(f"[r14] 确定性自证：重跑全链逐字节一致={det}")

    # top 零变更拷贝（逐字节+哈希见证）
    tops = {}
    for name in ("applied-top", "prep1-top"):
        src = R5_DIR / f"{name}.png"
        data = src.read_bytes()
        if _sha(src) != framing["top_zero_change"]["source_sha256"][name]:
            _fail(f"r5 top 源 sha 不符 framing：{name}")
        mode = _guard_write_bytes(R14_DIR / f"{name}.png", data)
        tops[name] = {"sha256": _sha(src), "bytes": len(data),
                      "source_rel": f"out/v3-tl2/calibration/renders-r5/"
                                    f"{name}.png"}
        print(f"[r14] top 拷贝 {name}.png {len(data)}B ({mode})")

    # framing 运行期间零改动复核 + 收工受保护/staging 复核
    if _sha(FRAMING_R14) != framing_sha_start:
        _fail("render-framing-r14.json 在 render 期间变动（冻结纪律破坏）")
    protected_end = _protected_check()
    staging_end = _staging_check()
    refs_end = _r5_refs()
    refs_end.pop("_deriv")

    doc = {
        "schema_version": "3.0",
        "kind": "tl2_calibration_render_witness_r14",
        "round_label": ROUND_LABEL,
        "round_id_constant": ROUND_ID,
        "date_constant": DATE_CONSTANT,
        "domain_id": DOMAIN_ID,
        "no_visual_reading": True,
        "instrument": (
            f"kicad-cli {KICAD_VERSION} pcb export pdf（probe 单层导出）+ "
            "PyMuPDF get_pixmap(dpi=640, alpha=False) 40pt 组合页光栅化 + "
            "PIL crop/save；base=renders-r4 冻结 combined bottom PDF"
            "（预注册=render-framing-r14.json）"),
        "kicad_cli_version": ver,
        "framing": {
            "path_rel": "out/v3-tl2/calibration/render-framing-r14.json",
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
                "staging-r4 与活板全程只读；probe 导出输入=staging-r4 逐字节"
                "冻结拷贝。"),
        },
        "r5_references": refs_end,
        "probe_artifacts": {
            "layers_dir_rel": "out/v3-tl2/calibration/renders-r14/layers",
            "layer_png_sha256": layer_png_sha,
            "probe_block": framing["probe_block"],
        },
        "color_mapping": framing["color_mapping"],
        "renders": results,
        "top_zero_change_copies": tops,
        "determinism_rerun_byte_identical": det,
        "determinism_scope": framing["synthesis_method"]["determinism_scope"],
        "palette_assertion_summary": {
            s: results[s]["palette"] for s in results},
        "conclusion": (
            "探针实证（witness probe_block）：两板 bottom 视 B.Silkscreen/"
            "B.Courtyard own-mask=0（单层导出逐字节相同、墨水⊂Edge.Cuts "
            "墨水=多层焊盘上下文剪影；板文件普查图元=0）。路线 A 显式配色"
            "在当前板上无着色目标：overlay 应用 0 像素，r14 bottom 与 "
            "renders-r5 同名件逐字节相同（同口径硬断言 pass）；调色板断言"
            "按预注册预测如实记 fail（黄/洋红计数=0），未以任何方式造数。"
            "若需 bottom 视出现丝印黄/洋红，须先由制板侧在 B.SilkS/B.CrtYd "
            "产出真实图元（prep-record 事项，非本轮渲染范围）。"),
        "degradation": None,
    }
    sha, mode = _write_canonical_guarded(WITNESS_R14, doc)
    print(f"[r14] witness 落盘：render-witness-r14.json sha256={sha[:16]}… "
          f"({mode})")


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
        _fail("用法：s50_render_r14.py probe|framing|render")


if __name__ == "__main__":
    main()
