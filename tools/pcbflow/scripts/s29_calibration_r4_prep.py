#!/usr/bin/env python
"""CAL-R4-PREP：reader 判读迭代第四轮预备包（写 out/v3-tl2/calibration/ R4 工件）。

四步（库侧 pcbflow/* 零改动零新增，只 import；本脚本仅编排+纯函数调用）：

  probe     仪器几何探针（产物只进系统临时目录，out/ 零写入）：
            kicad-cli 10.0.5 pcb export pdf（2D 图层绘图）+ PyMuPDF fitz
            固定参数光栅化的可行性实测——页面几何、图元计数 A/B（courtyard
            层存在性）、板像素界触缘检查、扩边 clip 可行性。纯几何/计数
            测量，无视觉判读。
  integrity T2：源板 sha256 实测 vs 冻结记录（calibration-run-r3.json
            preregistration.frozen_artifacts + render-framing.json）比对
            → 逐字节拷贝到 staging-r4/（零差异断言）→ 记录预注册件
            （render-framing-r4.json / observation-guidance-r4.md）sha256
            → staging-integrity-r4.json。
  render    T3+T4：对 staging-r4 逐字节拷贝做 4 张 2D PDF plot（图层清单
            =预注册定稿）→ fitz dpi=320 固定参数光栅化 PNG → renders-r4/；
            逐张实测 png_board_pixel_bounds + 纵横比 sanity [0.7,1.4] +
            sha256 + 逐字命令记录；活板渲染前后 sha256 见证（预期前 8=
            45320fbe，不符即停止）→ render-witness-r4.json。
  derive    T5：读 ground-truth-v2.json 的 gt_entries，board_box_mm 原样
            （零改动），用 pcbflow.calibration.box_mm_to_frame_pct 按 T3
            实测像素界逐条重投影（top 同向/bottom x 镜像）→
            derivation-log-r4.json；落盘后重读自检并打印一条结果行。

纪律：out/ 既有文件零改动（防覆写 guard）；渲染对象一律 staging 逐字节
拷贝，活板零写（前后 sha256 见证）；无 wall-clock（日期/轮次=声明常量
2026-09-06 / 2026-09-06-r4）；canonical JSON（hashing.canonical_json_bytes）；
hash=sha256_file 字节口径；无网络。

用法：python scripts/s29_calibration_r4_prep.py probe|integrity|render|derive
"""

from __future__ import annotations

import shutil
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from pcbflow import calibration, hashing  # noqa: E402

CAL_DIR = REPO / "out" / "v3-tl2" / "calibration"
STAGING_R4 = CAL_DIR / "staging-r4"
R4_DIR = CAL_DIR / "renders-r4"
FRAMING_R4 = CAL_DIR / "render-framing-r4.json"
GUIDANCE_R4 = CAL_DIR / "observation-guidance-r4.md"
INTEGRITY_R4 = CAL_DIR / "staging-integrity-r4.json"
WITNESS_R4 = CAL_DIR / "render-witness-r4.json"
DERIVATION_R4 = CAL_DIR / "derivation-log-r4.json"
RUN_R3 = CAL_DIR / "calibration-run-r3.json"

DATE_CONSTANT = "2026-09-06"
ROUND_ID = "2026-09-06-r4"

KICAD_CLI = Path(r"F:\kicad\bin\kicad-cli.exe")
KICAD_VERSION = "10.0.5"
RASTER_DPI = 320           # fitz get_pixmap(dpi=...) 固定参数（预注册）
COMPOSE_MARGIN_PT = 40.0   # fitz 组合页白边（pt，四侧）；probe 定值，framing 同步声明
MIN_IMAGE_SIDE_PX = 1200   # 图幅可读下限（s17 先例量级）
MIN_BOARD_SIDE_PX = 700    # 板像素界可读下限（70mm 板 @320dpi ≈ 882px）
ASPECT_RANGE = (0.7, 1.4)  # s17 先例 sanity 区间（70x70 方板）

