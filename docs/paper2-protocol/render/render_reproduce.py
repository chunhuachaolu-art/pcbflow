#!/usr/bin/env python
"""render_reproduce.py — deterministic PCB render reproduction pipeline
(release copy, PAPER-P2-3 artifact package).

Reimplements the render framework used throughout the development rounds
("r5 framework pipeline", registered in render-framing-r5.json and reused
byte-identically by s51/s62/s92 in the dev repo) as a single standalone
script with no dependency on the dev codebase.

Pipeline (per board file x view):
  1. copy the input board into the run work dir (NEVER render in place:
      kicad-cli writes a `<name>.kicad_prl` sidecar next to its input file —
      the "S40 incident" in the dev repo; rendering from a copy keeps frozen
      dataset trees pristine)
  2. kicad-cli pcb export pdf --mode-single --scale 1 --check-zones
      --drill-shape-opt 2 --layers <layers> [--mirror for bottom] -o <pdf>
  3. PyMuPDF (fitz): assert single page -> compose onto a white page with
      40 pt margin -> get_pixmap(dpi=640, alpha=False)
  4. board pixel bounds via per-row left-edge background differential
      (fail-closed port of the dev reference implementation
      pcbflow.calibration.png_board_pixel_bounds; same sampled-row checks,
      same rejection conditions)
  5. crop to board bounds + 120 px margin on all sides
  6. write PNG + local evidence JSON (canonical, sort_keys, indent=1, LF)

Determinism scope (preregistered in the dev repo since r4/r14b and
unchanged here):
  * asserted byte-deterministic: everything from the rasterization onward
    (composed raster -> bounds -> crop -> PNG bytes) plus every manifest
    field;
  * NOT asserted: kicad-cli PDF file bytes (kicad-cli embeds run-local
    metadata; r4/r14b evidence showed PDF sha differing across runs while
    the rasterized PNG stayed byte-identical). The PDF sha is therefore
    recorded in the per-run evidence file under pdf_sha256_run_local with
    an explicit no-cross-run-assertion note.

Instrument parameters (frozen, same values as the dev repo):
  RASTER_DPI = 640, COMPOSE_MARGIN_PT = 40.0, CROP_MARGIN_PX = 120,
  layers_top = "F.Cu,F.Mask,F.Silkscreen,Edge.Cuts,F.Courtyard",
  layers_bottom = "B.Cu,B.Mask,B.Silkscreen,Edge.Cuts,B.Courtyard",
  bottom view exported with --mirror.

No machine-specific path is hardcoded: locate kicad-cli via --kicad-cli /
env KICAD_CLI / PATH. Version is recorded, not asserted (use
--expect-version to opt into an assertion; dev repo reference renders used
kicad-cli 10.0.5).

Optional stage --recolor-r14b (bottom views; see color_legend.md):
applies the r14b white-disambiguation recolor — white ink vector drawings
(pad hole disks / pad outlines, the B.Cu u B.Mask shared drawing family)
-> orange (255,165,0); board-interior void white -> green (0,128,0) — with
the preregistered color-distance assertion (RGB Euclidean distance > 150
against every canvas base color). Masks are rebuilt deterministically from
the combined PDF vector data (fitz get_drawings), the mechanism ported from
dev script s51_render_r14b.py.

License: Apache-2.0.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import shutil
import struct
import subprocess
import sys
from pathlib import Path

DECLARED_DATE = "2026-09-12"

RASTER_DPI = 640
COMPOSE_MARGIN_PT = 40.0
CROP_MARGIN_PX = 120
LAYERS_TOP = "F.Cu,F.Mask,F.Silkscreen,Edge.Cuts,F.Courtyard"
LAYERS_BOTTOM = "B.Cu,B.Mask,B.Silkscreen,Edge.Cuts,B.Courtyard"
VIEWS = ("top", "bottom")

#: r14b recolor targets (preregistered constants, not sampled values)
TARGET_ORANGE = (255, 165, 0)
TARGET_GREEN = (0, 128, 0)
#: canvas base colors observed with kicad default palette (r5/r14b evidence)
CANVAS_COLORS = {
    "B.Cu_blue": (77, 126, 195),
    "B.Mask_cyan": (153, 255, 248),
    "Edge.Cuts_gray": (207, 209, 205),
    "canvas_white": (255, 255, 255),
}
COLOR_DIST_MIN = 150.0

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def _fail(msg: str) -> None:
    raise SystemExit(f"[render-reproduce] FAIL: {msg}")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json_bytes(obj) -> bytes:
    return (json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=1)
            + "\n").encode("utf-8")


# ---------------------------------------------------------------------------
# board pixel bounds (fail-closed port of png_board_pixel_bounds)
# ---------------------------------------------------------------------------


def png_board_pixel_bounds(png_bytes: bytes) -> dict:
    """Board pixel bounds by per-row left-edge background differential.

    Behavioral port of pcbflow.calibration.png_board_pixel_bounds (dev
    reference): per-row background = that row's left-edge pixel; pixels
    differing from it are board pixels; bounds = inclusive bbox. Fail-closed
    conditions identical to the reference:
      * sampled rows (stride max(1, h//16)) must have equal left/right edge
        colors (background horizontally uniform at sampled rows);
      * no row may have > 90% background-differing pixels (board touching
        the left edge / non-uniform row background);
      * fully uniform image (no board) is rejected;
      * bounds touching the image edge are rejected (centered rendering
        implies margins).
    Determinism: identical bytes -> identical bounds. The port was validated
    against the dev reference implementation on the example renders of this
    package (see SELFVERIFY-LOG.md).
    """
    if not png_bytes.startswith(PNG_MAGIC):
        _fail("png_board_pixel_bounds: PNG magic mismatch")
    from PIL import Image
    import numpy as np
    arr = np.asarray(Image.open(io.BytesIO(png_bytes)).convert("RGB"),
                     dtype=np.uint8)
    h, w = arr.shape[:2]
    stride = max(1, h // 16)
    for y in range(0, h, stride):
        if not np.array_equal(arr[y, 0], arr[y, w - 1]):
            _fail("png_board_pixel_bounds: background horizontally "
                  f"non-uniform at sampled row y={y} (left/right edge "
                  "colors differ; fail-closed)")
    bg = arr[:, 0, :][:, None, :]
    diff = np.any(arr != bg, axis=2)
    row_counts = diff.sum(axis=1)
    bad = int(np.argmax(row_counts)) if row_counts.max() > w * 0.9 else None
    if bad is not None:
        _fail("png_board_pixel_bounds: left-edge background sampling "
              f"failed at y={bad} ({int(row_counts[bad])}/{w} differing "
              "pixels; board touches left edge or row background "
              "non-uniform; fail-closed)")
    ys, xs = np.nonzero(diff)
    if ys.size == 0:
        _fail("png_board_pixel_bounds: uniform image (no board bounds)")
    x0, x1 = int(xs.min()), int(xs.max())
    y0, y1 = int(ys.min()), int(ys.max())
    if x0 <= 0 or y0 <= 0 or x1 >= w - 1 or y1 >= h - 1:
        _fail("png_board_pixel_bounds: board bounds touch image edge "
              "(centered rendering should leave margins; fail-closed)")
    return {"x0": x0, "y0": y0, "x1": x1, "y1": y1,
            "image_width": int(w), "image_height": int(h),
            "background_rgb": [int(v) for v in arr[0, 0]],
            "background_model": "vertical_gradient_row_sampled"}


# ---------------------------------------------------------------------------
# kicad-cli location and export
# ---------------------------------------------------------------------------


def locate_kicad_cli(explicit: str) -> Path:
    if explicit:
        p = Path(explicit)
        if not p.exists():
            _fail(f"kicad-cli not found at --kicad-cli path: {p}")
        return p
    env = os.environ.get("KICAD_CLI")
    if env:
        p = Path(env)
        if not p.exists():
            _fail(f"kicad-cli not found at env KICAD_CLI path: {p}")
        return p
    which = shutil.which("kicad-cli")
    if which:
        return Path(which)
    _fail("kicad-cli not found; pass --kicad-cli or set env KICAD_CLI, "
          "or put kicad-cli on PATH")


def kicad_version(cli: Path) -> str:
    proc = subprocess.run([str(cli), "version"], capture_output=True,
                          text=True, timeout=120)
    ver = (proc.stdout or proc.stderr).strip()
    if proc.returncode != 0 or not ver:
        _fail(f"kicad-cli version check failed rc={proc.returncode}: "
              f"{ver!r}")
    return ver


def export_pdf(cli: Path, board_copy: Path, out_pdf: Path, view: str,
               timeout_s: int) -> dict:
    """Step 2: single-page 2D PDF export for one view. Returns the command
    record (machine-independent: exe basename + relative names only)."""
    layers = LAYERS_TOP if view == "top" else LAYERS_BOTTOM
    cmd = [str(cli), "pcb", "export", "pdf", "--mode-single",
           "--scale", "1", "--check-zones", "--drill-shape-opt", "2",
           "--layers", layers]
    if view == "bottom":
        cmd.append("--mirror")
    cmd += ["-o", out_pdf.name, board_copy.name]
    if out_pdf.exists():
        _fail(f"refusing to overwrite existing PDF (anti-overwrite): "
              f"{out_pdf}")
    proc = subprocess.run(cmd, cwd=str(board_copy.parent),
                          capture_output=True, text=True, timeout=timeout_s)
    if proc.returncode != 0 or not out_pdf.exists():
        _fail(f"kicad-cli export failed rc={proc.returncode}: "
              f"{(proc.stderr or proc.stdout or '')[-500:]}")
    return {
        "command": ["kicad-cli", "pcb", "export", "pdf", "--mode-single",
                    "--scale", "1", "--check-zones", "--drill-shape-opt",
                    "2", "--layers", layers]
        + (["--mirror"] if view == "bottom" else [])
        + ["-o", out_pdf.name, board_copy.name],
        "layers": layers,
        "mirror": view == "bottom",
    }


# ---------------------------------------------------------------------------
# compose + rasterize + crop (fitz pipeline)
# ---------------------------------------------------------------------------


def compose_raster(pdf_path: Path) -> tuple:
    """Steps 3: fitz compose (40 pt white margin) + dpi640 rasterization.
    Returns (png_bytes, page_wh). Deterministic given identical PDF raster
    content (PDF file bytes themselves are not cross-run asserted)."""
    import fitz
    src = fitz.open(str(pdf_path))
    try:
        if src.page_count != 1:
            _fail(f"{pdf_path.name}: page count {src.page_count} != 1 "
                  "(--mode-single)")
        page_w = src[0].rect.width
        page_h = src[0].rect.height
        m = COMPOSE_MARGIN_PT
        out = fitz.open()
        try:
            page = out.new_page(width=page_w + 2 * m, height=page_h + 2 * m)
            page.show_pdf_page(fitz.Rect(m, m, m + page_w, m + page_h),
                               src, 0)
            pix = page.get_pixmap(dpi=RASTER_DPI, alpha=False)
            return pix.tobytes("png"), [pix.width, pix.height]
        finally:
            out.close()
    finally:
        src.close()


def crop_to_board(png_bytes: bytes, bounds: dict) -> tuple:
    """Step 5: crop full page to board bounds + CROP_MARGIN_PX on all sides.
    Returns (cropped_png_bytes, crop_box)."""
    from PIL import Image
    box = (bounds["x0"] - CROP_MARGIN_PX, bounds["y0"] - CROP_MARGIN_PX,
           bounds["x1"] + 1 + CROP_MARGIN_PX,
           bounds["y1"] + 1 + CROP_MARGIN_PX)
    im = Image.open(io.BytesIO(png_bytes))
    if box[0] < 0 or box[1] < 0 or box[2] > im.width or box[3] > im.height:
        _fail(f"crop box {box} exceeds image {im.width}x{im.height}")
    cropped = im.crop(box)
    bio = io.BytesIO()
    cropped.save(bio, "PNG")
    return bio.getvalue(), list(box)


# ---------------------------------------------------------------------------
# optional r14b recolor stage
# ---------------------------------------------------------------------------


def _is_white_fill(d: dict) -> bool:
    f = d.get("fill")
    return f is not None and all(abs(v - 1.0) < 1e-6 for v in f)


def _is_white_stroke(d: dict) -> bool:
    c = d.get("color")
    return (d.get("fill") is None and c is not None
            and all(abs(v - 1.0) < 1e-6 for v in c))


def rebuild_white_ink_masks(pdf_path: Path, page_wh: list):
    """Vector rebuild of the white ink drawings on the combined PDF:
    white fills drawn red, white strokes drawn green on a black canvas with
    the same 40 pt compose geometry, rasterized at dpi640, binarized >127.
    Port of dev s51_render_r14b.py _rebuild_white_masks (deterministic)."""
    import fitz
    import numpy as np
    doc = fitz.open(str(pdf_path))
    try:
        page = doc[0]
        w, h = page.rect.width, page.rect.height
        draws = page.get_drawings()
        m = COMPOSE_MARGIN_PT
        out = fitz.open()
        try:
            npg = out.new_page(width=w + 2 * m, height=h + 2 * m)
            npg.draw_rect(fitz.Rect(0, 0, w + 2 * m, h + 2 * m),
                          color=None, fill=(0, 0, 0))
            shape = npg.new_shape()
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
            pix = npg.get_pixmap(dpi=RASTER_DPI, alpha=False)
            arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
                pix.height, pix.width, pix.n)[:, :, :3]
            if [pix.width, pix.height] != page_wh:
                _fail("white-ink mask raster size != composed raster size")
            fill_mask = arr[:, :, 0] > 127
            stroke_mask = arr[:, :, 1] > 127
            meta = {"rebuilt_white_fill_drawings": nf,
                    "rebuilt_white_stroke_drawings": ns,
                    "mask_fill_pixel_count": int(fill_mask.sum()),
                    "mask_stroke_pixel_count": int(stroke_mask.sum())}
            return fill_mask, stroke_mask, meta
        finally:
            out.close()
    finally:
        doc.close()


def _euclid(a, b) -> float:
    return float(sum((int(x) - int(y)) ** 2 for x, y in zip(a, b))) ** 0.5


def color_distance_assertion() -> dict:
    table = {}
    ok = True
    for tname, tRGB in (("target_orange", TARGET_ORANGE),
                        ("target_green", TARGET_GREEN)):
        for cname, cRGB in CANVAS_COLORS.items():
            d = _euclid(tRGB, cRGB)
            table[f"{tname}_vs_{cname}"] = round(d, 2)
            if d <= COLOR_DIST_MIN:
                ok = False
    if not ok:
        _fail(f"r14b color-distance assertion failed: {table}")
    return {"distances": table, "min_required": COLOR_DIST_MIN,
            "all_above_threshold": True}


def apply_recolor_r14b(full_png: bytes, pdf_path: Path, page_wh: list,
                       bounds: dict) -> tuple:
    """r14b white-disambiguation recolor on the FULL composed raster:
    (a) white ink drawings (B.Cu u B.Mask shared family, rebuilt from PDF
    vectors) -> orange; (b) board-interior void white (board bounds x pure
    white x not white ink) -> green. Binary mask full replacement, no alpha
    blending (s51 convention). Returns (recolor_stats, new_full_png)."""
    import numpy as np
    from PIL import Image
    color_distance_assertion()
    fill_mask, stroke_mask, mask_meta = rebuild_white_ink_masks(
        pdf_path, page_wh)
    arr = np.asarray(Image.open(io.BytesIO(full_png)).convert("RGB"),
                     dtype=np.uint8).copy()
    if arr.shape[:2] != (page_wh[1], page_wh[0]):
        _fail("recolor input raster size mismatch")
    board = np.zeros(arr.shape[:2], dtype=bool)
    board[bounds["y0"]:bounds["y1"] + 1, bounds["x0"]:bounds["x1"] + 1] = True
    orange = np.array(TARGET_ORANGE, dtype=np.uint8)
    green = np.array(TARGET_GREEN, dtype=np.uint8)
    white = np.all(arr == 255, axis=2)
    sel_orange = (fill_mask | stroke_mask) & board
    sel_green = board & white & ~sel_orange
    arr[sel_orange] = orange
    arr[sel_green] = green
    bio = io.BytesIO()
    Image.fromarray(arr, "RGB").save(bio, "PNG")
    stats = {
        "white_ink_mask": mask_meta,
        "orange_pixel_count": int(sel_orange.sum()),
        "green_pixel_count": int(sel_green.sum()),
        "orange_green_intersection": int((sel_orange & sel_green).sum()),
        "white_before_full_page": int(white.sum()),
        "white_after_board_interior":
            int((board & np.all(arr == 255, axis=2)).sum()),
        "color_distance_assertion": "pass (>150 vs every canvas base color)",
        "note": "r14b recolor was developed as a Rev-C probe-specific "
                "instrument change and is NOT part of the default pipeline; "
                "official dev-repo holdout renders used the kicad default "
                "palette (zero overlay). Shipped here as a documented, "
                "optional, deterministic stage.",
    }
    return stats, bio.getvalue()


# ---------------------------------------------------------------------------
# per-view driver
# ---------------------------------------------------------------------------


def render_view(cli: Path, board_src: Path, work_dir: Path, view: str,
                board_label: str, recolor: bool, timeout_s: int,
                expect_version: str | None) -> dict:
    """Full pipeline for one (board, view). Returns the evidence record;
    writes <label>-<view>.png + <label>-<view>.render-evidence.json into
    work_dir. Board is copied in (never rendered in place)."""
    import numpy as np
    work_dir.mkdir(parents=True, exist_ok=True)
    board_copy = work_dir / (board_label + ".kicad_pcb")
    if board_copy.exists() and board_copy.read_bytes() != board_src.read_bytes():
        _fail(f"board copy exists with different bytes: {board_copy}")
    if not board_copy.exists():
        shutil.copyfile(board_src, board_copy)
    board_sha = sha256_bytes(board_copy.read_bytes())

    ver = kicad_version(cli)
    if expect_version and expect_version not in ver:
        _fail(f"kicad-cli version {ver!r} does not contain expected "
              f"{expect_version!r}")

    pdf_path = work_dir / f"{board_label}-{view}.pdf"
    cmd_rec = export_pdf(cli, board_copy, pdf_path, view, timeout_s)
    pdf_sha = sha256_file_local(pdf_path)
    full_png, page_wh = compose_raster(pdf_path)
    bounds = png_board_pixel_bounds(full_png)
    out_png = full_png
    recolor_stats = None
    if recolor:
        if view != "bottom":
            _fail("--recolor-r14b applies to bottom views only (r14b was a "
                  "bottom-view instrument change)")
        recolor_stats, out_png = apply_recolor_r14b(
            full_png, pdf_path, page_wh, bounds)
    cropped, crop_box = crop_to_board(out_png, bounds)

    png_path = work_dir / f"{board_label}-{view}.png"
    if png_path.exists():
        if png_path.read_bytes() != cropped:
            _fail(f"anti-overwrite: {png_path.name} exists with different "
                  "bytes")
    else:
        png_path.write_bytes(cropped)

    # determinism self-check: re-run the deterministic tail of the chain
    # (raster -> [recolor] -> bounds -> crop) and compare bytes
    full_png2, page_wh2 = compose_raster(pdf_path)
    bounds2 = png_board_pixel_bounds(full_png2)
    out_png2 = full_png2
    if recolor:
        _, out_png2 = apply_recolor_r14b(full_png2, pdf_path, page_wh2,
                                         bounds2)
    cropped2, crop_box2 = crop_to_board(out_png2, bounds2)
    det = (cropped2 == cropped and bounds2 == bounds
           and crop_box2 == crop_box)
    if not det:
        _fail(f"determinism self-check failed for {png_path.name}")

    sidecars = sorted(p.name for p in work_dir.glob("*.kicad_prl"))
    evidence = {
        "artifact": "render-reproduce-evidence",
        "declared_date": DECLARED_DATE,
        "board": {"label": board_label,
                  "source_file_name": board_src.name,
                  "source_sha256": sha256_file_local(board_src),
                  "work_copy": board_copy.name,
                  "work_copy_sha256": board_sha},
        "view": view,
        "instrument": {
            "kicad_cli_basename": cli.name,
            "kicad_cli_version": ver,
            "raster_dpi": RASTER_DPI,
            "compose_margin_pt": COMPOSE_MARGIN_PT,
            "crop_margin_px": CROP_MARGIN_PX,
            "pipeline": ("kicad-cli pcb export pdf --mode-single "
                         "--scale 1 --check-zones --drill-shape-opt 2 "
                         "[--mirror] -> fitz 40pt compose -> dpi640 "
                         "rasterize -> row-background board bounds -> "
                         "+120px crop"),
        },
        "export_command": cmd_rec["command"],
        "layers": cmd_rec["layers"],
        "mirror": cmd_rec["mirror"],
        "pdf": {"file": pdf_path.name,
                "pdf_sha256_run_local": pdf_sha,
                "cross_run_assertion": "none (kicad-cli PDF bytes are not "
                                       "cross-run deterministic; raster is)"},
        "full_page_wh": page_wh,
        "board_px_bounds": bounds,
        "crop_box": crop_box,
        "recolor_r14b": recolor_stats,
        "kicad_prl_sidecars_in_workdir": sidecars,
        "determinism_rerun_byte_identical": det,
        "output_png": {"file": png_path.name,
                       "sha256": sha256_bytes(cropped),
                       "bytes": len(cropped)},
    }
    ev_path = work_dir / f"{board_label}-{view}.render-evidence.json"
    ev_bytes = canonical_json_bytes(evidence)
    if ev_path.exists():
        if ev_path.read_bytes() != ev_bytes:
            _fail(f"anti-overwrite: {ev_path.name} exists with different "
                  "bytes (render evidence should be run-deterministic "
                  "given identical raster; PDF sha is the only run-local "
                  "field and it lives under pdf_sha256_run_local)")
    else:
        ev_path.write_bytes(ev_bytes)
    return evidence


def sha256_file_local(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--board", required=True, help="input .kicad_pcb")
    ap.add_argument("--label", default=None,
                    help="board label for output names (default: stem)")
    ap.add_argument("--views", default="top,bottom",
                    help="comma-separated subset of top,bottom")
    ap.add_argument("--out-dir", required=True, help="run work dir")
    ap.add_argument("--kicad-cli", default=None)
    ap.add_argument("--expect-version", default=None,
                    help="fail if kicad-cli version string lacks this")
    ap.add_argument("--timeout-s", type=int, default=1200)
    ap.add_argument("--recolor-r14b", action="store_true",
                    help="apply the optional r14b bottom-view white "
                         "disambiguation recolor (see color_legend.md)")
    args = ap.parse_args()

    board_src = Path(args.board)
    if not board_src.exists():
        _fail(f"board not found: {board_src}")
    label = args.label or board_src.stem
    views = tuple(v.strip() for v in args.views.split(",") if v.strip())
    for v in views:
        if v not in VIEWS:
            _fail(f"unknown view {v!r}; choose from {VIEWS}")
    cli = locate_kicad_cli(args.kicad_cli)

    summary = []
    for view in views:
        ev = render_view(cli, board_src, Path(args.out_dir), view, label,
                         args.recolor_r14b, args.timeout_s,
                         args.expect_version)
        summary.append({
            "view": view,
            "png": ev["output_png"]["file"],
            "png_sha256": ev["output_png"]["sha256"],
            "board_px_bounds": [ev["board_px_bounds"][k]
                                for k in ("x0", "y0", "x1", "y1")],
            "kicad_prl_sidecars_in_workdir":
                ev["kicad_prl_sidecars_in_workdir"],
            "determinism_rerun_byte_identical":
                ev["determinism_rerun_byte_identical"],
        })
        print(f"[render-reproduce] {label}-{view}: png sha256="
              f"{ev['output_png']['sha256'][:16]}… bounds="
              f"{[ev['board_px_bounds'][k] for k in ('x0','y0','x1','y1')]} "
              f"det_rerun={ev['determinism_rerun_byte_identical']}")
    print(f"[render-reproduce] done: {len(summary)} view(s) in "
          f"{args.out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
