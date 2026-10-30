#!/usr/bin/env python
"""run_example_chain.py — minimal deterministic example chain
(render -> blind-read input format -> rubric classification).

PAPER-P2-3 artifact package, render/example/. Walks the deterministic
skeleton of the evaluation methodology end to end WITHOUT any model call:

  step R  render       reproduce two instrument views (top/bottom) of one
                       open-source corpus board with the fitz pipeline
                       (render_reproduce.py; kicad-cli required)
  step B  blind-read   emit the reader-input manifest in the exact
                       blind-read input/output contract used by the
                       evaluation rounds (one image per reader instance;
                       reader-raw JSON schema with the five-key flag
                       projection + location_evidence), then fill a DEMO
                       reader-raw document with SYNTHETIC flags (hand
                       written, clearly marked, NOT model output, NOT the
                       frozen readings of any dev-repo round)
  step C  rubric       classify the demo flags with the shipped abstention
                       rubric (wordlists + priority adjudication algorithm)
                       and fail closed against preregistered expected
                       families

The board defaults to the PCBBenchmarks CC-BY-SA subset board bm1 from the
dev-repo corpus (datasets/pcbbenchmarks-r1/raw/bm1/bm1.routed.kicad_pcb).
The board is COPIED into the run directory before rendering (kicad-cli
writes a .kicad_prl sidecar next to its input; never render in place) and
the dataset tree is never written.

Determinism: every produced file except the per-view PDF evidence is
byte-deterministic (no wall-clock, no absolute paths, canonical JSON).
The script re-runs the deterministic tail of the render chain internally
and, via `--compare DIR1 DIR2`, compares two independent runs file by file.
kicad-cli PDF bytes are recorded as run-local provenance and explicitly NOT
compared (preregistered determinism scope; see render_reproduce.py).

Usage:
  python run_example_chain.py --out-dir RUN_DIR [--board PATH]
                              [--kicad-cli PATH]
  python run_example_chain.py --compare RUN_DIR_1 RUN_DIR_2

License: Apache-2.0.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RENDER_DIR = HERE.parent
PKG_DIR = RENDER_DIR.parent
sys.path.insert(0, str(RENDER_DIR))
sys.path.insert(0, str(PKG_DIR / "rubric"))

import render_reproduce as rr  # noqa: E402
from abstain_classifier import classify  # noqa: E402

DECLARED_DATE = "2026-09-12"
DEFAULT_BOARD = (PKG_DIR.parents[1] / "datasets" / "pcbbenchmarks-r1"
                 / "raw" / "bm1" / "bm1.routed.kicad_pcb")

# deterministic (cross-run byte-compared) output set
DETERMINISTIC_FILES = (
    "bm1-top.png",
    "bm1-bottom.png",
    "reader-input-manifest.json",
    "demo_reader_raw.json",
    "rubric_classification.json",
    "chain_manifest.json",
)
# run-local provenance, recorded but NOT cross-run asserted
RUN_LOCAL_FILES = (
    "bm1-top.pdf",
    "bm1-bottom.pdf",
    "bm1-top.render-evidence.json",
    "bm1-bottom.render-evidence.json",
)

# ---------------------------------------------------------------------------
# SYNTHETIC demo flags (hand-written format examples; NOT model output, NOT
# any dev-repo round's frozen readings). Expected families are preregistered
# below and asserted fail-closed in step C. Texts intentionally exercise the
# priority adjudication: B-001 has contact wording but classifies as
# existence_blackdot (blackdot precedes contact); B-006 has a contact word in
# silk/text context and lands in the residual class.
# ---------------------------------------------------------------------------

DEMO_FLAGS_TOP = [
    {
        "flag_id": "EXAMPLE-B-001",
        "category": "other_advisory",
        "confidence": 0.2,
        "abstain": True,
        "frame_box_pct": [0.29, 0.44, 0.37, 0.54],
        "location_evidence": (
            "图幅中下部偏左（约 x0.32,y0.48）一处孤立黑色实心圆点，全图仅此"
            "一处；该黑点与邻近焊盘环带是否接触无法分辨，黑点性质不明。"),
        "expected_family": "existence_blackdot",
    },
    {
        "flag_id": "EXAMPLE-B-002",
        "category": "other_advisory",
        "confidence": 0.3,
        "abstain": True,
        "frame_box_pct": [0.5, 0.55, 0.62, 0.66],
        "location_evidence": (
            "两相邻焊盘轮廓与走线端点（图幅中部约 x0.55,y0.60 一带）是否"
            "真实接触无法负责任地区分。"),
        "expected_family": "contact",
    },
    {
        "flag_id": "EXAMPLE-B-003",
        "category": "other_advisory",
        "confidence": 0.25,
        "abstain": True,
        "frame_box_pct": [0.65, 0.25, 0.76, 0.36],
        "location_evidence": (
            "图幅右侧板缘附近（约 x0.70,y0.30）一处异常反光区域，其性质"
            "不明，无法排除为关注现象。"),
        "expected_family": "existence_other",
    },
    {
        "flag_id": "EXAMPLE-B-004",
        "category": "other_advisory",
        "confidence": 0.2,
        "abstain": True,
        "frame_box_pct": [0.4, 0.47, 0.51, 0.57],
        "location_evidence": (
            "图幅左下（约 x0.45,y0.52）一段可疑影线，其走向无法追踪确认。"),
        "expected_family": "existence_other",
    },
    {
        "flag_id": "EXAMPLE-B-005",
        "category": "other_advisory",
        "confidence": 0.3,
        "abstain": True,
        "frame_box_pct": [0.75, 0.1, 0.86, 0.21],
        "location_evidence": (
            "图幅右上（约 x0.80,y0.15）一枚黄色图元无法归类，其设计含义"
            "无法从图面判断，图层归属无法分辨。"),
        "expected_family": "semantic_confusion",
    },
    {
        "flag_id": "EXAMPLE-B-006",
        "category": "other_advisory",
        "confidence": 0.35,
        "abstain": True,
        "frame_box_pct": [0.2, 0.15, 0.32, 0.26],
        "location_evidence": (
            "顶部丝印文字与焊盘图形叠压（约 x0.25,y0.20 一带），字形辨读"
            "受阻。"),
        "expected_family": "other",
    },
    {
        "flag_id": "EXAMPLE-B-007",
        "category": "other_advisory",
        "confidence": 0.4,
        "abstain": True,
        "frame_box_pct": [0.05, 0.8, 0.16, 0.91],
        "location_evidence": (
            "图幅左下角（约 x0.10,y0.85）整体观感异常，无具体可指认对象。"),
        "expected_family": "other",
    },
]

DEMO_FLAGS_BOTTOM = [
    {
        "flag_id": "EXAMPLE-B-008",
        "category": "other_advisory",
        "confidence": 0.2,
        "abstain": True,
        "frame_box_pct": [0.55, 0.65, 0.66, 0.76],
        "location_evidence": (
            "板内空区（约 x0.60,y0.70）一处小黑点，全图仅此一处，存在性"
            "不明。"),
        "expected_family": "existence_blackdot",
    },
]


def _fail(msg: str) -> None:
    raise SystemExit(f"[example-chain] FAIL: {msg}")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json_bytes(obj) -> bytes:
    return (json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=1)
            + "\n").encode("utf-8")


def write_guarded(path: Path, data: bytes) -> None:
    if path.exists():
        if path.read_bytes() != data:
            _fail(f"anti-overwrite: {path.name} exists with different bytes")
        return
    path.write_bytes(data)


# ---------------------------------------------------------------------------
# steps
# ---------------------------------------------------------------------------


def step_render(board: Path, out_dir: Path, kicad_cli, expect_version,
                timeout_s: int) -> dict:
    """Step R: reproduce both views via the standalone fitz pipeline."""
    ev = {}
    for view in ("top", "bottom"):
        ev[view] = rr.render_view(
            rr.locate_kicad_cli(kicad_cli), board, out_dir, view, "bm1",
            False, timeout_s, expect_version)
        png = out_dir / f"bm1-{view}.png"
        print(f"[example-chain] R render {view}: sha256="
              f"{sha256_bytes(png.read_bytes())[:16]}…")
    return ev


def step_blind_read_format(out_dir: Path, render_ev: dict) -> tuple:
    """Step B: reader-input manifest (the blind-read input contract) + a
    DEMO reader-raw document filled with synthetic flags."""
    manifest = {
        "artifact": "reader-input-manifest",
        "declared_date": DECLARED_DATE,
        "purpose": (
            "blind-read input contract: one reader instance receives exactly "
            "one rendered PNG plus dispatch instructions; zero GT, zero "
            "expected-defect hints, zero prior readings"),
        "tool_rule_v1_2": (
            "readers may only view the original image with a plain Read/"
            "view operation (repeatable); any programmatic image processing "
            "(crop/zoom/pixel analysis/derived images) is forbidden — "
            "tool behavior is pinned (protocol lineage v1.2, inherited by "
            "evaluation-protocol-v2 §0.3)"),
        "reader_id": "demo-reader-r1",
        "per_image": [
            {"image": f"bm1-{view}.png",
             "sha256": sha256_bytes(
                 (out_dir / f"bm1-{view}.png").read_bytes())}
            for view in ("top", "bottom")
        ],
        "output_format": (
            "reader-raw JSON: {reader_id, per_image:[{image, flags:["
            "{flag_id, category, confidence, abstain, frame_box_pct, "
            "location_evidence}]}], reading_notes}; five-key projection "
            "flag_id/category/confidence/abstain/frame_box_pct plus "
            "location_evidence free text; frame_box_pct is the box in "
            "fractions of the full image frame [x0,y0,x1,y1]"),
        "render_instrument": {
            "pipeline": render_ev["top"]["instrument"]["pipeline"],
            "raster_dpi": rr.RASTER_DPI,
            "compose_margin_pt": rr.COMPOSE_MARGIN_PT,
            "crop_margin_px": rr.CROP_MARGIN_PX,
            "kicad_cli_version": render_ev["top"]["instrument"]
            ["kicad_cli_version"],
        },
    }
    demo_raw = {
        "artifact": "demo_reader_raw",
        "declared_date": DECLARED_DATE,
        "synthetic": True,
        "synthetic_note": (
            "SYNTHETIC format demonstration: every flag below is a "
            "hand-written example constructed to exercise the rubric's "
            "priority adjudication. This document is NOT model output and "
            "NOT the frozen reading of any evaluation round; frozen reader "
            "readings are not redistributed with this package."),
        "reader_id": "demo-reader-r1",
        "per_image": [
            {"image": "bm1-top.png",
             "flags": [{k: fl[k] for k in ("flag_id", "category",
                                           "confidence", "abstain",
                                           "frame_box_pct",
                                           "location_evidence")}
                       for fl in DEMO_FLAGS_TOP]},
            {"image": "bm1-bottom.png",
             "flags": [{k: fl[k] for k in ("flag_id", "category",
                                           "confidence", "abstain",
                                           "frame_box_pct",
                                           "location_evidence")}
                       for fl in DEMO_FLAGS_BOTTOM]},
        ],
        "reading_notes": (
            "DEMO (synthetic): reading notes would here describe the "
            "independent judgment basis; see the shipped evaluation "
            "protocols for the blind-read discipline (protocol v1 §4 "
            "preregistration; v2 P2-2 reader blindness)."),
    }
    m_path = out_dir / "reader-input-manifest.json"
    d_path = out_dir / "demo_reader_raw.json"
    write_guarded(m_path, canonical_json_bytes(manifest))
    write_guarded(d_path, canonical_json_bytes(demo_raw))
    print(f"[example-chain] B blind-read format: manifest + demo reader-raw "
          f"({len(DEMO_FLAGS_TOP) + len(DEMO_FLAGS_BOTTOM)} synthetic flags)")
    return m_path, d_path


def step_rubric_classify(out_dir: Path, rubric_path: Path) -> Path:
    """Step C: classify the demo flags; fail closed on any family mismatch."""
    rubric_check = None
    if rubric_path.exists():
        from abstain_classifier import verify_rubric_json
        rubric_check = verify_rubric_json(rubric_path)
    results = []
    by_family = {}
    for fl in DEMO_FLAGS_TOP + DEMO_FLAGS_BOTTOM:
        family, hits = classify(fl["location_evidence"])
        ok = family == fl["expected_family"]
        if not ok:
            _fail(f"rubric classification mismatch: {fl['flag_id']} "
                  f"got={family} expected={fl['expected_family']}")
        by_family[family] = by_family.get(family, 0) + 1
        results.append({
            "flag_id": fl["flag_id"],
            "family": family,
            "expected_family": fl["expected_family"],
            "match": True,
            "matched": hits,
        })
    doc = {
        "artifact": "rubric-classification-demo",
        "declared_date": DECLARED_DATE,
        "input": "demo_reader_raw.json (synthetic flags)",
        "rubric_json": rubric_path.name,
        "rubric_json_sha256": (sha256_bytes(rubric_path.read_bytes())
                               if rubric_path.exists() else None),
        "keyword_tables_vs_classifier": (
            "equal" if rubric_check else "rubric JSON not found next to "
            "package; classifier built-in constants used"),
        "priority_as_implemented": list(
            __import__("abstain_classifier").PRIORITY_AS_IMPLEMENTED),
        "results": results,
        "summary": {"total_flags": len(results),
                    "all_match_expected": True,
                    "by_family": by_family},
    }
    c_path = out_dir / "rubric_classification.json"
    write_guarded(c_path, canonical_json_bytes(doc))
    print(f"[example-chain] C rubric classify: {len(results)}/{len(results)} "
          f"flags match expected families; by_family={by_family}")
    return c_path


def build_chain_manifest(out_dir: Path, board: Path, render_ev: dict,
                         rubric_path: Path) -> Path:
    """Deterministic end-to-end manifest (no wall-clock, no absolute paths)."""
    manifest = {
        "artifact": "paper2-protocol-example-chain-manifest",
        "declared_date": DECLARED_DATE,
        "chain": ["render", "blind_read_format", "rubric_classify"],
        "model_calls": 0,
        "board": {
            "label": "bm1",
            "source_file_name": board.name,
            "source_sha256": sha256_bytes(board.read_bytes()),
            "provenance": (
                "PCBBenchmarks CC-BY-SA subset board bm1 (Arduino-Mega-like "
                "benchmark); dev-repo corpus path "
                "datasets/pcbbenchmarks-r1/raw/bm1/bm1.routed.kicad_pcb; "
                "upstream license CC-BY-SA (attribution Arduino; see "
                "bm1.license.txt in the source corpus)"),
        },
        "steps": {
            "render": {
                "views": ["top", "bottom"],
                "png_sha256": {
                    v: sha256_bytes(
                        (out_dir / f"bm1-{v}.png").read_bytes())
                    for v in ("top", "bottom")},
                "board_px_bounds": {
                    v: [render_ev[v]["board_px_bounds"][k]
                        for k in ("x0", "y0", "x1", "y1")]
                    for v in ("top", "bottom")},
                "crop_box": {v: render_ev[v]["crop_box"]
                             for v in ("top", "bottom")},
                "instrument": render_ev["top"]["instrument"],
                "determinism_scope": (
                    "raster onward byte-deterministic; kicad-cli PDF bytes "
                    "are run-local provenance (see render-evidence files)"),
            },
            "blind_read_format": {
                "reader_input_manifest_sha256": sha256_bytes(
                    (out_dir / "reader-input-manifest.json").read_bytes()),
                "demo_reader_raw_sha256": sha256_bytes(
                    (out_dir / "demo_reader_raw.json").read_bytes()),
                "synthetic_flags": True,
            },
            "rubric_classify": {
                "rubric_json_sha256": (sha256_bytes(rubric_path.read_bytes())
                                       if rubric_path.exists() else None),
                "classification_sha256": sha256_bytes(
                    (out_dir / "rubric_classification.json").read_bytes()),
                "all_match_expected": True,
            },
        },
        "zero_write_declarations": [
            "dataset tree not written (board rendered from an in-run copy)",
            "kicad-cli .kicad_prl sidecars confined to the run work dir "
            "(sidecar listing per view in the render-evidence files)",
        ],
    }
    p = out_dir / "chain_manifest.json"
    write_guarded(p, canonical_json_bytes(manifest))
    print(f"[example-chain] chain manifest: sha256="
          f"{sha256_bytes(p.read_bytes())[:16]}…")
    return p


def run_chain(args) -> int:
    out_dir = Path(args.out_dir)
    board = Path(args.board) if args.board else DEFAULT_BOARD
    if not board.exists():
        _fail(f"board not found: {board} (pass --board; the default "
              "assumes the dev-repo corpus layout)")
    rubric_path = PKG_DIR / "rubric" / "abstain-rubric-r13-r16.json"
    render_ev = step_render(board, out_dir, args.kicad_cli,
                            args.expect_version, args.timeout_s)
    step_blind_read_format(out_dir, render_ev)
    step_rubric_classify(out_dir, rubric_path)
    build_chain_manifest(out_dir, board, render_ev, rubric_path)
    print(f"[example-chain] done: {out_dir}")
    return 0


def compare_runs(dir1: Path, dir2: Path) -> int:
    """Byte-compare the deterministic output set of two independent runs."""
    all_equal = True
    print(f"[example-chain] compare deterministic set: {dir1} vs {dir2}")
    for name in DETERMINISTIC_FILES:
        b1 = (dir1 / name).read_bytes()
        b2 = (dir2 / name).read_bytes()
        equal = b1 == b2
        all_equal &= equal
        print(f"  {name:<32} {'IDENTICAL' if equal else 'DIFFER'} "
              f"sha256={sha256_bytes(b1)[:16]}…")
    for name in RUN_LOCAL_FILES:
        b1 = (dir1 / name).read_bytes()
        b2 = (dir2 / name).read_bytes()
        print(f"  {name:<32} run-local (not asserted) "
              f"equal={b1 == b2}")
    print(f"[example-chain] deterministic set byte-identical: {all_equal}")
    return 0 if all_equal else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", default=None)
    ap.add_argument("--board", default=None)
    ap.add_argument("--kicad-cli", default=None)
    ap.add_argument("--expect-version", default=None)
    ap.add_argument("--timeout-s", type=int, default=1200)
    ap.add_argument("--compare", nargs=2, metavar=("RUN1", "RUN2"))
    args = ap.parse_args()
    if args.compare:
        return compare_runs(Path(args.compare[0]), Path(args.compare[1]))
    if not args.out_dir:
        _fail("--out-dir required (or use --compare RUN1 RUN2)")
    return run_chain(args)


if __name__ == "__main__":
    sys.exit(main())