APPLIED_REL = "out/revc-asm/board/applied.kicad_pcb"
PREP1_REL = "out/revc-asm/board/_pre-p1-batch-1.kicad_pcb"
#: 冻结记录（calibration-run-r3.json states.*.source_board / render-framing*.json）
APPLIED_SHA_FROZEN = "45320fbe3296a0594a3678a30ad2c1bf775e6c7e9666158abb82081fc2245d85"
PREP1_SHA_FROZEN = "332c71d4362b732d0a9cdc4d82ea9f8308e4647f2e3cd2fde0bc5497fc5a62c7"

#: 预注册图层清单（framing 定稿；top=F 面含 F.Courtyard，bottom=B 面含
#: B.Courtyard，bottom 视加 --mirror）。
LAYERS_TOP = "F.Cu,F.Mask,F.Silkscreen,Edge.Cuts,F.Courtyard"
LAYERS_BOTTOM = "B.Cu,B.Mask,B.Silkscreen,Edge.Cuts,B.Courtyard"

#: 渲染计划：(state, side, mirror)
RENDER_PLAN = (
    ("applied", "top", False),
    ("applied", "bottom", True),
    ("prep1", "top", False),
    ("prep1", "bottom", True),
)

STATE_BY_SOURCE = {"applied": APPLIED_REL, "prep1": PREP1_REL}
STAGED_NAMES = {"applied": "applied.kicad_pcb", "prep1": "prep1.kicad_pcb"}

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def _fail(msg: str) -> None:
    print(f"[r4-prep] FAIL: {msg}")
    sys.exit(1)


def _write_canonical(path: Path, obj) -> str:
    data = hashing.canonical_json_bytes(obj)
    path.write_bytes(data)
    return hashing.sha256_bytes(data)


def _sha(rel_or_path) -> str:
    return hashing.sha256_file(str(REPO / rel_or_path)
                               if not Path(rel_or_path).is_absolute()
                               else str(rel_or_path))


def _png_size(path: Path) -> tuple:
    data = path.read_bytes()
    if not data.startswith(PNG_MAGIC):
        _fail(f"{path.name}: 不是 PNG（magic 不符）")
    w, h = struct.unpack(">II", data[16:24])
    return w, h


def _export_cmd(state: str, side: str, *, out_rel: str, in_rel: str) -> list:
    """kicad-cli 2D PDF 导出命令（逐字记录=逐字执行；cwd=REPO）。"""
    layers = LAYERS_TOP if side == "top" else LAYERS_BOTTOM
    cmd = ["kicad-cli", "pcb", "export", "pdf", "--mode-single",
           "--scale", "1", "--check-zones", "--drill-shape-opt", "2",
           "--layers", layers]
    if side == "bottom":
        cmd.append("--mirror")
    cmd += ["-o", out_rel, in_rel]
    return cmd


def _run_kicad(cmd: list) -> None:
    if not KICAD_CLI.exists():
        _fail(f"kicad-cli 不存在：{KICAD_CLI}")
    proc = subprocess.run([str(KICAD_CLI)] + cmd[1:], cwd=str(REPO),
                          capture_output=True, text=True)
    if proc.returncode != 0:
        _fail(f"kicad-cli 失败 rc={proc.returncode}: "
              f"{(proc.stderr or proc.stdout or '')[-500:]} "
              f"cmd={' '.join(cmd)}")


def _rasterize(pdf_path: Path, png_path: Path):
    """fitz 固定参数光栅化：组合页白边（new_page 页边距 COMPOSE_MARGIN_PT，
    show_pdf_page 平移嵌入原页矢量内容）→ get_pixmap(dpi=RASTER_DPI,
    alpha=False) → PNG。白边原因与定值依据=render-framing-r4.json（probe
    实测板贴 PDF 页左上角，左缘取样会落入板内容；get_pixmap clip 超页被
    钳制不可用）。返回 (pix_w, pix_h)。"""
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
            pix.save(str(png_path))
            return pix.width, pix.height
        finally:
            out.close()
    finally:
        src.close()


def _measure_png(png_path: Path) -> dict:
    """板像素界实测 + 纵横比/尺寸 sanity（s17 先例口径；纯几何测量）。"""
    w, h = _png_size(png_path)
    bounds = calibration.png_board_pixel_bounds(png_path.read_bytes())
    px_w = bounds["x1"] - bounds["x0"]
    px_h = bounds["y1"] - bounds["y0"]
    aspect = px_w / px_h if px_h else 0.0
    if not ASPECT_RANGE[0] <= aspect <= ASPECT_RANGE[1]:
        _fail(f"{png_path.name}: 板像素界纵横比 {aspect:.3f} 越出 "
              f"{ASPECT_RANGE}（70x70 方板；bg={bounds['background_rgb']}）")
    if min(w, h) < MIN_IMAGE_SIDE_PX:
        _fail(f"{png_path.name}: 图幅 {w}x{h} 低于下限 {MIN_IMAGE_SIDE_PX}")
    if min(px_w, px_h) < MIN_BOARD_SIDE_PX:
        _fail(f"{png_path.name}: 板界 {px_w}x{px_h} 低于下限 "
              f"{MIN_BOARD_SIDE_PX}")
    return {
        "x0": bounds["x0"], "y0": bounds["y0"],
        "x1": bounds["x1"], "y1": bounds["y1"],
        "image_width": bounds["image_width"],
        "image_height": bounds["image_height"],
        "background_rgb": bounds["background_rgb"],
        "background_model": bounds["background_model"],
        "aspect_ratio": round(aspect, 6),
        "board_px_fraction_of_height": round(px_h / h, 6),
        "aspect_sanity_range": list(ASPECT_RANGE),
    }


# ---------------------------------------------------------------------------
# probe：仪器几何探针（临时目录；out/ 零写入）
# ---------------------------------------------------------------------------

def cmd_probe() -> None:
    import fitz

    tmp = Path(tempfile.mkdtemp(prefix="r4probe-"))
    print(f"[r4-prep] probe 临时目录：{tmp}")

    ver = subprocess.run([str(KICAD_CLI), "version"], capture_output=True,
                         text=True)
    print(f"[r4-prep] kicad-cli version: {ver.stdout.strip() or ver.stderr.strip()}")
    print(f"[r4-prep] fitz version: {fitz.__doc__}")

    src = REPO / APPLIED_REL
    st = tmp / "applied.kicad_pcb"
    shutil.copyfile(src, st)
    if hashing.sha256_file(str(st)) != APPLIED_SHA_FROZEN:
        _fail("probe staging 拷贝 sha 断言失败")
    print(f"[r4-prep] probe staging sha256 ok: {APPLIED_SHA_FROZEN[:8]}…")

    bbox = calibration.board_edge_bbox_mm(st.read_text(encoding="utf-8"))
    print(f"[r4-prep] Edge.Cuts bbox(mm): {bbox}")

    layers_all = LAYERS_TOP
    layers_nocY = "F.Cu,F.Mask,F.Silkscreen,Edge.Cuts"
    plan = [
        ("top-with-courtyard", layers_all, False),
        ("top-no-courtyard", layers_nocY, False),
        ("bottom-with-courtyard-mirror", LAYERS_BOTTOM, True),
    ]
    for name, layers, mirror in plan:
        pdf = tmp / f"{name}.pdf"
        rel_out = str(pdf)
        rel_in = str(st)
        cmd = ["kicad-cli", "pcb", "export", "pdf", "--mode-single",
               "--scale", "1", "--check-zones", "--drill-shape-opt", "2",
               "--layers", layers]
        if mirror:
            cmd.append("--mirror")
        cmd += ["-o", rel_out, rel_in]
        proc = subprocess.run([str(KICAD_CLI)] + cmd[1:], cwd=str(REPO),
                              capture_output=True, text=True)
        if proc.returncode != 0 or not pdf.exists():
            print(f"[r4-prep] probe {name}: EXPORT 失败 rc={proc.returncode} "
                  f"{(proc.stderr or proc.stdout or '')[-300:]}")
            continue
        doc = fitz.open(str(pdf))
        page = doc[0]
        n_draw = len(page.get_drawings())
        print(f"[r4-prep] probe {name}: pages={doc.page_count} "
              f"page_rect={page.rect} drawings={n_draw}")
        if name == "top-with-courtyard":
            png = tmp / "probe-top.png"
            pix = page.get_pixmap(dpi=RASTER_DPI, alpha=False)
            pix.save(str(png))
            print(f"[r4-prep] probe raster dpi={RASTER_DPI} "
                  f"pix={pix.width}x{pix.height}")
            try:
                b = calibration.png_board_pixel_bounds(png.read_bytes())
                print(f"[r4-prep] probe bounds OK: "
                      f"({b['x0']},{b['y0']})-({b['x1']},{b['y1']}) "
                      f"bg={b['background_rgb']}")
            except ValueError as e:
                print(f"[r4-prep] probe bounds FAIL: {e}")
            # 扩边 clip 可行性（备用：页缘白边扩边后能否通过 bounds）
            try:
                clip = fitz.Rect(-32, -32, page.rect.width + 32,
                                 page.rect.height + 32)
                pix2 = page.get_pixmap(dpi=RASTER_DPI, alpha=False, clip=clip)
                png2 = tmp / "probe-top-clip.png"
                pix2.save(str(png2))
                b2 = calibration.png_board_pixel_bounds(png2.read_bytes())
                print(f"[r4-prep] probe clip(+32pt) bounds OK: "
                      f"({b2['x0']},{b2['y0']})-({b2['x1']},{b2['y1']}) "
                      f"pix={pix2.width}x{pix2.height}")
            except (ValueError, Exception) as e:  # noqa: B014
                print(f"[r4-prep] probe clip(+32pt) FAIL: {e}")
        doc.close()
    print(f"[r4-prep] probe 完成（临时目录保留备查：{tmp}）")


# ---------------------------------------------------------------------------
# integrity（T2）
# ---------------------------------------------------------------------------

def _check_frozen_artifacts() -> list:
    """run-r3 preregistration.frozen_artifacts 全量 sha 复核（out/ 零改动证明）。"""
    run3 = _json_load(RUN_R3)
    frozen = run3["preregistration"]["frozen_artifacts"]
    results = []
    for item in frozen:
        measured = _sha(item["path_rel"])
        results.append({"path_rel": item["path_rel"], "role": item["role"],
                        "sha256_frozen": item["sha256"],
                        "sha256_measured": measured,
                        "match": measured == item["sha256"]})
    bad = [r for r in results if not r["match"]]
    if bad:
        _fail(f"冻结工件复核不符（out/ 疑被改动）：{bad}")
    return results


def _json_load(path: Path) -> dict:
    import json
    return json.loads(path.read_text(encoding="utf-8"))


def cmd_integrity() -> None:
    if INTEGRITY_R4.exists():
        _fail("staging-integrity-r4.json 已存在（防覆写）")
    if not FRAMING_R4.exists() or not GUIDANCE_R4.exists():
        _fail("预注册件缺失（须先落盘 render-framing-r4.json 与 "
              "observation-guidance-r4.md）")

    frozen_results = _check_frozen_artifacts()

    sources = {}
    for state, rel in STATE_BY_SOURCE.items():
        measured = _sha(rel)
        frozen = APPLIED_SHA_FROZEN if state == "applied" else PREP1_SHA_FROZEN
        if measured != frozen:
            _fail(f"{state} 源板 sha 实测不符冻结记录：{measured} != {frozen}")
        sources[state] = {"path_rel": rel, "sha256_measured": measured,
                          "sha256_frozen": frozen, "match": True}

    STAGING_R4.mkdir(parents=True, exist_ok=True)
    staged = {}
    for state, rel in STATE_BY_SOURCE.items():
        dst = STAGING_R4 / STAGED_NAMES[state]
        if dst.exists():
            _fail(f"{dst} 已存在（防覆写）")
        shutil.copyfile(REPO / rel, dst)
        ok = _sha(dst) == sources[state]["sha256_measured"]
        if not ok:
            _fail(f"{state} staging 逐字节断言失败")
        staged[state] = {"path_rel": f"out/v3-tl2/calibration/staging-r4/"
                                     f"{STAGED_NAMES[state]}",
                         "sha256": sources[state]["sha256_measured"],
                         "byte_equal_to_source": True}

    bbox_by_state = {}
    for state in STATE_BY_SOURCE:
        bbox = calibration.board_edge_bbox_mm(
            (STAGING_R4 / STAGED_NAMES[state]).read_text(encoding="utf-8"))
        expect = {"x_min": 0.0, "y_min": 0.0, "x_max": 70.0, "y_max": 70.0}
        if bbox != expect:
            _fail(f"{state} Edge.Cuts bbox {bbox} != 冻结声明 {expect}")
        bbox_by_state[state] = bbox

    doc = {
        "schema_version": "3.0",
        "kind": "tl2_calibration_staging_integrity_r4",
        "round_id_constant": ROUND_ID,
        "date_constant": DATE_CONSTANT,
        "domain_id": calibration.DOMAIN_ID,
        "sources": sources,
        "staged_copies": staged,
        "board_edge_bbox_mm": bbox_by_state["applied"],
        "board_edge_bbox_mm_note": "两 staged 板逐字解析一致（声明值 0,0,70,70）",
        "frozen_artifacts_check": {
            "scope": "calibration-run-r3.json preregistration.frozen_artifacts",
            "count": len(frozen_results),
            "all_match": True,
            "results": frozen_results,
        },
        "preregistration_hashes": {
            "render-framing-r4.json": {
                "path_rel": "out/v3-tl2/calibration/render-framing-r4.json",
                "sha256": _sha(FRAMING_R4)},
            "observation-guidance-r4.md": {
                "path_rel": "out/v3-tl2/calibration/observation-guidance-r4.md",
                "sha256": _sha(GUIDANCE_R4)},
        },
        "note": ("预注册件先于本记录落盘并在此固定 sha256；后续 render/derive "
                 "步骤复核其不变（盲读隔离纪律：指引写定后冻结）。staging-r4 "
                 "拷贝用后保留备查。"),
    }
    sha = _write_canonical(INTEGRITY_R4, doc)
    print(f"[r4-prep] integrity 写出：staging-integrity-r4.json "
          f"sha256={sha[:16]}…（冻结工件 {len(frozen_results)} 项全 match；"
          f"staging-r4 两拷贝零差异）")


# ---------------------------------------------------------------------------
# render（T3+T4）
# ---------------------------------------------------------------------------

def _prereg_freeze_check(integrity: dict) -> None:
    for key, path in (("render-framing-r4.json", FRAMING_R4),
                      ("observation-guidance-r4.md", GUIDANCE_R4)):
        rec = integrity["preregistration_hashes"][key]["sha256"]
        now = _sha(path)
        if now != rec:
            _fail(f"预注册件变动（冻结纪律破坏）：{key} {now} != {rec}")


def cmd_render() -> None:
    import fitz

    if WITNESS_R4.exists():
        _fail("render-witness-r4.json 已存在（防覆写）")
    if not INTEGRITY_R4.exists():
        _fail("staging-integrity-r4.json 缺失（先跑 integrity）")
    if R4_DIR.exists():
        _fail("renders-r4/ 已存在（防覆写；本包新建目录）")
    integrity = _json_load(INTEGRITY_R4)
    _prereg_freeze_check(integrity)

    # staging 拷贝完整性复核（渲染对象必须与源板逐字节一致）
    for state in STATE_BY_SOURCE:
        staged = STAGING_R4 / STAGED_NAMES[state]
        if _sha(staged) != integrity["sources"][state]["sha256_measured"]:
            _fail(f"{state} staging 拷贝与源板不符（拒绝渲染）")

    # 活板渲染前 sha256（预期 applied 前 8=45320fbe；不符即停止）
    live_before = {}
    for state, rel in STATE_BY_SOURCE.items():
        live_before[state] = _sha(rel)
    if live_before["applied"][:8] != APPLIED_SHA_FROZEN[:8]:
        _fail(f"applied 活板渲染前 sha 前 8={live_before['applied'][:8]} "
              f"!= 预期 45320fbe（立即停止）")

    R4_DIR.mkdir(parents=True)

    fitz_version = (fitz.__doc__ or "").strip().splitlines()[0]
    renders = []
    for state, side, _mirror in RENDER_PLAN:
        name = f"{state}-{side}"
        pdf_rel = f"out/v3-tl2/calibration/renders-r4/{name}.pdf"
        png_rel = f"out/v3-tl2/calibration/renders-r4/{name}.png"
        pdf_path = REPO / pdf_rel
        png_path = REPO / png_rel
        if pdf_path.exists() or png_path.exists():
            _fail(f"{name} 输出已存在（防覆写）")
        cmd = _export_cmd(state, side, out_rel=pdf_rel,
                          in_rel=f"out/v3-tl2/calibration/staging-r4/"
                                 f"{STAGED_NAMES[state]}")
        _run_kicad(cmd)
        if not pdf_path.exists():
            _fail(f"{name}: 导出 PDF 未生成")
        px_w, px_h = _rasterize(pdf_path, png_path)
        measured = _measure_png(png_path)
        if (measured["image_width"], measured["image_height"]) != (px_w, px_h):
            _fail(f"{name}: PNG 尺寸不符（ihdr {measured['image_width']}x"
                  f"{measured['image_height']} vs pix {px_w}x{px_h}）")
        renders.append({
            "state": state, "side": side,
            "file_rel": png_rel, "pdf_rel": pdf_rel,
            "sha256": _sha(png_path),
            "bytes": png_path.stat().st_size,
            "width": measured["image_width"],
            "height": measured["image_height"],
            "tool": f"kicad-cli {KICAD_VERSION} pcb export pdf "
                    f"+ PyMuPDF {fitz_version} get_pixmap",
            "command": cmd,
            "command_cwd": "repo_root",
            "layer_list": LAYERS_TOP if side == "top" else LAYERS_BOTTOM,
            "mirror": side == "bottom",
            "rasterization": {"tool": f"PyMuPDF {fitz_version}",
                              "dpi": RASTER_DPI, "alpha": False,
                              "colorspace": "RGB",
                              "compose_margin_pt": COMPOSE_MARGIN_PT},
            "board_pixel_bounds": measured,
            "bounds_source": "pcbflow.calibration.png_board_pixel_bounds",
        })
        print(f"[r4-prep] render ok: {name}.png {png_path.stat().st_size}B "
              f"{px_w}x{px_h} 板界 ({measured['x0']},{measured['y0']})-"
              f"({measured['x1']},{measured['y1']}) "
              f"aspect={measured['aspect_ratio']}")

    # 活板渲染后 sha256（零写见证）
    live_after = {}
    for state, rel in STATE_BY_SOURCE.items():
        live_after[state] = _sha(rel)
    witness_lines = {}
    for state in STATE_BY_SOURCE:
        ok = live_before[state] == live_after[state]
        if not ok:
            _fail(f"{state} 活板渲染前后 sha 不一致（零写见证失败）")
        witness_lines[state] = {
            "path_rel": STATE_BY_SOURCE[state],
            "sha256_before_render": live_before[state],
            "sha256_after_render": live_after[state],
            "unchanged": True,
            "expected_prefix": (APPLIED_SHA_FROZEN[:8]
                                if state == "applied" else
                                PREP1_SHA_FROZEN[:8]),
            "prefix_match": live_after[state][:8] == (
                APPLIED_SHA_FROZEN[:8] if state == "applied"
                else PREP1_SHA_FROZEN[:8]),
        }
    if not witness_lines["applied"]["prefix_match"]:
        _fail("applied 活板 sha 前 8 != 45320fbe（立即停止）")

    # staging 拷贝渲染后复核（export 只读输入）
    for state in STATE_BY_SOURCE:
        staged = STAGING_R4 / STAGED_NAMES[state]
        if _sha(staged) != integrity["sources"][state]["sha256_measured"]:
            _fail(f"{state} staging 拷贝渲染后被改动（不应发生）")

    doc = {
        "schema_version": "3.0",
        "kind": "tl2_calibration_render_witness_r4",
        "round_id_constant": ROUND_ID,
        "date_constant": DATE_CONSTANT,
        "domain_id": calibration.DOMAIN_ID,
        "instrument": ("kicad-cli 10.0.5 pcb export pdf（2D 图层绘图）+ "
                       f"PyMuPDF {fitz_version} get_pixmap(dpi={RASTER_DPI}, "
                       "alpha=False) 光栅化（预注册仪器=render-framing-r4.json）"),
        "live_board_witness": witness_lines,
        "live_board_witness_note": ("渲染全程只读活板；渲染对象=staging-r4 "
                                    "逐字节拷贝（零差异断言在 integrity 与 "
                                    "本步骤前后各复核一次）。"),
        "staging_zero_diff_assertion": True,
        "renders": renders,
        "degradation": None,
        "no_visual_reading_note": ("本包未做任何视觉判读：仅渲染、像素界几何"
                                   "测量与 hash 见证；flag 由后续独立 reader "
                                   "子智能体按 observation-guidance-r4.md "
                                   "产出。"),
    }
    sha = _write_canonical(WITNESS_R4, doc)
    print(f"[r4-prep] render 写出：render-witness-r4.json sha256={sha[:16]}…"
          f"（4 张；活板前后 sha 一致）")


# ---------------------------------------------------------------------------
# derive（T5）
# ---------------------------------------------------------------------------

def cmd_derive() -> None:
    if DERIVATION_R4.exists():
        _fail("derivation-log-r4.json 已存在（防覆写）")
    if not WITNESS_R4.exists():
        _fail("render-witness-r4.json 缺失（先跑 render）")
    integrity = _json_load(INTEGRITY_R4)
    _prereg_freeze_check(integrity)
    witness = _json_load(WITNESS_R4)

    # GT 语料实况（run-r3 preregistration.frozen_artifacts 与 states.*.gt_file
    # 均如此声明）：ground-truth-v1.json=种子 4 条（prep1 态，GT-REVC-P1-*）；
    # ground-truth-v2.json=扩样 9 条（applied 态，GT-REVC-AP-*）。合计 13 条。
    gt_specs = (
        ("prep1", "out/v3-tl2/calibration/ground-truth-v1.json",
         "GT-REVC-P1-", 4),
        ("applied", "out/v3-tl2/calibration/ground-truth-v2.json",
         "GT-REVC-AP-", 9),
    )
    gt_sources = []
    state_entries = {}
    for state, rel, prefix, expect_n in gt_specs:
        sha = _sha(rel)
        frozen = next(r["sha256_frozen"] for r in
                      integrity["frozen_artifacts_check"]["results"]
                      if r["path_rel"] == rel)
        if sha != frozen:
            _fail(f"GT 文件 sha 不符冻结记录：{rel} {sha} != {frozen}")
        gt = _json_load(REPO / rel)
        entries = gt["gt_entries"]
        if len(entries) != expect_n:
            _fail(f"{rel}: 条目数 {len(entries)} != 声明 {expect_n}")
        ids = [e["gt_id"] for e in entries]
        bad = [i for i in ids if not i.startswith(prefix)]
        if bad:
            _fail(f"{rel}: gt_id 前缀不符声明 {prefix}：{bad}")
        gt_sources.append({"path_rel": rel, "sha256": sha,
                           "sha256_frozen_match": True,
                           "state": state, "entry_count": len(entries),
                           "gt_id_prefix": prefix})
        for e in entries:
            state_entries.setdefault(state, []).append(e)

    # T3 实测像素界（state+side → px_bounds，含 image_width/height）
    px_by_key = {}
    for r in witness["renders"]:
        b = r["board_pixel_bounds"]
        px_by_key[(r["state"], r["side"])] = {
            "x0": b["x0"], "y0": b["y0"], "x1": b["x1"], "y1": b["y1"],
            "image_width": b["image_width"],
            "image_height": b["image_height"],
            "source_render": r["file_rel"],
        }
    missing = [k for k in (("applied", "top"), ("applied", "bottom"),
                           ("prep1", "top"), ("prep1", "bottom"))
               if k not in px_by_key]
    if missing:
        _fail(f"实测像素界缺失：{missing}")

    bbox = integrity["board_edge_bbox_mm"]
    out_entries = []
    for state in ("prep1", "applied"):
        for e in state_entries[state]:
            side = e["side"]
            if side not in ("top", "bottom"):
                _fail(f"{e['gt_id']}: side 非法 {side!r}")
            mm = [float(v) for v in e["board_box_mm"]]
            px = px_by_key[(state, side)]
            pct = calibration.box_mm_to_frame_pct(mm, bbox, px, side=side)
            out_entries.append({
                "gt_id": e["gt_id"],
                "state": state,
                "side": side,
                "gt_source_file": next(s["path_rel"] for s in gt_sources
                                       if s["state"] == state),
                "board_box_mm_verbatim": mm,
                "frame_box_pct_r4": pct,
                "frame_box_pct_gt_file": [float(v)
                                          for v in e["frame_box_pct"]],
                "conversion_inputs": {
                    "board_edge_bbox_mm": bbox,
                    "px_bounds": px,
                    "function":
                        "pcbflow.calibration.box_mm_to_frame_pct",
                    "side_convention": ("top 视 x/y 同向；bottom 视 x 镜像"
                                        "（y 同向）"),
                },
            })
    out_entries.sort(key=lambda d: (d["state"], d["gt_id"]))

    doc = {
        "schema_version": "3.0",
        "kind": "tl2_calibration_gt_reprojection_r4",
        "round_id_constant": ROUND_ID,
        "date_constant": DATE_CONSTANT,
        "domain_id": calibration.DOMAIN_ID,
        "gt_sources": gt_sources,
        "gt_corpus_note": (
            "13 条=ground-truth-v1.json（种子 4 条，prep1 态）+ "
            "ground-truth-v2.json（扩样 9 条，applied 态）；两文件均为 "
            "calibration-run-r3.json preregistration 冻结工件（sha 复核"
            "通过）。状态归属=文件归属+gt_id 前缀双重声明（v1=GT-REVC-P1-*"
            "→prep1；v2=GT-REVC-AP-*→applied），与 calibration-run-r3.json "
            "states.prep1/applied.gt_file 的归属一致。"),
        "mm_zero_change_declaration": (
            "全部 13 条 board_box_mm 从 GT 文件 gt_entries 逐字段原样取值"
            "（float 原值拷贝，零修改）；换算仅产生新的 frame_box_pct_r4，"
            "不改 mm 框。"),
        "state_attribution_rule": (
            "文件归属+前缀声明规则：ground-truth-v1.json 的 GT-REVC-P1-* "
            "→ prep1（4 条）；ground-truth-v2.json 的 GT-REVC-AP-* → "
            "applied（9 条）。"),
        "conversion_base": {
            "board_edge_bbox_mm": bbox,
            "px_bounds_by_state_side": {
                f"{s}-{v}": px_by_key[(s, v)]
                for s, v in (("applied", "top"), ("applied", "bottom"),
                             ("prep1", "top"), ("prep1", "bottom"))},
            "px_bounds_source": ("render-witness-r4.json renders[]"
                                 ".board_pixel_bounds（T3 实测，"
                                 "png_board_pixel_bounds 背景差分扫描）"),
            "function": "pcbflow.calibration.box_mm_to_frame_pct",
            "no_visual_reading": True,
        },
        "entries": out_entries,
        "self_check_rule": (
            "落盘后重读本文件与两 GT 文件：条目数相等（13）；每条 "
            "board_box_mm_verbatim 与其源 GT 条目逐字段 float 相等；"
            "frame_box_pct_r4 ∈ [0,1] 且 x0<x1、y0<y1。"),
    }
    sha = _write_canonical(DERIVATION_R4, doc)

    # 落盘后自检（重读三文件逐字段断言）并打印一条结果行
    relog = _json_load(DERIVATION_R4)
    gt_all = {}
    for _, rel, _, _ in gt_specs:
        for e in _json_load(REPO / rel)["gt_entries"]:
            gt_all[e["gt_id"]] = e
    assert len(relog["entries"]) == len(gt_all) == 13, "条目数不符"
    mm_all_equal = True
    pct_all_valid = True
    for e in relog["entries"]:
        src = gt_all[e["gt_id"]]
        if [float(v) for v in src["board_box_mm"]] != e["board_box_mm_verbatim"]:
            mm_all_equal = False
        b = e["frame_box_pct_r4"]
        if not (all(0.0 <= v <= 1.0 for v in b) and b[0] < b[2] and b[1] < b[3]):
            pct_all_valid = False
    print(f"[r4-prep] derive 自检：条目数={len(relog['entries'])}（预期 13）；"
          f"mm 框逐字段相等={mm_all_equal}；frame_box_pct_r4 合法="
          f"{pct_all_valid}；derivation-log-r4.json sha256={sha[:16]}…")


def main() -> None:
    step = sys.argv[1] if len(sys.argv) > 1 else ""
    if step == "probe":
        cmd_probe()
    elif step == "integrity":
        cmd_integrity()
    elif step == "render":
        cmd_render()
    elif step == "derive":
        cmd_derive()
    else:
        _fail("用法：s29_calibration_r4_prep.py probe|integrity|render|derive")


if __name__ == "__main__":
    main()
